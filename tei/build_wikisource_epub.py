#!/usr/bin/env python3
"""Convert a Wikisource EPUB anthology to standalone Bookstacks TEI P5."""

from __future__ import annotations

import argparse
import re
import zipfile
from datetime import date
from pathlib import Path, PurePosixPath

from lxml import etree


TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
XHTML_NS = "http://www.w3.org/1999/xhtml"
CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
OPF_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"

NS = {"x": XHTML_NS, "opf": OPF_NS, "dc": DC_NS}
ROMAN_ONLY = re.compile(r"^[IVXLCDM]+$", re.IGNORECASE)
SECTION_HEAD = re.compile(r"^([IVXLCDM]+)[.\u2014\u2013-]+\s*(.+)$", re.IGNORECASE)


def tei(name: str, **attributes: str) -> etree._Element:
    element = etree.Element(f"{{{TEI_NS}}}{name}")
    for key, value in attributes.items():
        if key == "xml_id":
            element.set(f"{{{XML_NS}}}id", value)
        elif key == "xml_lang":
            element.set(f"{{{XML_NS}}}lang", value)
        else:
            element.set(key, value)
    return element


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip()


def element_text(element: etree._Element) -> str:
    return clean_text("".join(element.itertext()))


def append_text(target: etree._Element, value: str | None) -> None:
    if not value:
        return
    value = re.sub(r"\s+", " ", value.replace("\u00a0", " "))
    if len(target):
        target[-1].tail = (target[-1].tail or "") + value
    else:
        target.text = (target.text or "") + value


def class_tokens(element: etree._Element) -> set[str]:
    return set(element.get("class", "").split())


def is_page_number(element: etree._Element) -> bool:
    return bool(class_tokens(element).intersection({"pagenum", "ws-pagenum"}))


def convert_inline(source: etree._Element, target: etree._Element) -> None:
    append_text(target, source.text)
    for child in source:
        local = etree.QName(child).localname.lower()
        if is_page_number(child):
            append_text(target, child.tail)
            continue

        if local in {"i", "em"}:
            converted = tei("hi", rend="italic")
            target.append(converted)
            convert_inline(child, converted)
        elif local in {"b", "strong"}:
            converted = tei("hi", rend="bold")
            target.append(converted)
            convert_inline(child, converted)
        elif local == "sup":
            converted = tei("hi", rend="superscript")
            target.append(converted)
            convert_inline(child, converted)
        elif local == "br":
            target.append(tei("lb"))
        else:
            convert_inline(child, target)
        append_text(target, child.tail)


def trim_mixed_content(element: etree._Element) -> None:
    if element.text:
        element.text = re.sub(r"\s+", " ", element.text)
        if element.text.startswith(" "):
            element.text = element.text[1:]
    for child in element:
        trim_mixed_content(child)
        if child.tail:
            child.tail = re.sub(r"\s+", " ", child.tail)
    if len(element):
        last = element[-1]
        if last.tail:
            last.tail = last.tail.rstrip()
    elif element.text:
        element.text = element.text.rstrip()


def ancestor_classes(element: etree._Element) -> set[str]:
    classes: set[str] = set()
    for ancestor in element.iterancestors():
        classes.update(class_tokens(ancestor))
    return classes


def paragraph_rendition(source: etree._Element) -> str | None:
    classes = ancestor_classes(source) | class_tokens(source)
    if "wst-right" in classes:
        return "right"
    if "wst-center" in classes:
        return "center"
    if classes.intersection({"wst-block-center", "wst-border", "wst-frame"}):
        return "letter"
    return None


def normalize_drop_initial(source: etree._Element, paragraph: etree._Element) -> None:
    has_drop_initial = source.xpath(
        ".//*[contains(concat(' ', normalize-space(@class), ' '), ' dropinitial ')]",
        namespaces=NS,
    )
    if not has_drop_initial or not paragraph.text:
        return
    text = paragraph.text
    text = re.sub(
        r'^([\u201c\u2018"]?)([A-Z]) ([A-Z]{2,})(\b)',
        lambda match: f"{match.group(1)}{match.group(2)} {match.group(3).lower()}{match.group(4)}",
        text,
        count=1,
    )
    text = re.sub(
        r'^([\u201c\u2018"]?)([A-Z]{2,})(\b)',
        lambda match: f"{match.group(1)}{match.group(2).title()}{match.group(3)}",
        text,
        count=1,
    )
    paragraph.text = text


def convert_paragraph(source: etree._Element, paragraph_id: str) -> etree._Element:
    attributes = {"xml_id": paragraph_id}
    rendition = paragraph_rendition(source)
    if rendition:
        attributes["rend"] = rendition
    paragraph = tei("p", **attributes)
    convert_inline(source, paragraph)
    trim_mixed_content(paragraph)
    while len(paragraph) and etree.QName(paragraph[0]).localname == "lb" and not paragraph.text:
        leading_break = paragraph[0]
        paragraph.text = leading_break.tail or ""
        paragraph.remove(leading_break)
    normalize_drop_initial(source, paragraph)
    return paragraph


def read_xml(archive: zipfile.ZipFile, path: str) -> etree._Element:
    return etree.fromstring(archive.read(path), parser=etree.XMLParser(recover=True))


def resolve_epub(archive: zipfile.ZipFile) -> tuple[str, etree._Element, dict[str, str], list[str]]:
    container = read_xml(archive, "META-INF/container.xml")
    opf_path = container.xpath(
        "string(//c:rootfile[1]/@full-path)", namespaces={"c": CONTAINER_NS}
    )
    if not opf_path:
        raise ValueError("EPUB container does not identify an OPF package")

    package = read_xml(archive, opf_path)
    opf_dir = PurePosixPath(opf_path).parent
    manifest = {
        item.get("id", ""): str(opf_dir / item.get("href", ""))
        for item in package.xpath("//opf:manifest/opf:item", namespaces=NS)
    }
    spine = [
        manifest.get(item.get("idref", ""), "")
        for item in package.xpath("//opf:spine/opf:itemref", namespaces=NS)
    ]
    return opf_path, package, manifest, [path for path in spine if path]


def metadata_value(package: etree._Element, expression: str) -> str:
    return clean_text(package.xpath(f"string({expression})", namespaces=NS))


def build_header(package: etree._Element, text_id: str) -> etree._Element:
    today = date.today().isoformat()
    source_title = metadata_value(package, "//dc:title[1]") or "His Last Bow"
    source_url = metadata_value(package, "//dc:source[1]")
    source_modified = metadata_value(
        package, "//opf:meta[@property='dcterms:modified'][1]"
    )

    header = tei("teiHeader", xml_lang="en")
    file_desc = tei("fileDesc")
    title_stmt = tei("titleStmt")

    title = tei("title", type="main", xml_lang="en")
    title.text = "His Last Bow: Some Later Reminiscences of Sherlock Holmes"
    author = tei("author")
    author.text = "Arthur Conan Doyle"

    source_resp = tei("respStmt", xml_id="wikisource-transcription")
    source_role = tei("resp")
    source_role.text = "electronic transcription and EPUB publication"
    source_name = tei("name")
    source_name.text = "Wikisource contributors"
    source_resp.extend((source_role, source_name))

    bookstacks_resp = tei("respStmt", xml_id="bookstacks-encoding")
    bookstacks_role = tei("resp")
    bookstacks_role.text = "Wikisource XHTML-to-TEI P5 conversion and structural encoding"
    bookstacks_name = tei("name")
    bookstacks_name.text = "Bookstacks project"
    bookstacks_resp.extend((bookstacks_role, bookstacks_name))
    title_stmt.extend((title, author, source_resp, bookstacks_resp))

    edition_stmt = tei("editionStmt")
    edition = tei("edition", n="1.1")
    edition.text = "Bookstacks TEI edition based on the Wikisource EPUB export"
    edition_stmt.append(edition)

    publication_stmt = tei("publicationStmt")
    publisher = tei("publisher")
    publisher.text = "Bookstacks project"
    publication_date = tei("date", when=today)
    publication_date.text = date.today().strftime("%d %B %Y")
    local_id = tei("idno", type="local")
    local_id.text = text_id
    availability = tei("availability", status="free")
    cc = tei("licence", target="https://creativecommons.org/licenses/by-sa/3.0/")
    cc.text = "Wikisource supplies its transcription under the Creative Commons Attribution-ShareAlike 3.0 license."
    gfdl = tei("licence", target="https://www.gnu.org/copyleft/fdl.html")
    gfdl.text = "Wikisource also supplies the transcription under the GNU Free Documentation License."
    availability.extend((cc, gfdl))
    publication_stmt.extend((publisher, publication_date, local_id, availability))

    source_desc = tei("sourceDesc")
    bibliography = tei("bibl")
    bibl_title = tei("title")
    bibl_title.text = source_title
    bibl_author = tei("author")
    bibl_author.text = "Arthur Conan Doyle"
    bibl_publisher = tei("publisher")
    bibl_publisher.text = "Wikisource"
    bibl_date = tei("date", when=source_modified[:10] if source_modified else today)
    bibl_date.text = source_modified[:10] if source_modified else today
    bibl_id = tei("idno", type="Wikisource")
    bibl_id.text = source_url
    bibl_ref = tei("ref", target=source_url)
    bibl_ref.text = source_url
    bibliography.extend(
        (bibl_title, bibl_author, bibl_publisher, bibl_date, bibl_id, bibl_ref)
    )
    source_desc.append(bibliography)
    file_desc.extend((title_stmt, edition_stmt, publication_stmt, source_desc))

    encoding_desc = tei("encodingDesc")
    project_desc = tei("projectDesc")
    project_note = tei("p")
    project_note.text = (
        "Converted from the Wikisource EPUB XHTML spine. Source navigation, "
        "page-number markers, title-page ornament, cover art, publisher devices, "
        "and license boilerplate are omitted. The preface, all eight stories, "
        "internal story sections, paragraphs, centered display text, inline "
        "typography, and line breaks are retained."
    )
    project_desc.append(project_note)
    encoding_desc.append(project_desc)

    profile_desc = tei("profileDesc")
    lang_usage = tei("langUsage")
    language = tei("language", ident="en")
    language.text = "English"
    lang_usage.append(language)
    profile_desc.append(lang_usage)

    revision_desc = tei("revisionDesc")
    change = tei("change", when=today, who="#bookstacks-encoding")
    change.text = (
        "Replaced the incomplete seven-story Gutenberg source with the complete "
        "eight-story Wikisource EPUB and converted it to standalone TEI P5."
    )
    revision_desc.append(change)
    header.extend((file_desc, encoding_desc, profile_desc, revision_desc))
    return header


def nav_titles(
    archive: zipfile.ZipFile, manifest: dict[str, str]
) -> dict[str, str]:
    nav_path = manifest.get("nav")
    if not nav_path:
        return {}
    nav = read_xml(archive, nav_path)
    titles: dict[str, str] = {}
    for anchor in nav.xpath("//x:nav//x:a[@href]", namespaces=NS):
        basename = PurePosixPath(anchor.get("href", "").split("#", 1)[0]).name
        if basename:
            titles[basename] = element_text(anchor)
    return titles


def find_preface(source: etree._Element) -> tuple[etree._Element, etree._Element | None]:
    paragraphs = source.xpath("//x:body//x:p", namespaces=NS)
    for index, paragraph in enumerate(paragraphs):
        if "friends of mr. sherlock holmes" not in element_text(paragraph).lower():
            continue
        signature = next(
            (
                candidate
                for candidate in paragraphs[index + 1 : index + 6]
                if "john h. watson" in element_text(candidate).lower()
            ),
            None,
        )
        return paragraph, signature
    raise ValueError("Could not locate the source preface")


def is_hidden_navigation(paragraph: etree._Element) -> bool:
    if "Layout 2" == element_text(paragraph):
        return True
    return any("wst-header-mainblock" in class_tokens(node) for node in paragraph.iterancestors())


def section_heading_text(paragraph: etree._Element) -> str | None:
    if not paragraph.xpath(".//x:span[contains(concat(' ', normalize-space(@class), ' '), ' wst-asc ')]", namespaces=NS):
        return None
    value = element_text(paragraph)
    numbered = SECTION_HEAD.match(value)
    if numbered:
        return clean_text(numbered.group(2))
    part = re.fullmatch(r"PART\s+([IVXLCDM]+)", value, re.IGNORECASE)
    if part:
        return f"Part {part.group(1).upper()}"
    return None


def title_case_heading(value: str) -> str:
    words = value.title().split()
    minor_words = {"A", "An", "And", "At", "For", "In", "Of", "On", "The", "To"}
    for index in range(1, len(words)):
        if words[index] in minor_words:
            words[index] = words[index].lower()
    return " ".join(words)


def build_document(epub_path: Path, text_id: str) -> etree._ElementTree:
    paragraph_number = 0

    def next_paragraph_id() -> str:
        nonlocal paragraph_number
        paragraph_number += 1
        return f"eng-p-{paragraph_number:06d}"

    root = tei("TEI", xml_id=text_id)
    root.append(build_header_from_source(epub_path, text_id))
    text = tei("text", xml_lang="en")
    front = tei("front")
    body = tei("body")
    edition = tei("div", type="edition", xml_id=f"{text_id}-eng-text")

    with zipfile.ZipFile(epub_path) as archive:
        _, package, manifest, spine = resolve_epub(archive)
        titles = nav_titles(archive, manifest)
        front_paths = [path for path in spine if PurePosixPath(path).name.startswith("c0_")]
        story_paths = [
            path
            for path in spine
            if re.match(r"c[1-8]_", PurePosixPath(path).name)
        ]
        if len(story_paths) != 8:
            raise ValueError(f"Expected eight Wikisource story files; found {len(story_paths)}")

        if front_paths:
            source_front = read_xml(archive, front_paths[0])
            preface_source, signature_source = find_preface(source_front)
            preface = tei("div", type="preface", n="1", xml_id="eng-front-01-preface")
            preface_head = tei("head")
            preface_head.text = "Preface"
            preface.append(preface_head)
            preface.append(convert_paragraph(preface_source, next_paragraph_id()))
            if signature_source is not None:
                signature = convert_paragraph(signature_source, next_paragraph_id())
                signature.set("rend", "right")
                preface.append(signature)
            front.append(preface)

        for story_number, story_path in enumerate(story_paths, start=1):
            source = read_xml(archive, story_path)
            basename = PurePosixPath(story_path).name
            story_title = titles.get(basename) or metadata_value(
                source, "//x:title[1]"
            )
            if not story_title:
                raise ValueError(f"No story title found for {basename}")

            story_id = f"{text_id}-eng-text-chapter-{story_number:03d}"
            story = tei("div", type="chapter", n=str(story_number), xml_id=story_id)
            story_head = tei("head")
            story_head.text = story_title
            story.append(story_head)

            current_container = story
            section_number = 0
            body_started = False
            for source_paragraph in source.xpath("//x:body//x:p", namespaces=NS):
                paragraph_text = element_text(source_paragraph)
                if not paragraph_text or is_hidden_navigation(source_paragraph):
                    continue

                section_heading = section_heading_text(source_paragraph)
                if section_heading:
                    section_number += 1
                    section = tei(
                        "div",
                        type="section",
                        n=str(section_number),
                        xml_id=f"{story_id}-section-{section_number:03d}",
                    )
                    section_head = tei("head")
                    if section_heading.lower().startswith("part "):
                        section_head.text = section_heading
                    else:
                        section_head.text = (
                            f"{section_number}. {title_case_heading(section_heading)}"
                        )
                    section.append(section_head)
                    story.append(section)
                    current_container = section
                    continue

                has_small_caps = source_paragraph.xpath(
                    ".//x:span[contains(concat(' ', normalize-space(@class), ' '), ' wst-asc ')]",
                    namespaces=NS,
                )
                if not body_started and has_small_caps:
                    story_head.text = (
                        f"{story_title}: {title_case_heading(paragraph_text)}"
                    )
                    continue

                if not body_started:
                    normalized_title = re.sub(r"[^A-Z0-9]+", "", story_title.upper())
                    normalized_paragraph = re.sub(r"[^A-Z0-9]+", "", paragraph_text.upper())
                    if ROMAN_ONLY.fullmatch(paragraph_text) or normalized_paragraph == normalized_title:
                        continue

                body_started = True
                if paragraph_text.upper() == "THE END":
                    trailer = tei("trailer")
                    trailer.text = paragraph_text
                    current_container.append(trailer)
                    continue
                current_container.append(
                    convert_paragraph(source_paragraph, next_paragraph_id())
                )

            if not story.xpath(".//tei:p", namespaces={"tei": TEI_NS}):
                raise ValueError(f"Story {story_title!r} contains no converted paragraphs")
            edition.append(story)

    body.append(edition)
    text.extend((front, body))
    root.append(text)
    tree = etree.ElementTree(root)
    root.addprevious(
        etree.ProcessingInstruction(
            "xml-model",
            'href="../tei_all.rng" schematypens="http://relaxng.org/ns/structure/1.0"',
        )
    )
    return tree


def build_header_from_source(epub_path: Path, text_id: str) -> etree._Element:
    with zipfile.ZipFile(epub_path) as archive:
        _, package, _, _ = resolve_epub(archive)
        return build_header(package, text_id)


def validate(tree: etree._ElementTree, schema_path: Path) -> None:
    schema = etree.RelaxNG(etree.parse(str(schema_path)))
    if not schema.validate(tree):
        details = "\n".join(str(entry) for entry in schema.error_log)
        raise ValueError(f"Generated TEI failed Relax NG validation:\n{details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--text-id", required=True)
    args = parser.parse_args()

    document = build_document(args.source, args.text_id)
    validate(document, args.schema)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    document.write(
        str(args.output),
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=True,
    )
    print(f"Generated {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
