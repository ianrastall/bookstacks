"""Convert supported Spanish Project Gutenberg drama EPUBs to TEI P5."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import sys

from lxml import etree

from build_gutenberg_drama_epub import (
    TEI,
    XML_ID,
    XML_LANG,
    DramaBuilder,
    add_cast_item,
    append_text,
    classes,
    clean_text,
    convert_inline,
    element_text,
    epub_data,
    local_name,
    project_gutenberg_id,
    split_break_lines,
    tei,
    validate_structure,
    write_document,
)


SUPPORTED_PLAYS = {
    "56454": {
        "slug": "hamlet",
        "translator": "Leandro Fernández de Moratín",
    },
}


class SpanishIds:
    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()

    def next(self, kind: str) -> str:
        self.counts[kind] += 1
        return f"spa-{kind}-{self.counts[kind]:06d}"


def spanish_speech_prefix(element: etree._Element) -> tuple[str, str, int] | None:
    raw = "".join(element.itertext())
    position = raw.find("—")
    if position < 1:
        return None
    label = clean_text(raw[:position])
    if not label.endswith("."):
        return None
    label = label[:-1].strip()
    if label.startswith("("):
        return None
    qualifier = ""
    qualified = re.fullmatch(r"(.+?)\s*\((.+)\)", label)
    if qualified:
        label = clean_text(qualified.group(1))
        qualifier = clean_text(qualified.group(2))
    letters = [character for character in label if character.isalpha()]
    if len(letters) < 2 or len(label) > 100:
        return None
    return label, qualifier, position + 1


def spanish_stage_type(value: str, before_speech: bool) -> str:
    folded = value.casefold().lstrip("(")
    if re.search(r"\b(vase|vanse|retírase|retíranse|se retira|se van)\b", folded):
        return "exit"
    if re.search(r"^(sale|salen|entra|entran|aparece|aparecen|vuelve|vuelven)\b", folded):
        return "entrance"
    return "setting" if before_speech else "business"


def looks_like_spanish_stage(element: etree._Element, before_speech: bool) -> bool:
    value = element_text(element)
    if classes(element) & {"hang", "hang2", "rt", "secthead"}:
        return True
    if value.startswith("(") and value.endswith((")", ").")):
        return True
    folded = value.casefold().lstrip("(")
    if re.match(r"^(sale|salen|entra|entran|aparece|aparecen|vase|vanse|retírase|retíranse)\b", folded):
        return True
    return before_speech


def looks_like_scene_cast(value: str) -> bool:
    letters = [character for character in value if character.isalpha()]
    uppercase = sum(character == character.upper() for character in letters)
    return bool(letters) and (uppercase / len(letters) >= 0.65 or "y dichos" in value.casefold())


class SpanishDramaBuilder(DramaBuilder):
    def __init__(
        self,
        metadata: dict[str, object],
        documents: list[etree._Element],
        text_id: str,
        translator: str,
    ) -> None:
        self.translator = translator
        self.finished = False
        self.scene_introduction: etree._Element | None = None
        super().__init__(metadata, documents, text_id)
        self.ids = SpanishIds()

    def make_document(self) -> etree._ElementTree:
        document = super().make_document()
        namespaces = {"tei": TEI}
        root = document.getroot()
        root.set(XML_LANG, "es")
        text = document.find(".//tei:text", namespaces)
        assert text is not None
        text.set(XML_LANG, "es")

        title = document.find(".//tei:titleStmt/tei:title", namespaces)
        if title is not None:
            title.set(XML_LANG, "es")

        title_stmt = document.find(".//tei:titleStmt", namespaces)
        assert title_stmt is not None
        translation = tei("respStmt")
        translation.append(tei("resp", "Spanish translation"))
        translation.append(tei("name", self.translator))
        encoding = document.find(".//tei:respStmt[@xml:id='bookstacks-encoding']", {"tei": TEI, "xml": "http://www.w3.org/XML/1998/namespace"})
        title_stmt.insert(title_stmt.index(encoding) if encoding is not None else len(title_stmt), translation)

        edition = document.find(".//tei:editionStmt/tei:edition", namespaces)
        if edition is not None:
            edition.text = "Bookstacks Spanish TEI edition"
        source = document.find(".//tei:sourceDesc/tei:p", namespaces)
        if source is not None:
            pg_id = project_gutenberg_id(self.metadata, Path(self.text_id))
            source.text = (
                f"Born-digital Spanish text from Project Gutenberg eBook #{pg_id}, "
                "converted from its EPUB XHTML reading order. Gutenberg administrative "
                "boilerplate, navigation, and decorative images were omitted."
            )
        language = document.find(".//tei:langUsage/tei:language", namespaces)
        if language is not None:
            language.set("ident", "es")
            language.text = "Spanish"
        change = document.find(".//tei:revisionDesc/tei:change", namespaces)
        if change is not None:
            change.text = "Converted the Spanish Project Gutenberg EPUB XHTML into standalone dramatic TEI P5."
        return document

    def new_spanish_scene(self, element: etree._Element) -> None:
        if self.current_act is None:
            self.new_prologue("Prólogo")
        lines = split_break_lines(element)
        heading = lines[0] if lines else element_text(element)
        self.scene_number += 1
        structural_parent = "prologue" if self.current_act.get("type") == "prologue" else f"act-{self.act_number:03d}"
        division = tei(
            "div",
            type="scene",
            n=str(self.scene_number),
            xml_id=f"{self.text_id}-{structural_parent}-scene-{self.scene_number:03d}",
        )
        division.append(tei("head", heading))
        introduction = None
        if len(lines) > 1:
            introduction = tei(
                "stage",
                type="setting",
                rend="scene-introduction",
                xml_id=self.ids.next("stage"),
            )
            for index, extra in enumerate(lines[1:]):
                if index:
                    introduction.append(tei("lb"))
                if looks_like_scene_cast(extra):
                    introduction.append(tei("name", extra, type="person"))
                else:
                    introduction.append(tei("hi", extra, rend="italic"))
            division.append(introduction)
        self.current_act.append(division)
        self.current_scene = division
        self.scene_introduction = introduction
        self.current_sp = None
        self.scene_has_speech = False

    def add_heading(self, element: etree._Element) -> None:
        if self.finished:
            return
        value = element_text(element)
        folded = value.casefold()
        if re.search(r"\bacto\b", folded) and not folded.startswith("fin "):
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
        if re.search(r"\bescena\b", folded):
            self.new_spanish_scene(element)
            return
        if "personajes" in folded or "dramatis personae" in folded:
            self.new_front("characters", value)
            return
        if self.current_act is None:
            kind = "introduction" if any(word in folded for word in ("advertencia", "introducción", "prólogo", "prefacio")) else "title-page"
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
        if self.current_scene is not None and not self.scene_has_speech:
            if self.scene_introduction is None:
                self.scene_introduction = tei(
                    "stage",
                    type="setting",
                    rend="scene-introduction",
                    xml_id=self.ids.next("stage"),
                )
                self.current_scene.append(self.scene_introduction)
            if len(self.scene_introduction) or clean_text(self.scene_introduction.text):
                self.scene_introduction.append(tei("lb"))
            description = tei("hi", rend="italic")
            convert_inline(element, description, self.ids, self.notes)
            self.scene_introduction.append(description)
            return
        stage = tei(
            "stage",
            type=spanish_stage_type(element_text(element), not self.scene_has_speech),
            xml_id=self.ids.next("stage"),
        )
        convert_inline(element, stage, self.ids, self.notes)
        self.target().append(stage)

    def add_cast_paragraph(self, element: etree._Element) -> None:
        lines = split_break_lines(element)
        if not lines:
            return
        if not any(line.startswith("VOLTIMAN") for line in lines):
            for line in lines:
                add_cast_item(self.cast_list, line)
            return

        regular_before = lines[:9]
        regular_after = lines[17:]
        for line in regular_before:
            add_cast_item(self.cast_list, line)

        for roles, description in (
            ("VOLTIMAN, CORNELIO, RICARDO y GUILLERMO", "cortesanos"),
            ("ENRIQUE, MARCELO, BERNARDO y FRANCISCO", "soldados"),
        ):
            item = tei("castItem")
            item.append(tei("role", roles))
            append_text(item, f", {description}.")
            self.cast_list.append(item)

        for line in regular_after:
            add_cast_item(self.cast_list, line)

    def add_paragraph(self, element: etree._Element) -> None:
        if self.finished:
            return
        value = element_text(element)
        if not value or re.fullmatch(r"[=*_\s-]+", value):
            return
        if re.match(r"^FIN\s+(?:DEL|DE)\s+ACTO", value, re.IGNORECASE):
            return
        if re.match(r"^FIN\s+DEL\s+DRAMA\b", value, re.IGNORECASE):
            self.current_sp = None
            paragraph = tei("p", xml_id=self.ids.next("p"), rend="center")
            convert_inline(element, paragraph, self.ids, self.notes)
            self.target().append(paragraph)
            self.finished = True
            return
        if self.cast_list is not None:
            if value.casefold().startswith("la escena"):
                self.add_stage(element)
            else:
                self.add_cast_paragraph(element)
            return

        prefix = spanish_speech_prefix(element) if self.current_scene is not None else None
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
            self.scene_introduction = None
            return

        if self.current_scene is not None and looks_like_spanish_stage(element, not self.scene_has_speech):
            self.add_stage(element)
            return

        paragraph = tei("p", xml_id=self.ids.next("p"))
        convert_inline(element, paragraph, self.ids, self.notes)
        if not element_text(paragraph) and not len(paragraph):
            return
        if self.current_scene is not None and self.current_sp is not None:
            self.current_sp.append(paragraph)
        else:
            self.target().append(paragraph)

    def add_poem(self, element: etree._Element) -> None:
        if self.finished:
            return
        stanzas = element.xpath("./*[contains(concat(' ', normalize-space(@class), ' '), ' stanza ')]")
        stanzas = stanzas or [element]
        for stanza in stanzas:
            group = tei("lg", xml_id=self.ids.next("verse-group"))
            source_lines = stanza.xpath("./*[local-name()='span']")
            for source_line in source_lines:
                line = tei("l", xml_id=self.ids.next("line"))
                indentation = next((name[1:] for name in classes(source_line) if re.fullmatch(r"i\d+", name)), None)
                if indentation:
                    line.set("rend", f"indent-{indentation}")
                convert_inline(source_line, line, self.ids, self.notes)
                if len(line) and local_name(line[-1]) == "lb" and not clean_text(line[-1].tail):
                    line.remove(line[-1])
                if element_text(line) or len(line):
                    group.append(line)
            if not len(group):
                continue
            if self.current_scene is not None and self.current_sp is not None:
                self.current_sp.append(group)
            else:
                self.target().append(group)

    def add_table(self, element: etree._Element) -> None:
        if self.finished:
            return
        if self.current_front is not None and self.current_front.get("type") == "title-page":
            targets = element.xpath(".//*[local-name()='a']/@href")
            if targets and all(".xhtml#" in target for target in targets):
                return
        super().add_table(element)

    def add_monospaced(self, element: etree._Element) -> None:
        if not self.finished:
            super().add_monospaced(element)

    def add_blockquote(self, element: etree._Element) -> None:
        if not self.finished:
            super().add_blockquote(element)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    args = parser.parse_args()

    metadata, documents = epub_data(args.source)
    pg_id = project_gutenberg_id(metadata, args.source)
    play = SUPPORTED_PLAYS.get(pg_id)
    if play is None:
        raise ValueError(f"Unsupported Spanish drama EPUB: Project Gutenberg #{pg_id}")
    if metadata.get("creator") != "William Shakespeare" or metadata.get("language") != "es":
        raise ValueError(f"Unexpected metadata in {args.source}: {metadata.get('creator')}, {metadata.get('language')}")

    slug = play["slug"]
    text_id = f"shakespeare-{slug}-spa"
    output = args.output_dir / f"shakespeare_{slug}_spa.xml"
    builder = SpanishDramaBuilder(metadata, documents, text_id, play["translator"])
    document = builder.build()
    schema = etree.RelaxNG(etree.parse(str(args.schema)))
    validate_structure(document, output, schema)
    write_document(document, output)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
