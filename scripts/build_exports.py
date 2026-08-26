#!/usr/bin/env python3
"""Build a LaTeX-powered PDF for each published Bookstacks TEI edition.

The TEI files remain canonical.  This script creates deterministic derivatives
under public/downloads without modifying the source corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
TEI_ROOT = ROOT / "tei"
OUTPUT_ROOT = Path(os.environ.get("BOOKSTACKS_EXPORT_ROOT", ROOT / "public" / "downloads")).resolve()
TMP_ROOT = ROOT / "tmp" / "exports"
FONT_PATH = ROOT / "src" / "assets" / "fonts" / "NewCM10-Regular.otf"
ITALIC_FONT_PATH = ROOT / "src" / "assets" / "fonts" / "NewCM10-Italic.otf"
BOLD_FONT_PATH = ROOT / "src" / "assets" / "fonts" / "NewCM10-Bold.otf"
BOLD_ITALIC_FONT_PATH = ROOT / "src" / "assets" / "fonts" / "NewCM10-BoldItalic.otf"
SMALL_FONT_PATH = ROOT / "src" / "assets" / "fonts" / "NewCM08-Regular.otf"
SMALL_ITALIC_FONT_PATH = ROOT / "src" / "assets" / "fonts" / "NewCM08-Italic.otf"
AUTHOR_PROFILES_PATH = ROOT / "src" / "data" / "author-profiles.json"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

AUTHOR_PROFILES: dict[str, dict[str, str]] = json.loads(AUTHOR_PROFILES_PATH.read_text(encoding="utf-8"))
PUBLISHED_AUTHORS = set(AUTHOR_PROFILES)

LANGUAGES = {
    "eng": {"code": "en", "name": "English", "contents": "Contents", "note": "Note"},
    "fra": {"code": "fr", "name": "Français", "contents": "Sommaire", "note": "Note"},
    "spa": {"code": "es", "name": "Español", "contents": "Índice", "note": "Nota"},
    "grc": {"code": "grc", "name": "Ἑλληνική", "contents": "Περιεχόμενα", "note": "Ὑποσημείωσις"},
    "rus": {"code": "ru", "name": "Русский", "contents": "Содержание", "note": "Примечание"},
}

KIND_LABELS = {
    "en": {"act": "Act", "scene": "Scene", "chapter": "Chapter", "section": "Section", "book": "Book", "volume": "Volume", "part": "Part", "stave": "Stave", "introduction": "Introduction", "preface": "Preface", "prologue": "Prologue", "epilogue": "Epilogue"},
    "fr": {"act": "Acte", "scene": "Scène", "chapter": "Chapitre", "section": "Section", "book": "Livre", "volume": "Tome", "part": "Partie", "stave": "Strophe", "introduction": "Introduction", "preface": "Préface", "prologue": "Prologue", "epilogue": "Épilogue"},
    "es": {"act": "Acto", "scene": "Escena", "chapter": "Capítulo", "section": "Sección", "book": "Libro", "volume": "Tomo", "part": "Parte", "stave": "Estrofa", "introduction": "Introducción", "preface": "Prefacio", "prologue": "Prólogo", "epilogue": "Epílogo"},
    "grc": {"act": "Πρᾶξις", "scene": "Σκηνή", "chapter": "Κεφάλαιον", "section": "Τμῆμα", "book": "Βιβλίον", "volume": "Τόμος", "part": "Μέρος", "stave": "Στροφή", "introduction": "Εἰσαγωγή", "preface": "Προοίμιον", "prologue": "Πρόλογος", "epilogue": "Ἐπίλογος"},
    "ru": {"act": "Действие", "scene": "Сцена", "chapter": "Глава", "section": "Раздел", "book": "Книга", "volume": "Том", "part": "Часть", "stave": "Часть", "introduction": "Введение", "preface": "Предисловие", "prologue": "Пролог", "epilogue": "Эпилог"},
}

WORD_PATTERN = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.UNICODE)
ROMAN_NUMERAL_PATTERN = re.compile(r"[IVXLCDM]+")
ENGLISH_MINOR_WORDS = {
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "from", "if",
    "in", "into", "nor", "of", "off", "on", "or", "over", "per", "the", "to",
    "up", "upon", "v", "via", "vs", "with", "yet",
}
PRESERVED_INITIALISMS = {
    "AI", "DNA", "EU", "HTML", "PDF", "TEI", "UK", "UN", "US", "USA", "USSR", "XML",
}
STRUCTURAL_HEADING_WORDS = {
    "act", "book", "chapter", "part", "scene", "section", "stave", "volume",
    "acte", "chapitre", "livre", "partie", "scène", "section", "tome",
    "acto", "capítulo", "escena", "estrofa", "libro", "parte", "sección", "tomo",
    "глава", "действие", "книга", "раздел", "том", "часть",
    "βιβλίον", "κεφάλαιον", "μέρος", "πρᾶξις", "σκηνή", "τμῆμα", "τόμος",
}

# A TEI <head> is always a real heading.  In its absence, synthesize a heading
# only for major reading divisions.  Lower-level textpart wrappers such as
# sections, subsections, subchapters, and canonical page ranges describe the
# source's citation structure; printing them makes the PDF read like an XML
# outline instead of a book.
SYNTHETIC_HEADING_TYPES = {
    "act", "scene", "chapter", "book", "volume", "part", "stave", "letter",
    "introduction", "preface", "prologue", "epilogue",
}

BLOCK_NAMES = {
    "div", "p", "sp", "lg", "castList", "list", "table", "figure", "floatingText",
    "opener", "closer", "postscript", "epigraph", "salute", "signed", "dateline", "trailer",
}
CHANGED_ASSETS: list[Path] = []


@dataclass
class Edition:
    source: Path
    author_slug: str
    work_slug: str
    tei_language: str
    locale: str
    language_name: str
    title: str
    author: str
    translator: str
    edition_statement: str
    publication_date: str
    source_citation: str
    identifier: str
    license_text: str
    license_url: str
    root: ET.Element

    @property
    def stem(self) -> str:
        return self.source.stem

    @property
    def canonical_url(self) -> str:
        return f"https://bookstacks.org/{self.locale}/authors/{self.author_slug}/{self.work_slug}"

    @property
    def output_dir(self) -> Path:
        return OUTPUT_ROOT / self.author_slug / self.stem


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def capitalize_heading_word(word: str) -> str:
    lowered = word.lower()
    if len(lowered) > 2 and lowered[1] in {"'", "’"} and lowered[0] in {"d", "l", "o"}:
        return lowered[0].upper() + lowered[1] + lowered[2].upper() + lowered[3:]
    return lowered[:1].upper() + lowered[1:]


def english_title_case(value: str) -> str:
    words = list(WORD_PATTERN.finditer(value))
    if not words:
        return value
    pieces: list[str] = []
    previous_end = 0
    previous_word = ""
    for index, match in enumerate(words):
        separator = value[previous_end:match.start()]
        pieces.append(separator)
        original = match.group(0)
        lowered = original.lower()
        follows_boundary = index == 0 or bool(re.search(r"[.!?:—–]", separator))
        is_last = index == len(words) - 1
        if original in PRESERVED_INITIALISMS:
            replacement = original
        elif ROMAN_NUMERAL_PATTERN.fullmatch(original) and (
            previous_word in STRUCTURAL_HEADING_WORDS or len(words) == 1
        ):
            replacement = original
        elif lowered in ENGLISH_MINOR_WORDS and not follows_boundary and not is_last:
            replacement = lowered
        else:
            replacement = capitalize_heading_word(original)
        pieces.append(replacement)
        previous_word = lowered
        previous_end = match.end()
    pieces.append(value[previous_end:])
    return "".join(pieces)


def sentence_case_heading(value: str) -> str:
    words = list(WORD_PATTERN.finditer(value))
    if not words:
        return value
    pieces: list[str] = []
    previous_end = 0
    previous_word = ""
    for index, match in enumerate(words):
        separator = value[previous_end:match.start()]
        pieces.append(separator)
        original = match.group(0)
        lowered = original.lower()
        if original in PRESERVED_INITIALISMS:
            replacement = original
        elif ROMAN_NUMERAL_PATTERN.fullmatch(original) and previous_word in STRUCTURAL_HEADING_WORDS:
            replacement = original
        elif index == 0 or re.search(r"[.!?:—–]", separator):
            replacement = capitalize_heading_word(original)
        else:
            replacement = lowered
        pieces.append(replacement)
        previous_word = lowered
        previous_end = match.end()
    pieces.append(value[previous_end:])
    return "".join(pieces)


def mixed_case_heading(value: str, locale: str) -> str:
    letters = [character for character in value if character.isalpha()]
    if not letters:
        return value
    if all(not character.islower() for character in letters):
        return english_title_case(value) if locale == "en" else sentence_case_heading(value)

    def normalize_shout_word(match: re.Match[str]) -> str:
        word = match.group(0)
        if not any(character.isalpha() for character in word) or any(character.islower() for character in word):
            return word
        if word in PRESERVED_INITIALISMS or ROMAN_NUMERAL_PATTERN.fullmatch(word):
            return word
        return capitalize_heading_word(word)

    return WORD_PATTERN.sub(normalize_shout_word, value)


def direct_children(element: ET.Element, name: str | None = None) -> list[ET.Element]:
    children = list(element)
    return children if name is None else [child for child in children if local_name(child) == name]


def first_descendant(element: ET.Element, name: str) -> ET.Element | None:
    return next((node for node in element.iter() if local_name(node) == name), None)


def first_direct(element: ET.Element, name: str) -> ET.Element | None:
    return next((node for node in list(element) if local_name(node) == name), None)


def element_text(element: ET.Element | None) -> str:
    return clean("".join(element.itertext())) if element is not None else ""


def person_name_text(element: ET.Element | None) -> str:
    if element is None:
        return ""

    name_parts: list[str] = []

    def collect_name(node: ET.Element) -> None:
        if node.text:
            name_parts.append(node.text)
        for child in direct_children(node):
            if local_name(child) != "note":
                collect_name(child)
            if child.tail:
                name_parts.append(child.tail)

    collect_name(element)
    name = clean(" ".join(name_parts))
    dates = [
        element_text(note).strip().strip("()")
        for note in element.iter()
        if local_name(note) == "note" and clean(note.get("type")).lower() == "dates"
    ]
    dates = [date for date in dates if date]
    if name and dates:
        return f"{name} ({'; '.join(dates)})"

    value = name or element_text(element)
    trailing_dates = re.fullmatch(r"(.+?)(?:,\s*|\s+)(\d{3,4}\s*[-–—]\s*\d{3,4})", value)
    if trailing_dates:
        return f"{trailing_dates.group(1).rstrip(',')} ({trailing_dates.group(2)})"
    return value


def canonical_author_text(author_slug: str, fallback: str) -> str:
    profile = AUTHOR_PROFILES.get(author_slug)
    if profile is None:
        return fallback
    name = clean(profile.get("name"))
    dates = clean(profile.get("dates"))
    if not name or not dates:
        raise ValueError(f"Author profile must include name and dates: {author_slug}")
    return f"{name} ({dates})"


def parse_edition(source: Path) -> Edition:
    match = re.match(r"^([^_]+)_(.+)_([a-z]{3})\.xml$", source.name)
    if not match:
        raise ValueError(f"Unexpected TEI filename: {source.name}")
    author_slug, work_slug, tei_language = match.groups()
    language = LANGUAGES.get(tei_language, {"code": tei_language, "name": tei_language})
    root = ET.parse(source).getroot()
    title_stmt = first_descendant(root, "titleStmt")
    title_node = first_direct(title_stmt, "title") if title_stmt is not None else None
    author_node = first_descendant(title_stmt, "author") if title_stmt is not None else None
    author_name_node = first_descendant(author_node, "persName") if author_node is not None else None
    publication_stmt = first_descendant(root, "publicationStmt")
    availability_node = first_direct(publication_stmt, "availability") if publication_stmt is not None else None
    license_node = first_descendant(availability_node, "licence") if availability_node is not None else None
    rights_text = element_text(license_node) or element_text(availability_node)
    translator_node = next(
        (
            node
            for node in title_stmt.iter()
            if local_name(node) == "editor" and clean(node.get("role")).lower() == "translator"
        ),
        None,
    ) if title_stmt is not None else None
    edition_stmt = first_descendant(root, "editionStmt")
    edition_node = first_descendant(edition_stmt, "edition") if edition_stmt is not None else None
    publication_date_node = first_direct(publication_stmt, "date") if publication_stmt is not None else None
    source_desc = first_descendant(root, "sourceDesc")
    source_monograph = first_descendant(source_desc, "monogr") if source_desc is not None else None
    source_parts: list[str] = []
    if source_monograph is not None:
        for source_name in ("title", "publisher", "date"):
            source_value = element_text(first_descendant(source_monograph, source_name))
            if source_value and source_value not in source_parts:
                source_parts.append(source_value)
    identifier = root.get(XML_ID) or source.stem.replace("_", "-")
    return Edition(
        source=source,
        author_slug=author_slug,
        work_slug=work_slug,
        tei_language=tei_language,
        locale=str(language["code"]),
        language_name=str(language["name"]),
        title=element_text(title_node) or work_slug.replace("-", " ").title(),
        author=canonical_author_text(
            author_slug,
            person_name_text(author_name_node if author_name_node is not None else author_node)
            or author_slug.replace("-", " ").title(),
        ),
        translator=element_text(translator_node),
        edition_statement=element_text(edition_node),
        publication_date=(
            element_text(publication_date_node)
            or (publication_date_node.get("when", "") if publication_date_node is not None else "")
        ),
        source_citation=". ".join(source_parts),
        identifier=identifier,
        license_text=rights_text,
        license_url=license_node.get("target", "") if license_node is not None else "",
        root=root,
    )


class LatexRenderer:
    """Render the curated TEI vocabulary directly to book-oriented LaTeX.

    The TEI Consortium stylesheets in assets/tei-xsl-7.61.0 informed the
    element mapping, especially for drama, verse, notes, and text divisions.
    A small local renderer keeps the publication build dependency-free and
    lets Bookstacks own its typography.
    """

    def __init__(self, edition: Edition):
        self.edition = edition
        self.notes = {
            node.get(XML_ID): node
            for node in edition.root.iter()
            if local_name(node) == "note" and node.get(XML_ID)
        }
        self.referenced_note_ids = {
            target[1:]
            for node in edition.root.iter()
            if local_name(node) == "ref"
            for target in [clean(node.get("target"))]
            if target.startswith("#") and target[1:] in self.notes
        }

    def render(self) -> str:
        text = first_descendant(self.edition.root, "text")
        if text is None:
            raise ValueError(f"No TEI text in {self.edition.source}")
        areas = {local_name(area): area for area in direct_children(text)}
        parts: list[str] = []
        if "front" in areas:
            parts.extend((r"\frontmatter", self.render_container(areas["front"], 0)))
        if "body" in areas:
            body = self.render_container(areas["body"], 0)
            if r"\addcontentsline" not in body:
                body = f"{self.heading(self.edition.title, 0)}\n{body}".strip()
            parts.extend((r"\mainmatter", body))
        if "back" in areas:
            parts.extend((r"\backmatter", self.render_container(areas["back"], 0)))
        if not parts:
            parts.append(self.render_container(text, 0))
        return "\n".join(part for part in parts if part.strip()).strip() + "\n"

    def render_container(self, parent: ET.Element, depth: int) -> str:
        return "\n".join(
            rendered
            for child in direct_children(parent)
            for rendered in [self.render_block(child, depth)]
            if rendered.strip()
        )

    def render_block(self, node: ET.Element, depth: int) -> str:
        name = local_name(node)
        if name == "head":
            return ""
        if name == "div":
            head = first_direct(node, "head")
            supplied_title = element_text(head)
            division_type = clean(node.get("subtype") or node.get("type")).lower()
            if not supplied_title and division_type in {"translation", "edition"}:
                return self.render_container(node, depth)
            if not supplied_title and division_type not in SYNTHETIC_HEADING_TYPES:
                return self.render_container(node, depth)
            title = supplied_title or self.division_label(node)
            heading = self.heading(title, depth)
            content = self.render_container(node, depth + 1)
            first_content = next(
                (child for child in direct_children(node) if local_name(child) != "head"),
                None,
            )
            if first_content is not None and local_name(first_content) in {"p", "ab"}:
                content = r"\noindent " + content
            return f"{heading}\n{content}".strip()
        if name in {"p", "ab"}:
            # Dialogue editions such as Plato's mark each utterance as
            # <q type="spoken">.  Preserve that editorial structure instead
            # of running several speakers together in a single PDF paragraph.
            content = self.inline_content(node, split_spoken=True).strip()
            if (
                "preformatted" in clean(node.get("rend")).lower()
                and re.fullmatch(r"[=_*\-]{3,}", element_text(node))
            ):
                return r"\par\smallskip\noindent\rule{\textwidth}{.35pt}\par\smallskip"
            return f"{content}\\par" if content else ""
        if name == "sp":
            speaker = first_direct(node, "speaker")
            label = element_text(speaker).rstrip(".") if speaker is not None else ""
            content = "\n".join(
                self.render_block(child, depth)
                for child in direct_children(node)
                if local_name(child) != "speaker"
            )
            return (
                f"\\begin{{bookstacksspeech}}{{{latex_escape(label)}}}\n"
                f"{content}\n"
                r"\end{bookstacksspeech}"
            )
        if name == "stage":
            content = self.inline_content(node).strip()
            return (
                "\\begin{bookstacksstage}\n"
                f"{content}\n"
                "\\end{bookstacksstage}"
            ) if content else ""
        if name == "lg":
            lines = [content for line in direct_children(node, "l") if (content := self.inline_content(line).strip())]
            return "\\begin{verse}\n" + " \\\\\n".join(lines) + "\n\\end{verse}" if lines else ""
        if name == "l":
            content = self.inline_content(node).strip()
            return f"{content} \\\\" if content else ""
        if name == "castList":
            head = first_direct(node, "head")
            title = self.heading(element_text(head), depth) if head is not None else ""
            items = [
                f"\\item {content}"
                for item in direct_children(node, "castItem")
                if (content := self.inline_content(item).strip())
            ]
            listing = "\\begin{bookstackscast}\n" + "\n".join(items) + "\n\\end{bookstackscast}" if items else ""
            return f"{title}\n{listing}".strip()
        if name == "list":
            ordered = clean(node.get("type") or node.get("rend")).lower() in {"ordered", "numbered", "ol"}
            environment = "enumerate" if ordered else "itemize"
            items = [
                f"\\item {content}"
                for item in direct_children(node, "item")
                if (content := self.inline_content(item).strip())
            ]
            return f"\\begin{{{environment}}}\n" + "\n".join(items) + f"\n\\end{{{environment}}}" if items else ""
        if name == "table":
            return self.render_table(node)
        if name in {"quote", "q", "epigraph"}:
            content = self.render_container(node, depth) or self.inline_content(node).strip()
            return f"\\begin{{quote}}\n{content}\n\\end{{quote}}" if content else ""
        if name in {"opener", "closer", "postscript", "floatingText"}:
            content = self.render_container(node, depth) or self.inline_content(node).strip()
            return f"\\begin{{quote}}\n{content}\n\\end{{quote}}" if content else ""
        if name in {"salute", "signed", "dateline", "trailer"}:
            content = self.inline_content(node).strip()
            return f"\\begin{{flushright}}{content}\\end{{flushright}}" if content else ""
        if name == "figure":
            caption = first_descendant(node, "figDesc")
            if caption is None:
                caption = first_descendant(node, "head")
            content = element_text(caption)
            return f"\\begin{{bookstacksstage}}{latex_escape(content)}\\end{{bookstacksstage}}" if content else ""
        if name in {"pb", "milestone", "fw", "metamark", "certainty", "shift"}:
            return ""
        if name in BLOCK_NAMES or any(local_name(child) in BLOCK_NAMES for child in direct_children(node)):
            return self.render_container(node, depth)
        content = self.inline_content(node).strip()
        return f"{content}\\par" if content else ""

    def heading(self, title: str, depth: int) -> str:
        if not title:
            return ""
        command, toc_level = [
            ("chapter", "chapter"),
            ("section", "section"),
            ("subsection", "subsection"),
            ("subsubsection", "subsubsection"),
        ][min(depth, 3)]
        escaped = latex_escape(mixed_case_heading(title, self.edition.locale))
        marks = f"\\markboth{{{escaped}}}{{{escaped}}}" if depth == 0 else f"\\markright{{{escaped}}}"
        return (
            r"\phantomsection" + "\n"
            f"\\{command}*{{{escaped}}}\n"
            f"\\addcontentsline{{toc}}{{{toc_level}}}{{{escaped}}}\n"
            f"{marks}"
        )

    def division_label(self, node: ET.Element) -> str:
        kind = clean(node.get("subtype") or node.get("type") or "section").replace("_", "-")
        label = KIND_LABELS.get(self.edition.locale, KIND_LABELS["en"]).get(
            kind, kind.replace("-", " ").title()
        )
        number = clean(node.get("n"))
        return f"{label} {number}" if number and not number.lower().startswith("urn:") else label

    def render_table(self, node: ET.Element) -> str:
        # ``lb`` normally renders as ``\\``, but inside tabularx that token
        # ends the entire row—even when it occurs inside formatting such as
        # ``\textsc{...}``.  Use a paragraph-mode line break within cells.
        def cell_content(cell: ET.Element) -> str:
            return self.inline_content(cell).strip().replace(r"\\", r"\newline{}")

        rows = [
            [cell_content(cell) for cell in direct_children(row, "cell")]
            for row in direct_children(node, "row")
        ]
        rows = [row for row in rows if row]
        if not rows:
            return ""
        width = max(len(row) for row in rows)
        rows = [row + [""] * (width - len(row)) for row in rows]
        columns = " ".join("X" for _ in range(width))
        lines = [" & ".join(row) + r" \\" for row in rows]
        if len(lines) > 1:
            lines.insert(1, r"\midrule")
        return (
            f"\\begin{{tabularx}}{{\\textwidth}}{{{columns}}}\n"
            "\\toprule\n" + "\n".join(lines) + "\n\\bottomrule\n"
            "\\end{tabularx}"
        )

    def inline_content(self, node: ET.Element, *, split_spoken: bool = False) -> str:
        result = self.text(node.text)
        for child in direct_children(node):
            result += self.inline(child, split_spoken=split_spoken)
            result += self.text(child.tail)
        result = re.sub(r"^\s*(?:\\\\\s*)+", "", result)
        return re.sub(r"(?:\s*\\\\)+\s*$", "", result)

    def inline(self, node: ET.Element, *, split_spoken: bool = False) -> str:
        name = local_name(node)
        # Notes may contain quoted examples of their own.  Those remain
        # inline even when the surrounding body paragraph is dialogue.  A
        # quotation nested inside one spoken utterance is likewise inline.
        is_spoken = name == "q" and clean(node.get("type")).lower() == "spoken"
        content = self.inline_content(
            node,
            split_spoken=split_spoken and name != "note" and not is_spoken,
        )
        if name == "note":
            note_id = node.get(XML_ID)
            return "" if note_id and note_id in self.referenced_note_ids else self.note_reference(node)
        if name == "ref":
            target = clean(node.get("target"))
            if target.startswith("#") and target[1:] in self.notes:
                return self.note_reference(self.notes[target[1:]])
            if target.startswith(("http://", "https://")):
                return f"\\href{{\\detokenize{{{target}}}}}{{{content or latex_escape(target)}}}"
            return content
        if name in {"emph", "foreign", "title", "bibl"}:
            return f"\\emph{{{content}}}"
        if name == "hi":
            rendition = f"{node.get('rend', '')} {node.get('style', '')}".lower()
            if "bold" in rendition:
                return f"\\textbf{{{content}}}"
            if "sup" in rendition:
                return f"\\textsuperscript{{{content}}}"
            if "sub" in rendition:
                return f"\\textsubscript{{{content}}}"
            if "small" in rendition:
                return f"\\textsc{{{content}}}"
            return f"\\emph{{{content}}}"
        if is_spoken and split_spoken:
            return f"\\bookstacksdialogue{{“{content}”}}"
        if name in {"q", "quote"}:
            return f"“{content}”"
        if name == "stage":
            return f"\\bookstacksinlinestage{{{content}}}"
        if name == "lb":
            return r"\\"
        if name in {"pb", "milestone", "graphic", "fw", "metamark", "certainty", "shift"}:
            return ""
        if name == "gap":
            return "[…]"
        if name == "choice":
            for preferred_name in ("corr", "reg", "expan", "orig", "sic", "abbr"):
                preferred = first_direct(node, preferred_name)
                if preferred is not None:
                    return self.inline_content(preferred)
        if name == "del":
            return f"\\sout{{{content}}}"
        if name == "add":
            return f"\\uline{{{content}}}"
        return content

    def note_reference(self, note: ET.Element) -> str:
        content = self.inline_content(note).strip()
        content = re.sub(r"^(?:\[(?:\*|\d+)\]|\*)\s*", "", content)
        return f"\\bookstacksnote{{{content}}}" if content else ""

    @staticmethod
    def text(value: str | None) -> str:
        if not value:
            return ""
        return latex_escape(re.sub(r"\s+", " ", value))


def run(command: list[str], *, cwd: Path | None = None) -> None:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode:
        raise RuntimeError(f"Command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}")


def find_tectonic() -> str:
    candidates = [
        os.environ.get("TECTONIC"),
        shutil.which("tectonic"),
        str(ROOT / ".tools" / "tectonic" / ("tectonic.exe" if os.name == "nt" else "tectonic")),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise RuntimeError("Tectonic is required to compile the LaTeX edition into PDF. Set TECTONIC or install it on PATH.")


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
        "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
        "\u0092": "’", "√": r"\ensuremath{\surd}", "≠": "", "⏑": r"\ensuremath{\smile}",
        "〈": r"\ensuremath{\langle}", "〉": r"\ensuremath{\rangle}", "\uf00f": "", "（": "(", "）": ")",
    }
    return "".join(replacements.get(character, character) for character in value)


def cover_tex(edition: Edition) -> str:
    title = latex_escape(edition.title)
    author = latex_escape(edition.author)
    language = latex_escape(edition.language_name)
    return rf"""
\thispagestyle{{empty}}
\begin{{tikzpicture}}[remember picture,overlay]
  \fill[booknight] (current page.south west) rectangle (current page.north east);
  \fill[bookoxblood] (current page.south west) rectangle ([xshift=.105\paperwidth]current page.north west);
  \draw[bookaccent!72!booknight,line width=.55pt]
    ([xshift=.155\paperwidth,yshift=-.055\paperheight]current page.north west)
    rectangle
    ([xshift=-.075\paperwidth,yshift=.055\paperheight]current page.south east);
  \node[anchor=north west,text=bookaccent]
    at ([xshift=.19\paperwidth,yshift=-.105\paperheight]current page.north west)
    {{\fontsize{{7.5}}{{9}}\selectfont\addfontfeatures{{LetterSpace=18}} BOOKSTACKS CLASSICS}};
  \node[anchor=north east,text=booklight!10!booknight]
    at ([xshift=-.055\paperwidth,yshift=-.12\paperheight]current page.north east)
    {{\fontsize{{104}}{{104}}\selectfont B}};
  \draw[bookaccent,line width=1.15pt]
    ([xshift=.19\paperwidth,yshift=-.165\paperheight]current page.north west)
    -- ([xshift=-.13\paperwidth,yshift=-.165\paperheight]current page.north east);
  \fill[bookaccent]
    ([xshift=.19\paperwidth,yshift=-.165\paperheight]current page.north west) circle (1.8pt);
  \node[anchor=west,align=left,text width=.65\paperwidth,text=booklight]
    at ([xshift=.19\paperwidth,yshift=.10\paperheight]current page.west)
    {{\fontsize{{28}}{{33}}\selectfont {title}}};
  \draw[bookaccent,line width=.7pt]
    ([xshift=.19\paperwidth,yshift=-.045\paperheight]current page.west)
    -- ([xshift=.29\paperwidth,yshift=-.045\paperheight]current page.west);
  \node[anchor=west,align=left,text width=.65\paperwidth,text=bookmuted]
    at ([xshift=.19\paperwidth,yshift=-.105\paperheight]current page.west)
    {{\fontsize{{12.5}}{{16}}\selectfont {author}}};
  \node[anchor=south west,text=bookmuted]
    at ([xshift=.19\paperwidth,yshift=.095\paperheight]current page.south west)
    {{\fontsize{{7.5}}{{9}}\selectfont\addfontfeatures{{LetterSpace=10}} {language} EDITION}};
  \fill[bookaccent]
    ([xshift=-.105\paperwidth,yshift=.095\paperheight]current page.south east) circle (2.2pt);
\end{{tikzpicture}}
\null
\clearpage
"""


def publication_page_tex(edition: Edition) -> str:
    title = latex_escape(edition.title)
    author = latex_escape(edition.author)
    translator = latex_escape(edition.translator)
    publication_date = latex_escape(edition.publication_date)
    edition_statement = latex_escape(edition.edition_statement)
    source_citation = latex_escape(edition.source_citation)
    identifier = latex_escape(edition.identifier)
    license_text = latex_escape(edition.license_text)
    public_domain_note = ""
    if edition.author_slug in {"plato", "aristotle"}:
        public_domain_note = (
            "The underlying ancient work is in the public domain. "
            "Rights in this translation and source encoding are described below."
        )
    license_link = ""
    if edition.license_url:
        license_link = rf"\href{{\detokenize{{{edition.license_url}}}}}{{View the canonical license terms.}}"

    rows = [
        ("Title", title),
        ("Author", author),
    ]
    if translator:
        rows.append(("Translator", translator))
    if edition_statement:
        rows.append(("Edition", edition_statement))
    if source_citation:
        rows.append(("Source", source_citation))
    if publication_date:
        rows.append(("Published", publication_date))
    rows.extend((
        ("Edition ID", identifier),
        ("Canonical URI", rf"\href{{\detokenize{{{edition.canonical_url}}}}}{{bookstacks.org}}"),
    ))
    table_rows = " \\\\\n".join(
        rf"\textsc{{{latex_escape(label)}}} & {value}"
        for label, value in rows
    )
    rights_parts = [part for part in (public_domain_note, license_text, license_link) if part]
    rights = " ".join(rights_parts)

    return rf"""
\thispagestyle{{empty}}
\vspace*{{.09\textheight}}
{{\noindent\fontsize{{7.5}}{{9}}\selectfont\addfontfeatures{{LetterSpace=17}}\color{{bookaccent}} BOOKSTACKS EDITION\par}}
\vspace{{1.3\baselineskip}}

{{\noindent\fontsize{{20}}{{24}}\selectfont Publication record\par}}
\vspace{{.45\baselineskip}}
{{\noindent\color{{bookaccent}}\rule{{2.5em}}{{.8pt}}\par}}
\vspace{{1.8\baselineskip}}

\noindent\begin{{tabularx}}{{\textwidth}}{{@{{}}>{{\small\color{{bookmuted}}}}l@{{\hspace{{.165in}}}}>{{\small\raggedright\arraybackslash}}X@{{}}}}
{table_rows}
\end{{tabularx}}

\vfill
\noindent\begin{{minipage}}{{\textwidth}}
\footnotesize
\textsc{{Rights and availability}}\par
\vspace{{.45\baselineskip}}
{rights}\par
\vspace{{.9\baselineskip}}
No ISBN has been assigned. The stable Bookstacks edition identifier and canonical URI above serve as the publication record for this digital edition. Bookstacks asserts no additional restriction over this generated PDF beyond the canonical source terms.
\end{{minipage}}
"""


def latex_document(
    edition: Edition,
    body: str,
    font_filename: str,
    italic_font_filename: str,
    bold_font_filename: str,
    bold_italic_font_filename: str,
) -> str:
    language = {
        "en": "english",
        "fr": "french",
        "es": "spanish",
        "grc": "greek",
        "ru": "russian",
    }.get(edition.locale, "english")
    title = latex_escape(edition.title)
    author = latex_escape(edition.author)
    contents = latex_escape(str(LANGUAGES.get(edition.tei_language, LANGUAGES["eng"])["contents"]))
    # Keep the contents page at the primary reading divisions (books, acts,
    # chapters). Deep section lists become unreadable in heavily annotated TEI.
    toc_depth = 0
    canonical_url = edition.canonical_url
    return rf"""\documentclass[11pt,twoside,openany]{{memoir}}
\usepackage{{fontspec}}
\setmainfont{{{font_filename}}}[
  BoldFont={{{bold_font_filename}}},
  ItalicFont={{{italic_font_filename}}},
  BoldItalicFont={{{bold_italic_font_filename}}}
]
\usepackage[{language}]{{babel}}
\usepackage{{microtype}}
\usepackage{{amssymb}}
\usepackage{{xcolor}}
\usepackage{{tikz}}
\usepackage{{bookmark}}
\usepackage{{hyperref}}
\usepackage{{booktabs}}
\usepackage{{tabularx}}
\usepackage{{array}}
\usepackage{{changepage}}
\usepackage{{enumitem}}
\usepackage{{needspace}}
\usepackage[normalem]{{ulem}}

\definecolor{{bookoxblood}}{{HTML}}{{6B2636}}
\definecolor{{bookink}}{{HTML}}{{24201D}}
\definecolor{{bookpaper}}{{HTML}}{{F7F1E5}}
\definecolor{{booknight}}{{HTML}}{{171614}}
\definecolor{{booklight}}{{HTML}}{{F1ECE3}}
\definecolor{{bookmuted}}{{HTML}}{{BEB5A9}}
\definecolor{{bookaccent}}{{HTML}}{{D79BA8}}
\hypersetup{{
  hidelinks,
  bookmarksopen=true,
  bookmarksnumbered=false,
  pdfdisplaydoctitle=true,
  pdftitle={{{title}}},
  pdfauthor={{{author}}},
  pdfsubject={{A Bookstacks offline edition}},
  pdfkeywords={{TEI, literature, Bookstacks}}
}}
\setstocksize{{9in}}{{6in}}
\settrimmedsize{{9in}}{{6in}}{{*}}
\setlrmarginsandblock{{.8in}}{{.57in}}{{*}}
\setulmarginsandblock{{.68in}}{{.72in}}{{*}}
\setheadfoot{{22pt}}{{24pt}}
\checkandfixthelayout
\setlength{{\parindent}}{{1.5em}}
\setlength{{\parskip}}{{0pt}}
\setlength{{\emergencystretch}}{{3em}}
\raggedbottom
\setlength{{\beforechapskip}}{{0pt}}
\setlength{{\afterchapskip}}{{1.7\baselineskip}}
\setlength{{\cftbeforechapterskip}}{{.6em}}
\setcounter{{tocdepth}}{{{toc_depth}}}
\renewcommand{{\contentsname}}{{{contents}}}
\renewcommand{{\cftchapterfont}}{{\normalfont\bfseries}}
\renewcommand{{\cftchapterpagefont}}{{\normalfont\bfseries}}
\renewcommand{{\cftsectionfont}}{{\normalfont}}
\renewcommand{{\cftsectionpagefont}}{{\normalfont}}
\makeatletter
\renewcommand{{\@pnumwidth}}{{3.25em}}
\renewcommand{{\@tocrmarg}}{{4em}}
\makeatother

\makechapterstyle{{bookstacks}}{{
  \renewcommand{{\chapnamefont}}{{}}
  \renewcommand{{\chapnumfont}}{{}}
  \renewcommand{{\chaptitlefont}}{{\normalfont\fontsize{{24}}{{29}}\selectfont\raggedright}}
  \renewcommand{{\printchaptername}}{{}}
  \renewcommand{{\printchapternum}}{{}}
  \renewcommand{{\afterchapternum}}{{}}
  \renewcommand{{\printchaptertitle}}[1]{{\chaptitlefont ##1\par\nobreak\vskip .45\baselineskip\color{{bookaccent}}\rule{{2.5em}}{{1pt}}}}
}}
\chapterstyle{{bookstacks}}
\setsecheadstyle{{\normalfont\fontsize{{18}}{{22}}\selectfont\raggedright}}
\setsubsecheadstyle{{\normalfont\fontsize{{15}}{{19}}\selectfont\itshape\raggedright}}
\setsubsubsecheadstyle{{\normalfont\normalsize\itshape\raggedright}}
\setbeforesecskip{{-2.5\baselineskip}}
\setaftersecskip{{.75\baselineskip}}
\setbeforesubsecskip{{-2\baselineskip}}
\setaftersubsecskip{{.55\baselineskip}}

\nouppercaseheads
\makepagestyle{{bookstacks}}
\makeevenhead{{bookstacks}}{{\small\color{{bookmuted}}\thepage}}{{}}{{\small\itshape\color{{bookmuted}}\leftmark}}
\makeoddhead{{bookstacks}}{{\small\itshape\color{{bookmuted}}\rightmark}}{{}}{{\small\color{{bookmuted}}\thepage}}
\makeheadrule{{bookstacks}}{{\textwidth}}{{.25pt}}
\makeevenfoot{{bookstacks}}{{}}{{}}{{}}
\makeoddfoot{{bookstacks}}{{}}{{}}{{}}
\pagestyle{{bookstacks}}
\aliaspagestyle{{chapter}}{{empty}}
\renewcommand{{\foottextfont}}{{\footnotesize\color{{booklight}}}}
\renewcommand{{\footnoterule}}{{%
  \kern-3pt
  {{\color{{bookmuted}}\hrule width .35\columnwidth height .25pt}}
  \kern 2.6pt
}}

\newenvironment{{bookstacksspeech}}[1]
  {{\par\Needspace{{4\baselineskip}}\addvspace{{.55\baselineskip}}\noindent\textsc{{#1}}\par\nobreak\smallskip\begin{{adjustwidth}}{{1.5em}}{{0pt}}\noindent\ignorespaces}}
  {{\end{{adjustwidth}}\par}}
\newenvironment{{bookstacksstage}}
  {{\begin{{quote}}\small\itshape\color{{bookmuted}}}}
  {{\end{{quote}}}}
\newcommand{{\bookstacksinlinestage}}[1]{{\textit{{[#1]}}}}
\newcommand{{\bookstacksdialogue}}[1]{{\par\indent\ignorespaces #1\unskip}}
\newcommand{{\bookstacksnote}}[1]{{\footnote{{\color{{booklight}}#1}}\color{{booklight}}\mbox{{}}}}
\newenvironment{{bookstackscast}}
  {{\begin{{itemize}}[leftmargin=2em,label={{}},itemsep=.35em]}}
  {{\end{{itemize}}}}
\setlist{{nosep,leftmargin=2em}}
\renewcommand{{\arraystretch}}{{1.15}}

\begin{{document}}
{cover_tex(edition)}
\pagecolor{{booknight}}
\color{{booklight}}
\makeatletter
\global\let\default@color\current@color
\makeatother
{publication_page_tex(edition)}
\frontmatter
\begingroup
\newcommand{{\bookstacksignorecontentsline}}[3]{{}}
\let\addcontentsline\bookstacksignorecontentsline
\tableofcontents
\endgroup
\cleardoublepage
{body}
\clearpage
\thispagestyle{{empty}}
\vspace*{{\fill}}
\begin{{center}}
  \small\color{{bookmuted}}
  This offline edition was generated from the canonical TEI text.\\[.7em]
  \href{{\detokenize{{{canonical_url}}}}}{{bookstacks.org}}
\end{{center}}
\vspace*{{\fill}}
\end{{document}}
"""


def validate_pdf(path: Path) -> dict[str, int]:
    reader = PdfReader(path)
    pages = len(reader.pages)
    if pages < 2:
        raise RuntimeError(f"PDF has too few pages: {path}")
    try:
        outline_count = len(reader.outline)
    except Exception:
        outline_count = 0
    if outline_count == 0:
        raise RuntimeError(f"PDF contains no heading bookmarks: {path}")
    return {"pages": pages, "outline_items": outline_count}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def edition_fingerprint(edition: Edition) -> str:
    digest = hashlib.sha256()
    inputs = [
        edition.source,
        Path(__file__).resolve(),
        FONT_PATH,
        ITALIC_FONT_PATH,
        BOLD_FONT_PATH,
        BOLD_ITALIC_FONT_PATH,
        SMALL_FONT_PATH,
        SMALL_ITALIC_FONT_PATH,
        AUTHOR_PROFILES_PATH,
        ROOT / "requirements-exports.txt",
    ]
    for path in inputs:
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def cached_edition(
    edition: Edition,
    fingerprint: str,
) -> dict[str, object] | None:
    manifest_path = edition.output_dir / "manifest.json"
    if not manifest_path.is_file():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if manifest.get("generator_fingerprint") != fingerprint:
        return None
    if not (edition.output_dir / f"{edition.stem}.pdf").is_file():
        return None
    return manifest


def safe_reset_directory(target: Path) -> None:
    resolved = target.resolve()
    root = TMP_ROOT.resolve()
    if not resolved.is_relative_to(root) or resolved == root:
        raise RuntimeError(f"Refusing to reset directory outside task temp root: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def build_edition(edition: Edition) -> dict[str, object]:
    edition.output_dir.mkdir(parents=True, exist_ok=True)
    fingerprint = edition_fingerprint(edition)
    cached = cached_edition(edition, fingerprint)
    if cached is not None:
        print("  reused validated PDF", flush=True)
        return cached
    work_dir = TMP_ROOT / edition.stem
    safe_reset_directory(work_dir)
    body = LatexRenderer(edition).render()
    latex_dir = work_dir / "latex"
    latex_dir.mkdir()
    for font_path in (
        FONT_PATH,
        ITALIC_FONT_PATH,
        BOLD_FONT_PATH,
        BOLD_ITALIC_FONT_PATH,
        SMALL_FONT_PATH,
        SMALL_ITALIC_FONT_PATH,
    ):
        shutil.copy2(font_path, latex_dir / font_path.name)
    tex_path = latex_dir / f"{edition.stem}.tex"
    tex_path.write_text(
        latex_document(
            edition,
            body,
            FONT_PATH.name,
            ITALIC_FONT_PATH.name,
            BOLD_FONT_PATH.name,
            BOLD_ITALIC_FONT_PATH.name,
        ),
        encoding="utf-8",
        newline="\n",
    )
    tectonic = find_tectonic()
    run([tectonic, "--keep-logs", "--outdir", str(latex_dir), tex_path.name], cwd=latex_dir)
    compiled_pdf = latex_dir / f"{edition.stem}.pdf"
    pdf_path = edition.output_dir / compiled_pdf.name
    shutil.copy2(compiled_pdf, pdf_path)
    validations: dict[str, object] = {"pdf": validate_pdf(pdf_path)}

    manifest = {
        "schema_version": "1.0",
        "edition_id": edition.identifier,
        "work_id": f"{edition.author_slug}:{edition.work_slug}",
        "title": edition.title,
        "author": edition.author,
        "language": edition.locale,
        "canonical_url": edition.canonical_url,
        "source_tei": edition.source.name,
        "generator_fingerprint": fingerprint,
        "validations": validations,
        "files": [{"name": pdf_path.name, "bytes": pdf_path.stat().st_size, "sha256": sha256(pdf_path)}],
    }
    manifest_path = edition.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CHANGED_ASSETS.append(pdf_path)
    return manifest


def source_files(arguments: argparse.Namespace) -> list[Path]:
    if arguments.file:
        files = []
        for value in arguments.file:
            supplied = Path(value)
            if supplied.is_absolute():
                files.append(supplied.resolve())
                continue
            cwd_path = (Path.cwd() / supplied).resolve()
            root_path = (ROOT / supplied).resolve()
            files.append(cwd_path if cwd_path.exists() else root_path)
    else:
        files = sorted(path for path in TEI_ROOT.glob("*/*.xml") if path.parent.name in PUBLISHED_AUTHORS)
    for path in files:
        if not path.is_file() or path.suffix.lower() != ".xml" or not path.is_relative_to(TEI_ROOT.resolve()):
            raise ValueError(f"Export input must be a TEI XML file inside {TEI_ROOT}: {path}")
    return files


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", action="append", help="Build one TEI file (relative to the repository or absolute).")
    parser.add_argument("--all", action="store_true", help="Build every published TEI edition (the default when --file is omitted).")
    arguments = parser.parse_args()
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    CHANGED_ASSETS.clear()
    files = source_files(arguments)
    manifests: list[dict[str, object]] = []
    for index, source in enumerate(files, 1):
        edition = parse_edition(source)
        print(f"[{index}/{len(files)}] {edition.title} ({edition.locale})", flush=True)
        manifests.append(build_edition(edition))
    changed_path = OUTPUT_ROOT / "_changed-assets.json"
    changed_path.write_text(
        json.dumps([path.relative_to(OUTPUT_ROOT).as_posix() for path in CHANGED_ASSETS], indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Built {len(manifests)} PDF edition(s).", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
