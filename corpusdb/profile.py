"""Bookstacks encoding profile, version 0.1.0 (prototype).

These rules extend tei/validate_tei.py; they do not replace it. Errors are
defects that block a release in the prototype database. Warnings record
drift whose resolution is an open editorial decision (normalize the TEI or
map source values in the profile); see docs/corpus-audit/README.md.
Changing any rule, list or severity requires a new PROFILE_VERSION.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from lxml import etree

PROFILE_VERSION = "0.1.0"
TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI_NS, "xml": XML_NS}
XML_ID = f"{{{XML_NS}}}id"
XML_LANG = f"{{{XML_NS}}}lang"

Finding = tuple[str, str]

# Assessment inventory from the Stage 1 audit: code, description, XPath counted per revision.
FEATURES: list[tuple[str, str, str]] = [
    ("front-matter", "Front matter", "//tei:text/tei:front"),
    ("back-matter", "Back matter", "//tei:text/tei:back"),
    ("notes", "Notes", "//tei:text//tei:note"),
    ("dramatic-speech", "Dramatic speeches", "//tei:text//tei:sp"),
    ("cast-list", "Cast lists", "//tei:castList"),
    ("verse", "Verse lines", "//tei:text//tei:l"),
    ("prose-dialogue", "Prose dialogue (said)", "//tei:text//tei:said"),
    ("attributed-speech", "Speaker or addressee attribution", "//tei:text//*[@who or @toWhom]"),
    ("quotation", "Quotations (q)", "//tei:text//tei:q"),
    ("page-milestones", "Page breaks", "//tei:text//tei:pb | //tei:text//tei:milestone[@unit='page']"),
    ("reference-milestones", "Reference-system milestones", "//tei:text//tei:milestone[@unit!='page']"),
    ("line-breaks", "Line breaks", "//tei:text//tei:lb"),
    ("figures", "Figures", "//tei:text//tei:figure"),
    ("tables", "Tables", "//tei:text//tei:table"),
    ("lists", "Lists", "//tei:text//tei:list"),
    ("letters", "Letters and embedded texts", "//tei:text//tei:floatingText | //tei:text//tei:opener | //tei:text//tei:closer"),
    ("epigraphs", "Epigraphs", "//tei:text//tei:epigraph"),
    ("editorial-choice", "Editorial alternatives", "//tei:text//tei:choice"),
    ("editorial-intervention", "Gaps, supplied, unclear, deleted or added text", "//tei:text//tei:gap | //tei:text//tei:supplied | //tei:text//tei:unclear | //tei:text//tei:del | //tei:text//tei:add"),
    ("foreign-language", "Passages in another language", "//tei:text//*[@xml:lang]"),
    ("named-entities", "Named entities", "//tei:text//tei:persName | //tei:text//tei:placeName | //tei:text//tei:rs | //tei:text//tei:name"),
    ("participant-register", "Participant registers", "//tei:particDesc//tei:person | //tei:particDesc//tei:personGrp | //tei:standOff//tei:person | //tei:standOff//tei:personGrp"),
]

POINTER_ATTRIBUTES = ("target", "corresp", "who", "toWhom", "ref", "sameAs", "next", "prev", "source", "ana", "copyOf", "synch", "spanTo", "resp")

# Language tags allowed inside texts. BCP 47 uses the shortest ISO 639 code, so
# deu, fre, lat and eng are not valid tags; the map gives the intended value.
LANGUAGE_TAGS = {"de", "el", "en", "es", "fr", "grc", "it", "la", "pl", "ru", "zh-Hans"}
LANGUAGE_CORRECTIONS = {"deu": "de", "ger": "de", "fre": "fr", "fra": "fr", "lat": "la", "eng": "en", "ita": "it", "spa": "es", "rus": "ru"}

# Canonical values and observed source aliases (decision pending: rewrite TEI or map here).
REND_VALUES = {"italic", "bold", "underline", "sup", "sub", "small", "small-caps", "letter-spaced"}
REND_ALIASES = {"Italic": "italic", "i(1)": "italic", "it": "italic", "#italic": "italic", "itlalic": "italic", "em": "italic", "strong": "bold", "superscript": "sup", "sc(1)": "small-caps", "Razradka": "letter-spaced"}
Q_TYPES = {"spoken", "thought", "written", "mentioned", "soCalled", "emph", "title", "foreign", "gloss", "term", "translation", "expression", "proverb"}
Q_ALIASES = {"socalled": "soCalled"}
MILESTONE_UNITS = {"section", "para", "line", "page", "part", "speech", "separator", "typographic"}
MILESTONE_ALIASES = {"Line": "line"}
NOTE_TYPES = {"editorial", "authorial", "translation", "dates", "source-provenance", "source-description", "translation-credit", "scope"}


def location(node: etree._Element) -> str:
    """Nearest identified ancestor-or-self, which survives unrelated edits better than an XPath."""
    for candidate in [node, *node.iterancestors()]:
        identifier = candidate.get(XML_ID)
        if identifier:
            suffix = "" if candidate is node else f" > {etree.QName(node).localname}"
            return f"#{identifier}{suffix}"
    return node.getroottree().getpath(node)


def check_pointers(tree: etree._Element, language: str) -> list[Finding]:
    ids = set(tree.xpath("//@xml:id", namespaces=NS))
    findings: list[Finding] = []
    for attribute in POINTER_ATTRIBUTES:
        for node in tree.xpath(f"//*[@{attribute}]"):
            for token in node.get(attribute).split():
                if token.startswith("#") and token[1:] not in ids:
                    findings.append((location(node), f"{etree.QName(node).localname}/@{attribute} points to undeclared {token}"))
    return findings


def check_text_language(tree: etree._Element, language: str) -> list[Finding]:
    text = tree.find(f"{{{TEI_NS}}}text")
    declared = text.get(XML_LANG) if text is not None else None
    if declared == language:
        return []
    return [("/TEI/text", f"text/@xml:lang is {declared!r}; the edition language is {language!r}")]


def check_language_tags(tree: etree._Element, language: str) -> list[Finding]:
    findings: list[Finding] = []
    for node in tree.xpath("//*[@xml:lang]", namespaces=NS):
        value = node.get(XML_LANG)
        if value not in LANGUAGE_TAGS:
            hint = f"; use {LANGUAGE_CORRECTIONS[value]!r}" if value in LANGUAGE_CORRECTIONS else "; not a recognized tag"
            findings.append((location(node), f"xml:lang {value!r}{hint}"))
    return findings


def check_required_header(tree: etree._Element, language: str) -> list[Finding]:
    required = {
        "main title": "tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title[normalize-space()]",
        "author": "tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:author[normalize-space()]",
        "publication identifier": "tei:teiHeader/tei:fileDesc/tei:publicationStmt/tei:idno[normalize-space()]",
        "licence": "tei:teiHeader/tei:fileDesc/tei:publicationStmt/tei:availability[normalize-space()]",
    }
    return [("/TEI/teiHeader", f"missing {label}") for label, expression in required.items() if not tree.xpath(expression, namespaces=NS)]


def check_language_usage(tree: etree._Element, language: str) -> list[Finding]:
    if tree.xpath("tei:teiHeader/tei:profileDesc/tei:langUsage/tei:language", namespaces=NS):
        return []
    return [("/TEI/teiHeader", "no profileDesc/langUsage declaration")]


def check_source_citation(tree: etree._Element, language: str) -> list[Finding]:
    expression = "tei:teiHeader/tei:fileDesc/tei:sourceDesc[.//tei:bibl or .//tei:biblStruct or .//tei:biblFull or .//tei:ref[starts-with(@target,'http')] or .//tei:ptr[starts-with(@target,'http')]]"
    if tree.xpath(expression, namespaces=NS):
        return []
    return [("/TEI/teiHeader/fileDesc/sourceDesc", "no structured bibliographic citation or source URL")]


def check_empty_header_elements(tree: etree._Element, language: str) -> list[Finding]:
    header = tree.find(f"{{{TEI_NS}}}teiHeader")
    findings: list[Finding] = []
    for node in header.iter() if header is not None else []:
        if isinstance(node.tag, str) and not len(node) and not (node.text or "").strip() and not node.attrib:
            findings.append((node.getroottree().getpath(node), f"empty {etree.QName(node).localname}"))
    return findings


def vocabulary_check(expression: str, attribute: str, allowed: set[str], aliases: dict[str, str], tokenized: bool = False) -> Callable[[etree._Element, str], list[Finding]]:
    def check(tree: etree._Element, language: str) -> list[Finding]:
        findings: list[Finding] = []
        for node in tree.xpath(expression, namespaces=NS):
            raw = node.get(attribute)
            for value in raw.split() if tokenized else [raw]:
                if value not in allowed:
                    hint = f"; profile value {aliases[value]!r}" if value in aliases else "; no profile value"
                    findings.append((location(node), f"@{attribute} {value!r}{hint}"))
        return findings

    return check


@dataclass(frozen=True)
class Rule:
    code: str
    severity: str
    description: str
    check: Callable[[etree._Element, str], list[Finding]]


RULES: list[Rule] = [
    Rule("pointer-resolves", "error", "Every local # pointer resolves to an xml:id in the same edition.", check_pointers),
    Rule("text-language-matches-edition", "error", "text/@xml:lang equals the edition language (BCP 47).", check_text_language),
    Rule("language-tag-allowed", "error", "Every xml:lang value is a valid, profile-declared BCP 47 tag.", check_language_tags),
    Rule("header-required-fields", "error", "The header has a main title, author, publication identifier and licence.", check_required_header),
    Rule("header-language-usage", "warning", "The header declares langUsage.", check_language_usage),
    Rule("header-source-citation", "warning", "sourceDesc has a structured citation or a source URL.", check_source_citation),
    Rule("header-no-empty-elements", "warning", "The header has no empty placeholder elements.", check_empty_header_elements),
    Rule("rend-vocabulary", "warning", "hi/@rend values come from the profile list.", vocabulary_check("//tei:text//tei:hi[@rend]", "rend", REND_VALUES, REND_ALIASES, tokenized=True)),
    Rule("q-type-vocabulary", "warning", "q/@type values come from the profile list.", vocabulary_check("//tei:text//tei:q[@type]", "type", Q_TYPES, Q_ALIASES)),
    Rule("milestone-unit-vocabulary", "warning", "milestone/@unit values come from the profile list.", vocabulary_check("//tei:text//tei:milestone[@unit]", "unit", MILESTONE_UNITS, MILESTONE_ALIASES)),
    Rule("note-type-vocabulary", "warning", "note/@type values come from the profile list.", vocabulary_check("//tei:note[@type]", "type", NOTE_TYPES, {})),
]

if len({rule.code for rule in RULES}) != len(RULES) or not all(re.fullmatch(r"[a-z][a-z-]+", rule.code) for rule in RULES):
    raise ValueError("Profile rule codes must be unique kebab-case identifiers")
