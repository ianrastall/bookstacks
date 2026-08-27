"""Convert supported Project Gutenberg prose EPUBs to standalone TEI P5."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path, PurePosixPath
import re
import sys
from zipfile import ZipFile

from lxml import etree


TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
XHTML = "http://www.w3.org/1999/xhtml"
OPF = "http://www.idpf.org/2007/opf"
DC = "http://purl.org/dc/elements/1.1/"
NS = {"opf": OPF, "dc": DC, "x": XHTML}

SUPPORTED_TEXTS = {
    "2142": {
        "groups": {"book": 0, "part": 0, "epilogue": 0},
        "chapters": 28,
        "unit_type": "chapter",
        "unit_heading_pattern": r"^(?:CHAPTER\s+)?[IVXLCDM]+(?:\.|\s+—)",
        "fronts": 0,
        "work_head": True,
    },
    "2450": {
        "groups": {"book": 0, "part": 0, "epilogue": 0},
        "chapters": 27,
        "unit_type": "chapter",
        "unit_heading_pattern": r"^(?:CHAPTER\s+)?[IVXLCDM]+(?:\.|\s+—)",
        "fronts": 0,
        "work_head": True,
    },
    "2637": {
        "groups": {"book": 0, "part": 0, "epilogue": 0},
        "chapters": 45,
        "unit_type": "chapter",
        "unit_heading_pattern": r"^(?:CHAPTER\s+)?[IVXLCDM]+(?:\.|\s+—)",
        "fronts": 0,
        "work_head": True,
    },
    "4761": {
        "groups": {"book": 0, "part": 0, "epilogue": 0},
        "chapters": 42,
        "unit_type": "chapter",
        "unit_heading_pattern": r"^(?:CHAPTER\s+)?[IVXLCDM]+\.?$",
        "fronts": 0,
        "work_head": True,
    },
    "2554": {
        "groups": {"book": 0, "part": 6, "epilogue": 1},
        "chapters": 41,
        "unit_type": "chapter",
        "unit_heading_pattern": r"^(?:CHAPTER\s+|[IVXLCDM]+\.?$)",
        "fronts": 1,
        "front_heading_prefixes": {
            "TRANSLATOR'S PREFACE": "translator-preface",
        },
    },
    "2638": {
        "groups": {"book": 0, "part": 4, "epilogue": 0},
        "chapters": 50,
        "unit_type": "chapter",
        "unit_heading_pattern": r"^[IVXLCDM]+\.?$",
        "fronts": 0,
        "section_paragraph_classes": ["center"],
        "sections": 1,
    },
    "28054": {
        "groups": {"book": 12, "part": 4, "epilogue": 1},
        "group_levels": {"part": 1, "book": 2, "epilogue": 1},
        "chapters": 96,
        "unit_type": "chapter",
        "fronts": 0,
        "backs": 1,
        "back_headings": {"FOOTNOTES": "notes"},
        "section_paragraph_classes": ["center"],
        "sections": 9,
    },
    "600": {
        "groups": {"book": 0, "part": 2, "epilogue": 0},
        "chapters": 21,
        "unit_type": "chapter",
        "unit_heading_pattern": r"^[IVXLCDM]+\.?$",
        "fronts": 1,
        "front_heading_prefixes": {
            "NOTES FROM THE UNDERGROUND": "authorial-note",
        },
    },
    "8117": {
        "groups": {"book": 0, "part": 3, "epilogue": 0},
        "chapters": 23,
        "unit_type": "chapter",
        "fronts": 0,
        "section_paragraph_classes": ["centered"],
        "sections": 102,
    },
    "98": {
        "groups": {"book": 3, "part": 0, "epilogue": 0},
        "chapters": 45,
        "unit_type": "chapter",
        "fronts": 0,
        "chapter_title_paragraph": None,
    },
    "1023": {
        "groups": {"book": 0, "part": 0, "epilogue": 0},
        "chapters": 67,
        "unit_type": "chapter",
        "fronts": 1,
        "chapter_title_paragraph": None,
    },
    "766": {
        "groups": {"book": 0, "part": 0, "epilogue": 0},
        "chapters": 64,
        "unit_type": "chapter",
        "fronts": 2,
        "chapter_title_paragraph": None,
    },
    "967": {
        "groups": {"book": 0, "part": 0, "epilogue": 0},
        "chapters": 65,
        "unit_type": "chapter",
        "fronts": 1,
        "chapter_title_paragraph": "pfirst",
    },
    "730": {
        "groups": {"book": 0, "part": 0, "epilogue": 0},
        "chapters": 53,
        "unit_type": "chapter",
        "fronts": 0,
        "chapter_title_paragraph": None,
    },
    "917": {
        "groups": {"book": 0, "part": 0, "epilogue": 0},
        "chapters": 82,
        "unit_type": "chapter",
        "fronts": 1,
        "chapter_title_paragraph": None,
    },
    "968": {
        "groups": {"book": 0, "part": 0, "epilogue": 0},
        "chapters": 54,
        "unit_type": "chapter",
        "fronts": 2,
        "chapter_title_paragraph": "any",
    },
    "24022": {
        "groups": {"book": 0, "part": 0, "epilogue": 0},
        "chapters": 5,
        "unit_type": "stave",
        "fronts": 2,
        "chapter_title_paragraph": None,
    },
    "1399": {
        "groups": {"book": 0, "part": 8, "epilogue": 0},
        "chapters": 239,
        "unit_type": "chapter",
        "fronts": 0,
        "chapter_title_paragraph": None,
    },
    "2600": {
        "groups": {"book": 15, "part": 0, "epilogue": 2},
        "chapters": 365,
        "unit_type": "chapter",
        "fronts": 0,
        "chapter_title_paragraph": None,
    },
}


def tei(name: str, **attributes: str) -> etree._Element:
    element = etree.Element(f"{{{TEI}}}{name}")
    for key, value in attributes.items():
        if key == "xml_id":
            element.set(f"{{{XML}}}id", value)
        elif key == "xml_lang":
            element.set(f"{{{XML}}}lang", value)
        else:
            element.set(key, value)
    return element


def normalized_text(element: etree._Element) -> str:
    return " ".join("".join(element.itertext()).split())


def append_text(parent: etree._Element, value: str | None) -> None:
    if not value:
        return
    if len(parent):
        parent[-1].tail = (parent[-1].tail or "") + value
    else:
        parent.text = (parent.text or "") + value


def convert_inline(source: etree._Element, target: etree._Element) -> None:
    append_text(target, source.text)
    for child in source:
        local = etree.QName(child).localname
        converted: etree._Element | None = None
        if local in {"i", "em"}:
            converted = tei("hi", rend="italic")
            convert_inline(child, converted)
        elif local in {"b", "strong"}:
            converted = tei("hi", rend="bold")
            convert_inline(child, converted)
        elif local in {"small", "big", "sup", "sub"}:
            converted = tei("hi", rend=local)
            convert_inline(child, converted)
        elif local == "br":
            converted = tei("lb")
        elif local == "span":
            converted = tei("seg")
            if "dropcap" in child.get("class", "").split():
                converted.set("rend", "dropcap")
            convert_inline(child, converted)
        elif local == "a":
            href = child.get("href")
            content = normalized_text(child)
            if content:
                converted = tei("ref")
                if href and not href.startswith("#"):
                    converted.set("target", href)
                convert_inline(child, converted)
        else:
            converted = tei("seg")
            converted.set("type", local)
            convert_inline(child, converted)

        if converted is not None:
            target.append(converted)
        tail = child.tail
        if "dropcap" in child.get("class", "").split() and tail:
            tail = tail.lstrip()
        append_text(target, tail)


def poem_lines(source: etree._Element) -> list[list[str]]:
    chunks: list[str] = []
    if source.text:
        chunks.append(source.text)
    for child in source:
        if etree.QName(child).localname == "br":
            chunks.append("\n")
        else:
            chunks.append("".join(child.itertext()))
        if child.tail:
            chunks.append(child.tail)
    raw_lines = "".join(chunks).replace("\xa0", " ").split("\n")
    stanzas: list[list[str]] = [[]]
    for raw_line in raw_lines:
        line = " ".join(raw_line.split())
        if line:
            stanzas[-1].append(line)
        elif stanzas[-1]:
            stanzas.append([])
    return [stanza for stanza in stanzas if stanza]


def convert_block(
    source: etree._Element,
    paragraph_number: int,
    note_number: int,
) -> tuple[etree._Element | None, int, int]:
    local = etree.QName(source).localname
    css_class = source.get("class", "")

    if local == "p" and "footnote" in css_class.split():
        note_number += 1
        text = normalized_text(source)
        note_type = "translation" if "TRANSLATOR" in text.upper() else "editorial"
        note = tei(
            "note",
            type=note_type,
            place="foot",
            xml_id=f"eng-note-{note_number:04d}",
        )
        note.text = text
        return note, paragraph_number, note_number

    if local == "p" and "poem" in css_class.split():
        outer = tei("lg", type="poem")
        for stanza_lines in poem_lines(source):
            stanza = tei("lg", type="stanza")
            for line_text in stanza_lines:
                line = tei("l")
                line.text = line_text
                stanza.append(line)
            outer.append(stanza)
        return (outer if len(outer) else None), paragraph_number, note_number

    if local == "p":
        if not normalized_text(source):
            return None, paragraph_number, note_number
        paragraph_number += 1
        paragraph = tei("p", xml_id=f"eng-p-{paragraph_number:06d}")
        rendition_classes = [
            class_name
            for class_name in css_class.split()
            if class_name in {"noindent", "letter", "right", "center", "centered", "p2"}
        ]
        if rendition_classes:
            paragraph.set("rend", " ".join(rendition_classes))
        convert_inline(source, paragraph)
        return paragraph, paragraph_number, note_number

    if local == "pre":
        if not normalized_text(source):
            return None, paragraph_number, note_number
        paragraph_number += 1
        paragraph = tei(
            "p", rend="preformatted", xml_id=f"eng-p-{paragraph_number:06d}"
        )
        lines = "".join(source.itertext()).splitlines()
        for index, line_text in enumerate(lines):
            if index:
                paragraph.append(tei("lb"))
            append_text(paragraph, line_text.rstrip())
        return paragraph, paragraph_number, note_number

    if local == "blockquote":
        quote = tei("quote")
        for child in source:
            converted, paragraph_number, note_number = convert_block(
                child, paragraph_number, note_number
            )
            if converted is not None:
                quote.append(converted)
        return quote, paragraph_number, note_number

    if local in {"ul", "ol"}:
        list_element = tei("list", type="ordered" if local == "ol" else "unordered")
        for child in source:
            if etree.QName(child).localname != "li":
                continue
            item = tei("item")
            convert_inline(child, item)
            list_element.append(item)
        return list_element, paragraph_number, note_number

    return None, paragraph_number, note_number


def get_epub_data(epub_path: Path) -> tuple[dict[str, str], list[tuple[str, bytes]]]:
    with ZipFile(epub_path) as archive:
        container = etree.fromstring(archive.read("META-INF/container.xml"))
        package_path = container.xpath(
            'string(//*[local-name()="rootfile"]/@full-path)'
        )
        package = etree.fromstring(archive.read(package_path))
        package_dir = PurePosixPath(package_path).parent
        manifest = {
            item.get("id"): (item.get("href"), item.get("media-type"))
            for item in package.xpath("//opf:manifest/opf:item", namespaces=NS)
        }
        spine = [
            manifest[item.get("idref")]
            for item in package.xpath("//opf:spine/opf:itemref", namespaces=NS)
        ]
        metadata = {
            "identifier": package.xpath("string(//dc:identifier[1])", namespaces=NS),
            "title": package.xpath("string(//dc:title[1])", namespaces=NS),
            "creator": package.xpath("string(//dc:creator[1])", namespaces=NS),
            "rights": package.xpath("string(//dc:rights[1])", namespaces=NS),
            "publication": package.xpath("string(//dc:date[1])", namespaces=NS),
            "conversion": package.xpath(
                "string(//dc:date[@opf:event='conversion'][1])", namespaces=NS
            ),
            "source": package.xpath("string(//dc:source[1])", namespaces=NS),
        }
        def contributor_names(role: str) -> list[str]:
            names: list[str] = []
            for contributor in package.xpath("//dc:contributor", namespaces=NS):
                contributor_role = contributor.get(f"{{{OPF}}}role") or contributor.get(
                    "role"
                )
                contributor_id = contributor.get("id")
                if contributor_id:
                    refined_role = package.xpath(
                        "string(//opf:meta[@property='role'][@refines=$target][1])",
                        namespaces=NS,
                        target=f"#{contributor_id}",
                    )
                    contributor_role = refined_role or contributor_role
                if contributor_role == role:
                    name = normalized_text(contributor)
                    if name:
                        names.append(name)
            return names

        metadata["translators"] = "|".join(contributor_names("trl"))
        metadata["illustrators"] = "|".join(contributor_names("ill"))
        documents = [
            (href, archive.read(str(package_dir / href)))
            for href, media_type in spine
            if media_type == "application/xhtml+xml"
        ]
    return metadata, documents


def gutenberg_number(metadata: dict[str, str]) -> str:
    return metadata["identifier"].rstrip("/").rsplit("/", 1)[-1]


def build_header(metadata: dict[str, str], text_id: str) -> etree._Element:
    header = tei("teiHeader", xml_lang="en")
    file_desc = tei("fileDesc")
    title_stmt = tei("titleStmt")
    title = tei("title", type="main", xml_lang="en")
    title.text = metadata["title"]
    title_stmt.append(title)
    author = tei("author")
    author.text = metadata["creator"]
    title_stmt.append(author)
    for translator_name in filter(None, metadata["translators"].split("|")):
        editor = tei("editor", role="translator")
        editor.text = translator_name
        title_stmt.append(editor)
    for illustrator_name in filter(None, metadata["illustrators"].split("|")):
        editor = tei("editor", role="illustrator")
        editor.text = illustrator_name
        title_stmt.append(editor)
    source_resp = tei("respStmt", xml_id="gutenberg-digitization")
    source_role = tei("resp")
    source_role.text = "electronic transcription and EPUB publication"
    source_name = tei("name")
    source_name.text = "Project Gutenberg"
    source_resp.extend((source_role, source_name))
    title_stmt.append(source_resp)
    bookstacks_resp = tei("respStmt", xml_id="bookstacks-encoding")
    conversion_role = tei("resp")
    conversion_role.text = "XHTML-to-TEI P5 conversion and structural encoding"
    conversion_name = tei("name")
    conversion_name.text = "Bookstacks project"
    bookstacks_resp.extend((conversion_role, conversion_name))
    title_stmt.append(bookstacks_resp)
    file_desc.append(title_stmt)

    edition_stmt = tei("editionStmt")
    edition = tei("edition", n="1.0")
    edition.text = (
        "Bookstacks TEI edition based on Project Gutenberg EPUB "
        + gutenberg_number(metadata)
    )
    edition_stmt.append(edition)
    file_desc.append(edition_stmt)

    publication_stmt = tei("publicationStmt")
    publisher = tei("publisher")
    publisher.text = "Bookstacks project"
    publication_date = tei("date", when=date.today().isoformat())
    publication_date.text = date.today().strftime("%d %B %Y")
    local_id = tei("idno", type="local")
    local_id.text = text_id
    availability = tei("availability", status="free")
    availability_note = tei("p")
    availability_note.text = metadata["rights"]
    availability.append(availability_note)
    publication_stmt.extend((publisher, publication_date, local_id, availability))
    file_desc.append(publication_stmt)

    source_desc = tei("sourceDesc")
    bibliography = tei("bibl")
    source_title = tei("title")
    source_title.text = metadata["title"]
    source_author = tei("author")
    source_author.text = metadata["creator"]
    bibliography.extend((source_title, source_author))
    for translator_name in filter(None, metadata["translators"].split("|")):
        translator = tei("editor", role="translator")
        translator.text = translator_name
        bibliography.append(translator)
    for illustrator_name in filter(None, metadata["illustrators"].split("|")):
        illustrator = tei("editor", role="illustrator")
        illustrator.text = illustrator_name
        bibliography.append(illustrator)
    source_publisher = tei("publisher")
    source_publisher.text = "Project Gutenberg"
    source_date = tei("date", when=metadata["publication"])
    source_date.text = metadata["publication"]
    identifier = tei("idno", type="ProjectGutenberg")
    identifier.text = metadata["identifier"]
    source_ref = tei("ref", target=metadata["source"])
    source_ref.text = metadata["source"]
    bibliography.extend((source_publisher, source_date, identifier, source_ref))
    source_desc.append(bibliography)
    file_desc.append(source_desc)
    header.append(file_desc)

    encoding_desc = tei("encodingDesc")
    project_desc = tei("projectDesc")
    description = tei("p")
    description.text = (
        "Converted from the Project Gutenberg XHTML spine. Gutenberg header, "
        "contents, and license boilerplate are omitted. Source book, part, "
        "epilogue, preface, chapter, subchapter section, paragraph, poetry, "
        "letter, emphasis, and footnote structures are retained where present."
    )
    project_desc.append(description)
    encoding_desc.append(project_desc)
    header.append(encoding_desc)

    profile_desc = tei("profileDesc")
    lang_usage = tei("langUsage")
    language = tei("language", ident="en")
    language.text = "English"
    lang_usage.append(language)
    profile_desc.append(lang_usage)
    header.append(profile_desc)

    revision_desc = tei("revisionDesc")
    change = tei(
        "change", when=date.today().isoformat(), who="#bookstacks-encoding"
    )
    change.text = "Converted the Project Gutenberg EPUB XHTML to standalone TEI P5."
    revision_desc.append(change)
    header.append(revision_desc)
    return header


def iter_reading_blocks(xhtml: etree._Element) -> list[etree._Element]:
    bodies = xhtml.xpath("//x:body", namespaces=NS)
    if not bodies:
        return []
    body = bodies[0]
    block_names = {
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "p",
        "pre",
        "blockquote",
        "ul",
        "ol",
    }
    container_names = {"p", "pre", "blockquote", "ul", "ol"}
    suppressed_classes = {"footer", "pg-boilerplate", "pgheader", "trans-note"}
    blocks: list[etree._Element] = []
    for element in body.iterdescendants():
        if not isinstance(element.tag, str):
            continue
        local = etree.QName(element).localname
        if local not in block_names:
            continue
        nested = False
        for ancestor in (element, *element.iterancestors()):
            if ancestor is body:
                break
            if suppressed_classes.intersection(ancestor.get("class", "").split()):
                nested = True
                break
            if isinstance(ancestor.tag, str) and etree.QName(ancestor).localname in container_names:
                if ancestor is not element:
                    nested = True
                    break
        if not nested:
            blocks.append(element)
    return blocks


def insert_note_at_marker(
    text_node: etree._ElementUnicodeResult,
    marker: str,
    note: etree._Element,
) -> None:
    value = str(text_node)
    before, after = value.rsplit(marker, 1)
    owner = text_node.getparent()
    if (
        owner.tag == f"{{{TEI}}}hi"
        and "sup" in owner.get("rend", "").split()
        and normalized_text(owner) == marker
    ):
        parent = owner.getparent()
        note.tail = owner.tail
        parent.replace(owner, note)
        return
    if text_node.is_text:
        owner.text = before
        owner.insert(0, note)
    else:
        parent = owner.getparent()
        owner.tail = before
        parent.insert(parent.index(owner) + 1, note)
    note.tail = after


def relocate_inline_notes(root: etree._Element) -> None:
    """Replace source note markers with their full TEI notes."""
    text = root.find(f"{{{TEI}}}text")
    if text is None:
        return
    notes = list(text.xpath(".//tei:note", namespaces={"tei": TEI}))
    element_order = {element: index for index, element in enumerate(text.iter())}
    original_note_order = {note: element_order[note] for note in notes}

    for note in notes:
        note_text = normalized_text(note)
        label_match = re.match(r"^(?:\[([*]|\d+)\]|([*]))\s*", note_text)
        label = next((value for value in label_match.groups() if value), None) if label_match else None
        if label is None:
            unmatched_stars = [
                node
                for node in text.xpath(
                    ".//text()[not(ancestor::tei:note)]",
                    namespaces={"tei": TEI},
                )
                if "[*]" in str(node)
                and element_order.get(node.getparent(), -1) < original_note_order[note]
            ]
            if unmatched_stars:
                label = "*"
        if label:
            marker = f"[{label}]"
            candidates = [
                node
                for node in text.xpath(
                    ".//text()[not(ancestor::tei:note)]",
                    namespaces={"tei": TEI},
                )
                if marker in str(node)
                and element_order.get(node.getparent(), -1) < original_note_order[note]
            ]
            if candidates:
                target = max(candidates, key=lambda node: element_order[node.getparent()])
                if note.text:
                    note.text = re.sub(
                        r"^\s*(?:\[(?:[*]|\d+)\]|[*])\s*",
                        "",
                        note.text,
                        count=1,
                    )
                insert_note_at_marker(target, marker, note)
                continue

        parent = note.getparent()
        previous = note.getprevious()
        target_paragraph: etree._Element | None = None
        while previous is not None and target_paragraph is None:
            if previous.tag == f"{{{TEI}}}p":
                target_paragraph = previous
            else:
                paragraphs = previous.xpath(".//tei:p", namespaces={"tei": TEI})
                target_paragraph = paragraphs[-1] if paragraphs else None
            previous = previous.getprevious()
        if target_paragraph is not None and parent is not target_paragraph:
            target_paragraph.append(note)
            note.tail = None

    for notes_div in text.xpath(
        ".//tei:div[@type='notes'][not(.//tei:note)]",
        namespaces={"tei": TEI},
    ):
        notes_div.getparent().remove(notes_div)
    for back in text.xpath("./tei:back[not(*)]", namespaces={"tei": TEI}):
        text.remove(back)
    for note in notes:
        wrapper = note.getparent()
        if (
            wrapper is not None
            and wrapper.tag == f"{{{TEI}}}hi"
            and "sup" in wrapper.get("rend", "").split()
            and len(wrapper) == 1
            and not (wrapper.text or "").strip()
            and not (note.tail or "").strip()
        ):
            parent = wrapper.getparent()
            note.tail = wrapper.tail
            parent.replace(wrapper, note)


def build_document(epub_path: Path, text_id: str) -> etree._ElementTree:
    metadata, documents = get_epub_data(epub_path)
    text_number = gutenberg_number(metadata)
    if text_number not in SUPPORTED_TEXTS:
        raise ValueError(f"Unsupported Project Gutenberg text: {metadata['identifier']}")
    profile = SUPPORTED_TEXTS[text_number]

    root = tei("TEI", xml_id=text_id)
    root.append(build_header(metadata, text_id))
    text = tei("text", xml_lang="en")
    front = tei("front") if profile["fronts"] else None
    if front is not None:
        text.append(front)
    body = tei("body")
    work_type = "translation" if metadata["translators"] else "edition"
    work = tei("div", type=work_type, xml_id=f"{text_id}-eng-text")
    if profile.get("work_head"):
        work_head = tei("head")
        work_head.text = metadata["title"]
        work.append(work_head)
    body.append(work)
    text.append(body)
    back = tei("back") if profile.get("backs", 0) else None
    if back is not None:
        text.append(back)
    root.append(text)

    grouped_work = any(profile["groups"].values())
    current_group: etree._Element | None = None if grouped_work else work
    current_groups: dict[int, etree._Element] = {}
    current_chapter: etree._Element | None = None
    current_section: etree._Element | None = None
    current_front: etree._Element | None = None
    current_back: etree._Element | None = None
    group_counts = {"book": 0, "part": 0, "epilogue": 0}
    chapter_number = 0
    section_number = 0
    paragraph_number = 0
    note_number = 0
    total_chapters = 0
    total_sections = 0
    front_number = 0
    back_number = 0
    chapter_has_content = False
    chapter_subtitle_set = False
    finished = False

    for _, raw_document in documents:
        xhtml = etree.fromstring(raw_document)
        for source_block in iter_reading_blocks(xhtml):
            local = etree.QName(source_block).localname
            block_text = normalized_text(source_block)
            if not block_text:
                continue
            canonical = block_text.upper().replace("’", "'")

            if canonical.startswith("*** END OF THE PROJECT GUTENBERG"):
                finished = True
                break

            if local in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                if canonical.startswith("THE FULL PROJECT GUTENBERG"):
                    finished = True
                    break

                front_type: str | None = None
                if canonical.startswith("PREFACE") or canonical.startswith(
                    "AUTHOR'S PREFACE"
                ):
                    front_type = "preface"
                elif canonical.startswith("TRANSLATOR'S PREFACE"):
                    front_type = "translator-preface"
                elif canonical == "POSTSCRIPT":
                    front_type = "postscript"
                elif canonical == "CHARACTERS":
                    front_type = "characters"
                if local != "h1":
                    for prefix, configured_type in profile.get(
                        "front_heading_prefixes", {}
                    ).items():
                        if canonical.startswith(prefix):
                            front_type = configured_type
                            break

                if front_type and front is not None:
                    front_number += 1
                    current_chapter = None
                    current_section = None
                    current_back = None
                    current_front = tei(
                        "div",
                        type=front_type,
                        n=str(front_number),
                        xml_id=f"eng-front-{front_number:02d}-{front_type}",
                    )
                    front_head = tei("head")
                    front_head.text = block_text
                    current_front.append(front_head)
                    front.append(current_front)
                    continue

                back_type = profile.get("back_headings", {}).get(canonical)
                if back_type and back is not None:
                    back_number += 1
                    current_chapter = None
                    current_section = None
                    current_front = None
                    current_back = tei(
                        "div",
                        type=back_type,
                        n=str(back_number),
                        xml_id=f"eng-back-{back_number:02d}-{back_type}",
                    )
                    back_head = tei("head")
                    back_head.text = block_text
                    current_back.append(back_head)
                    back.append(current_back)
                    continue

                if canonical in {"CONTENTS", "LIST OF ILLUSTRATIONS"}:
                    current_front = None
                    continue

                group_type: str | None = None
                if canonical.startswith("BOOK "):
                    group_type = "book"
                elif canonical.startswith("PART "):
                    group_type = "part"
                elif canonical == "EPILOGUE" or canonical.startswith(
                    ("FIRST EPILOGUE", "SECOND EPILOGUE")
                ):
                    group_type = "epilogue"

                if group_type:
                    group_counts[group_type] += 1
                    group_number = group_counts[group_type]
                    chapter_number = 0
                    current_chapter = None
                    current_section = None
                    current_front = None
                    current_back = None
                    group_level = profile.get("group_levels", {}).get(group_type, 1)
                    parent_levels = [level for level in current_groups if level < group_level]
                    group_parent = (
                        current_groups[max(parent_levels)] if parent_levels else work
                    )
                    current_groups = {
                        level: group
                        for level, group in current_groups.items()
                        if level < group_level
                    }
                    current_group = tei(
                        "div",
                        type=group_type,
                        n=str(group_number),
                        xml_id=f"eng-{group_type}-{group_number:02d}",
                    )
                    group_head = tei("head")
                    group_head.text = block_text
                    current_group.append(group_head)
                    group_parent.append(current_group)
                    current_groups[group_level] = current_group
                    continue

                unit_type = profile["unit_type"]
                unit_heading_pattern = profile.get("unit_heading_pattern")
                is_unit = (
                    re.match(unit_heading_pattern, canonical) is not None
                    if unit_heading_pattern
                    else (
                        canonical.startswith("CHAPTER ")
                        if unit_type == "chapter"
                        else canonical.startswith("STAVE ")
                    )
                )
                if is_unit:
                    if current_group is None:
                        continue
                    chapter_number += 1
                    total_chapters += 1
                    section_number = 0
                    current_front = None
                    current_back = None
                    group_id = current_group.get(f"{{{XML}}}id")
                    current_chapter = tei(
                        "div",
                        type=unit_type,
                        n=str(chapter_number),
                        xml_id=f"{group_id}-{unit_type}-{chapter_number:03d}",
                    )
                    chapter_head = tei("head")
                    chapter_head.text = block_text
                    current_chapter.append(chapter_head)
                    current_group.append(current_chapter)
                    current_section = None
                    chapter_has_content = False
                    chapter_subtitle_set = False
                    continue

                if (
                    current_chapter is not None
                    and not chapter_has_content
                    and canonical != "ORIGINAL"
                ):
                    chapter_head = current_chapter.find(f"{{{TEI}}}head")
                    chapter_head.text = (chapter_head.text or "") + " — " + block_text
                    chapter_subtitle_set = True
                continue

            source_classes = set(source_block.get("class", "").split())
            if (
                current_chapter is not None
                and local == "p"
                and profile.get("section_paragraph_classes")
                and source_classes.intersection(profile["section_paragraph_classes"])
            ):
                if canonical == "THE END":
                    trailer = tei("trailer")
                    convert_inline(source_block, trailer)
                    trailer_parent = (
                        current_section
                        if current_section is not None
                        else current_chapter
                    )
                    trailer_parent.append(trailer)
                    chapter_has_content = True
                    continue
                section_number += 1
                total_sections += 1
                chapter_id = current_chapter.get(f"{{{XML}}}id")
                current_section = tei(
                    "div",
                    type="section",
                    n=str(section_number),
                    xml_id=f"{chapter_id}-section-{section_number:03d}",
                )
                section_head = tei("head")
                convert_inline(source_block, section_head)
                current_section.append(section_head)
                current_chapter.append(current_section)
                chapter_has_content = True
                continue

            title_paragraph = profile.get("chapter_title_paragraph")
            if (
                current_chapter is not None
                and title_paragraph
                and not chapter_has_content
                and not chapter_subtitle_set
                and local == "p"
                and (
                    title_paragraph == "any"
                    or title_paragraph in source_block.get("class", "").split()
                )
            ):
                subtitle = re.sub(r"^([A-Z])\s+([a-z])", r"\1\2", block_text)
                chapter_head = current_chapter.find(f"{{{TEI}}}head")
                chapter_head.text = (chapter_head.text or "") + " — " + subtitle
                chapter_subtitle_set = True
                continue

            target = next(
                (
                    candidate
                    for candidate in (
                        current_section,
                        current_chapter,
                        current_front,
                        current_back,
                    )
                    if candidate is not None
                ),
                None,
            )
            if target is None:
                continue
            converted, paragraph_number, note_number = convert_block(
                source_block, paragraph_number, note_number
            )
            if converted is not None:
                target.append(converted)
                if current_chapter is not None:
                    chapter_has_content = True
        if finished:
            break

    expected_groups = profile["groups"]
    expected_chapters = profile["chapters"]
    expected_fronts = profile["fronts"]
    expected_backs = profile.get("backs", 0)
    expected_sections = profile.get("sections", 0)
    if (
        group_counts != expected_groups
        or total_chapters != expected_chapters
        or front_number != expected_fronts
        or back_number != expected_backs
        or total_sections != expected_sections
    ):
        raise ValueError(
            "Unexpected source structure: "
            f"groups={group_counts}, chapters={total_chapters}, sections={total_sections}, "
            f"fronts={front_number}, backs={back_number}; "
            f"expected groups={expected_groups}, chapters={expected_chapters}, "
            f"sections={expected_sections}, fronts={expected_fronts}, backs={expected_backs}"
        )
    relocate_inline_notes(root)
    return etree.ElementTree(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--text-id", required=True)
    args = parser.parse_args()

    document = build_document(args.source, args.text_id)
    schema = etree.RelaxNG(etree.parse(str(args.schema)))
    if not schema.validate(document):
        for entry in schema.error_log:
            print(entry, file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    xml_bytes = etree.tostring(
        document,
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=True,
    )
    model = (
        b'<?xml-model href="../tei_all.rng" '
        b'schematypens="http://relaxng.org/ns/structure/1.0"?>\n'
    )
    declaration_end = xml_bytes.index(b"?>") + 2
    xml_bytes = xml_bytes[:declaration_end] + b"\n" + model + xml_bytes[declaration_end + 1 :]
    args.output.write_bytes(xml_bytes)
    print(f"Generated {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
