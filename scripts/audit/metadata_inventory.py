"""Inventory Bookstacks edition metadata held outside the TEI files.

Read-only companion to tei_inventory.py. It compares the TEI inventory with
the catalogue data in site code, JSON side files and publication manifests.

    py scripts/audit/metadata_inventory.py --tei-inventory docs/corpus-audit/tei-inventory.json --output docs/corpus-audit/metadata-inventory.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "src" / "lib" / "library.ts"
PROFILES = ROOT / "src" / "data" / "author-profiles.json"
DOWNLOADS = ROOT / "public" / "downloads"
PORTRAITS = ROOT / "public" / "img" / "authors"
ASTRO_CONFIG = ROOT / "astro.config.mjs"
LANGUAGE_ROUTE = {"eng": "en", "fra": "fr", "spa": "es", "grc": "grc", "rus": "ru", "zho": "zh-Hans"}


def ts_object(source: str, name: str) -> dict[str, str]:
    start = source.index(f"const {name}")
    body = source[source.index("{", start):source.index("};", start)]
    return dict(re.findall(r"^\s+'?([^':\s]+)'?\s*:\s*\{?\s*(?:code:\s*)?'([^']*)'", body, re.M))


def ts_list(source: str, name: str) -> list[str]:
    start = source.index(f"const {name}")
    end = source.index(";", start)
    return re.findall(r"'([^']+)'", source[start:end])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tei-inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    inventory = json.loads(args.tei_inventory.read_text(encoding="utf-8"))
    editions = inventory["editions"]
    library = LIBRARY.read_text(encoding="utf-8")
    profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
    work_titles = ts_object(library, "WORK_TITLES")
    language_data = ts_object(library, "LANGUAGE_DATA")

    works: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for edition in editions:
        works[(edition["author_slug"], edition["work_slug"])].append(edition)
    work_slugs = {work for _, work in works}

    # Author identity: one profile name versus the header strings across that author's editions.
    authors = {}
    for slug in sorted({edition["author_slug"] for edition in editions}):
        header_forms = Counter(edition["header_author"] for edition in editions if edition["author_slug"] == slug)
        authors[slug] = {
            "profile_name": profiles.get(slug, {}).get("name"),
            "profile_dates": profiles.get(slug, {}).get("dates"),
            "portrait": profiles.get(slug, {}).get("portrait"),
            "header_author_forms": dict(sorted(header_forms.items(), key=lambda item: (-item[1], str(item[0])))),
        }

    # Work identity is derived only from file names; titles live in code or fall back to the slug.
    work_records = []
    for (author, work), items in sorted(works.items()):
        work_records.append({
            "author_slug": author,
            "work_slug": work,
            "editions": sorted(item["file_language"] for item in items),
            "title_source": "WORK_TITLES" if work in work_titles else "slug fallback",
            "header_titles": sorted({item["header_title"] or "" for item in items}),
        })

    # Edition language: file suffix, code table and TEI declarations.
    language_mismatches = [
        {"file": edition["file"], "file_language": edition["file_language"], "root_lang": edition["root_lang"], "text_lang": edition["text_lang"]}
        for edition in editions
        if edition["text_lang"] != LANGUAGE_ROUTE.get(edition["file_language"]) or (edition["root_lang"] and edition["root_lang"] != edition["text_lang"])
    ]

    # Publication manifests committed with exporter PDFs.
    tei_hashes = {Path(edition["file"]).name: edition["sha256"] for edition in editions}
    manifests = []
    for path in sorted(DOWNLOADS.glob("*/*/manifest.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        source = manifest.get("source_tei")
        stem = Path(source).stem if source else ""
        author, _, rest = stem.partition("_")
        work, _, language = rest.rpartition("_")
        expected_url = f"https://bookstacks.org/{LANGUAGE_ROUTE.get(language, language)}/authors/{author}/{work}"
        files = manifest.get("files", [])
        pdf_checks = []
        for item in files:
            pdf = path.parent / item["name"]
            pdf_checks.append(pdf.exists() and sha256(pdf) == item.get("sha256"))
        manifests.append({
            "manifest": path.relative_to(ROOT).as_posix(),
            "source_tei": source,
            "source_tei_exists": source in tei_hashes,
            "records_source_tei_hash": any(key in manifest for key in ("source_tei_sha256", "source_sha256", "tei_sha256")),
            "canonical_url_matches_route": manifest.get("canonical_url") == expected_url,
            "author_string": manifest.get("author"),
            "pdf_hashes_match": all(pdf_checks) if pdf_checks else None,
        })
    manifest_keys = Counter(key for path in DOWNLOADS.glob("*/*/manifest.json") for key in json.loads(path.read_text(encoding="utf-8")))
    tei_beside_pdfs = sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "tei").glob("*/*.pdf"))
    editions_with_export = {m["source_tei"] for m in manifests}

    portraits = sorted(path.name for path in PORTRAITS.glob("*.png"))
    referenced_portraits = {profile.get("portrait") for profile in profiles.values()}
    config = ASTRO_CONFIG.read_text(encoding="utf-8")

    result = {
        "generated_from": inventory["generated_from"],
        "summary": {
            "editions": len(editions),
            "works": len(works),
            "works_with_several_editions": sum(1 for items in works.values() if len(items) > 1),
            "work_titles_in_code": len(work_titles),
            "works_titled_by_slug_fallback": sum(1 for record in work_records if record["title_source"] == "slug fallback"),
            "work_titles_without_work": sorted(set(work_titles) - work_slugs),
            "author_profiles": len(profiles),
            "authors_with_several_header_forms": sum(1 for record in authors.values() if len(record["header_author_forms"]) > 1),
            "language_codes_in_code": language_data,
            "language_declaration_mismatches": len(language_mismatches),
            "export_manifests": len(manifests),
            "editions_without_export_manifest": len(editions) - len(editions_with_export),
            "manifests_recording_source_tei_hash": sum(1 for m in manifests if m["records_source_tei_hash"]),
            "manifests_with_canonical_url_mismatch": sum(1 for m in manifests if not m["canonical_url_matches_route"]),
            "manifests_with_pdf_hash_mismatch": sum(1 for m in manifests if m["pdf_hashes_match"] is False),
            "manifest_keys": dict(sorted(manifest_keys.items())),
            "pdfs_beside_tei": len(tei_beside_pdfs),
            "portrait_files": len(portraits),
            "portraits_referenced_by_profiles": len(referenced_portraits & set(portraits)),
            "route_redirects_in_astro_config": len(re.findall(r"^\s+'/authors/[^']+':", config, re.M)),
        },
        "code_held_editorial_rules": {
            "reading_kind_priority": ts_list(library, "READING_KIND_PRIORITY"),
            "supplementary_kinds": ts_list(library, "SUPPLEMENTARY_KINDS"),
            "wrapper_kinds": ts_list(library, "WRAPPER_KINDS"),
            "render_time_repairs": sorted(set(re.findall(r"function (repair\w+)", library))),
        },
        "authors": authors,
        "works": work_records,
        "language_declaration_mismatches": language_mismatches,
        "manifests": manifests,
        "unreferenced_portraits": sorted(set(portraits) - referenced_portraits),
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
