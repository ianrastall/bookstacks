"""Convert the French Project Gutenberg Shakespeare EPUBs to dramatic TEI P5."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import unquote
from zipfile import ZipFile

from lxml import etree


TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
OPF = "http://www.idpf.org/2007/opf"
DC = "http://purl.org/dc/elements/1.1/"
NS = {"opf": OPF, "dc": DC}
XML_ID = f"{{{XML}}}id"
XML_LANG = f"{{{XML}}}lang"

# The five explicitly excluded volumes are poetry, not plays.
NON_PLAYS = {
    "25694": "Venus et Adonis",
    "26757": "La mort de Lucrèce",
    "26758": "La plainte d'une amante",
    "27191": "Sonnets",
    "28150": "Le Pèlerin amoureux",
}

PLAY_SLUGS = {
    "13868": "macbeth",
    "15032": "hamlet",
    "15071": "the-tempest",
    "15303": "coriolanus",
    "15846": "much-ado-about-nothing",
    "15847": "julius-caesar",
    "15848": "the-comedy-of-errors",
    "15849": "timon-of-athens",
    "15942": "antony-and-cleopatra",
    "16128": "twelfth-night",
    "16710": "the-two-gentlemen-of-verona",
    "17930": "a-midsummer-nights-dream",
    "18143": "romeo-and-juliet",
    "18162": "as-you-like-it",
    "18169": "measure-for-measure",
    "18179": "othello",
    "18311": "the-winters-tale",
    "18312": "king-lear",
    "18313": "troilus-and-cressida",
    "19201": "cymbeline",
    "19219": "the-taming-of-the-shrew",
    "19227": "loves-labours-lost",
    "19228": "pericles-prince-of-tyre",
    "20720": "the-merry-wives-of-windsor",
    "20773": "the-merchant-of-venice",
    "21277": "king-richard-ii",
    "21856": "king-john",
    "22760": "king-henry-iv-part-1",
    "25707": "titus-andronicus",
    "25715": "king-henry-iv-part-2",
    "26759": "king-richard-iii",
    "26762": "king-henry-v",
    "26763": "king-henry-vi-part-1",
    "26764": "king-henry-vi-part-2",
    "26765": "king-henry-vi-part-3",
    "26766": "king-henry-viii",
    "28151": "alls-well-that-ends-well",
}


def tei(name: str, text: str | None = None, **attributes: str) -> etree._Element:
    element = etree.Element(f"{{{TEI}}}{name}")
    if text is not None:
        element.text = text
    for key, value in attributes.items():
        if key == "xml_id":
            element.set(XML_ID, value)
        elif key == "xml_lang":
            element.set(XML_LANG, value)
        else:
            element.set(key, value)
    return element


def local_name(element: etree._Element) -> str:
    return etree.QName(element).localname


def classes(element: etree._Element) -> set[str]:
    return set(element.get("class", "").split())


def clean_text(value: str | None) -> str:
    return " ".join((value or "").replace("\u00a0", " ").split())


def element_text(element: etree._Element) -> str:
    return clean_text("".join(element.itertext()))


def append_text(parent: etree._Element, value: str | None) -> None:
    if not value:
        return
    if len(parent):
        parent[-1].tail = (parent[-1].tail or "") + value
    else:
        parent.text = (parent.text or "") + value


class Ids:
    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()

    def next(self, kind: str) -> str:
        self.counts[kind] += 1
        return f"fra-{kind}-{self.counts[kind]:06d}"


def epub_data(epub_path: Path) -> tuple[dict[str, object], list[etree._Element]]:
    parser = etree.XMLParser(recover=True, huge_tree=True)
    with ZipFile(epub_path) as archive:
        container = etree.fromstring(archive.read("META-INF/container.xml"), parser)
        package_path = container.xpath("string(//*[local-name()='rootfile']/@full-path)")
        if not package_path:
            raise ValueError("EPUB has no OPF rootfile")
        package = etree.fromstring(archive.read(package_path), parser)
        package_dir = PurePosixPath(package_path).parent
        manifest = {
            item.get("id", ""): unquote(item.get("href", ""))
            for item in package.xpath("//*[local-name()='manifest']/*[local-name()='item']")
        }
        documents: list[etree._Element] = []
        for itemref in package.xpath("//*[local-name()='spine']/*[local-name()='itemref']"):
            href = manifest.get(itemref.get("idref", ""), "")
            if not re.search(r"\.(?:xhtml|html?|htm)$", href, re.IGNORECASE):
                continue
            member = str(package_dir / PurePosixPath(href))
            documents.append(etree.fromstring(archive.read(member), parser))

        def metadata(name: str) -> str:
            return clean_text(package.xpath(f"string(//dc:{name}[1])", namespaces=NS))

        contributors = []
        for item in package.xpath("//dc:contributor", namespaces=NS):
            contributors.append(
                {
                    "name": element_text(item),
                    "role": item.get(f"{{{OPF}}}role", ""),
                }
            )
        data: dict[str, object] = {
            "title": metadata("title"),
            "creator": metadata("creator"),
            "language": metadata("language"),
            "identifier": metadata("identifier"),
            "source": metadata("source"),
            "date": metadata("date"),
            "rights": metadata("rights"),
            "subjects": [element_text(item) for item in package.xpath("//dc:subject", namespaces=NS)],
            "contributors": contributors,
        }
        return data, documents


def project_gutenberg_id(metadata: dict[str, object], path: Path) -> str:
    identifier = str(metadata.get("identifier", ""))
    match = re.search(r"(?:ebooks/|gutenberg\.org/|#|pg)?(\d{3,6})(?:\D|$)", identifier)
    if match:
        return match.group(1)
    match = re.search(r"(\d{3,6})", path.stem)
    if not match:
        raise ValueError("Could not determine the Project Gutenberg number")
    return match.group(1)


def is_footnote(element: etree._Element) -> bool:
    return "footnote" in classes(element)


def note_number(element: etree._Element) -> str | None:
    match = re.search(r"\bNote\s+(\d+)\s*:", element_text(element), re.IGNORECASE)
    return match.group(1) if match else None


def extract_notes(documents: list[etree._Element]) -> dict[str, str]:
    notes: dict[str, str] = {}
    for document in documents:
        for element in document.xpath("//*[contains(concat(' ', normalize-space(@class), ' '), ' footnote ')]"):
            number = note_number(element)
            text = element_text(element)
            if number:
                text = re.sub(rf"^.*?\bNote\s+{re.escape(number)}\s*:\s*", "", text, count=1, flags=re.IGNORECASE)
                text = re.sub(r"^\(?\s*retour\s*\)?\s*", "", text, flags=re.IGNORECASE)
                notes[number] = text
            for identified in element.xpath(".//*[@id]"):
                value = identified.get("id", "")
                match = re.fullmatch(r"footnote(\d+)", value, re.IGNORECASE)
                if match and number:
                    notes[value.casefold()] = notes[number]
    return notes


def referenced_note(child: etree._Element, notes: dict[str, str]) -> tuple[str, str] | None:
    href = child.get("href", "")
    fragment = href.rsplit("#", 1)[-1].casefold() if "#" in href else ""
    number = clean_text("".join(child.itertext()))
    number_match = re.search(r"\d+", number)
    if fragment in notes:
        return (number_match.group(0) if number_match else fragment.removeprefix("footnote"), notes[fragment])
    if number_match and number_match.group(0) in notes:
        return number_match.group(0), notes[number_match.group(0)]
    return None


def convert_inline(
    source: etree._Element,
    target: etree._Element,
    ids: Ids,
    notes: dict[str, str],
    skip: int = 0,
) -> None:
    remaining = [skip]

    def consume(value: str | None) -> str:
        if not value:
            return ""
        if remaining[0] >= len(value):
            remaining[0] -= len(value)
            return ""
        if remaining[0]:
            value = value[remaining[0] :]
            remaining[0] = 0
        return value

    def walk(container: etree._Element, output: etree._Element) -> None:
        append_text(output, consume(container.text))
        for child in container:
            local = local_name(child)
            converted: etree._Element | None = None
            child_length = len("".join(child.itertext()))
            if remaining[0] and child_length and remaining[0] >= child_length:
                remaining[0] -= child_length
            elif local == "br":
                if remaining[0] == 0:
                    converted = tei("lb")
            elif local in {"a", "sup"} and (note := referenced_note(child, notes)):
                converted = tei("note", note[1], type="editorial", n=note[0], xml_id=ids.next("note"))
            elif local == "a" and not element_text(child):
                converted = None
            elif "stage2" in classes(child):
                converted = tei("stage", type="business", xml_id=ids.next("stage"))
                walk(child, converted)
            elif local in {"i", "em", "cite"}:
                converted = tei("hi", rend="italic")
                walk(child, converted)
            elif local in {"b", "strong"}:
                converted = tei("hi", rend="bold")
                walk(child, converted)
            elif local in {"small", "big", "sub", "sup"}:
                converted = tei("hi", rend=local)
                walk(child, converted)
            elif local == "a":
                converted = tei("ref")
                if child.get("href") and not child.get("href", "").startswith("#"):
                    converted.set("target", child.get("href", ""))
                walk(child, converted)
            elif local in {"span", "q"}:
                converted = tei("seg")
                if classes(child):
                    converted.set("rend", " ".join(sorted(classes(child))))
                walk(child, converted)
            else:
                converted = tei("seg", type=local)
                walk(child, converted)

            if converted is not None and (
                local == "br" or converted.text or len(converted) or element_text(converted)
            ):
                output.append(converted)
            append_text(output, consume(child.tail))

    walk(source, target)


def heading_text(element: etree._Element) -> str:
    copy = etree.fromstring(etree.tostring(element))
    for marker in copy.xpath(".//*[local-name()='sup'] | .//*[local-name()='a' and contains(@href, '#footnote')]"):
        tail = marker.tail
        parent = marker.getparent()
        previous = marker.getprevious()
        parent.remove(marker)
        if tail:
            if previous is not None:
                previous.tail = (previous.tail or "") + tail
            else:
                parent.text = (parent.text or "") + tail
    return element_text(copy)


def boilerplate(element: etree._Element) -> bool:
    blocked = {"pg-boilerplate", "pgheader", "pg-footer"}
    return bool(classes(element) & blocked) or element.get("id", "") in {"pg-header", "pg-footer"}


def iter_blocks(parent: etree._Element):
    for child in parent:
        if not isinstance(child.tag, str) or boilerplate(child) or is_footnote(child):
            continue
        local = local_name(child)
        child_classes = classes(child)
        if local in {"script", "style", "nav"}:
            continue
        if local in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote", "table", "hr"}:
            yield child
        elif local == "div" and ("poem" in child_classes or "pgmonospaced" in child_classes):
            yield child
        elif local in {"div", "section", "main"}:
            yield from iter_blocks(child)


def uppercase_role_prefix(value: str) -> str | None:
    output = []
    for character in value.strip():
        if character.isalpha() and character != character.upper():
            break
        output.append(character)
    candidate = "".join(output).strip(" ,.\t\r\n")
    letters = [character for character in candidate if character.isalpha()]
    if len(letters) < 2 or len(candidate) > 100 or not all(character == character.upper() for character in letters):
        return None
    return candidate


def speech_prefix(element: etree._Element) -> tuple[str, str, int] | None:
    raw = "".join(element.itertext())
    separators = [(raw.find("—"), 1), (raw.find("--"), 2)]
    separators = [(position, length) for position, length in separators if position >= 0]
    if not separators:
        return None
    position, length = min(separators)
    before = re.sub(r"\d+$", "", clean_text(raw[:position]).rstrip(".- "))
    role = uppercase_role_prefix(before)
    if not role:
        return None
    qualifier = clean_text(before[len(role) :]).strip(" ,.")
    return role, qualifier, position + length


def stage_type(value: str, before_speech: bool) -> str:
    folded = value.casefold()
    if re.search(r"\b(entre|entrent|rentre|rentrent|paraît|paraissent|arrive|arrivent|survient)\b", folded):
        return "entrance"
    if re.search(r"\b(sort|sortent|s'en va|ils s'en vont|exeunt)\b", folded):
        return "exit"
    return "setting" if before_speech else "business"


def looks_like_stage(element: etree._Element, before_speech: bool) -> bool:
    value = element_text(element)
    if classes(element) & {"stage1", "mid"}:
        return True
    if value.startswith("(") and value.endswith(")"):
        return True
    folded = value.casefold().lstrip("(")
    if re.match(r"^(entre|entrent|rentre|rentrent|paraît|paraissent|sort|sortent|survient)\b", folded):
        return True
    return before_speech


def add_cast_item(cast_list: etree._Element, value: str, continuation: bool = False) -> None:
    value = clean_text(value)
    if not value:
        return
    if continuation and len(cast_list):
        append_text(cast_list[-1], " " + value)
        return
    item = tei("castItem")
    boundary = min([position for position in (value.find(","), value.find(".")) if position >= 0] or [len(value)])
    candidate = value[:boundary].strip()
    role = uppercase_role_prefix(candidate)
    if role and role == candidate:
        role_element = tei("role", candidate)
        item.append(role_element)
        append_text(item, value[boundary:])
    else:
        item.text = value
    cast_list.append(item)


def split_break_lines(element: etree._Element) -> list[str]:
    lines = [""]

    def walk(container: etree._Element) -> None:
        if container.text:
            lines[-1] += container.text
        for child in container:
            if local_name(child) == "br":
                lines.append("")
            else:
                walk(child)
            if child.tail:
                lines[-1] += child.tail

    walk(element)
    return [clean_text(line) for line in lines if clean_text(line)]


class DramaBuilder:
    def __init__(self, metadata: dict[str, object], documents: list[etree._Element], text_id: str) -> None:
        self.metadata = metadata
        self.documents = documents
        self.text_id = text_id
        self.ids = Ids()
        self.notes = extract_notes(documents)
        self.document = self.make_document()
        self.body = self.document.find(f".//{{{TEI}}}body")
        assert self.body is not None
        self.current_front: etree._Element | None = None
        self.current_act: etree._Element | None = None
        self.current_scene: etree._Element | None = None
        self.current_sp: etree._Element | None = None
        self.cast_list: etree._Element | None = None
        self.act_number = 0
        self.scene_number = 0
        self.scene_has_speech = False

    def make_document(self) -> etree._ElementTree:
        title = str(self.metadata["title"])
        root = etree.Element(f"{{{TEI}}}TEI", nsmap={None: TEI})
        root.set(XML_ID, self.text_id)
        root.set(XML_LANG, "fr")
        header = tei("teiHeader")
        file_desc = tei("fileDesc")
        title_stmt = tei("titleStmt")
        title_stmt.append(tei("title", title, xml_lang="fr"))
        author = tei("author")
        author.append(tei("persName", "William Shakespeare"))
        author.append(tei("note", "1564–1616", type="dates"))
        title_stmt.append(author)
        translators = [
            str(item["name"])
            for item in self.metadata.get("contributors", [])
            if isinstance(item, dict) and item.get("role") == "trl"
        ]
        if translators:
            responsibility = tei("respStmt")
            responsibility.append(tei("resp", "French translation"))
            responsibility.append(tei("name", ", ".join(translators)))
            title_stmt.append(responsibility)
        encoding = tei("respStmt", xml_id="bookstacks-encoding")
        encoding.append(tei("resp", "XHTML-to-TEI drama conversion and structural encoding"))
        encoding.append(tei("name", "Bookstacks project"))
        title_stmt.append(encoding)
        file_desc.append(title_stmt)
        edition_stmt = tei("editionStmt")
        edition_stmt.append(tei("edition", "Bookstacks French TEI edition", n="1.0"))
        file_desc.append(edition_stmt)
        publication = tei("publicationStmt")
        publication.append(tei("publisher", "Bookstacks project"))
        publication.append(tei("pubPlace", "United States"))
        publication.append(tei("date", date.today().strftime("%d %B %Y"), when=date.today().isoformat()))
        publication.append(tei("idno", self.text_id, type="local"))
        availability = tei("availability", status="free")
        availability.append(
            tei(
                "licence",
                "This derived TEI file is made available under the Creative Commons Attribution-ShareAlike 4.0 International License; the Project Gutenberg source is public domain in the United States.",
                target="https://creativecommons.org/licenses/by-sa/4.0/",
            )
        )
        publication.append(availability)
        file_desc.append(publication)
        source_desc = tei("sourceDesc")
        pg_id = project_gutenberg_id(self.metadata, Path(self.text_id))
        source_desc.append(
            tei(
                "p",
                f"Born-digital French text from Project Gutenberg eBook #{pg_id}, converted from its EPUB XHTML reading order. Gutenberg administrative boilerplate and navigation were omitted.",
            )
        )
        file_desc.append(source_desc)
        header.append(file_desc)
        encoding_desc = tei("encodingDesc")
        project_desc = tei("projectDesc")
        project_desc.append(
            tei(
                "p",
                "Acts, scenes, dramatic speakers, prose speeches, stage directions, cast material, songs and verse, editorial notices, inline typography, and referenced translator notes were mapped to TEI P5 without inventing speaker identities.",
            )
        )
        encoding_desc.append(project_desc)
        header.append(encoding_desc)
        profile_desc = tei("profileDesc")
        lang_usage = tei("langUsage")
        lang_usage.append(tei("language", "French", ident="fr"))
        profile_desc.append(lang_usage)
        subjects = [str(subject) for subject in self.metadata.get("subjects", []) if subject]
        if subjects:
            text_class = tei("textClass")
            keywords = tei("keywords", scheme="https://www.gutenberg.org")
            for subject in subjects:
                keywords.append(tei("term", subject))
            text_class.append(keywords)
            profile_desc.append(text_class)
        header.append(profile_desc)
        revision = tei("revisionDesc")
        revision.append(
            tei(
                "change",
                "Converted the French Project Gutenberg EPUB XHTML into standalone dramatic TEI P5.",
                when=date.today().isoformat(),
                who="#bookstacks-encoding",
            )
        )
        header.append(revision)
        root.append(header)
        text = tei("text", xml_lang="fr")
        text.append(tei("body"))
        root.append(text)
        return etree.ElementTree(root)

    def target(self) -> etree._Element:
        if self.current_scene is not None:
            return self.current_scene
        if self.current_act is not None:
            return self.current_act
        if self.current_front is None:
            self.new_front("title-page", str(self.metadata["title"]))
        assert self.current_front is not None
        return self.current_front

    def new_front(self, kind: str, heading: str) -> None:
        division = tei("div", type=kind, xml_id=self.ids.next(kind))
        division.append(tei("head", heading))
        self.body.append(division)
        self.current_front = division
        self.current_act = None
        self.current_scene = None
        self.current_sp = None
        self.cast_list = None
        if kind == "characters":
            self.cast_list = tei("castList")
            division.append(self.cast_list)

    def new_prologue(self, heading: str = "Induction") -> None:
        division = tei("div", type="prologue", xml_id=f"{self.text_id}-prologue")
        division.append(tei("head", heading))
        self.body.append(division)
        self.current_act = division
        self.current_scene = None
        self.current_front = None
        self.current_sp = None
        self.cast_list = None
        self.scene_number = 0

    def add_heading(self, element: etree._Element) -> None:
        value = heading_text(element)
        folded = value.casefold()
        if "induction" in folded:
            self.new_prologue(value)
            return
        if re.search(r"\bacte\b", folded) and not folded.startswith("fin "):
            self.act_number += 1
            self.scene_number = 0
            division = tei(
                "div",
                type="act",
                n=str(self.act_number),
                xml_id=f"{self.text_id}-act-{self.act_number:03d}",
            )
            division.append(tei("head", value))
            self.body.append(division)
            self.current_act = division
            self.current_scene = None
            self.current_front = None
            self.current_sp = None
            self.cast_list = None
            return
        if re.search(r"\bsc[èe]ne\b", folded):
            if self.current_act is None:
                self.new_prologue()
            self.scene_number += 1
            structural_parent = "prologue" if self.current_act.get("type") == "prologue" else f"act-{self.act_number:03d}"
            division = tei(
                "div",
                type="scene",
                n=str(self.scene_number),
                xml_id=f"{self.text_id}-{structural_parent}-scene-{self.scene_number:03d}",
            )
            division.append(tei("head", value))
            self.current_act.append(division)
            self.current_scene = division
            self.current_sp = None
            self.scene_has_speech = False
            return
        if "personnages" in folded or "dramatis personae" in folded:
            self.new_front("characters", value)
            return
        if self.current_act is None:
            kind = "introduction" if any(word in folded for word in ("notice", "préface", "introduction")) else "title-page"
            if self.current_front is None or self.current_front.get("type") != kind or kind == "introduction":
                self.new_front(kind, value)
            else:
                paragraph = tei("p", xml_id=self.ids.next("p"), rend="subheading")
                convert_inline(element, paragraph, self.ids, self.notes)
                self.current_front.append(paragraph)
            return
        paragraph = tei("p", xml_id=self.ids.next("p"), rend="subheading")
        convert_inline(element, paragraph, self.ids, self.notes)
        self.target().append(paragraph)

    def add_stage(self, element: etree._Element) -> None:
        stage = tei(
            "stage",
            type=stage_type(element_text(element), not self.scene_has_speech),
            xml_id=self.ids.next("stage"),
        )
        convert_inline(element, stage, self.ids, self.notes)
        self.target().append(stage)

    def add_paragraph(self, element: etree._Element) -> None:
        value = element_text(element)
        if not value or re.fullmatch(r"[=*_\-\s]+", value):
            return
        if re.match(r"^FIN\s+DU\s+.*ACTE\.?$", value, re.IGNORECASE):
            return
        if self.cast_list is not None:
            if value.casefold().startswith(("la scène", "le lieu de la scène")):
                self.add_stage(element)
            else:
                add_cast_item(self.cast_list, value, any(name.startswith("i") for name in classes(element)))
            return
        prefix = speech_prefix(element) if self.current_scene is not None else None
        if prefix:
            role, qualifier, skip = prefix
            speech = tei("sp", xml_id=self.ids.next("speech"))
            speech.append(tei("speaker", role))
            if qualifier:
                speech.append(tei("stage", qualifier, type="business", xml_id=self.ids.next("stage")))
            paragraph = tei("p", xml_id=self.ids.next("p"))
            convert_inline(element, paragraph, self.ids, self.notes, skip=skip)
            if element_text(paragraph) or len(paragraph):
                speech.append(paragraph)
            self.target().append(speech)
            self.current_sp = speech
            self.scene_has_speech = True
            return
        if self.current_scene is not None and looks_like_stage(element, not self.scene_has_speech):
            self.add_stage(element)
            return
        paragraph = tei("p", xml_id=self.ids.next("p"))
        raw = "".join(element.itertext())
        separator = re.match(r"^\s*=+\s*", raw)
        convert_inline(element, paragraph, self.ids, self.notes, skip=separator.end() if separator else 0)
        if not element_text(paragraph) and not len(paragraph):
            return
        if self.current_scene is not None and self.current_sp is not None:
            self.current_sp.append(paragraph)
        else:
            self.target().append(paragraph)

    def add_poem(self, element: etree._Element) -> None:
        paragraphs = element.xpath(".//*[local-name()='p']")
        if self.cast_list is not None:
            for paragraph in paragraphs:
                add_cast_item(
                    self.cast_list,
                    element_text(paragraph),
                    any(name.startswith("i") for name in classes(paragraph)),
                )
            return
        stanzas = element.xpath("./*[contains(concat(' ', normalize-space(@class), ' '), ' stanza ')]")
        stanzas = stanzas or [element]
        for stanza in stanzas:
            group = tei("lg", xml_id=self.ids.next("verse-group"))
            for paragraph in stanza.xpath(".//*[local-name()='p']"):
                line = tei("l", xml_id=self.ids.next("line"))
                indentation = next((name[1:] for name in classes(paragraph) if re.fullmatch(r"i\d+", name)), None)
                if indentation:
                    line.set("rend", f"indent-{indentation}")
                convert_inline(paragraph, line, self.ids, self.notes)
                if element_text(line) or len(line):
                    group.append(line)
            if not len(group):
                continue
            if self.current_scene is not None and self.current_sp is not None:
                self.current_sp.append(group)
            else:
                self.target().append(group)

    def add_monospaced(self, element: etree._Element) -> None:
        lines = split_break_lines(element)
        if self.cast_list is not None:
            for line in lines:
                add_cast_item(self.cast_list, line)
            return
        for line in lines:
            paragraph = tei("p", line, xml_id=self.ids.next("p"), rend="preformatted")
            if self.current_scene is not None and self.current_sp is not None:
                self.current_sp.append(paragraph)
            else:
                self.target().append(paragraph)

    def add_blockquote(self, element: etree._Element) -> None:
        for paragraph in element.xpath(".//*[local-name()='p']"):
            converted = tei("p", xml_id=self.ids.next("p"), rend="blockquote")
            convert_inline(paragraph, converted, self.ids, self.notes)
            self.target().append(converted)

    def add_table(self, element: etree._Element) -> None:
        if self.cast_list is not None:
            for row in element.xpath(".//*[local-name()='tr']"):
                add_cast_item(self.cast_list, " ".join(element_text(cell) for cell in row.xpath("./*[local-name()='td' or local-name()='th']")))
            return
        table = tei("table")
        for source_row in element.xpath(".//*[local-name()='tr']"):
            row = tei("row")
            for source_cell in source_row.xpath("./*[local-name()='td' or local-name()='th']"):
                cell = tei("cell")
                convert_inline(source_cell, cell, self.ids, self.notes)
                row.append(cell)
            table.append(row)
        if len(table):
            self.target().append(table)

    def build(self) -> etree._ElementTree:
        for document in self.documents:
            bodies = document.xpath("//*[local-name()='body']")
            if not bodies:
                continue
            for block in iter_blocks(bodies[0]):
                local = local_name(block)
                if local.startswith("h") and local[1:].isdigit():
                    self.add_heading(block)
                elif local == "p":
                    self.add_paragraph(block)
                elif local == "div" and "poem" in classes(block):
                    self.add_poem(block)
                elif local == "div" and "pgmonospaced" in classes(block):
                    self.add_monospaced(block)
                elif local == "blockquote":
                    self.add_blockquote(block)
                elif local == "table":
                    self.add_table(block)
        return self.document


def validate_structure(document: etree._ElementTree, path: Path, schema: etree.RelaxNG) -> None:
    if not schema.validate(document):
        details = "\n".join(str(entry) for entry in schema.error_log)
        raise ValueError(f"Generated TEI failed Relax NG validation:\n{details}")
    acts = document.xpath("count(//tei:div[@type='act'])", namespaces={"tei": TEI})
    scenes = document.xpath("count(//tei:div[@type='scene'])", namespaces={"tei": TEI})
    speeches = document.xpath("count(//tei:sp)", namespaces={"tei": TEI})
    if acts != 5:
        raise ValueError(f"Expected five acts, generated {int(acts)}")
    if scenes < 5 or speeches < 100:
        raise ValueError(f"Implausible dramatic structure: {int(scenes)} scenes, {int(speeches)} speeches")
    print(f"Generated {path.resolve()} ({int(acts)} acts, {int(scenes)} scenes, {int(speeches)} speeches)")


def write_document(document: etree._ElementTree, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    instruction = etree.ProcessingInstruction(
        "xml-model", 'href="../tei_all.rng" schematypens="http://relaxng.org/ns/structure/1.0"'
    )
    document.getroot().addprevious(instruction)
    document.write(str(output), encoding="UTF-8", xml_declaration=True, pretty_print=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-pattern", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    args = parser.parse_args()

    pattern = Path(args.source_pattern)
    sources = sorted(pattern.parent.glob(pattern.name))
    if not sources:
        raise FileNotFoundError(f"No EPUBs matched {args.source_pattern}")
    schema = etree.RelaxNG(etree.parse(str(args.schema)))
    seen: set[str] = set()
    excluded: list[tuple[str, str]] = []
    for source in sources:
        metadata, documents = epub_data(source)
        pg_id = project_gutenberg_id(metadata, source)
        if pg_id in NON_PLAYS:
            excluded.append((source.name, NON_PLAYS[pg_id]))
            continue
        if pg_id not in PLAY_SLUGS:
            raise ValueError(f"Unclassified EPUB {source.name} (Project Gutenberg #{pg_id})")
        if metadata.get("creator") != "William Shakespeare" or metadata.get("language") != "fr":
            raise ValueError(f"Unexpected metadata in {source.name}: {metadata.get('creator')}, {metadata.get('language')}")
        slug = PLAY_SLUGS[pg_id]
        text_id = f"shakespeare-{slug}-fra"
        output = args.output_dir / f"shakespeare_{slug}_fra.xml"
        builder = DramaBuilder(metadata, documents, text_id)
        document = builder.build()
        validate_structure(document, output, schema)
        write_document(document, output)
        seen.add(pg_id)

    missing = sorted(set(PLAY_SLUGS) - seen)
    if missing:
        raise ValueError("Missing expected play EPUBs: " + ", ".join(missing))
    for filename, title in excluded:
        print(f"Excluded non-play {filename}: {title}")
    print(f"Converted {len(seen)} French plays; excluded {len(excluded)} non-play volumes.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
