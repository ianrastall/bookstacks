"""Import pinned Standard Ebooks EPUBs into Bookstacks TEI.

Explicit offline command; site deployment and PDF publication never run it.
Sources are listed in tei/standard-ebooks-sources.json and cached in the
ignored assets/source-standard-ebooks directory. Each EPUB must match its
recorded SHA-256 before it is converted.

    python tei/build_standard_ebooks.py [--download] [work-slug ...]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

from lxml import etree
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'tei/standard-ebooks-sources.json'
CACHE = ROOT / 'assets/source-standard-ebooks'
SCHEMA = ROOT / 'tei/tei_all.rng'
EDITION_DATE = '2026-11-22'

TEI = 'http://www.tei-c.org/ns/1.0'
XML = 'http://www.w3.org/XML/1998/namespace'
XHTML = 'http://www.w3.org/1999/xhtml'
EPUB = 'http://www.idpf.org/2007/ops'
OPF = {'o': 'http://www.idpf.org/2007/opf', 'dc': 'http://purl.org/dc/elements/1.1/'}

# Standard Ebooks production pages that are not part of the literary text.
SKIPPED = {'titlepage', 'imprint', 'halftitlepage', 'toc', 'loi', 'colophon',
           'copyright-page', 'endnotes'}
# Structural divisions: Standard Ebooks semantic type -> TEI division type.
DIVISIONS = {'chapter': 'chapter', 'part': 'part', 'se:short-story': 'story',
             'prologue': 'prologue', 'epilogue': 'epilogue', 'dedication': 'dedication',
             'preface': 'preface', 'foreword': 'foreword', 'afterword': 'afterword',
             'appendix': 'appendix'}
# Untitled divisions receive the conventional English label, as in other Bookstacks editions.
DEFAULT_HEADS = {'dedication': 'Dedication', 'prologue': 'Prologue', 'epilogue': 'Epilogue',
                 'preface': 'Preface', 'foreword': 'Foreword', 'afterword': 'Afterword',
                 'appendix': 'Appendix'}
# Untitled front matter that belongs with the title page rather than a route of its own.
TITLE_PAGE_MATTER = {'introduction', 'epigraph'}
VERSE = {'z3998:verse', 'z3998:song', 'z3998:poem', 'z3998:hymn'}
RIGHT_ALIGNED = {'z3998:signature', 'z3998:sender', 'se:letter.dateline'}


def tei(name, text=None, **attrs):
    node = etree.Element(f'{{{TEI}}}{name}')
    for key, value in attrs.items():
        node.set({'xml_id': f'{{{XML}}}id', 'xml_lang': f'{{{XML}}}lang'}.get(key, key), value)
    if text is not None:
        node.text = text
    return node


def sub(parent, name, text=None, **attrs):
    node = tei(name, text, **attrs)
    parent.append(node)
    return node


def local(node):
    return etree.QName(node).localname if isinstance(node.tag, str) else ''


def types(node):
    return set((node.get(f'{{{EPUB}}}type') or '').split())


def norm(value):
    return ' '.join(value.split())


def squash(value):
    return re.sub(r'\s+', '', value)


def append_text(parent, value):
    if not value:
        return
    if len(parent):
        parent[-1].tail = (parent[-1].tail or '') + value
    else:
        parent.text = (parent.text or '') + value


def elements(node):
    return [child for child in node if isinstance(child.tag, str)]


class Book:
    def __init__(self, item):
        self.item = item
        path = CACHE / item['epub']
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise SystemExit(f'{item["epub"]}: source changed; review it before importing.')
        self.zip = zipfile.ZipFile(io.BytesIO(raw))
        self.opf = etree.fromstring(self.zip.read('epub/content.opf'))
        manifest = {node.get('id'): node.get('href') for node in self.opf.xpath('//o:manifest/o:item', namespaces=OPF)}
        self.spine = [manifest[node.get('idref')] for node in self.opf.xpath('//o:spine/o:itemref', namespaces=OPF)]
        self.notes = {}
        if 'text/endnotes.xhtml' in self.spine:
            doc = etree.fromstring(self.zip.read('epub/text/endnotes.xhtml'))
            self.notes = {li.get('id'): li for li in doc.iter(f'{{{XHTML}}}li') if li.get('id')}
        self.figures = []
        self.note_count = 0
        self.slug = f'{item["author"]}_{item["work"]}_eng'

    def meta(self, xpath):
        return [norm(value) for value in self.opf.xpath(xpath, namespaces=OPF)]

    # Inline content ---------------------------------------------------------
    def inline(self, source, target):
        append_text(target, source.text)
        for child in source:
            if not isinstance(child.tag, str):
                append_text(target, child.tail)
                continue
            name, kinds = local(child), types(child)
            lang = child.get(f'{{{XML}}}lang')
            if name == 'a' and 'noteref' in kinds:
                target.append(self.note(child))
            elif name == 'a' and 'backlink' in kinds:
                pass
            elif name == 'br':
                target.append(tei('lb'))
            else:
                out = None
                if name in {'i', 'em', 'cite'}:
                    out = tei('hi', rend='italic')
                elif name == 'b':
                    # Standard Ebooks renders <b> as small capitals.
                    out = tei('hi', rend='smallcaps')
                elif name == 'strong':
                    out = tei('hi', rend='bold')
                elif name in {'sup', 'sub'}:
                    out = tei('hi', rend=name)
                elif name == 'a' and child.get('href', '').startswith('http'):
                    out = tei('ref', target=child.get('href'))
                elif lang:
                    out = tei('foreign')
                if out is None:
                    # Semantic wrappers (abbr, span, time) carry no display change.
                    self.inline(child, target)
                else:
                    if lang:
                        out.set(f'{{{XML}}}lang', lang)
                    self.inline(child, out)
                    target.append(out)
            append_text(target, child.tail)

    def note(self, anchor):
        source = self.notes[anchor.get('href').rsplit('#', 1)[-1]]
        self.note_count += 1
        note = tei('note', type='authorial', place='foot', n=norm(''.join(anchor.itertext())),
                   xml_id=f'note-{self.note_count:03d}')
        paragraphs = [p for p in elements(source) if local(p) == 'p']
        if len(paragraphs) == 1:
            self.inline(paragraphs[0], note)
        else:
            for p in paragraphs:
                self.inline(p, sub(note, 'p'))
        for ref in note.iter(f'{{{TEI}}}ref'):
            if ref.get('target', '').endswith('noteref'):
                ref.getparent().remove(ref)
        return note

    # Block content -----------------------------------------------------------
    def blocks(self, source, target):
        for child in elements(source):
            self.block(child, target)

    def block(self, source, target):
        name, kinds = local(source), types(source)
        classes = set((source.get('class') or '').split())
        if name == 'p':
            if not norm(''.join(source.itertext())) and not len(source):
                return
            p = sub(target, 'p')
            rend = []
            if kinds & RIGHT_ALIGNED:
                rend.append('right')
            if 'continued' in classes:
                rend.append('noindent')
            if 'z3998:stage-direction' in kinds:
                rend.append('italic')
            if rend:
                p.set('rend', ' '.join(rend))
            self.inline(source, p)
        elif name == 'blockquote':
            self.quote(source, target)
        elif name in {'h2', 'h3', 'h4', 'h5', 'h6'}:
            p = sub(target, 'p', rend='subheading')
            self.inline(source, p)
        elif name == 'hgroup':
            for child in elements(source):
                p = sub(target, 'p', rend='subheading')
                self.inline(child, p)
        elif name == 'hr':
            sub(target, 'milestone', unit='section')
        elif name == 'figure':
            self.figure(source, target)
        elif name == 'table':
            self.table(source, target)
        elif name in {'ol', 'ul'}:
            listing = sub(target, 'list', type='ordered' if name == 'ol' else 'unordered')
            for li in elements(source):
                item = sub(listing, 'item')
                if any(local(c) in {'p', 'blockquote'} for c in elements(li)):
                    self.blocks(li, item)
                else:
                    self.inline(li, item)
        elif name == 'cite':
            self.inline(source, sub(target, 'bibl'))
        elif name in {'div', 'footer', 'header', 'section', 'article'}:
            self.blocks(source, target)
        else:
            raise ValueError(f'{self.slug}: unhandled block <{name}>')

    def quote(self, source, target):
        kinds = types(source)
        quote = sub(target, 'quote')
        if 'epigraph' in kinds:
            quote.set('type', 'epigraph')
        elif 'z3998:letter' in kinds:
            quote.set('type', 'letter')
        elif kinds & VERSE:
            quote.set('type', 'verse')
        if kinds & VERSE:
            stanzas = [c for c in elements(source) if local(c) == 'p']
            group = sub(quote, 'lg') if len(stanzas) > 1 else quote
            for child in elements(source):
                if local(child) == 'p':
                    self.stanza(child, group)
                else:
                    self.block(child, quote)
        else:
            self.blocks(source, quote)

    def stanza(self, source, target):
        lg = sub(target, 'lg', type='stanza') if target.tag == f'{{{TEI}}}lg' else sub(target, 'lg')
        lines = [c for c in elements(source) if local(c) == 'span']
        if not lines or norm(source.text or ''):
            # Prose-like stanza without line spans: keep its breaks as lines.
            line = sub(lg, 'l')
            self.inline(source, line)
            return
        for span in lines:
            indent = next((c[1:] for c in (span.get('class') or '').split() if re.fullmatch(r'i\d', c)), None)
            line = sub(lg, 'l', **({'rend': f'indent-{int(indent) * 2}'} if indent else {}))
            self.inline(span, line)
            line.tail = None
        for child in elements(source):
            if local(child) not in {'span', 'br'}:
                raise ValueError(f'{self.slug}: unexpected <{local(child)}> in verse')

    def figure(self, source, target):
        img = source.find(f'{{{XHTML}}}img')
        number = len(self.figures) + 1
        file = f'img/{self.item["work"]}-figure-{number}.png'
        src = img.get('src').replace('../', 'epub/')
        hidpi = src.replace('.png', '-2x.png')
        self.figures.append((hidpi if hidpi in self.zip.namelist() else src, file))
        figure = sub(target, 'figure')
        sub(figure, 'graphic', url=file, n=norm(img.get('alt') or ''))
        caption = source.find(f'{{{XHTML}}}figcaption')
        if caption is not None:
            self.inline(caption, sub(figure, 'p'))

    def table(self, source, target):
        table = sub(target, 'table')
        caption = source.find(f'{{{XHTML}}}caption')
        if caption is not None:
            self.inline(caption, sub(table, 'head'))
        for tr in source.iter(f'{{{XHTML}}}tr'):
            row = sub(table, 'row')
            for td in elements(tr):
                cell = sub(row, 'cell', role='label' if local(td) == 'th' else 'data')
                if td.get('colspan'):
                    cell.set('cols', td.get('colspan'))
                if any(local(c) in {'p', 'blockquote', 'table'} for c in elements(td)):
                    self.blocks(td, cell)
                else:
                    self.inline(td, cell)

    # Divisions -------------------------------------------------------------
    def heading(self, section):
        """Return (head element or None, leftover header blocks)."""
        header = next((c for c in elements(section) if local(c) == 'header'), None)
        holder = header if header is not None else section
        group = next((c for c in elements(holder) if local(c) in {'hgroup', 'h2', 'h3', 'h4'}), None)
        extra = [c for c in elements(header) if c is not group] if header is not None else []
        if group is None:
            return None, extra, header
        head = tei('head')
        parts = elements(group) if local(group) == 'hgroup' else [group]
        kind = DIVISIONS.get(next(iter(types(section) & DIVISIONS.keys()), ''), '')
        for index, part in enumerate(parts):
            if index:
                strip_trailing(head)
                append_text(head, '. ')
            if index == 0 and kind in {'chapter'} and re.fullmatch(r'[IVXLC]+', norm(''.join(part.itertext()))):
                append_text(head, 'Chapter ')
            self.inline(part, head)
        for node in head.iter():
            if node.text:
                node.text = re.sub(r'\s+', ' ', node.text)
            if node.tail:
                node.tail = re.sub(r'\s+', ' ', node.tail)
        head.text = (head.text or '').lstrip()
        return head, extra, (header if header is not None else group)

    def division(self, section, parent, registry):
        kinds = types(section)
        kind = DIVISIONS[next(iter(kinds & DIVISIONS.keys()))]
        ident = section.get('id')
        div = registry.get(ident)
        if div is None:
            div = sub(parent, 'div', type=kind, xml_id=ident)
            registry[ident] = div
            head, extra, skip = self.heading(section)
            if head is None and kind in DEFAULT_HEADS:
                head = tei('head', DEFAULT_HEADS[kind], type='supplied')
            if head is not None:
                div.append(head)
            for block in extra:
                self.block(block, div)
        else:
            skip = next((c for c in elements(section) if local(c) in {'header', 'hgroup', 'h2', 'h3'}), None)
        for child in elements(section):
            if child is skip:
                continue
            if local(child) in {'section', 'article'} and types(child) & DIVISIONS.keys():
                self.division(child, div, registry)
            else:
                self.block(child, div)

    def build(self):
        root = tei('TEI', xml_id=self.slug)
        root.append(self.header())
        text = sub(root, 'text', xml_lang='en')
        body = sub(text, 'body')
        registry = {}
        title_page = None
        for href in self.spine:
            doc = etree.fromstring(self.zip.read(f'epub/{href}'))
            body_source = doc.find(f'{{{XHTML}}}body')
            for section in elements(body_source):
                kinds = types(section)
                if kinds & SKIPPED or local(section) == 'nav':
                    continue
                if kinds & TITLE_PAGE_MATTER:
                    if title_page is None:
                        title_page = sub(body, 'div', type='title-page', xml_id='title-page')
                        sub(title_page, 'head', self.item_title(), type='supplied')
                    self.blocks(section, title_page)
                    continue
                if not kinds & DIVISIONS.keys():
                    raise ValueError(f'{self.slug}: unhandled section {kinds} in {href}')
                self.division(section, body, registry)
        for index, p in enumerate(text.iter(f'{{{TEI}}}p'), 1):
            if p.getparent().tag != f'{{{TEI}}}note':
                p.set(f'{{{XML}}}id', f'p-{index:05d}')
        for kind in ('chapter', 'story', 'part'):
            divs = [d for d in body.iter(f'{{{TEI}}}div') if d.get('type') == kind]
            for n, div in enumerate(divs, 1):
                div.set('n', str(n))
        counts = {kind: sum(1 for d in body.iter(f'{{{TEI}}}div') if d.get('type') == kind) for kind in self.item['units']}
        if counts != self.item['units']:
            raise ValueError(f'{self.slug}: expected {self.item["units"]}, found {counts}')
        self.verify(text)
        return etree.ElementTree(root)

    def item_title(self):
        return self.meta('//dc:title[@id="title"]/text()')[0]

    # Verification ----------------------------------------------------------
    def verify(self, text):
        """Every source word in the converted pages must survive conversion."""
        source = []
        for href in self.spine:
            doc = etree.fromstring(self.zip.read(f'epub/{href}'))
            for section in elements(doc.find(f'{{{XHTML}}}body')):
                if types(section) & SKIPPED or local(section) == 'nav':
                    continue
                clone = etree.fromstring(etree.tostring(section))
                for anchor in clone.iter(f'{{{XHTML}}}a'):
                    if 'noteref' in types(anchor):
                        anchor.text = ''
                source.append(''.join(clone.itertext()))
        clone = etree.fromstring(etree.tostring(text))
        for head in list(clone.iter(f'{{{TEI}}}head')):
            if head.get('type') == 'supplied':
                append_text_before(head)
                head.getparent().remove(head)
        for note in list(clone.iter(f'{{{TEI}}}note')):
            parent = note.getparent()
            append_text_before(note)
            parent.remove(note)
        produced = squash(''.join(clone.itertext()))
        expected = squash(''.join(source))
        # Bookstacks adds "Chapter" before bare chapter numerals and ". " between heading parts.
        produced = produced.replace('Chapter', '')
        expected = expected.replace('Chapter', '')
        produced = re.sub(r'\.', '', produced)
        expected = re.sub(r'\.', '', expected)
        if produced != expected:
            at = next((i for i, (a, b) in enumerate(zip(produced, expected)) if a != b), min(len(produced), len(expected)))
            raise ValueError(f'{self.slug}: text mismatch near …{expected[max(0, at - 60):at + 60]}… / …{produced[max(0, at - 60):at + 60]}…')
        expected_notes = []
        for li in self.notes.values():
            clone = etree.fromstring(etree.tostring(li))
            for anchor in list(clone.iter(f'{{{XHTML}}}a')):
                if 'backlink' in types(anchor):
                    append_text_before(anchor)
                    anchor.getparent().remove(anchor)
            expected_notes.append(''.join(clone.itertext()))
        produced_notes = ''.join(''.join(n.itertext()) for n in text.iter(f'{{{TEI}}}note'))
        if len(self.notes) != self.note_count or squash(''.join(expected_notes)) != squash(produced_notes):
            raise ValueError(f'{self.slug}: endnote mismatch')

    # Header ----------------------------------------------------------------
    def header(self):
        item = self.item
        title = self.item_title()
        subtitle = self.meta('//dc:title[@id="subtitle"]/text()')
        header = tei('teiHeader')
        desc = sub(header, 'fileDesc')
        stmt = sub(desc, 'titleStmt')
        sub(stmt, 'title', title, type='main')
        for value in subtitle:
            sub(stmt, 'title', value, type='sub')
        sub(stmt, 'author', item['authorName'])
        transcribers = self.meta('//dc:contributor[starts-with(@id,"transcriber")]/text()')
        producers = self.meta('//dc:contributor[starts-with(@id,"producer")]/text()')
        if transcribers:
            resp = sub(stmt, 'respStmt')
            sub(resp, 'resp', 'Source transcription')
            for name in transcribers:
                sub(resp, 'name', name)
        resp = sub(stmt, 'respStmt', xml_id='standard-ebooks-production')
        sub(resp, 'resp', 'Standard Ebooks proofreading and production')
        for name in producers:
            sub(resp, 'name', name)
        resp = sub(stmt, 'respStmt', xml_id='bookstacks-encoding')
        sub(resp, 'resp', 'XHTML-to-TEI P5 conversion')
        sub(resp, 'name', 'Bookstacks')
        sub(sub(desc, 'editionStmt'), 'edition', f'Standard Ebooks edition of the {item["firstPublished"]} text', n='1.0')
        pub = sub(desc, 'publicationStmt')
        sub(pub, 'publisher', 'Bookstacks')
        sub(pub, 'date', EDITION_DATE, when=EDITION_DATE)
        sub(pub, 'idno', self.slug, type='local')
        availability = sub(pub, 'availability', status='free')
        sub(availability, 'licence',
            f'First published in {item["firstPublished"]}; public domain in the United States. '
            'Standard Ebooks dedicates its own contributions to the public domain under CC0 1.0. '
            'Copyright status may differ outside the United States.',
            target='https://creativecommons.org/publicdomain/zero/1.0/')
        sources = self.meta('//dc:source/text()')
        sub(sub(desc, 'notesStmt'), 'note',
            f'First published in {item["firstPublished"]}. Text from the Standard Ebooks edition, '
            f'which was proofread against the page scans it cites. All stories, chapters, epigraphs, '
            f'letters, verse, figures and footnotes are retained.',
            type='source-description')
        bibl = sub(sub(desc, 'sourceDesc'), 'bibl')
        sub(bibl, 'title', title)
        sub(bibl, 'author', item['authorName'])
        sub(bibl, 'publisher', 'Standard Ebooks')
        sub(bibl, 'ref', f'Standard Ebooks: {title}', type='source', target=item['url'])
        for url in sources:
            sub(bibl, 'ref', url, type='transcription-source', target=url)
        sub(bibl, 'idno', item['sha256'], type='source-file-sha256')
        profile = sub(header, 'profileDesc')
        sub(sub(profile, 'langUsage'), 'language', 'English', ident='en')
        return header


def strip_trailing(node):
    last = node[-1] if len(node) else None
    if last is not None:
        last.tail = (last.tail or '').rstrip() or None
        if last.tail is None and last.text and not len(last):
            last.text = last.text.rstrip()
    else:
        node.text = (node.text or '').rstrip()


def append_text_before(node):
    """Keep a removed element's tail text attached to the preceding content."""
    tail = node.tail or ''
    previous = node.getprevious()
    parent = node.getparent()
    if previous is not None:
        previous.tail = (previous.tail or '') + tail
    else:
        parent.text = (parent.text or '') + tail


def flatten(data):
    image = Image.open(io.BytesIO(data)).convert('RGBA')
    canvas = Image.new('RGBA', image.size, (255, 255, 255, 255))
    canvas.alpha_composite(image)
    out = io.BytesIO()
    canvas.convert('RGB').save(out, 'PNG', optimize=True)
    return out.getvalue()


def write(item, schema):
    book = Book(item)
    tree = book.build()
    if not schema.validate(tree):
        (ROOT / 'tmp').mkdir(exist_ok=True)
        tree.write(str(ROOT / 'tmp' / f'{book.slug}.invalid.xml'), encoding='UTF-8', pretty_print=True)
        raise ValueError(f'{book.slug}: {schema.error_log}')
    target_dir = ROOT / 'tei' / item['author']
    target_dir.mkdir(exist_ok=True)
    for source, file in book.figures:
        path = target_dir / file
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(flatten(book.zip.read(source)))
    data = etree.tostring(tree, encoding='UTF-8', xml_declaration=True, pretty_print=True)
    end = data.index(b'?>') + 2
    model = b'<?xml-model href="../tei_all.rng" schematypens="http://relaxng.org/ns/structure/1.0"?>'
    (target_dir / f'{book.slug}.xml').write_bytes(data[:end] + b'\n' + model + data[end:])
    units = {kind: count for kind, count in item['units'].items()}
    print(f'{book.slug}: {units}, {book.note_count} notes, {len(book.figures)} figures')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('works', nargs='*', help='work slugs to import (default: all)')
    parser.add_argument('--download', action='store_true', help='fetch missing EPUBs from Standard Ebooks')
    args = parser.parse_args()
    items = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if args.works:
        items = [item for item in items if item['work'] in args.works]
    CACHE.mkdir(parents=True, exist_ok=True)
    for item in items:
        path = CACHE / item['epub']
        if not path.exists() and args.download:
            url = f'{item["url"]}/downloads/{item["epub"]}?source=download'
            request = urllib.request.Request(url, headers={'User-Agent': 'Bookstacks importer'})
            path.write_bytes(urllib.request.urlopen(request).read())
    schema = etree.RelaxNG(etree.parse(str(SCHEMA)))
    for item in items:
        write(item, schema)
    return 0


if __name__ == '__main__':
    sys.exit(main())
