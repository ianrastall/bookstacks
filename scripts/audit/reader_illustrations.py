"""Check sidebar illustration coverage in an Astro production build."""

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path


ART = re.compile(
    rb'<figure\b[^>]*class="reader-illustration (tei-engraving|reader-photo)"[^>]*>'
    rb'\s*<img\b[^>]*\bsrc="([^"]+)"'
)
SKETCH = b"tei-engraving"
PHOTO = b"reader-photo"


def audit(root: Path) -> int:
    editions = defaultdict(list)
    for html in root.glob("*/authors/*/*/**/*.html"):
        contents = html.read_bytes()
        if b'id="reader-online"' in contents:
            route = html.relative_to(root).with_suffix("")
            editions[route.parts[:4]].append((route.as_posix(), ART.findall(contents)))

    if not editions:
        print(f"No built reading pages found in {root}")
        return 1

    problems = []
    checked = set()
    paired_pages = sketch_only_pages = 0
    for edition, pages in sorted(editions.items()):
        totals = Counter(style for _, images in pages for style, _ in images)
        if not totals:
            continue

        paired = bool(totals[PHOTO])
        print(f"{'/'.join(edition)}: {len(pages)} pages, "
              f"{totals[SKETCH]} sketches, {totals[PHOTO]} photos")
        for route, images in pages:
            sources = Counter(style for style, _ in images)
            if paired:
                if sources == {SKETCH: 1, PHOTO: 1} and len({src for _, src in images}) == 2:
                    paired_pages += 1
                else:
                    problems.append(f"{route}: expected two distinct images, one of each style")
            elif sources[SKETCH] == 1:
                sketch_only_pages += 1

            for _, src in images:
                if src in checked:
                    continue
                checked.add(src)
                url = src.decode("utf-8")
                relative = Path(url.removeprefix("/"))
                file = root / relative
                if not url.startswith("/tei/") or ".." in relative.parts or not file.is_file() or not file.stat().st_size:
                    problems.append(f"{route}: missing reader image {url}")

    print(f"\nChecked {sum(map(len, editions.values()))} reading pages in {len(editions)} editions.")
    print(f"{paired_pages} paired pages, {sketch_only_pages} sketch-only pages, {len(checked)} image URLs.")
    for problem in problems:
        print(problem)
    return int(bool(problems))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", nargs="?", type=Path, default=Path("dist"))
    raise SystemExit(audit(parser.parse_args().build))
