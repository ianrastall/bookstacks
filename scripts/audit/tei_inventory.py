"""Inventory the Bookstacks TEI corpus for the corpus-database Stage 1 audit.

Read-only: parses every tei/<author>/*.xml file and writes a deterministic
JSON inventory. It does not modify, rebuild or validate the corpus; use
tei/validate_tei.py for schema and project-rule validation.

    py scripts/audit/tei_inventory.py --output docs/corpus-audit/tei-inventory.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from lxml import etree

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ROOT = Path(__file__).resolve().parents[2]
TEI_ROOT = ROOT / "tei"
RENDERER = ROOT / "src" / "lib" / "library.ts"
FILE_PATTERN = re.compile(r"^([^_]+)_(.+)_([a-z]{3})\.xml$")

# Attributes whose values are a controlled vocabulary worth listing in full.
VOCABULARY_ATTRIBUTES = {"type", "subtype", "rend", "rendition", "unit", "place", "role", "reason", "status", "resp", "cert", "scheme", "ed", "part"}
# Attributes holding one or more URI pointers.
POINTER_ATTRIBUTES = {"target", "corresp", "who", "toWhom", "ref", "sameAs", "next", "prev", "facs", "source", "ana", "url", "copyOf", "synch", "spanTo", "resp", "scheme", "key"}
# Elements whose text content is metadata or editorial apparatus rather than reading text.
HEADER_FIELDS = {
    "title_main": "tei:fileDesc/tei:titleStmt/tei:title[@type='main' or not(@type)]",
    "author": "tei:fileDesc/tei:titleStmt/tei:author",
    "editor_or_translator": "tei:fileDesc/tei:titleStmt/tei:editor | tei:fileDesc/tei:titleStmt/tei:respStmt[not(@xml:id='bookstacks-encoding')]",
    "edition_statement": "tei:fileDesc/tei:editionStmt",
    "publication_date": "tei:fileDesc/tei:publicationStmt/tei:date",
    "publication_idno": "tei:fileDesc/tei:publicationStmt/tei:idno",
    "licence": "tei:fileDesc/tei:publicationStmt/tei:availability",
    "source_bibl": "tei:fileDesc/tei:sourceDesc//tei:bibl | tei:fileDesc/tei:sourceDesc//tei:biblStruct | tei:fileDesc/tei:sourceDesc//tei:biblFull",
    "source_ref_url": "tei:fileDesc/tei:sourceDesc//tei:ref[starts-with(@target,'http')] | tei:fileDesc/tei:sourceDesc//tei:ptr[starts-with(@target,'http')]",
    "source_description_note": "tei:fileDesc/tei:notesStmt/tei:note[@type='source-description']",
    "lang_usage": "tei:profileDesc/tei:langUsage",
    "text_class": "tei:profileDesc/tei:textClass",
    "partic_desc": "tei:profileDesc/tei:particDesc",
    "encoding_desc": "tei:encodingDesc",
    "editorial_decl": "tei:encodingDesc/tei:editorialDecl",
    "revision_desc": "tei:revisionDesc",
}
FEATURES = {
    "notes": "//tei:text//tei:note",
    "dramatic_speech": "//tei:text//tei:sp",
    "cast_list": "//tei:castList",
    "verse_lines": "//tei:text//tei:l",
    "prose_said": "//tei:text//tei:said",
    "attributed_speech": "//tei:text//*[@who or @toWhom]",
    "quotation_q": "//tei:text//tei:q",
    "page_breaks": "//tei:text//tei:pb",
    "line_breaks": "//tei:text//tei:lb",
    "milestones": "//tei:text//tei:milestone",
    "figures": "//tei:text//tei:figure",
    "tables": "//tei:text//tei:table",
    "lists": "//tei:text//tei:list",
    "letters_or_floating_text": "//tei:text//tei:floatingText | //tei:text//tei:opener | //tei:text//tei:closer",
    "epigraphs": "//tei:text//tei:epigraph",
    "editorial_choice": "//tei:text//tei:choice | //tei:text//tei:sic | //tei:text//tei:corr | //tei:text//tei:reg | //tei:text//tei:orig",
    "editorial_intervention": "//tei:text//tei:gap | //tei:text//tei:supplied | //tei:text//tei:unclear | //tei:text//tei:del | //tei:text//tei:add",
    "foreign_language_spans": "//tei:text//*[@xml:lang]",
    "named_entities": "//tei:text//tei:persName | //tei:text//tei:placeName | //tei:text//tei:rs | //tei:text//tei:name",
    "stand_off": "//tei:standOff",
    "front_matter": "//tei:text/tei:front | //tei:group/tei:text/tei:front",
    "back_matter": "//tei:text/tei:back | //tei:group/tei:text/tei:back",
    "comments_in_text": "//tei:text//comment()",
}
NS = {"tei": TEI_NS, "xml": XML_NS}


def qname(node: etree._Element) -> str:
    tag = etree.QName(node)
    if tag.namespace == TEI_NS:
        return tag.localname
    return f"{{{tag.namespace}}}{tag.localname}" if tag.namespace else tag.localname


def attribute_name(name: str) -> str:
    tag = etree.QName(name)
    if tag.namespace == XML_NS:
        return f"xml:{tag.localname}"
    return f"{{{tag.namespace}}}{tag.localname}" if tag.namespace else tag.localname


def renderer_elements() -> list[str]:
    source = RENDERER.read_text(encoding="utf-8")
    body = source[source.index("function renderNode"):]
    return sorted(set(re.findall(r"case '([A-Za-z]+)':", body)))


def git_revision() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def inventory_file(path: Path, corpus: dict) -> dict:
    data = path.read_bytes()
    parser = etree.XMLParser(huge_tree=True, remove_comments=False, remove_pis=False, collect_ids=False)
    tree = etree.fromstring(data, parser)
    match = FILE_PATTERN.match(path.name)
    author, work, language = match.groups() if match else (path.parent.name, path.stem, "")

    ids: Counter[str] = Counter()
    element_count = 0
    text_nodes = 0
    text_chars = 0
    mixed_elements = 0
    edge_whitespace_text = 0
    max_depth = 0
    max_div_depth = 0
    pointer_stats: dict[str, Counter[str]] = defaultdict(Counter)
    pointers: list[tuple[str, str]] = []
    explicit_langs: Counter[str] = Counter()
    seen_elements: set[str] = set()
    header = tree.find(f"{{{TEI_NS}}}teiHeader")
    text_root = tree.find(f"{{{TEI_NS}}}text")
    in_text: set[etree._Element] = set(text_root.iter()) if text_root is not None else set()

    def walk(node: etree._Element, depth: int, div_depth: int) -> None:
        nonlocal element_count, text_nodes, text_chars, mixed_elements, edge_whitespace_text, max_depth, max_div_depth
        if not isinstance(node.tag, str):
            kind = "comment" if isinstance(node, etree._Comment) else "processing_instruction"
            corpus["non_element_nodes"][kind] += 1
            if has_text(node.tail):
                text_nodes += 1
                text_chars += len(node.tail)
            return
        name = qname(node)
        element_count += 1
        seen_elements.add(name)
        corpus["elements"][name] += 1
        if etree.QName(node).namespace != TEI_NS:
            corpus["non_tei_namespace_elements"][name] += 1
        max_depth = max(max_depth, depth)
        if name == "div":
            div_depth += 1
            max_div_depth = max(max_div_depth, div_depth)
        parent = node.getparent()
        if parent is not None and node in in_text:
            corpus["text_parent_child"][f"{qname(parent)}>{name}"] += 1
        for raw, value in node.attrib.items():
            attribute = attribute_name(raw)
            corpus["attributes"][f"{name}@{attribute}"] += 1
            if attribute == "xml:id":
                ids[value] += 1
            if attribute == "xml:lang" and parent is not None:
                explicit_langs[value] += 1
            if attribute == "xml:space":
                corpus["xml_space"][value] += 1
            if attribute in VOCABULARY_ATTRIBUTES:
                corpus["vocabulary"][f"{name}@{attribute}"][value] += 1
            if attribute in POINTER_ATTRIBUTES:
                for token in value.split():
                    kind = "local" if token.startswith("#") else "external" if re.match(r"^[a-z][a-z0-9+.-]*:", token, re.I) else "relative_or_key"
                    pointer_stats[attribute][kind] += 1
                    if kind == "local":
                        pointers.append((attribute, token[1:]))
        child_elements = [child for child in node if isinstance(child.tag, str)]
        own_text = [node.text] + [child.tail for child in node]
        if child_elements and any(has_text(value) for value in own_text):
            mixed_elements += 1
            corpus["mixed_content_elements"][name] += 1
        for value in own_text:
            if has_text(value):
                text_nodes += 1
                text_chars += len(value)
                if node in in_text and child_elements and value != value.strip() and value.strip():
                    edge_whitespace_text += 1
        for child in node:
            walk(child, depth + 1, div_depth)

    walk(tree, 1, 0)
    for element in seen_elements:
        corpus["element_editions"][element] += 1
    corpus["explicit_text_languages"].update(explicit_langs)

    unresolved: Counter[str] = Counter()
    for attribute, target in pointers:
        if target not in ids:
            unresolved[attribute] += 1

    def xpath_count(expression: str, context=tree) -> int:
        return int(context.xpath(f"count({expression})", namespaces=NS))

    header_fields: dict[str, str] = {}
    for field, expression in HEADER_FIELDS.items():
        nodes = header.xpath(expression, namespaces=NS) if header is not None else []
        if not nodes:
            header_fields[field] = "absent"
        elif all(not has_text("".join(node.itertext())) and not len(node) for node in nodes):
            header_fields[field] = "empty"
        else:
            header_fields[field] = "present"
    empty_header_elements = 0
    if header is not None:
        for node in header.iter():
            if isinstance(node.tag, str) and not len(node) and not has_text(node.text) and not node.attrib:
                empty_header_elements += 1

    title_nodes = header.xpath(HEADER_FIELDS["title_main"], namespaces=NS) if header is not None else []
    author_nodes = header.xpath(HEADER_FIELDS["author"], namespaces=NS) if header is not None else []
    div_types = Counter(div.get("type") or "(untyped)" for div in tree.iter(f"{{{TEI_NS}}}div"))
    duplicate_ids = sorted(value for value, count in ids.items() if count > 1)

    return {
        "file": path.relative_to(ROOT).as_posix(),
        "author_slug": author,
        "work_slug": work,
        "file_language": language,
        "root_id": tree.get(f"{{{XML_NS}}}id"),
        "root_lang": tree.get(f"{{{XML_NS}}}lang"),
        "text_lang": text_root.get(f"{{{XML_NS}}}lang") if text_root is not None else None,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "header_title": " ".join("".join(title_nodes[0].itertext()).split()) if title_nodes else None,
        "header_author": " ".join("".join(author_nodes[0].itertext()).split()) if author_nodes else None,
        "elements": element_count,
        "distinct_elements": len(seen_elements),
        "text_nodes": text_nodes,
        "text_characters": text_chars,
        "mixed_content_elements": mixed_elements,
        "edge_whitespace_text_nodes_in_text": edge_whitespace_text,
        "max_element_depth": max_depth,
        "max_div_depth": max_div_depth,
        "div_types": dict(sorted(div_types.items())),
        "xml_ids": sum(ids.values()),
        "duplicate_xml_ids": duplicate_ids,
        "local_pointers": len(pointers),
        "unresolved_local_pointers": dict(sorted(unresolved.items())),
        "pointer_kinds": {key: dict(sorted(value.items())) for key, value in sorted(pointer_stats.items())},
        "explicit_inner_languages": dict(sorted(explicit_langs.items())),
        "header_fields": header_fields,
        "empty_header_elements": empty_header_elements,
        "features": {name: xpath_count(expression) for name, expression in FEATURES.items()},
        "persons": xpath_count("//tei:person | //tei:personGrp"),
        "places": xpath_count("//tei:place"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    corpus: dict = {
        "elements": Counter(),
        "element_editions": Counter(),
        "attributes": Counter(),
        "vocabulary": defaultdict(Counter),
        "text_parent_child": Counter(),
        "mixed_content_elements": Counter(),
        "non_tei_namespace_elements": Counter(),
        "non_element_nodes": Counter(),
        "explicit_text_languages": Counter(),
        "xml_space": Counter(),
    }
    files = sorted(path for path in TEI_ROOT.glob("*/*.xml"))
    editions = [inventory_file(path, corpus) for path in files]
    rendered = renderer_elements()
    text_elements = {pair.split(">")[1] for pair in corpus["text_parent_child"]}

    summary = {
        "editions": len(editions),
        "authors": len({edition["author_slug"] for edition in editions}),
        "bytes": sum(edition["bytes"] for edition in editions),
        "elements": sum(edition["elements"] for edition in editions),
        "text_nodes": sum(edition["text_nodes"] for edition in editions),
        "text_characters": sum(edition["text_characters"] for edition in editions),
        "mixed_content_elements": sum(edition["mixed_content_elements"] for edition in editions),
        "xml_ids": sum(edition["xml_ids"] for edition in editions),
        "local_pointers": sum(edition["local_pointers"] for edition in editions),
        "unresolved_local_pointers": sum(sum(edition["unresolved_local_pointers"].values()) for edition in editions),
        "editions_with_duplicate_ids": sum(1 for edition in editions if edition["duplicate_xml_ids"]),
        "distinct_elements": len(corpus["elements"]),
        "distinct_text_parent_child_pairs": len(corpus["text_parent_child"]),
        "distinct_element_attribute_pairs": len(corpus["attributes"]),
        "max_div_depth": max(edition["max_div_depth"] for edition in editions),
        "max_element_depth": max(edition["max_element_depth"] for edition in editions),
        "feature_editions": {name: sum(1 for edition in editions if edition["features"][name]) for name in FEATURES},
        "header_field_status": {
            field: dict(Counter(edition["header_fields"][field] for edition in editions)) for field in HEADER_FIELDS
        },
        "editions_with_empty_header_elements": sum(1 for edition in editions if edition["empty_header_elements"]),
    }
    result = {
        "generated_from": {"git_revision": git_revision(), "tei_root": "tei", "renderer": RENDERER.relative_to(ROOT).as_posix()},
        "summary": summary,
        "renderer": {
            "handled_elements": rendered,
            "text_elements_not_explicitly_handled": sorted(text_elements - set(rendered)),
        },
        "elements": {name: {"occurrences": count, "editions": corpus["element_editions"][name]} for name, count in sorted(corpus["elements"].items())},
        "attributes": dict(sorted(corpus["attributes"].items())),
        "vocabulary": {key: dict(sorted(values.items(), key=lambda item: (-item[1], item[0]))) for key, values in sorted(corpus["vocabulary"].items())},
        "text_parent_child": dict(sorted(corpus["text_parent_child"].items())),
        "mixed_content_elements": dict(sorted(corpus["mixed_content_elements"].items())),
        "non_tei_namespace_elements": dict(sorted(corpus["non_tei_namespace_elements"].items())),
        "non_element_nodes": dict(sorted(corpus["non_element_nodes"].items())),
        "explicit_text_languages": dict(sorted(corpus["explicit_text_languages"].items())),
        "xml_space": dict(sorted(corpus["xml_space"].items())),
        "editions": editions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"Inventoried {summary['editions']} editions: {summary['elements']} elements, {summary['distinct_elements']} element types -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
