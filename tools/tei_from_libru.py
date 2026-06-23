#!/usr/bin/env python3
"""Convert a Lib.ru (az.lib.ru) HTML volume of a Russian work into TEI chapter
blocks for Bookstacks.

Each emitted chapter is a single Russian-original version:

    <div type="chapter" n="G">
      <head>Volume {V}, Part {P}, Chapter {R}</head>
      <div type="version" xml:lang="ru" subtype="original">
        <p>...</p>
      </div>
    </div>

Tolstoy's numbered footnotes (the "Примечания" block at the end) are inlined as
<note>...</note> right where their superscript marker stood. French is NOT
wrapped in <foreign> here -- add that, and the English <seg type="origfr"> flags,
by hand during the translation pass (see tei-source/TRANSLATION-STYLE.md).

Usage:
    python tools/tei_from_libru.py --in tolstoy-wp-rus.html \
        --volume I --skip 1 --start 2 > chapters.xml

Then splice the output into the book's TEI file before </body>.
"""
import argparse, html, re, sys

PART_NAMES = {
    "ПЕРВАЯ": "Part One", "ВТОРАЯ": "Part Two", "ТРЕТЬЯ": "Part Three",
    "ЧЕТВЕРТАЯ": "Part Four", "ПЯТАЯ": "Part Five",
}
ROMAN = re.compile(r"^[IVXLCDM]+$")
HEAD_RE = re.compile(r'<h4><div align="center"[^>]*>\s*<p[^>]*>\s*<b>(.*?)</b>', re.S)

# private-use sentinels survive tag-stripping and XML-escaping
NOTE_A, NOTE_B = chr(0xE000), chr(0xE001)
EMPH_A, EMPH_B = chr(0xE002), chr(0xE003)


def xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def clean_para(raw: str, notes: dict) -> str:
    """Turn one <dd> fragment into a TEI <p> (empty string if nothing left)."""
    s = re.sub(r"<sup><u>\s*(\d+)\s*</u></sup>",
               lambda m: f"{NOTE_A}{m.group(1)}{NOTE_B}", raw)
    s = s.replace("<i>", EMPH_A).replace("</i>", EMPH_B)
    s = re.sub(r"<[^>]+>", "", s)            # drop remaining tags
    s = html.unescape(s)                      # entities -> chars
    s = s.replace("\xa0", " ").replace("ò", "о")  # stray grave-о -> о
    s = re.sub(r"\s+", " ", s).strip()
    s = xml_escape(s)
    s = s.replace("--", "—")
    s = s.replace(EMPH_A, "<emph>").replace(EMPH_B, "</emph>")

    def note_sub(m):
        gloss = notes.get(m.group(1), "").strip()
        if not gloss:
            return ""
        gloss = xml_escape(html.unescape(gloss)).replace("--", "—")
        return f"<note>{gloss}</note>"

    s = re.sub(f"{NOTE_A}(\\d+){NOTE_B}", note_sub, s)
    return f"<p>{s}</p>" if s else ""


def parse_notes(text: str) -> dict:
    m = re.search(r"Примечания", text)
    if not m:
        return {}
    block = html.unescape(re.sub(r"<[^>]+>", "", text[m.start():]))
    notes = {}
    for line in block.splitlines():
        mm = re.match(r"\s*(\d+)\s+(.*\S)", line)
        if mm:
            notes[mm.group(1)] = mm.group(2)
    return notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--volume", default="I")
    ap.add_argument("--start", type=int, default=1, help="global n of first emitted chapter")
    ap.add_argument("--skip", type=int, default=0, help="skip this many leading chapters")
    args = ap.parse_args()

    text = open(args.inp, encoding="windows-1251").read()
    notes = parse_notes(text)
    body = text[:re.search(r"Примечания", text).start()] if "Примечания" in text else text

    token = re.compile(r'(<h4><div align="center".*?</h4>)|(<dd>.*?)(?=<dd>|<h4>|\Z)', re.S)
    part = None
    chapters = []
    cur = None
    for m in token.finditer(body):
        if m.group(1):
            hm = HEAD_RE.search(m.group(1))
            label = html.unescape(re.sub(r"<[^>]+>", "", hm.group(1))).strip() if hm else ""
            up = label.upper().rstrip(".")
            if "ЧАСТ" in up:
                part = PART_NAMES.get(up.replace("ЧАСТЬ", "").strip(), label)
                cur = None
            elif "ТОМ" in up:
                cur = None
            elif ROMAN.match(up):
                cur = (part, up, [])
                chapters.append(cur)
            else:
                cur = None
        elif m.group(2) is not None and cur is not None:
            cur[2].append(m.group(2))

    chapters = chapters[args.skip:]
    n = args.start
    out = []
    for part, roman, paras in chapters:
        head = f"Volume {args.volume}"
        if part:
            head += f", {part}"
        head += f", Chapter {roman}"
        ps = [clean_para(p, notes) for p in paras]
        ps = "\n\t\t\t\t\t".join(p for p in ps if p)
        out.append(
            f'\t\t\t<div type="chapter" n="{n}">\n'
            f"\t\t\t\t<head>{xml_escape(head)}</head>\n"
            f'\t\t\t\t<div type="version" xml:lang="ru" subtype="original">\n'
            f"\t\t\t\t\t{ps}\n"
            f"\t\t\t\t</div>\n"
            f"\t\t\t</div>"
        )
        n += 1
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(out))
    sys.stderr.write(f"emitted {len(out)} chapters (n {args.start}..{n - 1})\n")


if __name__ == "__main__":
    main()
