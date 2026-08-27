"""Build the selected English Tolstoy novella collection from Standard Ebooks XHTML."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
import sys

from lxml import etree


TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
XHTML = "http://www.w3.org/1999/xhtml"
EPUB = "http://www.idpf.org/2007/ops"
NS = {"x": XHTML}

SHORT_FICTION_URL = (
    "https://standardebooks.org/ebooks/leo-tolstoy/short-fiction/various-translators"
)
HADJI_MURAD_URL = (
    "https://standardebooks.org/ebooks/leo-tolstoy/hadji-murad/aylmer-maude"
)

# The order is literary chronology by composition.  Hadji Murad is stored in
# its own Standard Ebooks source; the other works come from Short Fiction.
WORKS = [
    ("family-happiness", "Family Happiness", "novella"),
    ("god-sees-the-truth-but-waits", "God Sees the Truth, But Waits", "short-story"),
    ("the-death-of-ivan-ilyitch", "The Death of Ivan Ilyitch", "novella"),
    ("the-kreutzer-sonata", "The Kreutzer Sonata", "novella"),
    ("the-devil", "The Devil", "novella"),
    ("father-sergius", "Father Sergius", "novella"),
    ("master-and-man", "Master and Man", "novella"),
    ("hadji-murad", "Hadji Murad", "novella"),
    ("the-forged-coupon", "The Forged Coupon", "novella"),
]


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


def slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-").lower()
    return value or "item"


def load_endnotes(text_dir: Path) -> dict[str, etree._Element]:
    path = text_dir / "endnotes.xhtml"
    if not path.exists():
        return {}
    document = etree.parse(str(path))
    return {
        item.get("id"): item
        for item in document.xpath("//x:li[@id]", namespaces=NS)
        if item.get("id")
    }


def append_note_content(source: etree._Element, target: etree._Element) -> None:
    paragraphs = source.xpath("./x:p", namespaces=NS)
    for paragraph in paragraphs:
        convert_inline(paragraph, target, {}, skip_backlinks=True)


def convert_inline(
    source: etree._Element,
    target: etree._Element,
    endnotes: dict[str, etree._Element],
    *,
    skip_backlinks: bool = False,
) -> None:
    append_text(target, source.text)
    for child in source:
        if not isinstance(child.tag, str):
            append_text(target, child.tail)
            continue
        local = etree.QName(child).localname
        epub_type = child.get(f"{{{EPUB}}}type", "")
        converted: etree._Element | None = None

        if local == "a" and "backlink" in epub_type and skip_backlinks:
            converted = None
        elif local == "a" and "noteref" in epub_type:
            note_id = (child.get("href") or "").rsplit("#", 1)[-1]
            source_note = endnotes.get(note_id)
            if source_note is not None:
                converted = tei("note", type="editorial", place="foot")
                append_note_content(source_note, converted)
        elif local in {"i", "em", "cite"}:
            converted = tei("hi", rend="italic")
            convert_inline(child, converted, endnotes, skip_backlinks=skip_backlinks)
        elif local in {"b", "strong"}:
            converted = tei("hi", rend="bold")
            convert_inline(child, converted, endnotes, skip_backlinks=skip_backlinks)
        elif local in {"sup", "sub", "small"}:
            converted = tei("hi", rend=local)
            convert_inline(child, converted, endnotes, skip_backlinks=skip_backlinks)
        elif local == "br":
            converted = tei("lb")
        elif local == "a":
            converted = tei("ref")
            href = child.get("href")
            if href:
                converted.set("target", href)
            convert_inline(child, converted, endnotes, skip_backlinks=skip_backlinks)
        else:
            converted = tei("seg")
            converted.set("type", local)
            source_lang = child.get(f"{{{XML}}}lang")
            if source_lang:
                converted.set(f"{{{XML}}}lang", source_lang)
            convert_inline(child, converted, endnotes, skip_backlinks=skip_backlinks)

        if converted is not None:
            target.append(converted)
        append_text(target, child.tail)


class Converter:
    def __init__(self, text_id: str):
        self.text_id = text_id
        self.paragraph_number = 0
        self.note_number = 0

    def assign_note_ids(self, element: etree._Element) -> None:
        for note in element.xpath(".//tei:note", namespaces={"tei": TEI}):
            self.note_number += 1
            note.set(f"{{{XML}}}id", f"{self.text_id}-eng-note-{self.note_number:04d}")

    def block(
        self,
        source: etree._Element,
        endnotes: dict[str, etree._Element],
    ) -> etree._Element | None:
        local = etree.QName(source).localname
        if local == "p":
            if not normalized_text(source):
                return None
            self.paragraph_number += 1
            paragraph = tei(
                "p", xml_id=f"{self.text_id}-eng-p-{self.paragraph_number:06d}"
            )
            classes = set(source.get("class", "").split())
            retained = sorted(classes.intersection({"center", "epigraph", "signature"}))
            if retained:
                paragraph.set("rend", " ".join(retained))
            convert_inline(source, paragraph, endnotes)
            self.assign_note_ids(paragraph)
            return paragraph

        if local == "blockquote":
            quote = tei("quote")
            if "epigraph" in source.get(f"{{{EPUB}}}type", ""):
                quote.set("type", "epigraph")
            for child in source:
                if not isinstance(child.tag, str):
                    continue
                converted = self.block(child, endnotes)
                if converted is not None:
                    quote.append(converted)
            return quote if len(quote) else None

        if local in {"ol", "ul"}:
            listing = tei("list", type="ordered" if local == "ol" else "unordered")
            for child in source:
                if not isinstance(child.tag, str) or etree.QName(child).localname != "li":
                    continue
                item = tei("item")
                nested_paragraphs = child.xpath("./x:p", namespaces=NS)
                if nested_paragraphs:
                    for paragraph in nested_paragraphs:
                        converted = self.block(paragraph, endnotes)
                        if converted is not None:
                            item.append(converted)
                else:
                    convert_inline(child, item, endnotes)
                    self.assign_note_ids(item)
                listing.append(item)
            return listing if len(listing) else None

        if local == "table":
            table = tei("table")
            for row_source in source.xpath(".//x:tr", namespaces=NS):
                row = tei("row")
                for cell_source in row_source.xpath("./x:th | ./x:td", namespaces=NS):
                    cell = tei("cell", role="label" if etree.QName(cell_source).localname == "th" else "data")
                    convert_inline(cell_source, cell, endnotes)
                    self.assign_note_ids(cell)
                    row.append(cell)
                if len(row):
                    table.append(row)
            return table if len(table) else None

        if local == "hr":
            return tei("milestone", unit="separator")

        return None

    def section(
        self,
        source: etree._Element,
        endnotes: dict[str, etree._Element],
        work_slug: str,
        section_counter: list[int],
    ) -> etree._Element:
        epub_type = source.get(f"{{{EPUB}}}type", "")
        division_type = "chapter" if "chapter" in epub_type else "section"
        section_counter[0] += 1
        division = tei(
            "div",
            type=division_type,
            n=str(section_counter[0]),
            xml_id=f"{self.text_id}-eng-{work_slug}-{division_type}-{section_counter[0]:03d}",
        )
        for child in source:
            if not isinstance(child.tag, str):
                continue
            local = etree.QName(child).localname
            if local in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                head = tei("head")
                convert_inline(child, head, endnotes)
                division.append(head)
            elif local == "section":
                division.append(self.section(child, endnotes, work_slug, section_counter))
            else:
                converted = self.block(child, endnotes)
                if converted is not None:
                    division.append(converted)
        return division

    def article(
        self,
        source: etree._Element,
        endnotes: dict[str, etree._Element],
        work_slug: str,
        work_title: str,
        work_type: str,
    ) -> etree._Element:
        work = tei(
            "div",
            type=work_type,
            xml_id=f"{self.text_id}-eng-{work_slug}",
        )
        head = tei("head")
        head.text = work_title
        work.append(head)
        section_counter = [0]
        for child in source:
            if not isinstance(child.tag, str):
                continue
            local = etree.QName(child).localname
            if local == "header":
                for header_child in child:
                    header_local = etree.QName(header_child).localname
                    if header_local in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                        continue
                    converted = self.block(header_child, endnotes)
                    if converted is not None:
                        work.append(converted)
            elif local in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                # The collection supplies its own normalized work heading.
                continue
            elif local == "section":
                work.append(self.section(child, endnotes, work_slug, section_counter))
            else:
                converted = self.block(child, endnotes)
                if converted is not None:
                    work.append(converted)
        return work


def build_header(text_id: str) -> etree._Element:
    header = tei("teiHeader", xml_lang="en")
    file_desc = tei("fileDesc")
    title_stmt = tei("titleStmt")
    title = tei("title", type="main", xml_lang="en", xml_id=f"{text_id}-title")
    title.text = "Novellas"
    author = tei("author")
    author.text = "Leo Tolstoy"
    title_stmt.extend((title, author))
    for translator_name in (
        "Louise Maude",
        "Aylmer Maude",
        "Nathan Haskell Dole",
        "Constance Garnett",
        "J. D. Duff",
        "Leo Wiener",
        "R. S. Townsend",
        "Hagberg Wright",
        "Benjamin Tucker",
        "Everyman's Library",
        "Vladimir Chertkov",
        "Isabella Fyvie Mayo",
    ):
        translator = tei("editor", role="translator")
        translator.text = translator_name
        title_stmt.append(translator)
    source_resp = tei("respStmt", xml_id="standard-ebooks-production")
    source_role = tei("resp")
    source_role.text = "source transcription, proofreading, and EPUB production"
    source_name = tei("name")
    source_name.text = "Standard Ebooks"
    source_resp.extend((source_role, source_name))
    title_stmt.append(source_resp)
    bookstacks_resp = tei("respStmt", xml_id="bookstacks-encoding")
    conversion_role = tei("resp")
    conversion_role.text = "selected-work compilation and XHTML-to-TEI P5 conversion"
    conversion_name = tei("name")
    conversion_name.text = "Bookstacks project"
    bookstacks_resp.extend((conversion_role, conversion_name))
    title_stmt.append(bookstacks_resp)
    file_desc.append(title_stmt)

    edition_stmt = tei("editionStmt")
    edition = tei("edition", n="1.0")
    edition.text = "Bookstacks selected novellas edition based on Standard Ebooks XHTML"
    edition_stmt.append(edition)
    file_desc.append(edition_stmt)

    publication_stmt = tei("publicationStmt")
    publisher = tei("publisher")
    publisher.text = "Bookstacks project"
    pub_place = tei("pubPlace")
    pub_place.text = "United States"
    publication_date = tei("date", when=date.today().isoformat())
    publication_date.text = date.today().strftime("%d %B %Y")
    local_id = tei("idno", type="local")
    local_id.text = text_id
    availability = tei("availability", status="free")
    licence = tei(
        "licence", target="https://creativecommons.org/publicdomain/zero/1.0/"
    )
    licence.text = (
        "The source texts are believed to be in the United States public domain; "
        "Standard Ebooks dedicates its contributions to the public domain under CC0."
    )
    availability.append(licence)
    publication_stmt.extend((publisher, pub_place, publication_date, local_id, availability))
    file_desc.append(publication_stmt)

    source_desc = tei("sourceDesc")
    source_list = tei("listBibl")
    for source_title, source_url in (
        ("Short Fiction", SHORT_FICTION_URL),
        ("Hadji Murad", HADJI_MURAD_URL),
    ):
        bibliography = tei("bibl")
        bibl_title = tei("title")
        bibl_title.text = source_title
        bibl_author = tei("author")
        bibl_author.text = "Leo Tolstoy"
        bibl_publisher = tei("publisher")
        bibl_publisher.text = "Standard Ebooks"
        source_ref = tei("ref", target=source_url)
        source_ref.text = source_url
        bibliography.extend((bibl_title, bibl_author, bibl_publisher, source_ref))
        source_list.append(bibliography)
    source_desc.append(source_list)
    file_desc.append(source_desc)
    header.append(file_desc)

    encoding_desc = tei("encodingDesc")
    project_desc = tei("projectDesc")
    description = tei("p")
    description.text = (
        "Nine selected Tolstoy novellas and stories are compiled as independent work "
        "divisions. Source chapters, paragraphs, epigraphs, inline typography, and "
        "referenced endnotes are retained."
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
    change = tei("change", when=date.today().isoformat(), who="#bookstacks-encoding")
    change.text = "Compiled the selected English translations and converted XHTML to TEI P5."
    revision_desc.append(change)
    header.append(revision_desc)
    return header


def parse_article(path: Path) -> etree._Element:
    document = etree.parse(str(path))
    articles = document.xpath("//x:article", namespaces=NS)
    if len(articles) != 1:
        raise ValueError(f"Expected one article in {path}, found {len(articles)}")
    return articles[0]


def build_document(short_fiction_root: Path, hadji_root: Path, text_id: str) -> etree._ElementTree:
    short_text_dir = short_fiction_root / "src" / "epub" / "text"
    hadji_text_dir = hadji_root / "src" / "epub" / "text"
    short_notes = load_endnotes(short_text_dir)
    hadji_notes = load_endnotes(hadji_text_dir)
    converter = Converter(text_id)

    root = tei("TEI", xml_id=text_id)
    root.append(build_header(text_id))
    text = tei("text", xml_lang="en")
    body = tei("body")
    collection = tei("div", type="collection", xml_id=f"{text_id}-eng-collection")
    collection_head = tei("head")
    collection_head.text = "Novellas"
    collection.append(collection_head)
    body.append(collection)
    text.append(body)
    root.append(text)

    for work_slug, work_title, work_type in WORKS:
        if work_slug == "hadji-murad":
            work = tei(
                "div", type=work_type, xml_id=f"{text_id}-eng-{work_slug}"
            )
            head = tei("head")
            head.text = work_title
            work.append(head)

            preface_document = etree.parse(str(hadji_text_dir / "preface.xhtml"))
            preface_sections = preface_document.xpath("//x:section", namespaces=NS)
            if preface_sections:
                counter = [0]
                preface = converter.section(
                    preface_sections[0], hadji_notes, f"{work_slug}-preface", counter
                )
                preface.set("type", "preface")
                work.append(preface)

            for chapter_number in range(1, 26):
                chapter_document = etree.parse(
                    str(hadji_text_dir / f"chapter-{chapter_number}.xhtml")
                )
                chapter_sections = chapter_document.xpath("//x:section", namespaces=NS)
                if len(chapter_sections) != 1:
                    raise ValueError(
                        f"Expected one chapter section in Hadji Murad chapter {chapter_number}"
                    )
                counter = [chapter_number - 1]
                chapter = converter.section(
                    chapter_sections[0], hadji_notes, work_slug, counter
                )
                chapter.set("n", str(chapter_number))
                work.append(chapter)
            collection.append(work)
            continue

        source_path = short_text_dir / f"{work_slug}.xhtml"
        article = parse_article(source_path)
        collection.append(
            converter.article(article, short_notes, work_slug, work_title, work_type)
        )

    return etree.ElementTree(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--short-fiction-root", type=Path, required=True)
    parser.add_argument("--hadji-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--text-id", required=True)
    args = parser.parse_args()

    document = build_document(args.short_fiction_root, args.hadji_root, args.text_id)
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
