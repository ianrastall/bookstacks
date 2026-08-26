"""Convert the six supplied Spanish Jane Austen EPUBs to standalone TEI P5.

The sources come from several unrelated EPUB production pipelines.  This
converter deliberately reconstructs logical books rather than treating every
spine item as a chapter or flattening XHTML to a bag of paragraphs.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import unquote
from zipfile import ZipFile

from lxml import etree, html


TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
XML_ID = f"{{{XML_NS}}}id"
XML_LANG = f"{{{XML_NS}}}lang"
NS = {"tei": TEI_NS}


@dataclass(frozen=True)
class Profile:
    filename: str
    slug: str
    title: str
    uniform_title: str
    first_publication: str
    chapter_count: int
    provider: str
    provider_url: str | None
    source_date: str | None
    translator: str | None = None
    translator_kind: str = "person"
    source_note: str = ""
    rights_note: str = ""
    mode: str = "page-chapters"
    chapter_name_pattern: str = ""
    chapter_heading_tags: tuple[str, ...] = ("h1", "h2", "h3")
    chapter_heading_pattern: str = r"(?i)^cap[ií]tulo\b|^[IVXLCDM]+$"
    minimum_paragraphs: int = 0
    minimum_characters: int = 0
    volumes: tuple[tuple[int, int, str], ...] = ()
    source_url: str | None = None
    source_rights_url: str | None = None

    @property
    def text_id(self) -> str:
        return f"austen-{self.slug}-spa"

    @property
    def output_name(self) -> str:
        return f"austen_{self.slug}_spa.xml"


PROFILES = (
    Profile(
        filename="Sentido_y_sensibilidad-Jane_Austen.epub",
        slug="sense-and-sensibility",
        title="Sentido y sensibilidad",
        uniform_title="Sense and Sensibility",
        first_publication="1811",
        chapter_count=50,
        provider="Elejandría",
        provider_url="https://www.elejandria.com",
        source_date="2022-11-22",
        translator="Anónima",
        source_note="EPUB export of the Spanish Wikisource transcription.",
        rights_note="The EPUB records Creative Commons BY-SA 3.0 and GNU Free Documentation License source terms.",
        source_url="https://es.wikisource.org/wiki/Sentido_y_sensibilidad",
        source_rights_url="https://creativecommons.org/licenses/by-sa/3.0/",
        chapter_name_pattern=r"^OPS/c\d+_",
        chapter_heading_tags=("h1",),
        chapter_heading_pattern=r"(?i)^capítulo\s+\d+$",
        minimum_paragraphs=1800,
        minimum_characters=570_000,
    ),
    Profile(
        filename="Emma-Jane_Austen.epub",
        slug="emma",
        title="Emma",
        uniform_title="Emma",
        first_publication="1815",
        chapter_count=55,
        provider="Freeditorial",
        provider_url="https://freeditorial.com/es",
        source_date="2016-05-10",
        source_note="The EPUB does not identify the Spanish translator.",
        rights_note="The source EPUB was distributed as a free electronic edition; no translator or source-edition rights statement is present in its package metadata.",
        mode="continuous",
        minimum_paragraphs=2500,
        minimum_characters=825_000,
    ),
    Profile(
        filename="Orgullo_y_prejuicio-Jane_Austen.epub",
        slug="pride-and-prejudice",
        title="Orgullo y prejuicio",
        uniform_title="Pride and Prejudice",
        first_publication="1813",
        chapter_count=61,
        provider="Elejandría",
        provider_url="https://www.elejandria.com",
        source_date="2024-04-10",
        translator="José Jordán de Urríes y Azara",
        source_note='EPUB export of the 1924 Talleres "Calpe" edition preserved by Spanish Wikisource.',
        rights_note="The provider presents this scanned edition and transcription as a public-domain book.",
        source_url="https://es.wikisource.org/wiki/Orgullo_y_prejuicio",
        chapter_name_pattern=r"^OPS/Capitulo \d+\.xhtml$",
        chapter_heading_tags=("h3",),
        chapter_heading_pattern=r"(?i)^capitulo\s+(?:primero|[ivxlcdm]+)$",
        minimum_paragraphs=2050,
        minimum_characters=545_000,
        volumes=((1, 34, "Tomo primero"), (35, 61, "Tomo segundo y último")),
    ),
    Profile(
        filename="La_abadia_de_Northanger-Jane_Austen.epub",
        slug="northanger-abbey",
        title="La abadía de Northanger",
        uniform_title="Northanger Abbey",
        first_publication="1818",
        chapter_count=31,
        provider="Elejandría",
        provider_url="https://www.elejandria.com",
        source_date=None,
        translator="Elejandría",
        translator_kind="organization",
        source_note="The display title page credits standardebooks.org as source and Elejandría for the translation.",
        rights_note="The provider presents this edition as a public-domain book.",
        chapter_name_pattern=r"^EPUB/index_split_\d+\.html$",
        chapter_heading_tags=("h2",),
        chapter_heading_pattern=r"^[IVXLCDM]+$",
        minimum_paragraphs=1120,
        minimum_characters=360_000,
    ),
    Profile(
        filename="Persuasion-Jane_Austen.epub",
        slug="persuasion",
        title="Persuasión",
        uniform_title="Persuasion",
        first_publication="1818",
        chapter_count=24,
        provider="ePubLibre / Le Libros",
        provider_url=None,
        source_date="2013-08-15",
        source_note="The EPUB package identifies ePubLibre; its opening provider leaf identifies Le Libros. The translator is not identified.",
        rights_note="No reusable-license statement for the Spanish source edition is present in the EPUB package metadata.",
        chapter_name_pattern=r"^OEBPS/Text/(?:I|V|X)+\.xhtml$",
        chapter_heading_tags=("h1",),
        chapter_heading_pattern=r"(?i)^capitulo\s+[ivxlcdm]+$",
        minimum_paragraphs=1030,
        minimum_characters=360_000,
    ),
    Profile(
        filename="Mansfield_Park-Jane_Austen.epub",
        slug="mansfield-park",
        title="Mansfield Park",
        uniform_title="Mansfield Park",
        first_publication="1814",
        chapter_count=48,
        provider="Elejandría",
        provider_url="https://www.elejandria.com",
        source_date="2020-04-24",
        source_note="The EPUB package identifies Elejandría as publisher but does not identify the Spanish translator.",
        rights_note="The provider presents this edition as a public-domain book; the package does not name a translator.",
        chapter_name_pattern=r"^OEBPS/\d{4}\.xhtml$",
        chapter_heading_tags=("h2",),
        # Chapter XXXVIII is misspelled "Capítuo" in the source EPUB.  Match
        # that source form without silently correcting the encoded head.
        chapter_heading_pattern=r"(?i)^capítu(?:l)?o\s+[ivxlcdm]+$",
        minimum_paragraphs=1900,
        minimum_characters=720_000,
    ),
)


@dataclass
class SpineDocument:
    name: str
    root: etree._Element


@dataclass
class EpubData:
    metadata: list[tuple[str, str, dict[str, str]]]
    spine: list[SpineDocument]
    uuid: str

    def values(self, name: str) -> list[str]:
        return [value for local, value, _ in self.metadata if local == name and value]


@dataclass
class Context:
    profile: Profile
    paragraph_number: int = 0
    letter_number: int = 0
    verse_group_number: int = 0
    line_number: int = 0
    figure_number: int = 0
    page_break_number: int = 0
    seen_pages: set[tuple[str, str]] = field(default_factory=set)
    current_document: str = ""

    def paragraph(self, parent: etree._Element, text: str | None = None, **attrs: str) -> etree._Element:
        self.paragraph_number += 1
        node = sub(parent, "p", **attrs)
        node.set(XML_ID, f"spa-p-{self.paragraph_number:06d}")
        if text is not None:
            node.text = text
        return node

    def page_break(self, parent: etree._Element, title: str) -> etree._Element | None:
        match = re.match(r"^Página:(.+?Tomo\s+([IVX]+)\s+\(1924\)\.pdf)/(\d+)$", title)
        if not match:
            return None
        volume = match.group(2)
        page = match.group(3)
        key = (volume, page)
        if key in self.seen_pages:
            return None
        self.seen_pages.add(key)
        self.page_break_number += 1
        marker = sub(parent, "pb", n=page, ed=f"Calpe-1924-tomo-{volume}")
        marker.set(XML_ID, f"spa-pb-v{roman_to_int(volume)}-{int(page):03d}")
        return marker


def tei(name: str, text: str | None = None, **attrs: str) -> etree._Element:
    node = etree.Element(f"{{{TEI_NS}}}{name}")
    for key, value in attrs.items():
        if key == "xml_id":
            node.set(XML_ID, value)
        elif key == "xml_lang":
            node.set(XML_LANG, value)
        else:
            node.set(key, value)
    if text is not None:
        node.text = text
    return node


def sub(parent: etree._Element, name: str, text: str | None = None, **attrs: str) -> etree._Element:
    node = tei(name, text, **attrs)
    parent.append(node)
    return node


def local_name(node: etree._Element) -> str:
    return etree.QName(node).localname.lower() if isinstance(node.tag, str) else ""


def normalized_text(node: etree._Element) -> str:
    return " ".join("".join(node.itertext()).replace("\xa0", " ").split())


def append_text(parent: etree._Element, value: str | None) -> None:
    if not value:
        return
    value = re.sub(r"\s+", " ", value.replace("\xa0", " "))
    if not value:
        return
    if len(parent):
        current = parent[-1].tail or ""
        if current.endswith(" ") and value.startswith(" "):
            value = value[1:]
        parent[-1].tail = current + value
    else:
        current = parent.text or ""
        if current.endswith(" ") and value.startswith(" "):
            value = value[1:]
        parent.text = current + value


def trim_inline(node: etree._Element) -> None:
    if node.text:
        node.text = node.text.lstrip()
    if len(node) and node[-1].tail:
        node[-1].tail = node[-1].tail.rstrip()
    elif node.text:
        node.text = node.text.rstrip()


def roman_to_int(value: str) -> int:
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    previous = 0
    for character in reversed(value.upper()):
        current = values[character]
        total += -current if current < previous else current
        previous = max(previous, current)
    return total


def read_epub(path: Path) -> EpubData:
    with ZipFile(path) as archive:
        container = etree.fromstring(archive.read("META-INF/container.xml"))
        opf_name = container.xpath('string(//*[local-name()="rootfile"]/@full-path)')
        if not opf_name:
            raise ValueError(f"No OPF rootfile in {path}")
        opf = etree.fromstring(archive.read(opf_name))
        metadata: list[tuple[str, str, dict[str, str]]] = []
        for element in opf.xpath('//*[local-name()="metadata"]/*'):
            metadata.append(
                (
                    etree.QName(element).localname,
                    normalized_text(element),
                    {etree.QName(key).localname: value for key, value in element.attrib.items()},
                )
            )
        manifest = {
            element.get("id"): element.get("href")
            for element in opf.xpath('//*[local-name()="manifest"]/*[local-name()="item"]')
        }
        spine_ids = [
            element.get("idref")
            for element in opf.xpath('//*[local-name()="spine"]/*[local-name()="itemref"]')
        ]
        base = PurePosixPath(opf_name).parent
        documents: list[SpineDocument] = []
        for item_id in spine_ids:
            href = manifest.get(item_id)
            if not href:
                continue
            document_name = str(base / PurePosixPath(unquote(href)))
            try:
                root = html.fromstring(archive.read(document_name))
            except KeyError:
                # Zip member names sometimes retain URL encoding.
                document_name = str(base / PurePosixPath(href))
                root = html.fromstring(archive.read(document_name))
            documents.append(SpineDocument(document_name, root))
        identifiers = [value.removeprefix("urn:uuid:") for value in EpubData(metadata, [], "").values("identifier")]
        uuid = next((value for value in identifiers if re.fullmatch(r"[0-9a-fA-F-]{36}", value)), identifiers[0] if identifiers else "")
        return EpubData(metadata, documents, uuid)


def first_body(document: SpineDocument) -> etree._Element | None:
    bodies = document.root.xpath("//body")
    return bodies[0] if bodies else None


BLOCK_TAGS = {"p", "blockquote", "table", "ol", "ul", "figure", "hr", "h1", "h2", "h3", "h4", "h5", "h6"}


def reading_blocks(body: etree._Element) -> list[etree._Element]:
    blocks: list[etree._Element] = []
    for element in body.iterdescendants():
        name = local_name(element)
        classes = set(element.get("class", "").split())
        special_div = name == "div" and bool(classes & {"cita", "cabecera-pagina2"})
        if name not in BLOCK_TAGS and not special_div:
            continue
        protected = False
        for ancestor in element.iterancestors():
            if ancestor is body:
                break
            ancestor_name = local_name(ancestor)
            ancestor_classes = set(ancestor.get("class", "").split())
            if ancestor_name in {"p", "blockquote", "table", "ol", "ul", "figure"}:
                protected = True
                break
            if ancestor_name == "div" and ancestor_classes & {"cita", "cabecera-pagina2"}:
                protected = True
                break
        if not protected:
            blocks.append(element)
    return blocks


def normalize_target(href: str, profile: Profile) -> str:
    decoded = unquote(href)
    match = re.search(r"Capitulo\s*(\d+)\.xhtml", decoded, re.IGNORECASE)
    if match and profile.slug == "pride-and-prejudice":
        return f"#{profile.text_id}-chapter-{int(match.group(1)):03d}"
    if href.startswith(("http://", "https://", "mailto:")):
        return href
    return f"epub:/{href.lstrip('/')}"


def convert_inline(source: etree._Element, target: etree._Element, context: Context) -> None:
    page_title = source.get("title", "")
    if page_title.startswith("Página:"):
        context.page_break(target, page_title)
        return

    append_text(target, source.text)
    for child in source:
        name = local_name(child)
        classes = set(child.get("class", "").split())
        converted: etree._Element | None = None
        if child.get("title", "").startswith("Página:"):
            converted = context.page_break(target, child.get("title", ""))
        elif "calibre32" in classes:
            # Printed running head; the adjacent page milestone is retained.
            converted = None
        elif name in {"i", "em"}:
            converted = tei("hi", rend="italic")
            convert_inline(child, converted, context)
        elif name in {"b", "strong"}:
            converted = tei("hi", rend="bold")
            convert_inline(child, converted, context)
        elif name in {"sup", "sub", "small", "big", "code", "kbd", "samp"}:
            rendition = {"code": "monospace", "kbd": "monospace", "samp": "monospace"}.get(name, name)
            converted = tei("hi", rend=rendition)
            convert_inline(child, converted, context)
        elif name == "cite":
            converted = tei("quote", type="citation")
            convert_inline(child, converted, context)
        elif name in {"q", "quote"}:
            converted = tei("q")
            convert_inline(child, converted, context)
        elif name == "a":
            converted = tei("ref")
            if child.get("href"):
                converted.set("target", normalize_target(child.get("href", ""), context.profile))
            convert_inline(child, converted, context)
            if not normalized_text(converted):
                converted = None
        elif name == "br":
            converted = tei("lb")
        elif name in {"img", "image"}:
            converted = tei("graphic")
            source_url = child.get("src") or child.get("href") or child.get("{http://www.w3.org/1999/xlink}href")
            if source_url:
                base = PurePosixPath(context.current_document).parent
                converted.set("url", f"epub:/{base / PurePosixPath(unquote(source_url))}")
        elif name == "span" and child.get(XML_LANG):
            converted = tei("foreign", xml_lang=child.get(XML_LANG))
            convert_inline(child, converted, context)
        else:
            # Presentation-only spans and publisher wrappers are transparent.
            convert_inline(child, target, context)

        if converted is not None and converted.getparent() is None:
            target.append(converted)
        append_text(target, child.tail)


def line_texts(source: etree._Element) -> list[str]:
    serialized = html.tostring(source, encoding="unicode", method="html")
    serialized = re.sub(r"<br\b[^>]*>", "\n", serialized, flags=re.IGNORECASE)
    plain = html.fromstring(serialized).text_content()
    return [" ".join(line.replace("\xa0", " ").split()) for line in plain.splitlines() if line.strip()]


def looks_like_verse(source: etree._Element, profile: Profile) -> bool:
    if profile.slug != "mansfield-park" or not source.xpath(".//br"):
        return False
    lines = line_texts(source)
    return len(lines) == 2 and all(15 <= len(line) <= 110 for line in lines) and not any(
        greeting in lines[0].lower() for greeting in ("querida", "querido")
    )


def paragraph_from_source(source: etree._Element, parent: etree._Element, context: Context) -> etree._Element | None:
    raw_text = normalized_text(source)
    page_markers = source.xpath('.//*[@title and starts-with(@title, "Página:")]')
    if not raw_text and not page_markers:
        return None

    paragraph = context.paragraph(parent)
    classes = set(source.get("class", "").split())
    if "negrita" in classes:
        paragraph.set("rend", "bold")
    convert_inline(source, paragraph, context)
    trim_inline(paragraph)
    while len(paragraph) and local_name(paragraph[0]) == "lb" and not (paragraph.text or "").strip():
        paragraph.remove(paragraph[0])
    while len(paragraph) and local_name(paragraph[-1]) == "lb" and not (paragraph[-1].tail or "").strip():
        paragraph.remove(paragraph[-1])
    if not normalized_text(paragraph) and not paragraph.xpath(".//tei:pb | .//tei:graphic", namespaces=NS):
        parent.remove(paragraph)
        context.paragraph_number -= 1
        return None
    if not normalized_text(paragraph) and all(local_name(child) == "pb" for child in paragraph):
        position = parent.index(paragraph)
        for marker in list(paragraph):
            paragraph.remove(marker)
            parent.insert(position, marker)
            position += 1
        parent.remove(paragraph)
        context.paragraph_number -= 1
        return None
    return paragraph


def convert_letter(source: etree._Element, parent: etree._Element, context: Context) -> etree._Element:
    context.letter_number += 1
    number = context.letter_number
    floating = sub(parent, "floatingText", type="letter")
    floating.set(XML_ID, f"{context.profile.text_id}-letter-{number:03d}")
    body = sub(floating, "body")
    division = sub(body, "div", type="letter", n=str(number))
    division.set(XML_ID, f"{context.profile.text_id}-letter-{number:03d}-text")
    paragraphs = [element for element in source.xpath("./p") if normalized_text(element)]
    signed_index = next(
        (index for index, element in enumerate(paragraphs) if "derecha" in element.get("class", "").split()),
        None,
    )
    content_start = 0
    opener: etree._Element | None = None
    if paragraphs and re.fullmatch(r"\d{1,2}\s+de\s+\w+", normalized_text(paragraphs[0]), flags=re.IGNORECASE):
        opener = sub(division, "opener")
        dateline = sub(opener, "dateline")
        sub(dateline, "date", normalized_text(paragraphs[0]))
        content_start = 1
    if content_start < len(paragraphs) and re.match(
        r"(?i)^(mi\s+)?querid[oa]", normalized_text(paragraphs[content_start])
    ):
        opener = opener if opener is not None else sub(division, "opener")
        sub(opener, "salute", normalized_text(paragraphs[content_start]))
        content_start += 1

    end = signed_index if signed_index is not None else len(paragraphs)
    for element in paragraphs[content_start:end]:
        paragraph_from_source(element, division, context)

    if signed_index is not None:
        closer = sub(division, "closer")
        sub(closer, "signed", normalized_text(paragraphs[signed_index]))
        if signed_index + 1 < len(paragraphs):
            postscript = sub(division, "postscript")
            for element in paragraphs[signed_index + 1 :]:
                paragraph_from_source(element, postscript, context)
    return floating


def convert_table(source: etree._Element, parent: etree._Element, context: Context) -> etree._Element:
    table = sub(parent, "table")
    for source_row in source.xpath(".//tr"):
        row = sub(table, "row")
        for source_cell in source_row.xpath("./th|./td"):
            cell = sub(row, "cell")
            convert_inline(source_cell, cell, context)
            trim_inline(cell)
    return table


def convert_list(source: etree._Element, parent: etree._Element, context: Context) -> etree._Element:
    result = sub(parent, "list", type="ordered" if local_name(source) == "ol" else "simple")
    for source_item in source.xpath("./li"):
        item = sub(result, "item")
        convert_inline(source_item, item, context)
        trim_inline(item)
    return result


def convert_figure(source: etree._Element, parent: etree._Element, context: Context) -> etree._Element | None:
    image = source if local_name(source) in {"img", "image"} else next(
        iter(source.xpath(".//*[local-name()='img' or local-name()='image']")), None
    )
    if image is None:
        return None
    context.figure_number += 1
    figure = sub(parent, "figure", type="source-illustration")
    figure.set(XML_ID, f"spa-figure-{context.figure_number:04d}")
    graphic = sub(figure, "graphic")
    source_url = image.get("src") or image.get("href") or image.get("{http://www.w3.org/1999/xlink}href")
    if source_url:
        base = PurePosixPath(context.current_document).parent
        graphic.set("url", f"epub:/{base / PurePosixPath(unquote(source_url))}")
    alt = image.get("alt") or image.get("title")
    if alt:
        sub(figure, "figDesc", alt)
    return figure


def convert_block(source: etree._Element, parent: etree._Element, context: Context) -> etree._Element | None:
    name = local_name(source)
    classes = set(source.get("class", "").split())
    if name == "div" and "cita" in classes:
        return convert_letter(source, parent, context)
    if name == "div" and "cabecera-pagina2" in classes:
        paragraph = context.paragraph(parent, rend="center")
        convert_inline(source, paragraph, context)
        trim_inline(paragraph)
        return paragraph
    if name == "p" and "cita" in classes:
        quote = sub(parent, "quote", type="quoted-document")
        paragraph_from_source(source, quote, context)
        return quote
    if name == "p" and looks_like_verse(source, context.profile):
        context.verse_group_number += 1
        group = sub(parent, "lg", type="verse")
        group.set(XML_ID, f"spa-verse-group-{context.verse_group_number:04d}")
        for text in line_texts(source):
            context.line_number += 1
            line = sub(group, "l", text)
            line.set(XML_ID, f"spa-line-{context.line_number:05d}")
        return group
    if name == "p":
        return paragraph_from_source(source, parent, context)
    if name == "blockquote":
        quote = sub(parent, "quote")
        child_paragraphs = source.xpath("./p")
        if child_paragraphs:
            for child in child_paragraphs:
                paragraph_from_source(child, quote, context)
        else:
            paragraph = context.paragraph(quote)
            convert_inline(source, paragraph, context)
            trim_inline(paragraph)
        return quote
    if name == "table":
        return convert_table(source, parent, context)
    if name in {"ol", "ul"}:
        return convert_list(source, parent, context)
    if name == "figure":
        return convert_figure(source, parent, context)
    if name == "hr":
        return sub(parent, "milestone", unit="typographic-break")
    return None


def build_header(profile: Profile, epub: EpubData) -> etree._Element:
    today = date.today()
    header = tei("teiHeader", xml_lang="es")
    file_desc = sub(header, "fileDesc")
    title_stmt = sub(file_desc, "titleStmt")
    sub(title_stmt, "title", profile.title, type="main", xml_lang="es")
    sub(title_stmt, "title", profile.uniform_title, type="uniform", xml_lang="en")
    author = sub(title_stmt, "author", ref="https://viaf.org/viaf/102333412")
    person_name = sub(author, "persName", "Jane Austen")
    sub(person_name, "note", "1775–1817", type="dates")
    if profile.translator:
        editor = sub(title_stmt, "editor", role="translator")
        if profile.translator_kind == "organization":
            sub(editor, "orgName", profile.translator)
        else:
            editor.text = profile.translator
    source_resp = sub(title_stmt, "respStmt", xml_id="source-epub-publication")
    sub(source_resp, "resp", "Spanish electronic-edition preparation and EPUB publication")
    if profile.provider_url:
        source_name = sub(source_resp, "name")
        sub(source_name, "ref", profile.provider, target=profile.provider_url)
    else:
        sub(source_resp, "name", profile.provider)
    encoding_resp = sub(title_stmt, "respStmt", xml_id="bookstacks-encoding")
    sub(encoding_resp, "resp", "XHTML-to-TEI P5 conversion, structural reconstruction, and source-feature encoding")
    sub(encoding_resp, "name", "Bookstacks project")

    edition_stmt = sub(file_desc, "editionStmt")
    sub(edition_stmt, "edition", "Bookstacks TEI P5 edition derived from the supplied Spanish EPUB", n="1.0")

    publication_stmt = sub(file_desc, "publicationStmt")
    sub(publication_stmt, "publisher", "Bookstacks project")
    sub(publication_stmt, "pubPlace", "United States")
    sub(publication_stmt, "date", today.strftime("%d %B %Y"), when=today.isoformat())
    sub(publication_stmt, "idno", profile.text_id, type="local")
    availability = sub(publication_stmt, "availability", status="free")
    sub(
        availability,
        "licence",
        "The Bookstacks TEI encoding is available under CC BY-SA 4.0; rights in the underlying Spanish source edition remain governed by the source terms recorded below.",
        target="https://creativecommons.org/licenses/by-sa/4.0/",
    )
    if profile.source_rights_url:
        sub(availability, "licence", profile.rights_note, target=profile.source_rights_url)
    else:
        sub(availability, "p", profile.rights_note)

    notes_stmt = sub(file_desc, "notesStmt")
    translator_note = (
        f"Translation credit in source: {profile.translator}."
        if profile.translator
        else "The source EPUB does not identify the Spanish translator; none has been conjecturally supplied."
    )
    sub(notes_stmt, "note", translator_note, type="translation-credit")

    source_desc = sub(file_desc, "sourceDesc")
    bibliography = sub(source_desc, "biblStruct", type="electronic")
    monograph = sub(bibliography, "monogr")
    sub(monograph, "title", profile.title, level="m", xml_lang="es")
    sub(monograph, "author", "Jane Austen")
    if profile.translator:
        sub(monograph, "editor", profile.translator, role="translator")
    imprint = sub(monograph, "imprint")
    sub(imprint, "publisher", profile.provider)
    if profile.source_date:
        sub(imprint, "date", profile.source_date, when=profile.source_date)
    source_note = sub(bibliography, "note", type="source-provenance")
    source_note.text = f"Local source: assets/source-epub/{profile.filename}. EPUB UUID: {epub.uuid}. {profile.source_note} "
    if profile.source_url:
        reference = sub(source_note, "ref", profile.source_url, target=profile.source_url)

    encoding_desc = sub(header, "encodingDesc")
    project_desc = sub(encoding_desc, "projectDesc")
    project_text = (
        "Generated from the EPUB reading order while reconstructing logical chapters independently of file boundaries. "
        "Front matter, body, back matter, headings, paragraphs, inline emphasis, references, verse, explicit display letters, "
        "tables, ornaments, trailers, and source page milestones are retained where the source supplies them."
    )
    sub(project_desc, "p", project_text)
    editorial = sub(encoding_desc, "editorialDecl")
    correction = sub(editorial, "correction", status="low")
    sub(correction, "p", "No silent lexical or orthographic corrections are made; source spellings and punctuation are retained.")
    normalization = sub(editorial, "normalization", method="markup")
    sub(normalization, "p", "XHTML whitespace and packaging artifacts are normalized without modernizing the Spanish text.")
    segmentation = sub(editorial, "segmentation")
    sub(segmentation, "p", "Logical volumes and chapters follow the source edition; arbitrary EPUB file splits do not create textual divisions.")
    quotation = sub(editorial, "quotation", marks="all")
    sub(quotation, "p", "Prose dialogue remains in paragraphs because the EPUBs do not identify speakers semantically. Explicit inset letters and quotations are encoded without invented attribution.")

    profile_desc = sub(header, "profileDesc")
    creation = sub(profile_desc, "creation")
    sub(creation, "date", f"First published in English in {profile.first_publication}.", when=profile.first_publication, type="first-publication")
    lang_usage = sub(profile_desc, "langUsage")
    sub(lang_usage, "language", "Spanish", ident="es", usage="99")
    sub(lang_usage, "language", "English (uniform title and source-language metadata)", ident="en", usage="1")
    text_class = sub(profile_desc, "textClass")
    keywords = sub(text_class, "keywords", scheme="http://id.loc.gov/authorities/subjects")
    for term in ("English fiction", "Domestic fiction", "Love stories", "Translations into Spanish"):
        sub(keywords, "term", term)

    revision = sub(header, "revisionDesc")
    sub(
        revision,
        "change",
        "Converted the supplied Spanish EPUB into a source-faithful standalone TEI P5 edition.",
        when=today.isoformat(),
        who="#bookstacks-encoding",
        status="published",
    )
    return header


def add_title_page(front: etree._Element, profile: Profile) -> None:
    title_page = sub(front, "titlePage", type="epub-display")
    document_title = sub(title_page, "docTitle")
    sub(document_title, "titlePart", profile.title, type="main")
    sub(title_page, "docAuthor", "Jane Austen")
    if profile.translator:
        sub(title_page, "byline", f"Traducción: {profile.translator}")
    imprint = sub(title_page, "docImprint")
    sub(imprint, "publisher", profile.provider)
    if profile.source_date:
        sub(imprint, "docDate", profile.source_date)


def add_source_title_page(front: etree._Element, number: int, volume: str, series_numbers: str) -> None:
    title_page = sub(front, "titlePage", type="source-print", n=str(number))
    sub(title_page, "docEdition", f"Colección Universal, números {series_numbers}")
    sub(title_page, "docAuthor", "Jane Austen")
    document_title = sub(title_page, "docTitle")
    sub(document_title, "titlePart", "Orgullo y prejuicio", type="main")
    sub(document_title, "titlePart", "Novela", type="sub")
    sub(title_page, "byline", volume)
    imprint = sub(title_page, "docImprint")
    sub(imprint, "pubPlace", "Madrid")
    sub(imprint, "publisher", 'Talleres "Calpe"')
    source_date = sub(imprint, "docDate", "1924")
    source_date.tail = "; Precio: 1,50 pesetas"


def new_text_div(parent: etree._Element, context: Context, kind: str, suffix: str, head: str | None = None) -> etree._Element:
    division = sub(parent, "div", type=kind)
    division.set(XML_ID, f"{context.profile.text_id}-{suffix}")
    if head:
        sub(division, "head", head)
    return division


def find_document(epub: EpubData, name: str) -> SpineDocument | None:
    return next((document for document in epub.spine if document.name == name), None)


def add_orgullo_contents(front: etree._Element, epub: EpubData, context: Context) -> None:
    document = find_document(epub, "OPS/Indice.xhtml")
    if document is None:
        raise ValueError("Orgullo y prejuicio EPUB has no source contents page")
    outer = new_text_div(front, context, "contents", "front-contents", "Índice")
    headings = [normalized_text(element) for element in document.root.xpath("//h3") if normalized_text(element)]
    tables = document.root.xpath("//table")
    if len(headings) != 2 or len(tables) != 2:
        raise ValueError(f"Unexpected Orgullo source contents: {len(headings)} headings, {len(tables)} tables")
    for number, (heading, source_table) in enumerate(zip(headings, tables), start=1):
        division = sub(outer, "div", type="contents", n=str(number))
        division.set(XML_ID, f"{context.profile.text_id}-front-contents-{number}")
        sub(division, "head", heading)
        convert_table(source_table, division, context)


def build_front(profile: Profile, epub: EpubData, context: Context) -> etree._Element:
    front = tei("front")
    add_title_page(front, profile)
    if profile.slug == "pride-and-prejudice":
        add_source_title_page(front, 1, "Tomo I", "958 a 960")
        add_source_title_page(front, 2, "Tomo II y último", "961 a 963")
        biography_doc = find_document(epub, "OPS/Portada original_split_002.xhtml")
        if biography_doc is None or first_body(biography_doc) is None:
            raise ValueError("Missing source biographical note in Orgullo y prejuicio")
        biography = new_text_div(front, context, "biographical-note", "front-biographical-note", "Jane Austen")
        context.paragraph(biography, normalized_text(first_body(biography_doc)))
        add_orgullo_contents(front, epub, context)
    elif profile.slug == "persuasion":
        description = epub.values("description")
        if description:
            summary = new_text_div(front, context, "summary", "front-summary", "Sinopsis")
            context.paragraph(summary, description[0])
        provider = new_text_div(front, context, "publisher-note", "front-publisher-note", "Nota del proveedor")
        paragraph = context.paragraph(provider)
        paragraph.text = "El primer elemento del lomo del EPUB identifica al equipo Le Libros y su sitio de distribución."
    return front


def chapter_documents(profile: Profile, epub: EpubData) -> list[SpineDocument]:
    pattern = re.compile(profile.chapter_name_pattern)
    return [document for document in epub.spine if pattern.search(document.name)]


def find_chapter_heading(blocks: list[etree._Element], profile: Profile) -> int:
    pattern = re.compile(profile.chapter_heading_pattern)
    for index, block in enumerate(blocks):
        if local_name(block) in profile.chapter_heading_tags and pattern.fullmatch(normalized_text(block)):
            return index
    return -1


def first_source_page_title(document: SpineDocument) -> str | None:
    values = document.root.xpath('//*[@title and starts-with(@title, "Página:")]/@title')
    return values[0] if values else None


def chapter_parent(body_wrapper: etree._Element, profile: Profile, chapter_number: int, volume_nodes: list[etree._Element]) -> etree._Element:
    if not profile.volumes:
        return body_wrapper
    for index, (start, end, _) in enumerate(profile.volumes):
        if start <= chapter_number <= end:
            return volume_nodes[index]
    raise ValueError(f"Chapter {chapter_number} is outside configured volumes")


def build_page_chapters(profile: Profile, epub: EpubData, context: Context, body_wrapper: etree._Element) -> None:
    documents = chapter_documents(profile, epub)
    if len(documents) != profile.chapter_count:
        raise ValueError(f"{profile.title}: expected {profile.chapter_count} chapter documents, found {len(documents)}")

    volume_nodes: list[etree._Element] = []
    for volume_number, (_, _, heading) in enumerate(profile.volumes, start=1):
        volume = sub(body_wrapper, "div", type="volume", n=str(volume_number))
        volume.set(XML_ID, f"{profile.text_id}-volume-{volume_number}")
        sub(volume, "head", heading)
        volume_nodes.append(volume)

    for chapter_number, document in enumerate(documents, start=1):
        context.current_document = document.name
        body = first_body(document)
        if body is None:
            raise ValueError(f"No XHTML body in {document.name}")
        blocks = reading_blocks(body)
        heading_index = find_chapter_heading(blocks, profile)
        if heading_index < 0:
            raise ValueError(f"No chapter heading in {document.name}")
        source_heading = normalized_text(blocks[heading_index])
        parent = chapter_parent(body_wrapper, profile, chapter_number, volume_nodes)
        chapter = sub(parent, "div", type="chapter", n=str(chapter_number))
        chapter.set(XML_ID, f"{profile.text_id}-chapter-{chapter_number:03d}")
        sub(chapter, "head", source_heading)
        if profile.slug == "pride-and-prejudice":
            page_title = first_source_page_title(document)
            if page_title:
                context.page_break(chapter, page_title)

        trailer: str | None = None
        for block in blocks[heading_index + 1 :]:
            block_text = normalized_text(block)
            if local_name(block) in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                if re.match(r"(?i)^fin del tomo", block_text):
                    trailer = block_text
                    break
                if block_text:
                    label = sub(chapter, "ab", block_text, type="subheading")
                    label.set(XML_ID, f"{profile.text_id}-chapter-{chapter_number:03d}-subheading")
                continue
            convert_block(block, chapter, context)
        if profile.slug == "pride-and-prejudice":
            # One page marker in chapter XXVI is a standalone Wikisource span
            # between block elements. Inline conversion cannot attach it to a
            # paragraph, so retain any still-unseen marker at chapter level.
            for page_title in document.root.xpath('//*[@title and starts-with(@title, "Página:")]/@title'):
                context.page_break(chapter, page_title)
        if trailer:
            sub(chapter, "trailer", trailer)


def build_continuous_chapters(profile: Profile, epub: EpubData, context: Context, body_wrapper: etree._Element) -> None:
    chapter: etree._Element | None = None
    chapter_number = 0
    for document in epub.spine:
        if not document.name.startswith("index_split_") or document.name == "index_split_000.html":
            continue
        context.current_document = document.name
        body = first_body(document)
        if body is None:
            continue
        for block in reading_blocks(body):
            if local_name(block) != "p":
                continue
            classes = set(block.get("class", "").split())
            text = normalized_text(block)
            if "block_4" in classes and re.match(r"(?i)^cap.tulo\b", text):
                chapter_number += 1
                chapter = sub(body_wrapper, "div", type="chapter", n=str(chapter_number))
                chapter.set(XML_ID, f"{profile.text_id}-chapter-{chapter_number:03d}")
                sub(chapter, "head", text)
                continue
            if chapter is not None and "block_5" in classes and text:
                paragraph_from_source(block, chapter, context)
    if chapter_number != profile.chapter_count:
        raise ValueError(f"{profile.title}: expected {profile.chapter_count} chapters, found {chapter_number}")


def build_body(profile: Profile, epub: EpubData, context: Context) -> etree._Element:
    body = tei("body")
    translation = sub(body, "div", type="translation")
    translation.set(XML_ID, f"{profile.text_id}-text")
    if profile.mode == "continuous":
        build_continuous_chapters(profile, epub, context, translation)
    else:
        build_page_chapters(profile, epub, context, translation)
    return body


def add_back_div(back: etree._Element, context: Context, kind: str, suffix: str, heading: str, text: str) -> None:
    division = new_text_div(back, context, kind, suffix, heading)
    context.paragraph(division, text)


def build_back(profile: Profile, epub: EpubData, context: Context) -> etree._Element | None:
    back = tei("back")
    if profile.slug == "persuasion":
        document = find_document(epub, "OEBPS/Text/autor.xhtml")
        if document is not None and first_body(document) is not None:
            add_back_div(
                back,
                context,
                "biographical-note",
                "back-author-biography",
                "Jane Austen",
                normalized_text(first_body(document)),
            )
    elif profile.slug == "emma":
        add_back_div(
            back,
            context,
            "publisher-note",
            "back-publisher-note",
            "Nota del editor electrónico",
            "¿Te gustó este libro? Para más libros electrónicos gratuitos, visita freeditorial.com/es.",
        )
    elif profile.slug in {"sense-and-sensibility", "northanger-abbey", "pride-and-prejudice"}:
        add_back_div(
            back,
            context,
            "publisher-note",
            "back-publisher-note",
            "Nota del editor electrónico",
            "Gracias por leer este libro de Elejandría. El EPUB remite a la colección de obras de dominio público en castellano de www.elejandria.com.",
        )
    return back if len(back) else None


def build_document(profile: Profile, epub_path: Path) -> etree._ElementTree:
    epub = read_epub(epub_path)
    titles = epub.values("title")
    creators = epub.values("creator")
    languages = epub.values("language")
    if not titles or titles[0].casefold() != profile.title.casefold():
        raise ValueError(f"Unexpected EPUB title in {epub_path}: {titles}")
    if not creators or creators[0] != "Jane Austen" or not languages or languages[0] != "es":
        raise ValueError(f"Unexpected EPUB creator/language in {epub_path}: {creators}, {languages}")

    context = Context(profile)
    root = etree.Element(f"{{{TEI_NS}}}TEI", nsmap={None: TEI_NS})
    root.set(XML_ID, profile.text_id)
    root.set(XML_LANG, "es")
    root.append(build_header(profile, epub))
    text = sub(root, "text", xml_lang="es")
    text.append(build_front(profile, epub, context))
    text.append(build_body(profile, epub, context))
    back = build_back(profile, epub, context)
    if back is not None:
        text.append(back)
    return etree.ElementTree(root)


def validate_invariants(document: etree._ElementTree, profile: Profile) -> dict[str, int]:
    chapters = document.xpath('//tei:div[@type="chapter"]', namespaces=NS)
    paragraphs = document.xpath("//tei:text//tei:p", namespaces=NS)
    body_text = " ".join(document.xpath("//tei:body//text()", namespaces=NS))
    characters = len(re.sub(r"\s+", "", body_text))
    ids = document.xpath("//@xml:id", namespaces={"xml": XML_NS})
    duplicate_ids = {value for value in ids if ids.count(value) > 1}
    if duplicate_ids:
        raise ValueError(f"Duplicate xml:id values: {sorted(duplicate_ids)[:10]}")
    if len(chapters) != profile.chapter_count:
        raise ValueError(f"{profile.title}: expected {profile.chapter_count} chapters, found {len(chapters)}")
    if len(paragraphs) < profile.minimum_paragraphs:
        raise ValueError(f"{profile.title}: only {len(paragraphs)} paragraphs; expected at least {profile.minimum_paragraphs}")
    if characters < profile.minimum_characters:
        raise ValueError(f"{profile.title}: only {characters} body characters; expected at least {profile.minimum_characters}")
    for element_name in ("div", "p"):
        missing = document.xpath(f"//tei:text//tei:{element_name}[not(@xml:id)]", namespaces=NS)
        if missing:
            raise ValueError(f"{profile.title}: {len(missing)} {element_name} elements lack xml:id")
    if profile.slug == "pride-and-prejudice":
        pages = document.xpath("//tei:body//tei:pb", namespaces=NS)
        volumes = document.xpath('//tei:body//tei:div[@type="volume"]', namespaces=NS)
        contents_tables = document.xpath('//tei:front//tei:div[@type="contents"]//tei:table', namespaces=NS)
        if len(pages) != 488 or len(volumes) != 2 or len(contents_tables) != 2:
            raise ValueError(
                f"Orgullo semantic structure incomplete: {len(pages)} pages, {len(volumes)} volumes, {len(contents_tables)} contents tables"
            )
    if profile.slug == "persuasion":
        letters = document.xpath('//tei:body//tei:floatingText[@type="letter"]', namespaces=NS)
        if len(letters) != 4:
            raise ValueError(f"Persuasión: expected 4 display letters, found {len(letters)}")
    if profile.slug == "mansfield-park":
        verse_groups = document.xpath('//tei:body//tei:lg[@type="verse"]', namespaces=NS)
        if len(verse_groups) < 2:
            raise ValueError(f"Mansfield Park: expected at least 2 verse groups, found {len(verse_groups)}")
    return {
        "chapters": len(chapters),
        "paragraphs": len(paragraphs),
        "characters": characters,
        "page_breaks": len(document.xpath("//tei:body//tei:pb", namespaces=NS)),
        "letters": len(document.xpath("//tei:body//tei:floatingText", namespaces=NS)),
        "verse_groups": len(document.xpath("//tei:body//tei:lg", namespaces=NS)),
    }


def write_document(document: etree._ElementTree, output: Path) -> None:
    etree.indent(document, space="  ")
    serialized = etree.tostring(document, encoding="utf-8", xml_declaration=True, pretty_print=True)
    model = b'<?xml-model href="../tei_all.rng" schematypens="http://relaxng.org/ns/structure/1.0"?>\n'
    declaration, body = serialized.split(b"\n", 1)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(declaration + b"\n" + model + body)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--work", choices=[profile.slug for profile in PROFILES])
    args = parser.parse_args()

    schema = etree.RelaxNG(etree.parse(str(args.schema)))
    selected = [profile for profile in PROFILES if not args.work or profile.slug == args.work]
    failures = 0
    for profile in selected:
        source = args.source_dir / profile.filename
        output = args.output_dir / profile.output_name
        try:
            if not source.is_file():
                raise FileNotFoundError(source)
            document = build_document(profile, source)
            statistics = validate_invariants(document, profile)
            if not schema.validate(document):
                errors = "\n".join(str(entry) for entry in schema.error_log)
                raise ValueError(f"Relax NG validation failed:\n{errors}")
            write_document(document, output)
            print(
                f"Wrote {output}: {statistics['chapters']} chapters, "
                f"{statistics['paragraphs']} paragraphs, {statistics['characters']} body characters, "
                f"{statistics['page_breaks']} page breaks, {statistics['letters']} letters, "
                f"{statistics['verse_groups']} verse groups"
            )
        except Exception as exc:
            failures += 1
            print(f"FAIL {profile.title}: {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
