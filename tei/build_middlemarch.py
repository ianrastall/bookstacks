"""Build a standalone TEI P5 edition of George Eliot's Middlemarch.

The Open Editions source is an eight-file, HTML-like research corpus rather
than well-formed TEI.  This converter resolves the source's checked-in merge
conflicts, repairs its known malformed annotation tags, preserves its speech
and free-indirect-discourse attribution, and supplies the document structure
and identifiers required by Bookstacks.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
from pathlib import Path
import re
import subprocess
import sys

from lxml import etree, html


TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NSMAP = {None: TEI_NS}
BOOK_TITLES = {
    1: "Miss Brooke",
    2: "Old and Young",
    3: "Waiting for Death",
    4: "Three Love Problems",
    5: "The Dead Hand",
    6: "The Widow and the Wife",
    7: "Two Temptations",
    8: "Sunset and Sunrise",
}
ROMAN_BOOKS = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII"}
POINTER_ALIASES = {
    "Bulstrode": "B",
    "Chicely": "Chichely",
    "LAD": "Lad",
    "Mawmsey": "MrMawmsey",
    "MC": "MB",
    "MrB": "MrV",
    "Neumann": "Naumann",
    "RafB": "Raffles",
    "Thesinger": "Thesiger",
}
PERSON_NAMES = {
    "Abel": "Mrs. Abel",
    "B": "Nicholas Bulstrode",
    "Ben": "Ben Garth",
    "C": "Edward Casaubon",
    "Celia": "Celia Brooke",
    "D": "Dorothea Brooke",
    "F": "Fred Vincy",
    "FB": "Camden Farebrother",
    "JC": "Sir James Chettam",
    "LC": "Lady Chettam",
    "Lad": "Will Ladislaw",
    "Lyd": "Tertius Lydgate",
    "M": "Mary Garth",
    "MB": "Mr. Brooke",
    "MFB": "Mrs. Farebrother",
    "MM": "Middlemarch narrator",
    "MrF": "Peter Featherstone",
    "MrG": "Caleb Garth",
    "MrV": "Walter Vincy",
    "MrsB": "Harriet Bulstrode",
    "MrsCad": "Mrs. Cadwallader",
    "MrsG": "Susan Garth",
    "MrsV": "Lucy Vincy",
    "R": "Rosamond Vincy",
}


def tei(name: str, text: str | None = None, **attributes: str) -> etree._Element:
    element = etree.Element(f"{{{TEI_NS}}}{name}")
    if text is not None:
        element.text = text
    for key, value in attributes.items():
        if key == "xml_id":
            element.set(f"{{{XML_NS}}}id", value)
        elif key == "xml_lang":
            element.set(f"{{{XML_NS}}}lang", value)
        else:
            element.set(key.replace("_", "-"), value)
    return element


def append(parent: etree._Element, *children: etree._Element) -> etree._Element:
    for child in children:
        parent.append(child)
    return parent


def resolve_conflicts(source: str) -> str:
    pattern = re.compile(
        r"^<<<<<<<[^\n]*\n(.*?)^=======\s*$\n.*?^>>>>>>>[^\n]*\n?",
        flags=re.MULTILINE | re.DOTALL,
    )
    while pattern.search(source):
        source = pattern.sub(lambda match: match.group(1), source)
    if re.search(r"^(?:<<<<<<<|=======|>>>>>>>)", source, flags=re.MULTILINE):
        raise ValueError("unresolved merge-conflict marker remains in source")
    return source


def repair_source(source: str) -> str:
    source = resolve_conflicts(source.replace("\r\n", "\n"))
    # The character list is source metadata placed between the Prelude and
    # Chapter I.  The consolidated edition supplies a complete listPerson in
    # the header, so it must not leak into the Prelude's reading text.
    source = re.sub(
        r"<list\s+type=[\"']Characters[\"'][^>]*>.*?</list>",
        "",
        source,
        flags=re.IGNORECASE | re.DOTALL,
    )
    source = re.sub(r"(<epigraph\b[^>]*>)\s*>", r"\1", source, flags=re.IGNORECASE)
    source = re.sub(r"<sai\b", "<said", source, flags=re.IGNORECASE)
    source = re.sub(r"<saidwho\b", "<said who", source, flags=re.IGNORECASE)
    source = re.sub(
        r"(<said\s+who\s*=\s*[\"'][^\"']+[\"'])(?=[A-Za-z])",
        r"\1>",
        source,
        flags=re.IGNORECASE,
    )
    source = re.sub(r"</(?:fid)(?:\s+who\s*=\s*[\"'][^\"']+[\"'])?\s*>", "</said>", source, flags=re.IGNORECASE)
    source = re.sub(r"</fid(?=\s*</p>)", "</said>", source, flags=re.IGNORECASE)
    source = re.sub(r"</fid\s+(?=Mr\.\s+Mawmsey)", "</said> ", source, flags=re.IGNORECASE)
    source = re.sub(r"<fid\b", '<said direct="false" aloud="false"', source, flags=re.IGNORECASE)
    source = re.sub(r"</fi\s*>", "</first>", source, flags=re.IGNORECASE)
    source = re.sub(r"</irst\s*>", "</first>", source, flags=re.IGNORECASE)
    return source


def repository_revision(source_dir: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(source_dir), "rev-parse", "--short=12", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown revision"


def normalize_pointer(value: str | None) -> str | None:
    if not value:
        return None
    identifiers = []
    for token in value.split():
        identifier = token.lstrip("#")
        identifier = POINTER_ALIASES.get(identifier, identifier)
        identifier = re.sub(r"[^A-Za-z0-9_.-]+", "-", identifier).strip("-")
        if identifier:
            identifiers.append(f"#{identifier}")
    return " ".join(identifiers) or None


def display_name(identifier: str) -> str:
    if identifier in PERSON_NAMES:
        return PERSON_NAMES[identifier]
    words = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", identifier).replace("_", " ")
    words = re.sub(r"^Mrs\b", "Mrs.", words)
    words = re.sub(r"^Mr\b", "Mr.", words)
    return words[:1].upper() + words[1:]


class BodyBuilder:
    def __init__(self) -> None:
        self.paragraph_count = 0
        self.said_count = 0
        self.speakers: Counter[str] = Counter()

    @staticmethod
    def normalized_space(value: str | None) -> str | None:
        if value is None:
            return None
        return re.sub(r"\s+", " ", value)

    def copy_mixed_content(self, source: etree._Element, target: etree._Element, chapter_id: str) -> None:
        target.text = self.normalized_space(source.text)
        for child in source:
            converted = self.convert_inline(child, chapter_id)
            tail = self.normalized_space(child.tail)
            if converted is None:
                if len(target):
                    target[-1].tail = (target[-1].tail or "") + (self.normalized_space("".join(child.itertext())) or "") + (tail or "")
                else:
                    target.text = (target.text or "") + (self.normalized_space("".join(child.itertext())) or "") + (tail or "")
                continue
            target.append(converted)
            converted.tail = tail

        if target.text:
            target.text = target.text.lstrip()
        if len(target) and target[-1].tail:
            target[-1].tail = target[-1].tail.rstrip()
        elif target.text:
            target.text = target.text.rstrip()

    def convert_inline(self, source: etree._Element, chapter_id: str) -> etree._Element | None:
        name = source.tag.lower() if isinstance(source.tag, str) else ""
        if name in {"said", "fid"}:
            self.said_count += 1
            target = tei("said", xml_id=f"{chapter_id}-said-{self.said_count:05d}")
            who = normalize_pointer(source.get("who"))
            if who:
                target.set("who", who)
                for pointer in who.split():
                    self.speakers[pointer[1:]] += 1
            for attribute in ("direct", "aloud"):
                value = (source.get(attribute) or "").lower()
                if value in {"true", "false"}:
                    target.set(attribute, value)
            if name == "fid":
                target.set("direct", "false")
                target.set("aloud", "false")
            self.copy_mixed_content(source, target, chapter_id)
            return target
        if name in {"emph", "i", "em"}:
            target = tei("hi", rend="italic")
            self.copy_mixed_content(source, target, chapter_id)
            return target
        if name in {"first", "irst"}:
            target = tei("seg", type="narratorial-first-person")
            self.copy_mixed_content(source, target, chapter_id)
            return target
        if name == "second":
            target = tei("seg", type="narratorial-second-person")
            self.copy_mixed_content(source, target, chapter_id)
            return target
        if name == "br":
            return tei("lb")
        if name in {"span", "seg"}:
            target = tei("seg")
            self.copy_mixed_content(source, target, chapter_id)
            return target
        if name == "foreign":
            target = tei("foreign")
            language = source.get("xml:lang") or source.get("lang")
            if language:
                target.set(f"{{{XML_NS}}}lang", language)
            self.copy_mixed_content(source, target, chapter_id)
            return target
        if name in {"a", "name"}:
            target = tei("seg")
            self.copy_mixed_content(source, target, chapter_id)
            return target
        if name == "p":
            target = tei("seg", type="source-paragraph-boundary")
            self.copy_mixed_content(source, target, chapter_id)
            return target
        target = tei("seg")
        self.copy_mixed_content(source, target, chapter_id)
        return target

    def make_paragraph(self, source: etree._Element, chapter_id: str) -> etree._Element | None:
        self.paragraph_count += 1
        target = tei("p", xml_id=f"{chapter_id}-p-{self.paragraph_count:05d}")
        self.copy_mixed_content(source, target, chapter_id)
        if "".join(target.itertext()).strip() or len(target):
            return target
        self.paragraph_count -= 1
        return None

    def convert_fragment(self, markup: str, chapter_id: str) -> list[etree._Element]:
        parser = html.HTMLParser(encoding="utf-8", recover=True)
        wrapper = html.fragment_fromstring(markup, create_parent="div", parser=parser)
        output: list[etree._Element] = []
        loose = tei("p")

        def flush_loose() -> None:
            nonlocal loose
            if "".join(loose.itertext()).strip() or len(loose):
                self.paragraph_count += 1
                loose.set(f"{{{XML_NS}}}id", f"{chapter_id}-p-{self.paragraph_count:05d}")
                output.append(loose)
            loose = tei("p")

        if wrapper.text and wrapper.text.strip():
            loose.text = self.normalized_space(wrapper.text)
        for child in wrapper:
            name = child.tag.lower() if isinstance(child.tag, str) else ""
            if name == "p":
                flush_loose()
                paragraph = self.make_paragraph(child, chapter_id)
                if paragraph is not None:
                    output.append(paragraph)
            elif name == "epigraph":
                flush_loose()
                epigraph = tei("epigraph")
                paragraph = self.make_paragraph(child, chapter_id)
                if paragraph is not None:
                    epigraph.append(paragraph)
                    output.append(epigraph)
            elif name in {"br", "div", "body", "html"}:
                flush_loose()
            else:
                converted = self.convert_inline(child, chapter_id)
                if converted is not None:
                    loose.append(converted)
            if child.tail and child.tail.strip():
                addition = self.normalized_space(child.tail)
                if len(loose):
                    loose[-1].tail = (loose[-1].tail or "") + (addition or "")
                else:
                    loose.text = (loose.text or "") + (addition or "")
        flush_loose()
        return output


MARKER_PATTERN = re.compile(
    r"<div\s+type=[\"']chapter[\"']\s+n=[\"'](?P<divn>[^\"']+)[\"'][^>]*>"
    r"|<a\s+name=[\"']chap(?P<anchor>\d+)[\"'][^>]*>\s*</a>"
    r"|<h3[^>]*>\s*(?P<finale>finale\.)\s*</h3>",
    flags=re.IGNORECASE,
)


def chapter_segments(source: str) -> list[tuple[str, str, str]]:
    markers = list(MARKER_PATTERN.finditer(source))
    segments: list[tuple[str, str, str]] = []
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(source)
        block = source[marker.end():end]
        if marker.group("divn") is not None:
            number = str(int(marker.group("divn")))
            head = re.match(r"\s*<head[^>]*>(.*?)</head>", block, flags=re.IGNORECASE | re.DOTALL)
            label = re.sub(r"<[^>]+>", " ", head.group(1)) if head else ("PRELUDE" if number == "0" else f"CHAPTER {number}")
            if head:
                block = block[head.end():]
        elif marker.group("anchor") is not None:
            number = str(int(marker.group("anchor")))
            heading = re.search(r"<h3[^>]*>(.*?)</h3>", block, flags=re.IGNORECASE | re.DOTALL)
            if not heading:
                raise ValueError(f"chapter {number} has no H3 heading")
            label = re.sub(r"<[^>]+>", " ", heading.group(1))
            block = block[heading.end():]
        else:
            number = "finale"
            label = "FINALE"
        label = " ".join(label.split())
        block = re.sub(r"(?:</?(?:tei|text|body|html)>|</div>)\s*$", "", block, flags=re.IGNORECASE)
        segments.append((number, label, block))
    return segments


def build_header(revision: str, speakers: Counter[str]) -> etree._Element:
    header = tei("teiHeader")
    file_desc = tei("fileDesc")
    title_stmt = tei("titleStmt")
    title_stmt.append(tei("title", "Middlemarch"))
    author = tei("author")
    author.append(tei("persName", "George Eliot"))
    title_stmt.append(author)
    source_resp = tei("respStmt", xml_id="open-editions-annotation")
    append(source_resp, tei("resp", "Source transcription and research annotation"), tei("name", "Open Editions contributors"))
    title_stmt.append(source_resp)
    encoding_resp = tei("respStmt", xml_id="bookstacks-encoding")
    append(encoding_resp, tei("resp", "TEI P5 normalization, structural repair, and speaker-reference integrity"), tei("name", "Bookstacks project"))
    title_stmt.append(encoding_resp)

    edition_stmt = tei("editionStmt")
    edition_stmt.append(tei("edition", "Bookstacks TEI edition from the Open Editions annotated corpus", n="1.0"))
    publication_stmt = tei("publicationStmt")
    append(
        publication_stmt,
        tei("publisher", "Bookstacks project"),
        tei("pubPlace", "United States"),
        tei("date", date.today().strftime("%d %B %Y"), when=date.today().isoformat()),
        tei("idno", "eliot_middlemarch", type="local"),
    )
    availability = tei("availability", status="free")
    availability.append(tei("p", "George Eliot's text is in the public domain in the United States. The Open Editions repository does not state a separate license for its research annotations."))
    publication_stmt.append(availability)

    source_desc = tei("sourceDesc")
    source_bibl = tei("bibl")
    append(
        source_bibl,
        tei("title", "Middlemarch"),
        tei("author", "George Eliot"),
        tei("pubPlace", "New York and Boston"),
        tei("publisher", "H. M. Caldwell Company"),
    )
    source_desc.append(source_bibl)
    electronic = tei("bibl", type="electronic-source")
    electronic.text = "Open Editions, "
    link = tei("ref", "corpus-eliot-middlemarch-tei", target="https://github.com/open-editions/corpus-eliot-middlemarch-tei")
    electronic.append(link)
    link.tail = f", revision {revision}; based on Project Gutenberg eBook 145."
    source_desc.append(electronic)
    append(file_desc, title_stmt, edition_stmt, publication_stmt, source_desc)
    header.append(file_desc)

    encoding_desc = tei("encodingDesc")
    project_desc = tei("projectDesc")
    project_desc.append(tei("p", "The eight source fragments were consolidated into one standalone TEI P5 document. Checked-in merge conflicts and malformed HTML-like tags were repaired deterministically; dialogue, represented thought, free indirect discourse, and narratorial person annotations were retained."))
    encoding_desc.append(project_desc)
    editorial_decl = tei("editorialDecl")
    normalization = tei("normalization")
    normalization.append(tei("p", "Source wording and punctuation are retained. Custom FID annotations are represented as said elements with direct and aloud set to false; first and second person narratorial annotations are represented as typed seg elements. Obvious speaker-token variants are reconciled to a single local identifier."))
    editorial_decl.append(normalization)
    encoding_desc.append(editorial_decl)
    header.append(encoding_desc)

    profile_desc = tei("profileDesc")
    lang_usage = tei("langUsage")
    lang_usage.append(tei("language", "English", ident="en"))
    profile_desc.append(lang_usage)
    partic_desc = tei("particDesc")
    list_person = tei("listPerson")
    list_person.append(tei("head", "Speakers and represented consciousnesses in the source annotation"))
    for identifier in sorted(speakers, key=lambda item: display_name(item).casefold()):
        person = tei("person", xml_id=identifier)
        person.append(tei("persName", display_name(identifier)))
        person.append(tei("note", f"Source annotation token {identifier}; referenced by {speakers[identifier]} attributed passage(s)."))
        list_person.append(person)
    partic_desc.append(list_person)
    profile_desc.append(partic_desc)
    header.append(profile_desc)

    revision_desc = tei("revisionDesc")
    revision_desc.append(tei("change", "Consolidated and normalized for Bookstacks.", when=date.today().isoformat(), who="#bookstacks-encoding"))
    header.append(revision_desc)
    return header


def build_document(source_dir: Path) -> tuple[etree._ElementTree, dict[str, int]]:
    builder = BodyBuilder()
    text = tei("text", xml_lang="en")
    front = tei("front")
    title_page = tei("div", type="title-page", xml_id="eliot_middlemarch-eng-title-page")
    title_page.append(tei("head", "Middlemarch"))
    title_page.append(tei("p", "George Eliot", xml_id="eliot_middlemarch-eng-title-page-p-00001"))
    title_page.append(tei("p", "New York and Boston: H. M. Caldwell Company, Publishers", xml_id="eliot_middlemarch-eng-title-page-p-00002"))
    dedication = tei("div", type="dedication", xml_id="eliot_middlemarch-eng-dedication")
    dedication.append(tei("head", "Dedication"))
    dedication.append(tei("p", "To my dear Husband, George Henry Lewes, in this nineteenth year of our blessed union.", xml_id="eliot_middlemarch-eng-dedication-p-00001"))
    append(front, title_page, dedication)
    text.append(front)

    body = tei("body")
    edition = tei("div", type="edition", xml_id="eliot_middlemarch-eng-text")
    body.append(edition)
    text.append(body)

    numbered: list[int] = []
    unit_count = 0
    for book_number in range(1, 9):
        source_path = source_dir / f"book{book_number}.xml"
        if not source_path.is_file():
            raise FileNotFoundError(f"missing source fragment: {source_path}")
        source = repair_source(source_path.read_text(encoding="utf-8-sig"))
        segments = chapter_segments(source)
        book_div = tei("div", type="book", n=str(book_number), xml_id=f"eliot_middlemarch-eng-book-{book_number:02d}")
        book_div.append(tei("head", f"Book {ROMAN_BOOKS[book_number]}. {BOOK_TITLES[book_number]}"))
        for number, label, markup in segments:
            if number == "0":
                parent = edition
                chapter_id = "eliot_middlemarch-eng-prelude"
            elif number == "finale":
                parent = book_div
                chapter_id = "eliot_middlemarch-eng-finale"
            else:
                chapter_number = int(number)
                numbered.append(chapter_number)
                parent = book_div
                chapter_id = f"eliot_middlemarch-eng-chapter-{chapter_number:03d}"
            chapter = tei("div", type="chapter", n=number, xml_id=chapter_id)
            chapter.append(tei("head", label.rstrip(".") if number in {"0", "finale"} else label))
            for element in builder.convert_fragment(markup, chapter_id):
                chapter.append(element)
            parent.append(chapter)
            unit_count += 1
        edition.append(book_div)

    if numbered != list(range(1, 87)):
        raise ValueError(f"expected chapters 1-86 exactly once, got {numbered}")
    if unit_count != 88:
        raise ValueError(f"expected Prelude + 86 chapters + Finale, got {unit_count} units")

    root = etree.Element(f"{{{TEI_NS}}}TEI", nsmap=NSMAP)
    root.set(f"{{{XML_NS}}}id", "eliot_middlemarch")
    root.append(build_header(repository_revision(source_dir), builder.speakers))
    root.append(text)
    tree = etree.ElementTree(root)
    model = etree.ProcessingInstruction(
        "xml-model",
        'href="../tei_all.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"',
    )
    root.addprevious(model)
    return tree, {
        "units": unit_count,
        "paragraphs": builder.paragraph_count + 3,
        "said": builder.said_count,
        "speakers": len(builder.speakers),
    }


def validate(document: etree._ElementTree, schema_path: Path) -> None:
    schema = etree.RelaxNG(etree.parse(str(schema_path)))
    if not schema.validate(document):
        errors = "\n".join(str(entry) for entry in schema.error_log)
        raise ValueError(f"generated TEI failed Relax NG validation:\n{errors}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    args = parser.parse_args()

    document, stats = build_document(args.source_dir.resolve())
    validate(document, args.schema.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    document.write(
        str(args.output),
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=True,
    )
    print(
        f"Generated {args.output.resolve()} "
        f"({stats['units']} units, {stats['paragraphs']} paragraphs, "
        f"{stats['said']} attributed passages, {stats['speakers']} registry entries)."
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
