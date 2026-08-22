"""Normalize a root-level collection of legacy prose TEI into Bookstacks TEI."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
from pathlib import Path
import re
import sys

from lxml import etree


TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI_NS, "xml": XML_NS}
XML_ID = f"{{{XML_NS}}}id"
XML_LANG = f"{{{XML_NS}}}lang"


def tei(name: str, **attributes: str) -> etree._Element:
    element = etree.Element(f"{{{TEI_NS}}}{name}")
    for key, value in attributes.items():
        element.set(key, value)
    return element


def local_name(element: etree._Element) -> str:
    return etree.QName(element).localname


def clean_text(value: str | None) -> str:
    return " ".join((value or "").split())


def element_text(element: etree._Element | None) -> str:
    return clean_text("".join(element.itertext())) if element is not None else ""


def xml_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip().lstrip("#"))
    token = re.sub(r"-+", "-", token).strip("-") or "item"
    return token if re.match(r"^[A-Za-z_]", token) else f"id-{token}"


def direct_child(parent: etree._Element, name: str) -> etree._Element | None:
    return parent.find(f"{{{TEI_NS}}}{name}")


def replace_body_with_work(document: etree._ElementTree, work: etree._Element, title: str) -> None:
    body = document.find(".//tei:text/tei:body", NS)
    if body is None:
        raise ValueError("Source document has no TEI body")
    shared_blocks = [
        deepcopy(child)
        for child in body
        if isinstance(child.tag, str) and local_name(child) != "div"
    ]
    if shared_blocks:
        text = body.getparent()
        front = direct_child(text, "front")
        if front is None:
            front = tei("front")
            text.insert(text.index(body), front)
        credits = tei("div", type="credits")
        credits_head = tei("head")
        credits_head.text = "Edition"
        credits.append(credits_head)
        credits.extend(shared_blocks)
        front.append(credits)
    for child in list(body):
        body.remove(child)

    blocks: list[etree._Element] = []
    divisions: list[etree._Element] = []
    for child in work:
        if not isinstance(child.tag, str) or local_name(child) == "head":
            continue
        copied = deepcopy(child)
        if local_name(copied) == "div":
            divisions.append(copied)
        else:
            blocks.append(copied)

    if blocks:
        opening = tei("div", type="prologue")
        opening_head = tei("head")
        opening_head.text = "Prologue"
        opening.append(opening_head)
        opening.extend(blocks)
        body.append(opening)

    if divisions:
        body.extend(divisions)
    else:
        section = tei("div", type="section", n="1")
        section_head = tei("head")
        section_head.text = title
        section.append(section_head)
        section.extend(blocks)
        if blocks and len(body):
            body.remove(body[0])
        body.append(section)


def flatten_single_work_wrapper(document: etree._ElementTree, title: str) -> None:
    body = document.find(".//tei:text/tei:body", NS)
    if body is None:
        raise ValueError("Source document has no TEI body")
    direct_divisions = body.findall("tei:div", NS)
    if len(direct_divisions) != 1:
        return
    wrapper = direct_divisions[0]
    if wrapper.get("type") or element_text(direct_child(wrapper, "head")).casefold() != title.casefold():
        return
    child_divisions = wrapper.findall("tei:div", NS)
    if not child_divisions:
        return
    insertion = body.index(wrapper)
    body.remove(wrapper)
    for child in child_divisions:
        body.insert(insertion, deepcopy(child))
        insertion += 1


def normalize_division_types(document: etree._ElementTree) -> None:
    for division in document.xpath("//tei:text//tei:div", namespaces=NS):
        head = element_text(direct_child(division, "head"))
        folded = head.casefold()
        normalized_type: str | None = None
        if folded == "preface":
            normalized_type = "preface"
        elif folded == "prologue":
            normalized_type = "prologue"
        elif folded == "epilogue":
            normalized_type = "epilogue"
        elif folded in {"introduction", "[with an introduction by edward garnett]"}:
            normalized_type = "introduction"
        elif "names of the characters" in folded:
            normalized_type = "characters"
        elif folded == "a novel":
            normalized_type = "title-page"
        elif folded.startswith("translated from"):
            normalized_type = "credits"
        elif folded.startswith("london:"):
            normalized_type = "publication-note"
        elif folded in {"the end", "the riverside press", "cambridge . massachusetts", "u . s . a"}:
            normalized_type = "colophon"
        elif not division.get("type") and division.get("n") and division.findall("tei:p", NS):
            normalized_type = "chapter"
        elif not division.get("type"):
            normalized_type = "section"
        if normalized_type:
            division.set("type", normalized_type)
        if normalized_type in {"preface", "prologue", "epilogue", "introduction"}:
            division.attrib.pop("n", None)


def normalize_header(document: etree._ElementTree, title: str, text_id: str) -> None:
    header = document.getroot().find("tei:teiHeader", NS)
    if header is None:
        raise ValueError("Source document has no TEI header")
    file_desc = direct_child(header, "fileDesc")
    if file_desc is None:
        raise ValueError("Source document has no TEI fileDesc")
    title_stmt = direct_child(file_desc, "titleStmt")
    if title_stmt is None:
        raise ValueError("Source document has no TEI titleStmt")
    title_element = direct_child(title_stmt, "title")
    if title_element is None:
        title_element = tei("title")
        title_stmt.insert(0, title_element)
    title_element.text = title

    for old in title_stmt.xpath('./tei:respStmt[@xml:id="bookstacks-encoding"]', namespaces=NS):
        title_stmt.remove(old)
    responsibility = tei("respStmt")
    responsibility.set(XML_ID, "bookstacks-encoding")
    resp = tei("resp")
    resp.text = "TEI P5 normalization, structural identifiers, and collection separation"
    name = tei("name")
    name.text = "Bookstacks project"
    responsibility.extend((resp, name))
    title_stmt.append(responsibility)

    edition_stmt = direct_child(file_desc, "editionStmt")
    if edition_stmt is None:
        edition_stmt = tei("editionStmt")
        edition = tei("edition", n="1.0")
        edition.text = "Bookstacks TEI edition, based on the source electronic edition"
        edition_stmt.append(edition)
        file_desc.insert(file_desc.index(title_stmt) + 1, edition_stmt)

    publication = direct_child(file_desc, "publicationStmt")
    if publication is None:
        publication = tei("publicationStmt")
        file_desc.insert(file_desc.index(edition_stmt) + 1, publication)
    for child in list(publication):
        publication.remove(child)
    publisher = tei("publisher")
    publisher.text = "Bookstacks project"
    place = tei("pubPlace")
    place.text = "United States"
    published = tei("date", when=date.today().isoformat())
    published.text = date.today().strftime("%d %B %Y")
    identifier = tei("idno", type="local")
    identifier.text = text_id
    availability = tei("availability", status="free")
    licence = tei("licence", target="https://creativecommons.org/licenses/by-sa/4.0/")
    licence.text = (
        "This derived TEI file is made available under the Creative Commons "
        "Attribution-ShareAlike 4.0 International License; source rights remain "
        "as recorded in sourceDesc."
    )
    availability.append(licence)
    publication.extend((publisher, place, published, identifier, availability))

    revision = direct_child(header, "revisionDesc")
    if revision is None:
        revision = tei("revisionDesc")
        header.append(revision)
    for old in revision.xpath('./tei:change[@who="#bookstacks-encoding"]', namespaces=NS):
        revision.remove(old)
    change = tei("change", when=date.today().isoformat(), who="#bookstacks-encoding")
    change.text = "Normalized legacy TEI structure and added stable project identifiers."
    revision.insert(0, change)


def add_structural_ids(document: etree._ElementTree, text_id: str) -> None:
    root = document.getroot()
    root.set(XML_ID, text_id)
    root.set(XML_LANG, "en")
    text = document.getroot().find("tei:text", NS)
    if text is None:
        raise ValueError("Source document has no TEI text")
    text.set(XML_LANG, "en")

    used: set[str] = {text_id}
    counters: dict[tuple[int, str], int] = {}
    for division in document.xpath("//tei:text//tei:div", namespaces=NS):
        parent = division.getparent()
        parent_id = parent.get(XML_ID) if parent is not None else None
        parent_id = parent_id or f"{text_id}-eng"
        kind = xml_token(division.get("subtype") or division.get("type") or "division")
        key = (id(parent), kind)
        counters[key] = counters.get(key, 0) + 1
        number = xml_token(division.get("n") or f"{counters[key]:03d}")
        candidate = xml_token(f"{parent_id}-{kind}-{number}")
        suffix = 2
        unique = candidate
        while unique in used:
            unique = f"{candidate}-{suffix}"
            suffix += 1
        division.set(XML_ID, unique)
        used.add(unique)

    for index, paragraph in enumerate(document.xpath("//tei:text//tei:p", namespaces=NS), 1):
        paragraph.set(XML_ID, f"eng-p-{index:06d}")
    for index, utterance in enumerate(
        document.xpath('//tei:text//tei:said | //tei:text//tei:q[@type="spoken" or @who or @toWhom]', namespaces=NS),
        1,
    ):
        utterance.set(XML_ID, f"eng-utterance-{index:06d}")

    for element in document.xpath("//*[@id and namespace-uri(@id) = '']"):
        if element.get(XML_ID) is None:
            element.set(XML_ID, xml_token(element.get("id") or "item"))
        element.attrib.pop("id", None)


def write_document(document: etree._ElementTree, output: Path, schema: etree.RelaxNG) -> None:
    if not schema.validate(document):
        details = "\n".join(str(entry) for entry in schema.error_log)
        raise ValueError(f"Generated TEI failed Relax NG validation:\n{details}")
    output.parent.mkdir(parents=True, exist_ok=True)
    processing = etree.ProcessingInstruction(
        "xml-model", 'href="../tei_all.rng" schematypens="http://relaxng.org/ns/structure/1.0"'
    )
    root = document.getroot()
    root.addprevious(processing)
    document.write(str(output), encoding="UTF-8", xml_declaration=True, pretty_print=True)
    print(f"Generated {output.resolve()}")


def build_one(
    source: Path,
    output: Path,
    work_slug: str,
    title: str,
    author_slug: str,
    schema: etree.RelaxNG,
    selected_work: etree._Element | None = None,
) -> None:
    parser = etree.XMLParser(collect_ids=False, huge_tree=True, remove_blank_text=False)
    document = etree.parse(str(source), parser)
    if selected_work is not None:
        replace_body_with_work(document, selected_work, title)
    else:
        flatten_single_work_wrapper(document, title)
    text_id = f"{author_slug}-{work_slug}"
    normalize_division_types(document)
    normalize_header(document, title, text_id)
    add_structural_ids(document, text_id)
    write_document(document, output, schema)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-pattern", required=True)
    parser.add_argument("--source-prefix", required=True)
    parser.add_argument("--author-slug", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    args = parser.parse_args()

    pattern = Path(args.source_pattern)
    sources = sorted(pattern.parent.glob(pattern.name))
    if not sources:
        raise FileNotFoundError(f"No legacy TEI files matched {args.source_pattern}")
    schema = etree.RelaxNG(etree.parse(str(args.schema)))
    filename_pattern = re.compile(rf"^{re.escape(args.source_prefix)}_(.+)_en\.xml$")

    for source in sources:
        match = filename_pattern.match(source.name)
        if match is None:
            raise ValueError(f"Unexpected source filename: {source.name}")
        work_slug = match.group(1)
        document = etree.parse(str(source), etree.XMLParser(collect_ids=False, huge_tree=True))
        title = clean_text(document.xpath("string(//tei:titleStmt/tei:title[1])", namespaces=NS))

        if args.author_slug == "turgenev" and work_slug == "the-torrents-of-spring":
            works = document.xpath("//tei:text/tei:body/tei:div", namespaces=NS)
            expected = {
                "the torrents of spring": ("the-torrents-of-spring", "The Torrents of Spring"),
                "first love": ("first-love", "First Love"),
                "mumu": ("mumu", "Mumu"),
            }
            for work in works:
                work_title = element_text(direct_child(work, "head"))
                if work_title.casefold() not in expected:
                    raise ValueError(f"Unexpected omnibus work: {work_title}")
                split_slug, split_title = expected[work_title.casefold()]
                output = args.output_dir / f"{args.author_slug}_{split_slug}_eng.xml"
                build_one(source, output, split_slug, split_title, args.author_slug, schema, work)
            continue

        output = args.output_dir / f"{args.author_slug}_{work_slug}_eng.xml"
        build_one(source, output, work_slug, title, args.author_slug, schema)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
