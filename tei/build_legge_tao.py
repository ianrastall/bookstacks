"""Build only the complete Legge translation from reviewed Gutenberg 216 HTML.

Fetch the source separately into assets/source-chinese/216.html. This importer
and PDF generation are never part of a site build or deployment.
"""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from lxml import etree, html

ROOT = Path(__file__).resolve().parent.parent
TEI = 'http://www.tei-c.org/ns/1.0'
XML = 'http://www.w3.org/XML/1998/namespace'
SOURCE = 'https://www.gutenberg.org/cache/epub/216/pg216-images.html'
SHA256 = '2e90738a0501c5ff7253ef24b982edb9d5819e20365736e16160d1a424e072e9'


def element(parent, tag, text=None, **attrs):
    node = etree.SubElement(parent, f'{{{TEI}}}{tag}', attrs)
    node.text = text
    return node


def normalized(value):
    return ' '.join(value.split())


def build(source: Path, output: Path):
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError('Source changed: review Gutenberg 216 before updating its fingerprint.')
    document = html.fromstring(data, parser=html.HTMLParser(encoding='utf-8'))
    root = etree.Element(f'{{{TEI}}}TEI', nsmap={None: TEI})
    root.set(f'{{{XML}}}id', 'laozi_tao-te-ching_eng')
    header = element(root, 'teiHeader'); header.set(f'{{{XML}}}lang', 'en')
    desc = element(header, 'fileDesc')
    title = element(desc, 'titleStmt')
    element(title, 'title', 'The Tao Teh King, or the Tao and its Characteristics', type='main')
    element(title, 'author', 'Laozi (traditional attribution)')
    resp = element(title, 'respStmt')
    element(resp, 'resp', 'English translation'); element(resp, 'name', 'James Legge (1815–1897)')
    resp = element(title, 'respStmt')
    element(resp, 'resp', 'electronic transcription'); element(resp, 'name', 'Gregory Walker and David Widger')
    edition = element(desc, 'editionStmt')
    element(edition, 'edition', 'Bookstacks English edition of the complete James Legge translation', n='1.0')
    pub = element(desc, 'publicationStmt')
    element(pub, 'publisher', 'Bookstacks project')
    element(pub, 'date', '2026-10-24', when='2026-10-24')
    availability = element(pub, 'availability', status='free')
    element(availability, 'p', 'Original work and James Legge translation are public domain in the USA. Source: Project Gutenberg ebook 216; transcription by Gregory Walker and David Widger.')
    notes = element(desc, 'notesStmt')
    element(notes, 'note', 'Complete English translation by James Legge, from Project Gutenberg ebook 216. Both parts and all 81 chapters are retained, including the lineated verse. Source paragraph and verse numbering is preserved; chapter numbers become headings. This edition follows its own source structure independently of the Chinese edition.', type='source-description')
    bibl = element(element(desc, 'sourceDesc'), 'bibl')
    element(bibl, 'ref', 'Project Gutenberg ebook 216: The Tao Teh King', target=SOURCE, type='source')
    element(bibl, 'idno', SHA256, type='source-file-sha256')
    element(element(element(header, 'profileDesc'), 'langUsage'), 'language', 'English', ident='en')
    text = element(root, 'text'); text.set(f'{{{XML}}}lang', 'en')
    body = element(text, 'body')
    part = chapter = None
    number = 0
    expected = []
    actual = []
    for node in document.xpath('//h2[contains(normalize-space(.),"PART 1.")]/following-sibling::*'):
        if node.get('id') == 'pg-footer':
            break
        value = normalized(''.join(node.itertext()))
        if node.tag == 'h2' and value.startswith('PART'):
            part = None
            continue
        if node.tag not in {'p', 'pre'} or not value:
            continue
        if node.tag == 'p':
            marker = re.match(r'^(?:Ch\.\s*)?' + str(number + 1) + r'\.\s*' + (r'(?=1\.)' if number + 1 < 6 else ''), value)
            if marker:
                number += 1
                if number in {1, 38}:
                    part_number = '1' if number == 1 else '2'
                    part = element(body, 'div', type='part', n=part_number)
                    part.set(f'{{{XML}}}id', f'legge-part-{part_number}')
                    element(part, 'head', 'Part I' if number == 1 else 'Part II')
                chapter = element(part, 'div', type='chapter', n=str(number))
                chapter.set(f'{{{XML}}}id', f'legge-chapter-{number}')
                element(chapter, 'head', f'Chapter {number}')
                value = value[marker.end():]
            if chapter is None:
                raise ValueError(f'Unassigned source paragraph: {value}')
            if value:
                target = element(chapter, 'p', value)
                expected.append(value)
                actual.append(normalized(''.join(target.itertext())))
        else:
            target = element(chapter, 'lg')
            # Blank lines delimit source stanzas; preserve them as nested groups.
            for stanza in re.split(r'\n\s*\n', ''.join(node.itertext()).strip()):
                group = element(target, 'lg')
                for line in stanza.splitlines():
                    if line.strip(): element(group, 'l', line.strip())
            expected.append(value)
            actual.append(normalized(' '.join(target.itertext())))
    if number != 81 or expected != actual:
        raise ValueError('Chapter sequence or source block preservation check failed.')
    for index, node in enumerate(text.iter(), 1):
        if node.tag == f'{{{TEI}}}p': node.set(f'{{{XML}}}id', f'legge-p-{index:04d}')
    tree = etree.ElementTree(root)
    schema = etree.RelaxNG(etree.parse(str(ROOT / 'tei/tei_all.rng')))
    schema.assertValid(tree)
    tree.write(str(output), encoding='UTF-8', xml_declaration=True, pretty_print=True)
    print(f'{output}: 81 chapters; {len(expected)} source blocks preserved')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'assets/source-chinese/216.html')
    parser.add_argument('--output', type=Path, default=ROOT / 'tei/laozi/laozi_tao-te-ching_eng.xml')
    args = parser.parse_args()
    build(args.source, args.output)
