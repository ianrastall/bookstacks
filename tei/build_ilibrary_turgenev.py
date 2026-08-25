#!/usr/bin/env python3
"""Download iLibrary's public-domain Turgenev texts and encode them as TEI P5.

The source HTML is cached under assets/ so that extraction can be audited and
repeated without issuing another request for every source section.  Only the
seven works that have an exact English counterpart in Bookstacks are selected.
iLibrary does not currently list Новь (Virgin Soil).
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from lxml import etree, html


TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NSMAP = {None: TEI_NS}
XML_ID = f"{{{XML_NS}}}id"
XML_LANG = f"{{{XML_NS}}}lang"
BASE_URL = "https://ilibrary.ru"
USER_AGENT = "Bookstacks-TEI-Builder/1.0"


@dataclass(frozen=True)
class Work:
    slug: str
    title: str
    source_id: int


WORKS = (
    Work("the-torrents-of-spring", "Вешние воды", 4302),
    Work("rudin", "Рудин", 1198),
    Work("on-the-eve", "Накануне", 1648),
    Work("mumu", "Муму", 1250),
    Work("first-love", "Первая любовь", 1335),
    Work("fathers-and-children", "Отцы и дети", 96),
    Work("a-house-of-gentlefolk", "Дворянское гнездо", 1647),
)


def tei(name: str, **attributes: str) -> etree._Element:
    return etree.Element(f"{{{TEI_NS}}}{name}", attributes)


def sub(parent: etree._Element, name: str, text: str | None = None, **attributes: str) -> etree._Element:
    child = etree.SubElement(parent, f"{{{TEI_NS}}}{name}", attributes)
    if text is not None:
        child.text = text
    return child


def source_url(work: Work, page: int) -> str:
    return f"{BASE_URL}/text/{work.source_id}/p.{page}/index.html"


def fetch(url: str, destination: Path, refresh: bool, delay: float) -> bytes:
    if destination.exists() and not refresh:
        return destination.read_bytes()
    if delay:
        time.sleep(delay)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=45) as response:
        payload = response.read()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return payload


def parse_html(payload: bytes) -> html.HtmlElement:
    # All selected pages declare windows-1251.  Decoding before HTML parsing
    # avoids platform-dependent guesses by libxml2.
    return html.fromstring(payload.decode("windows-1251"))


def c1_to_unicode(value: str) -> str:
    """Repair HTML numeric references such as &#151; parsed as C1 controls."""
    repaired: list[str] = []
    for character in value:
        code = ord(character)
        if 0x80 <= code <= 0x9F:
            try:
                character = bytes([code]).decode("windows-1252")
            except UnicodeDecodeError:
                pass
        repaired.append(character)
    return "".join(repaired)


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = c1_to_unicode(value).replace("\xa0", " ")
    return re.sub(r"\s+", " ", value)


def append_text(parent: etree._Element, value: str | None) -> None:
    text = clean_text(value)
    if not text:
        return
    if len(parent):
        parent[-1].tail = (parent[-1].tail or "") + text
    else:
        parent.text = (parent.text or "") + text


def trim_mixed_content(element: etree._Element) -> None:
    if element.text:
        element.text = element.text.lstrip()
    if len(element) and element[-1].tail:
        element[-1].tail = element[-1].tail.rstrip()
    elif element.text:
        element.text = element.text.rstrip()


def note_number(node: html.HtmlElement) -> str | None:
    candidates = node.xpath(".//a/@id | .//a/@name | .//a/text()")
    for candidate in candidates:
        match = re.search(r"(\d+)", str(candidate))
        if match:
            return match.group(1)
    return None


def note_definitions(container: html.HtmlElement) -> dict[str, str]:
    notes: dict[str, str] = {}
    for node in container.xpath('.//div[contains(concat(" ", normalize-space(@class), " "), " fns ")]//span[starts-with(@id, "fnt")]'):
        number = re.search(r"(\d+)", node.get("id", ""))
        paragraphs = node.xpath(".//z")
        text_value = " ".join(clean_text(p.text_content()).strip() for p in paragraphs)
        if number and text_value:
            notes[number.group(1)] = text_value
    return notes


def copy_inline(
    source: html.HtmlElement,
    target: etree._Element,
    notes: dict[str, str],
    page_url: str,
) -> None:
    append_text(target, source.text)
    for child in source:
        tag = child.tag.lower() if isinstance(child.tag, str) else ""
        output: etree._Element | None = None
        if tag in {"o", "c", "script", "style"}:
            pass
        elif tag == "fn":
            number = note_number(child)
            output = sub(target, "note", n=number or "", place="foot")
            output.set(XML_ID, f"rus-note-placeholder-{number or 'x'}")
            output.text = notes.get(number or "", "Примечание отсутствует в исходной HTML-странице.")
        elif tag == "br":
            output = sub(target, "lb")
        elif tag in {"i", "em"}:
            output = sub(target, "hi", rend="italic")
            copy_inline(child, output, notes, page_url)
        elif tag in {"b", "strong"}:
            output = sub(target, "hi", rend="bold")
            copy_inline(child, output, notes, page_url)
        elif tag == "sup":
            output = sub(target, "hi", rend="superscript")
            copy_inline(child, output, notes, page_url)
        elif tag == "a":
            href = child.get("href")
            output = sub(target, "ref", target=urljoin(page_url, href) if href else page_url)
            copy_inline(child, output, notes, page_url)
        elif tag == "span":
            style = (child.get("style") or "").casefold()
            classes = set((child.get("class") or "").split())
            if "letter-spacing" in style:
                output = sub(target, "hi", rend="letter-spaced")
                copy_inline(child, output, notes, page_url)
            elif "dedication" in classes:
                output = sub(target, "hi", rend="dedication")
                copy_inline(child, output, notes, page_url)
            else:
                copy_inline(child, target, notes, page_url)
        else:
            copy_inline(child, target, notes, page_url)
        append_text(target, child.tail)
        if output is not None:
            trim_mixed_content(output)


def paragraph_from(source: html.HtmlElement, notes: dict[str, str], page_url: str) -> etree._Element:
    paragraph = tei("p")
    copy_inline(source, paragraph, notes, page_url)
    trim_mixed_content(paragraph)
    return paragraph


def verse_from(source: html.HtmlElement, notes: dict[str, str], page_url: str) -> etree._Element:
    group = tei("lg")
    for verse_line in source.xpath(".//v"):
        line = sub(group, "l")
        copy_inline(verse_line, line, notes, page_url)
        trim_mixed_content(line)
    return group


def epigraph_from(source: html.HtmlElement, notes: dict[str, str], page_url: str) -> etree._Element:
    epigraph = tei("epigraph")
    verses = source.xpath(".//v")
    if verses:
        quote = sub(epigraph, "quote")
        quote.append(verse_from(source, notes, page_url))
    else:
        quote = sub(epigraph, "quote")
        quote.text = clean_text(source.text_content()).strip()
    citations = source.xpath('.//*[contains(concat(" ", normalize-space(@class), " "), " epigraf_source ")]')
    if citations:
        citation = clean_text(citations[0].text_content()).strip()
        if citation:
            sub(epigraph, "bibl", citation)
    return epigraph


def letter_from(source: html.HtmlElement, notes: dict[str, str], page_url: str) -> etree._Element:
    quote = tei("quote", type="letter")
    for child in source.iterchildren():
        classes = set((child.get("class") or "").split())
        if "letter_formaddress" in classes:
            salute = sub(quote, "p", rend="salutation")
            copy_inline(child, salute, notes, page_url)
            trim_mixed_content(salute)
        elif "letter_signature" in classes:
            signed = sub(quote, "p", rend="signature")
            copy_inline(child, signed, notes, page_url)
            trim_mixed_content(signed)
        elif child.tag.lower() == "z":
            quote.append(paragraph_from(child, notes, page_url))
        elif clean_text(child.text_content()).strip():
            paragraph = sub(quote, "p")
            copy_inline(child, paragraph, notes, page_url)
            trim_mixed_content(paragraph)
    return quote


def is_navigation(node: html.HtmlElement) -> bool:
    if node.tag in {"iframe", "script", "style"}:
        return True
    if node.get("id") in {"tbd", "bnav", "bnbg"}:
        return True
    if node.xpath('.//*[@id="bnav" or @id="bnbg"]'):
        return True
    classes = set((node.get("class") or "").split())
    return bool(classes & {"fns", "thdr", "author", "title"})


def append_source_block(
    source: html.HtmlElement,
    division: etree._Element,
    notes: dict[str, str],
    page_url: str,
) -> bool:
    tag = source.tag.lower() if isinstance(source.tag, str) else ""
    classes = set((source.get("class") or "").split())
    if is_navigation(source) or tag == "br":
        return False
    if tag == "z":
        if source.xpath(".//v"):
            division.append(verse_from(source, notes, page_url))
        else:
            paragraph = paragraph_from(source, notes, page_url)
            if clean_text("".join(paragraph.itertext())).strip():
                division.append(paragraph)
        return True
    if tag in {"pm", "pms"} or source.xpath("./pm | ./pms"):
        division.append(verse_from(source, notes, page_url))
        return True
    if "epigraf" in classes:
        division.append(epigraph_from(source, notes, page_url))
        return True
    if "letter" in classes:
        division.append(letter_from(source, notes, page_url))
        return True
    if "dedication" in classes:
        opener = sub(division, "opener")
        dedication = sub(opener, "salute")
        copy_inline(source, dedication, notes, page_url)
        trim_mixed_content(dedication)
        return True
    if classes & {"i0", "tc"} and "✦" in clean_text(source.text_content()):
        sub(division, "milestone", unit="section", rend="ornament")
        return True
    if "divider_line_short_0" in classes:
        sub(division, "milestone", unit="section", rend="separator")
        return True
    text_value = clean_text(source.text_content()).strip()
    if text_value and tag in {"div", "span"}:
        paragraph = sub(division, "p", rend="center" if "centered" in classes else "block")
        copy_inline(source, paragraph, notes, page_url)
        trim_mixed_content(paragraph)
        return True
    return False


def total_pages(document: html.HtmlElement) -> int:
    values = document.xpath('//*[@id="toc"]/text()')
    if values:
        match = re.search(r"\d+\s*/\s*(\d+)", values[0])
        if match:
            return int(match.group(1))
    return 1


def print_source(document: html.HtmlElement) -> str:
    descriptions = document.xpath('//meta[translate(@name, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")="description"]/@content')
    if not descriptions:
        return "Print source not stated in the source HTML."
    description = clean_text(descriptions[0]).strip()
    match = re.search(r"Источник:\s*(.*?)\s*Интернет-библиотека", description)
    return match.group(1).strip() if match else description


def new_division(body: etree._Element, kind: str, number: str, work: Work, serial: int) -> etree._Element:
    division = sub(body, "div", type=kind, n=number)
    division.set(XML_ID, f"turgenev-{work.slug}-rus-{kind}-{serial:03d}")
    return division


def route_safe_number(heading: str) -> str:
    special = {
        "эпилог": "epilogue",
        "заключение": "conclusion",
        "послесловие": "postscript",
    }
    return special.get(heading.casefold(), heading)


def build_body(work: Work, pages: list[tuple[int, str, html.HtmlElement]]) -> etree._Element:
    body = tei("body")
    current: etree._Element | None = None
    division_serial = 0
    page_started = False

    for page_number, page_url, document in pages:
        container = document.get_element_by_id("text")
        notes = note_definitions(container)
        page_started = False
        for node in container.iterchildren():
            tag = node.tag.lower() if isinstance(node.tag, str) else ""
            if tag in {"h2", "h3", "h4"}:
                heading = clean_text(node.text_content()).strip()
                if not heading:
                    continue
                division_serial += 1
                current = new_division(body, "chapter", route_safe_number(heading), work, division_serial)
                sub(current, "head", heading)
                if not page_started:
                    sub(current, "pb", n=str(page_number), facs=page_url)
                    page_started = True
                continue
            if is_navigation(node) or tag == "br":
                continue
            if current is None:
                division_serial += 1
                kind = "text" if len(pages) == 1 else "prologue"
                current = new_division(body, kind, "1", work, division_serial)
            if not page_started:
                sub(current, "pb", n=str(page_number), facs=page_url)
                page_started = True
            append_source_block(node, current, notes, page_url)

    paragraph_number = 0
    note_number_value = 0
    for paragraph in body.xpath(".//tei:p", namespaces={"tei": TEI_NS}):
        paragraph_number += 1
        paragraph.set(XML_ID, f"rus-p-{paragraph_number:06d}")
    for note in body.xpath(".//tei:note", namespaces={"tei": TEI_NS}):
        note_number_value += 1
        note.set(XML_ID, f"rus-note-{note_number_value:06d}")
    return body


def build_header(work: Work, first_url: str, source_citation: str) -> etree._Element:
    today = date.today()
    header = tei("teiHeader")
    file_desc = sub(header, "fileDesc")
    title_stmt = sub(file_desc, "titleStmt")
    sub(title_stmt, "title", work.title)
    author = sub(title_stmt, "author")
    person = sub(author, "persName", "Иван Сергеевич Тургенев")
    sub(person, "note", "1818–1883", type="dates")
    source_resp = sub(title_stmt, "respStmt")
    sub(source_resp, "resp", "Source HTML publication and proofreading")
    sub(source_resp, "name", "Интернет-библиотека Алексея Комарова")
    encoding_resp = sub(title_stmt, "respStmt")
    encoding_resp.set(XML_ID, "bookstacks-encoding")
    sub(encoding_resp, "resp", "TEI P5 encoding, structural identifiers, and source-note integration")
    sub(encoding_resp, "name", "Bookstacks project")

    edition_stmt = sub(file_desc, "editionStmt")
    sub(edition_stmt, "edition", "Bookstacks TEI edition, based on the source HTML edition", n="1.0")
    publication_stmt = sub(file_desc, "publicationStmt")
    sub(publication_stmt, "publisher", "Bookstacks project")
    sub(publication_stmt, "pubPlace", "United States")
    sub(publication_stmt, "date", today.strftime("%d %B %Y"), when=today.isoformat())
    sub(publication_stmt, "idno", f"turgenev-{work.slug}", type="local")
    availability = sub(publication_stmt, "availability", status="free")
    sub(
        availability,
        "licence",
        "The Bookstacks TEI encoding is available under CC BY-SA 4.0. The underlying Turgenev text is public domain; source-site selection and presentation are not reproduced.",
        target="https://creativecommons.org/licenses/by-sa/4.0/",
    )

    source_desc = sub(file_desc, "sourceDesc")
    paragraph = sub(source_desc, "p")
    paragraph.text = f"Born-digital transcription from {source_citation} Published as HTML by "
    reference = sub(paragraph, "ref", "Интернет-библиотека Алексея Комарова", target=first_url)
    reference.tail = ". The source page identifies the literary work as public domain."

    profile = sub(header, "profileDesc")
    languages = sub(profile, "langUsage")
    sub(languages, "language", "Russian", ident="ru")
    text_class = sub(profile, "textClass")
    sub(text_class, "classCode", "PG", scheme="http://id.loc.gov/authorities/classification")
    keywords = sub(text_class, "keywords")
    sub(keywords, "term", "Russian literature")
    sub(keywords, "term", "Fiction")

    encoding = sub(header, "encodingDesc")
    project = sub(encoding, "projectDesc")
    sub(
        project,
        "p",
        "Generated from the work's paginated iLibrary HTML. Source navigation and presentation were omitted; headings, paragraphs, verse, inline emphasis, notes, epigraphs, dedications, ornaments, and HTML-section boundaries were retained.",
    )
    revision = sub(header, "revisionDesc")
    sub(
        revision,
        "change",
        "Encoded the Russian source as standalone TEI P5.",
        when=today.isoformat(),
        who="#bookstacks-encoding",
    )
    return header


def build_work(
    work: Work,
    cache_dir: Path,
    output_dir: Path,
    schema: etree.RelaxNG,
    refresh: bool,
    delay: float,
) -> Path:
    first_path = cache_dir / work.slug / "p.1.html"
    first_payload = fetch(source_url(work, 1), first_path, refresh, delay)
    first_document = parse_html(first_payload)
    count = total_pages(first_document)
    pages = [(1, source_url(work, 1), first_document)]
    for page_number in range(2, count + 1):
        url = source_url(work, page_number)
        payload = fetch(url, cache_dir / work.slug / f"p.{page_number}.html", refresh, delay)
        pages.append((page_number, url, parse_html(payload)))

    root = etree.Element(f"{{{TEI_NS}}}TEI", nsmap=NSMAP)
    root.set(XML_LANG, "ru")
    root.set(XML_ID, f"turgenev-{work.slug}")
    root.append(build_header(work, source_url(work, 1), print_source(first_document)))
    text = sub(root, "text")
    text.set(XML_LANG, "ru")
    text.append(build_body(work, pages))
    document = etree.ElementTree(root)
    if not schema.validate(document):
        details = "\n".join(str(entry) for entry in schema.error_log)
        raise ValueError(f"Generated {work.title} TEI failed validation:\n{details}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"turgenev_{work.slug}_rus.xml"
    processing = etree.ProcessingInstruction(
        "xml-model", 'href="../tei_all.rng" schematypens="http://relaxng.org/ns/structure/1.0"'
    )
    root.addprevious(processing)
    document.write(str(output), encoding="UTF-8", xml_declaration=True, pretty_print=True)
    print(f"Generated {output.resolve()} from {count} source HTML section(s)")
    return output


def check_robots(works: tuple[Work, ...]) -> None:
    parser = RobotFileParser(f"{BASE_URL}/robots.txt")
    parser.read()
    blocked = [source_url(work, 1) for work in works if not parser.can_fetch(USER_AGENT, source_url(work, 1))]
    if blocked:
        raise PermissionError("robots.txt disallows selected source URL(s): " + ", ".join(blocked))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--refresh", action="store_true", help="Download every HTML page again")
    parser.add_argument("--delay", type=float, default=0.15, help="Seconds between uncached requests")
    parser.add_argument("--work", action="append", choices=[work.slug for work in WORKS])
    args = parser.parse_args()

    selected = tuple(work for work in WORKS if not args.work or work.slug in args.work)
    check_robots(selected)
    schema = etree.RelaxNG(etree.parse(str(args.schema)))
    for work in selected:
        build_work(work, args.cache_dir, args.output_dir, schema, args.refresh, args.delay)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
