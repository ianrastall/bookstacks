"""Build three complete Simplified Chinese originals from recorded HTML sources.

Install requirements-chinese.txt, then run from the repository root. Cached HTML
is reused; --download fetches missing sources at the recorded Wikisource revisions.
Content fingerprints prevent upstream transcription edits from silently changing
an edition. --record-sources is an explicit curator operation after source review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from lxml import etree, html
from opencc import OpenCC

TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI}
ROOT = Path(__file__).resolve().parent.parent
CONVERTER = OpenCC("t2s")
# Historical glyph forms in the scanned Lu Xun printings; wording is preserved.
GLYPHS = str.maketrans({"靑": "青", "眞": "真", "硏": "研", "卽": "即", "吿": "告", "鄕": "乡"})
HAN = r"\u2e80-\u9fff\uf900-\ufaff\U00020000-\U0002ffff"
STORIES = [
    ("狂人日記", "madmans-diary"), ("孔乙己", "kong-yiji"),
    ("藥", "medicine"), ("明天", "tomorrow"),
    ("一件小事", "a-small-incident"), ("頭髮的故事", "the-story-of-hair"),
    ("風波", "a-storm-in-a-teacup"), ("故鄉", "hometown"),
    ("阿Ｑ正傳", "the-true-story-of-ah-q"), ("端午節", "dragon-boat-festival"),
    ("白光", "the-white-light"), ("兔和貓", "rabbits-and-cats"),
    ("鴨的喜劇", "a-comedy-of-ducks"), ("社戲", "village-opera"),
]
BOOKS = {
    "call-to-arms": ("lu-xun", "呐喊", "鲁迅"),
    "journey-to-the-west": ("wu-chengen", "西游记", "吴承恩（传统归属）"),
    "tao-te-ching": ("laozi", "道德经", "老子（传统归属）"),
}
SOURCE_NOTES = {
    "call-to-arms": "收录自序及十四篇小说。以维基文库所录《鲁迅全集》第一卷（1948年）为主要底本；《鸭的喜剧》采用《妇女杂志》第八卷第十二号（1922年）的初刊文本。保留各篇原文与内部标题，繁体字转换为简体字。",
    "journey-to-the-west": "收录一百回中文原文，传统上归于吴承恩。底本为 Project Gutenberg 第23962号电子文本；该电子版本未注明具体印刷底本。保留回目、段落及诗文换行，繁体字转换为简体字。",
    "tao-te-ching": "收录八十一章中文原文，传统上归于老子。底本为 Project Gutenberg 第7337号电子文本，按道经、德经编排；该电子版本未注明具体印刷底本。保留所选文本的字句与章次，繁体字转换为简体字。",
}


def compact(value: str) -> str:
    value = re.sub(r"[\u200b\ufeff]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return re.sub(rf"(?<=[{HAN}]) +| +(?=[{HAN}])", "", value)


def simplified(value: str) -> str:
    return CONVERTER.convert(value.translate(GLYPHS))


def node(name: str, text: str | None = None, **attrs: str) -> etree._Element:
    el = etree.Element(f"{{{TEI}}}{name}")
    for key, value in attrs.items():
        el.set(f"{{{XML}}}{key[4:]}" if key.startswith("xml_") else key, value)
    if text is not None:
        el.text = text
    return el


def has_class(el: etree._Element, name: str) -> bool:
    return name in el.get("class", "").split()


def source_root(data: bytes, provider: str) -> etree._Element:
    doc = html.fromstring(data.decode("utf-8-sig"))
    if provider == "wikisource":
        matches = doc.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " prp-pages-output ")]')
        if len(matches) != 1:
            raise ValueError("Expected one scan-backed Wikisource text container")
        root = matches[0]
        for el in list(root.iter()):
            if not isinstance(el.tag, str):
                continue
            if any(has_class(el, cls) for cls in ("pagenum", "mw-editsection", "ws-noexport")):
                el.drop_tree()
    else:
        root = doc.find("body")
        if root is None:
            raise ValueError("Gutenberg HTML has no body")
        for el in list(root):
            if el.get("id") in {"pg-header", "pg-footer"}:
                root.remove(el)
    for el in list(root.iter()):
        if not isinstance(el.tag, str) or el.tag in {"script", "style"}:
            if el.getparent() is not None:
                el.getparent().remove(el)
    return root


def signature(root: etree._Element) -> str:
    # Includes element structure and significant inline formatting, excludes skin.
    blocks = []
    for el in root.iter():
        if el.tag in {"p", "dd", "h1", "h2", "h3", "h4", "h5", "h6", "br", "hr", "i", "em", "b", "strong", "span"}:
            text = compact(el.text_content())
            if text or el.tag in {"br", "hr"}:
                blocks.append([el.tag, el.get("style", ""), text])
    return hashlib.sha256(json.dumps(blocks, ensure_ascii=False).encode("utf-8")).hexdigest()


def read_source(entry: dict, args: argparse.Namespace) -> etree._Element:
    path = args.cache_dir / entry["cache"]
    if not path.exists():
        if not args.download:
            raise FileNotFoundError(f"{path}: run with --download or supply the reviewed cached HTML")
        url = entry["url"]
        if entry.get("revision"):
            url += "?oldid=" + str(entry["revision"])
        request = urllib.request.Request(url, headers={"User-Agent": "Bookstacks/1.0 (public-domain text preparation)"})
        data = urllib.request.urlopen(request, timeout=45).read()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    data = path.read_bytes()
    root = source_root(data, entry["provider"])
    fingerprint = signature(root)
    if args.record_sources:
        entry["content_sha256"] = fingerprint
        revision = re.search(rb'"wgRevisionId":(\d+)', data)
        if revision:
            entry["revision"] = int(revision[1])
    elif fingerprint != entry.get("content_sha256"):
        raise ValueError(f"Source content changed: {entry['key']}; review before updating its fingerprint")
    return root


def append_text(target: etree._Element, text: str | None) -> None:
    if text:
        if len(target):
            target[-1].tail = (target[-1].tail or "") + text
        else:
            target.text = (target.text or "") + text


def inline(source: etree._Element, target: etree._Element) -> None:
    append_text(target, source.text)
    for child in source:
        if not isinstance(child.tag, str):
            append_text(target, child.tail)
            continue
        if child.tag == "br":
            target.append(node("lb"))
        else:
            rend = None
            if child.tag in {"i", "em"}:
                rend = "italic"
            elif child.tag in {"b", "strong"}:
                rend = "bold"
            elif "text-decoration: underline" in child.get("style", ""):
                rend = "underline"
            if rend:
                converted = node("hi", rend=rend)
                target.append(converted)
                inline(child, converted)
            else:
                inline(child, target)
        append_text(target, child.tail)


def normalize_block(el: etree._Element) -> None:
    # Reflow the source's hard-wrapped Chinese without inserting word spaces.
    for part in el.iter():
        if part.text:
            part.text = simplified(compact(part.text))
        if part.tail:
            part.tail = simplified(compact(part.tail))


def add_paragraph(source: etree._Element, parent: etree._Element) -> None:
    if not compact(source.text_content()):
        return
    p = node("p")
    inline(source, p)
    normalize_block(p)
    parent.append(p)


def iter_blocks(root: etree._Element):
    for child in root:
        if not isinstance(child.tag, str):
            continue
        if child.tag in {"p", "dd", "h1", "h2", "h3", "h4", "h5", "h6", "hr"}:
            yield child
        else:
            yield from iter_blocks(child)


def header(work: str, entries: list[dict], build_date: str) -> etree._Element:
    author_slug, title, author = BOOKS[work]
    root = etree.Element(f"{{{TEI}}}TEI", nsmap={None: TEI})
    root.set(f"{{{XML}}}id", f"{author_slug}_{work}_zho")
    hdr = node("teiHeader", xml_lang="en")
    root.append(hdr)
    desc = node("fileDesc")
    hdr.append(desc)
    titles = node("titleStmt")
    desc.append(titles)
    titles.append(node("title", title, type="main", xml_lang="zh-Hans"))
    titles.append(node("author", author, xml_lang="zh-Hans"))
    for ident, responsibility, name in [
        ("source-transcription", "electronic transcription", "Chinese Wikisource contributors" if work == "call-to-arms" else "Project Gutenberg contributors"),
        ("bookstacks-encoding", "TEI encoding and Simplified Chinese character conversion", "Bookstacks project"),
    ]:
        resp = node("respStmt", xml_id=ident)
        resp.extend([node("resp", responsibility), node("name", name)])
        titles.append(resp)
    edition = node("editionStmt")
    edition.append(node("edition", "Bookstacks Simplified Chinese original-language edition", n="1.0"))
    desc.append(edition)
    publication = node("publicationStmt")
    publication.extend([node("publisher", "Bookstacks project"), node("date", build_date, when=build_date)])
    availability = node("availability", status="free")
    availability.append(node("p", "The original literary work is public domain. Source transcription credits and provenance are retained in this header; this edition contains no modern translation or modern editorial annotations."))
    publication.append(availability)
    desc.append(publication)
    notes = node("notesStmt")
    notes.append(node("note", SOURCE_NOTES[work], type="source-description", xml_lang="zh-Hans"))
    desc.append(notes)
    sources = node("sourceDesc")
    if work == "call-to-arms":
        bibl = node("bibl")
        bibl.extend([node("title", "鲁迅全集，第一卷", xml_lang="zh-Hans"), node("publisher", "鲁迅全集出版社", xml_lang="zh-Hans"), node("date", "1948", when="1948"), node("ref", "1948年版扫描本", type="source", target="https://zh.wikisource.org/wiki/Index:魯迅全集01_(1948).pdf", xml_lang="zh-Hans")])
        sources.append(bibl)
    for entry in entries:
        bibl = node("bibl")
        bibl.append(node("ref", simplified(entry["title"]), type="source" if entry["provider"] == "gutenberg" or entry["key"] in {"preface", "a-comedy-of-ducks"} else "transcription", target=entry["url"], xml_lang="zh-Hans"))
        if entry.get("revision"):
            bibl.append(node("idno", str(entry["revision"]), type="Wikisource-revision"))
        bibl.append(node("idno", entry["content_sha256"], type="source-content-sha256"))
        sources.append(bibl)
    desc.append(sources)
    encoding = node("encodingDesc")
    project = node("projectDesc")
    project.append(node("p", "Source paragraphs, internal headings, and explicit line breaks are retained. Website navigation and source boilerplate are omitted. Dialogue remains unattributed prose. Chinese character forms are converted with opencc-python-reimplemented 0.1.7, t2s; six historical glyph variants are normalized before conversion. This is script conversion, not a modern-language paraphrase."))
    encoding.append(project)
    hdr.append(encoding)
    profile = node("profileDesc")
    usage = node("langUsage")
    usage.append(node("language", "Simplified Chinese", ident="zh-Hans"))
    profile.append(usage)
    hdr.append(profile)
    revision = node("revisionDesc")
    revision.append(node("change", "Encoded the reviewed source texts as a complete Simplified Chinese TEI edition.", when=build_date, who="#bookstacks-encoding"))
    hdr.append(revision)
    text = node("text", xml_lang="zh-Hans")
    root.append(text)
    return root


def build_lu_xun(roots: dict[str, etree._Element], text: etree._Element) -> None:
    front, body = node("front"), node("body")
    text.extend([front, body])
    preface = node("div", type="preface", n="1")
    preface.append(node("head", "自序"))
    front.append(preface)
    for block in iter_blocks(roots["preface"]):
        if block.tag in {"p", "dd"}:
            add_paragraph(block, preface)
    for index, (title, key) in enumerate(STORIES, 1):
        story = node("div", type="story", n=str(index))
        story.append(node("head", simplified(title)))
        body.append(story)
        current = story
        intro = None
        headings = 0
        for block in iter_blocks(roots[key]):
            label = compact(block.text_content())
            if block.tag.startswith("h") and block.tag != "hr":
                # Keep subheadings inside a single story reading page.
                current = node("div", type="subsection", n=str(headings + 1))
                current.append(node("head", simplified(label)))
                story.append(current)
                headings += 1
            elif block.tag in {"p", "dd"} and label:
                if current is story and key in {"madmans-diary", "the-true-story-of-ah-q"}:
                    if intro is None:
                        intro = node("div", type="introduction", n="0")
                        story.append(intro)
                    add_paragraph(block, intro)
                else:
                    add_paragraph(block, current)
            elif block.tag == "hr":
                current.append(node("milestone", unit="separator"))
        expected = {"madmans-diary": 13, "medicine": 4, "the-true-story-of-ah-q": 9}.get(key, 0)
        if headings != expected:
            raise ValueError(f"{key}: expected {expected} internal headings, got {headings}")
        if len("".join(story.itertext())) < 500:
            raise ValueError(f"Suspiciously short story: {key}")


def chinese_number(value: str) -> int:
    value = value.replace("○", "零").replace("〇", "零").replace("Ｏ", "零")
    digits = {char: n for n, char in enumerate("零一二三四五六七八九")}
    if "百" in value:
        left, right = value.split("百", 1)
        return digits.get(left, 1) * 100 + (chinese_number(right) if right else 0)
    if "十" in value:
        left, right = value.split("十", 1)
        return digits.get(left, 1) * 10 + digits.get(right, 0)
    return int("".join(str(digits[char]) for char in value))


def build_gutenberg(work: str, source: etree._Element, text: etree._Element) -> None:
    body = node("body")
    text.append(body)
    parent = body
    current = None
    numbers = []
    chapter_pattern = re.compile(r"^第([一二三四五六七八九十百零〇○Ｏ]+)(回|章)(.*)$")
    for block in iter_blocks(source):
        label = compact(block.text_content())
        match = chapter_pattern.match(label)
        if match:
            number = chinese_number(match[1])
            numbers.append(number)
            current = node("div", type="chapter", n=str(number))
            current.append(node("head", simplified(label)))
            parent.append(current)
        elif work == "tao-te-ching" and label in {"老子道經", "老子德經"}:
            parent = node("div", type="part", n="1" if "道經" in label else "2")
            parent.append(node("head", simplified(label)))
            body.append(parent)
            current = None
        elif current is not None and block.tag in {"p", "h1", "h2", "h3", "h4", "h5", "h6"}:
            add_paragraph(block, current)
    expected = 100 if work == "journey-to-the-west" else 81
    if numbers != list(range(1, expected + 1)):
        raise ValueError(f"{work}: chapters are missing, duplicated, or out of order")
    for chapter in body.findall(".//tei:div[@type='chapter']", NS):
        if not chapter.findall("tei:p", NS):
            raise ValueError("Empty chapter")


def assign_ids(root: etree._Element, work: str) -> None:
    for index, el in enumerate(root.findall("tei:text//*", NS), 1):
        if etree.QName(el).localname in {"div", "p", "lg", "l"}:
            el.set(f"{{{XML}}}id", f"{work}-{etree.QName(el).localname}-{index:06}")


def verify_preservation(work: str, roots: dict[str, etree._Element], root: etree._Element) -> None:
    # Every literary source block must survive script conversion without loss.
    source_blocks = []
    for source in roots.values():
        started = work == "call-to-arms"
        for block in iter_blocks(source):
            label = compact(block.text_content())
            if work != "call-to-arms" and re.match(r"^第[一二三四五六七八九十百零〇○Ｏ]+(?:回|章)", label):
                started = True
                continue
            if label in {"老子道經", "老子德經"}:
                continue
            if started and block.tag in {"p", "dd", "h1", "h2", "h3", "h4", "h5", "h6"} and label:
                # Clone conversion to include the same inline glyph boundaries.
                p = node("p")
                inline(block, p)
                normalize_block(p)
                source_blocks.append(re.sub(r"\s+", "", "".join(p.itertext())))
    output_blocks = [re.sub(r"\s+", "", "".join(p.itertext())) for p in root.findall("tei:text//tei:p", NS)]
    if work == "call-to-arms":
        output_blocks += [re.sub(r"\s+", "", "".join(h.itertext())) for h in root.findall("tei:text//tei:div[@type='subsection']/tei:head", NS)]
    if sorted(source_blocks) != sorted(output_blocks):
        raise ValueError(f"{work}: literary block preservation check failed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "assets/source-chinese")
    parser.add_argument("--manifest", type=Path, default=ROOT / "tei/chinese-sources.json")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--record-sources", action="store_true")
    parser.add_argument("--date", default="2026-10-05")
    args = parser.parse_args()
    entries = json.loads(args.manifest.read_text(encoding="utf-8"))
    roots = {entry["key"]: read_source(entry, args) for entry in entries}
    if args.record_sources:
        args.manifest.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    schema = etree.RelaxNG(etree.parse(str(ROOT / "tei/tei_all.rng")))
    for work, (author, _, _) in BOOKS.items():
        selected = [entry for entry in entries if entry["work"] == work]
        work_roots = {entry["key"]: roots[entry["key"]] for entry in selected}
        root = header(work, selected, args.date)
        text = root.find("tei:text", NS)
        if work == "call-to-arms":
            build_lu_xun(work_roots, text)
        else:
            build_gutenberg(work, next(iter(work_roots.values())), text)
        assign_ids(root, work)
        verify_preservation(work, work_roots, root)
        schema.assertValid(root)
        target = ROOT / "tei" / author / f"{author}_{work}_zho.xml"
        target.parent.mkdir(parents=True, exist_ok=True)
        root.addprevious(etree.ProcessingInstruction("xml-model", 'href="../tei_all.rng" schematypens="http://relaxng.org/ns/structure/1.0"'))
        etree.ElementTree(root).write(str(target), encoding="UTF-8", xml_declaration=True, pretty_print=True)
        print(f"Wrote {target.relative_to(ROOT)}: {len(root.findall('tei:text//tei:p', NS))} paragraphs")


if __name__ == "__main__":
    main()
