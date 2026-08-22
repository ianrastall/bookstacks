"""Validate generated Bookstacks TEI and its project-level invariants."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

from lxml import etree


TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI_NS, "xml": XML_NS}


def validate_file(path: Path, schema: etree.RelaxNG) -> list[str]:
    errors: list[str] = []
    parser = etree.XMLParser(collect_ids=False, huge_tree=True)
    try:
        document = etree.parse(str(path), parser)
    except etree.XMLSyntaxError as exc:
        return [f"not well-formed XML: {exc}"]

    if not schema.validate(document):
        errors.extend(str(entry) for entry in schema.error_log)

    ids = document.xpath("//@xml:id", namespaces=NS)
    duplicates = sorted(value for value, count in Counter(ids).items() if count > 1)
    if duplicates:
        errors.append("duplicate xml:id values: " + ", ".join(duplicates))

    declared_people = set(
        document.xpath("//tei:person/@xml:id | //tei:personGrp/@xml:id", namespaces=NS)
    )
    attributed_speech = document.xpath(
        "//tei:said[@who or @toWhom] | //tei:q[@who or @toWhom]", namespaces=NS
    )
    for speech in attributed_speech:
        for attribute_name in ("who", "toWhom"):
            value = speech.get(attribute_name)
            if value is None:
                continue
            for pointer in value.split():
                role = "speaker" if attribute_name == "who" else "addressee"
                if not pointer.startswith("#"):
                    errors.append(f"non-local {role} pointer: {pointer}")
                elif pointer[1:] not in declared_people:
                    errors.append(f"unresolved {role} pointer: {pointer}")

    missing_utterance_ids = document.xpath("//tei:said[not(@xml:id)]", namespaces=NS)
    if missing_utterance_ids:
        errors.append(f"said elements without xml:id: {len(missing_utterance_ids)}")

    missing_attributed_quote_ids = document.xpath(
        "//tei:q[(@type = 'spoken' or @who or @toWhom) and not(@xml:id)]",
        namespaces=NS,
    )
    if missing_attributed_quote_ids:
        errors.append(
            "spoken/attributed q elements without xml:id: "
            + str(len(missing_attributed_quote_ids))
        )

    missing_division_ids = document.xpath("//tei:text//tei:div[not(@xml:id)]", namespaces=NS)
    if missing_division_ids:
        errors.append(f"text divisions without xml:id: {len(missing_division_ids)}")

    missing_paragraph_ids = document.xpath("//tei:text//tei:p[not(@xml:id)]", namespaces=NS)
    if missing_paragraph_ids:
        errors.append(f"text paragraphs without xml:id: {len(missing_paragraph_ids)}")

    dramatic_speeches = document.xpath("//tei:text//tei:sp", namespaces=NS)
    if dramatic_speeches:
        dramatic_checks = (
            ("//tei:text//tei:sp[not(@xml:id)]", "dramatic speeches without xml:id"),
            ("//tei:text//tei:sp[not(tei:speaker)]", "dramatic speeches without speaker"),
            (
                "//tei:text//tei:sp[not(tei:p or tei:lg)]",
                "dramatic speeches without prose or verse content",
            ),
            ("//tei:text//tei:lg[not(@xml:id)]", "verse groups without xml:id"),
            ("//tei:text//tei:l[not(@xml:id)]", "verse lines without xml:id"),
            ("//tei:text//tei:stage[not(@xml:id)]", "stage directions without xml:id"),
        )
        for expression, message in dramatic_checks:
            matches = document.xpath(expression, namespaces=NS)
            if matches:
                errors.append(f"{message}: {len(matches)}")

    unqualified_ids = document.xpath("//@id[namespace-uri() = '']")
    if unqualified_ids:
        errors.append(f"unqualified id attributes: {len(unqualified_ids)}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="TEI files or directories (defaults to author subdirectories)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    schema = etree.RelaxNG(etree.parse(str(script_dir / "tei_all.rng")))
    inputs = args.paths or sorted(
        directory
        for directory in script_dir.iterdir()
        if directory.is_dir() and any(directory.glob("*.xml"))
    )
    files: list[Path] = []
    for item in inputs:
        files.extend(sorted(item.rglob("*.xml")) if item.is_dir() else [item])

    failures = 0
    for path in files:
        errors = validate_file(path, schema)
        if errors:
            failures += 1
            print(f"FAIL {path}")
            for error in errors:
                print(f"  {error}")
        else:
            print(f"OK   {path}")

    print(f"\nValidated {len(files)} files; {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
