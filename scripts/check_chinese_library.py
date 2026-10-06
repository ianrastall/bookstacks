"""Check the Chinese corpus and every local link in its built site pages."""

from pathlib import Path
from urllib.parse import unquote, urlsplit

from lxml import etree, html

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
TEI = {"t": "http://www.tei-c.org/ns/1.0"}
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
BOOKS = [
    ("lu-xun", "call-to-arms", "呐喊", "story", 14, 15),
    ("wu-chengen", "journey-to-the-west", "西游记", "chapter", 100, 100),
    ("laozi", "tao-te-ching", "道德经", "chapter", 81, 81),
]


def target_file(url: str) -> Path:
    path = DIST / unquote(urlsplit(url).path).lstrip("/")
    if path.is_file():
        return path
    if path.with_suffix(".html").is_file():
        return path.with_suffix(".html")
    return path / "index.html"


def main() -> None:
    errors = []
    for author, work, title, kind, divisions, units in BOOKS:
        doc = etree.parse(str(ROOT / "tei" / author / f"{author}_{work}_zho.xml"))
        text = doc.find("t:text", TEI)
        assert text is not None and text.get(XML_LANG) == "zh-Hans"
        sections = doc.findall(f"t:text//t:div[@type='{kind}']", TEI)
        assert len(sections) == divisions, (work, len(sections))
        assert [int(section.get("n")) for section in sections] == list(range(1, divisions + 1))
        assert doc.find("t:teiHeader/t:fileDesc/t:titleStmt/t:title", TEI).text == title
        assert all(section.findall(".//t:p", TEI) for section in sections)
        if work == "call-to-arms":
            assert len(doc.findall("t:text/t:front/t:div[@type='preface']", TEI)) == 1
            assert len(doc.findall("t:text//t:div[@type='subsection']", TEI)) == 26
        index = target_file(f"/zh-Hans/authors/{author}/{work}")
        assert index.is_file(), index
        page = html.parse(str(index))
        reader_links = page.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," toc-tree ")]//a/@href')
        assert len(reader_links) == units, (work, len(reader_links))
        assert page.xpath('//aside[@class="edition-source-note"]//a/@href')
        assert target_file(f"/tei/{author}/{author}_{work}_zho.xml").is_file()
        legacy = html.parse(str(target_file(f"/authors/{author}")))
        refresh = legacy.xpath('//meta[translate(@http-equiv,"REFSH","refsh")="refresh"]/@content')
        assert any(f"/zh-Hans/authors/{author}" in value for value in refresh), (author, refresh)

    pages = [DIST / "zh-Hans.html", *(path for path in (DIST / "zh-Hans").rglob("*.html") if path != DIST / "zh-Hans/index.html")]
    assert len(pages) == 204, len(pages)
    alias = DIST / "zh-Hans/index.html"
    if alias.exists():
        assert alias.read_bytes() == (DIST / "zh-Hans.html").read_bytes()
    homepage = html.parse(str(DIST / "index.html"))
    assert homepage.xpath('//a[@href="/zh-Hans"]')
    for path in pages:
        assert path.is_file(), path
        page = html.parse(str(path))
        assert page.getroot().get("lang") == "zh-Hans", path
        assert page.xpath('//a[starts-with(@href,"/zh-Hans")]'), path
        for href in page.xpath('//a/@href | //img/@src | //script/@src | //link/@href'):
            if href.startswith("/") and not href.startswith("//"):
                target = target_file(href)
                if not target.is_file():
                    errors.append(f"{path.relative_to(DIST)} -> {href}")
    assert not errors, "Broken local links:\n" + "\n".join(errors)
    print("Verified 3 complete Chinese books, 196 reading units, and all local links on 204 Chinese pages.")


if __name__ == "__main__":
    main()
