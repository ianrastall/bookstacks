#!/usr/bin/env python3
"""Stage only newly generated publication files into stable GitHub Release groups."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LANGUAGE_TAGS = {"fra": "publications-fr", "grc": "publications-grc", "rus": "publications-ru"}


def release_tag(relative: Path) -> str:
    if relative.parts[0] == "corpus":
        return "publications-corpus"
    language_source = relative.parent.name if relative.name == "manifest.json" else relative.name
    match = re.search(r"_(eng|fra|grc|rus)(?:\.|$)", language_source)
    if not match:
        raise ValueError(f"Cannot determine publication language from {relative}")
    language = match.group(1)
    if language == "eng":
        author_slug = relative.parts[0]
        return f"publications-en-{'a-m' if author_slug[0].lower() < 'n' else 'n-z'}"
    return LANGUAGE_TAGS[language]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    source = arguments.input.resolve()
    target = arguments.output.resolve()
    if not source.is_relative_to(ROOT) or not target.is_relative_to(ROOT) or target.name != "release-assets":
        parser.error("Input and output must be workspace paths, and output must be named release-assets.")
    changed_manifest = source / "_changed-assets.json"
    if not changed_manifest.is_file():
        parser.error(f"Missing exporter change manifest: {changed_manifest}")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    changed = [Path(value) for value in json.loads(changed_manifest.read_text(encoding="utf-8"))]
    counts: Counter[str] = Counter()
    for relative in changed:
        asset = (source / relative).resolve()
        if not asset.is_file() or not asset.is_relative_to(source):
            raise ValueError(f"Invalid changed asset: {relative}")
        tag = release_tag(relative)
        asset_name = f"{relative.parent.name}.manifest.json" if asset.name == "manifest.json" else asset.name
        destination = target / tag / asset_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise ValueError(f"Release asset name collision: {destination.name}")
        shutil.copy2(asset, destination)
        counts[tag] += 1

    for tag, count in sorted(counts.items()):
        if count > 1000:
            raise ValueError(f"{tag} exceeds GitHub's 1,000-asset release limit: {count}")
        print(f"{tag}: {count} changed asset(s)")
    if not counts:
        print("No changed release assets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
