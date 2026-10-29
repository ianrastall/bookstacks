"""Explicit offline import of pinned Gutenberg Christie HTML; never run by deployment."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from lxml import etree, html

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'tei/christie'
CACHE = ROOT / 'assets/source-christie'
NS = 'http://www.tei-c.org/ns/1.0'
XML = 'http://www.w3.org/XML/1998/namespace'


def norm(s):
    return ' '.join(s.split())


def add(parent, tag, text=None, **attrs):
    out = etree.SubElement(parent, f'{{{NS}}}{tag}', attrs)
    out.text = text
    return out


def read_source(item):
    raw = (CACHE / f'{item["id"]}.html').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item['sha256'], item['id']
    doc = html.fromstring(raw.decode('utf8').replace('\r\n', '\n'))
    # Printed page numbers are apparatus, not part of the literary text.
    for node in doc.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," pagenum ")]'):
        node.drop_tree()
    for node in doc.xpath('//tbody|//thead|//tfoot'):
        node.drop_tag()
    for node in doc.xpath('//a[not(normalize-space()) and not(*)]'):
        node.drop_tree()
    return doc


def heading(node):
    if node.tag in {'h2', 'h3'}:
        return node
    return next(iter(node.xpath('./h2|./h3')), None)


def boundary(item, h):
    value = norm(h.text_content())
    n = item['id']
    if n in {'67173', '67160', '66446'}:
        return False
    if n == '61262':
        return bool(re.fullmatch(r'CH\d+', h.get('id', '')))
    if n == '78084':
        return h.get('id') in item['storyIds']
    if n == '78262':
        return bool(re.match(r'^(?:Prologue|Book |chapter )', value, re.I)) and h.tag == 'h2'
    return bool(re.match(r'^(?:CHAPTER\s+|\d+|PROLOGUE$)', value, re.I))


def sections(item):
    doc = read_source(item)
    current = None
    groups = []
    book = 0
    for node in doc.xpath('//body/*'):
        if node.tag == 'footer':
            break
        if node.tag == 'header':
            continue
        cls = node.get('class', '')
        # Preserve editorial source notes separately, exclude publisher advertisements.
        if 'transnote' in cls or cls in {'tn'} or norm(node.text_content()).startswith("Transcriber's Notes:"):
            break
        if item['id'] == '69087' and current is not None and node.tag == 'div' and 'THE END' in norm(node.text_content()) and len(norm(node.text_content())) < 20:
            break
        h = heading(node)
        if h is not None and boundary(item, h):
            title = norm(h.text_content())
            if item['id'] == '78262' and title.lower().startswith('book '):
                book += 1
                current = None
                continue
            kind = 'prologue' if title.upper() == 'PROLOGUE' else ('story' if item['id'] in {'61262', '78084'} else 'chapter')
            current = dict(title=title, kind=kind, book=book, nodes=[])
            groups.append(current)
            if node is not h:
                current['nodes'].extend(c for c in node if c is not h and isinstance(c.tag, str))
            continue
        if current is None and item['id'] in {'67173', '67160', '66446'} and node.tag == 'p':
            current = dict(title=item['title'], kind='story', book=0, nodes=[])
            groups.append(current)
        if current is not None:
            if node.tag == 'hr' and 'chap' in cls:
                continue
            if node.tag == 'div' and not norm(node.text_content()) and not node.xpath('.//img'):
                continue
            current['nodes'].append(node)
    for i, section in enumerate(groups, 1):
        nodes = section['nodes']
        # Some editions put the chapter title in the next element.
        if nodes and (nodes[0].get('class') in {'subhead', 'chtitle'} or (item['id'] == '78342' and nodes[0].tag == 'h3')):
            section['title'] += '. ' + norm(nodes.pop(0).text_content())
        section['slug'] = f'{item["slug"]}-{i:03d}'
        section['excerpt'] = norm(' '.join(e.text_content() for e in nodes if e.tag == 'p'))[:1000]
    assert len(groups) == item['sections'], (item['id'], len(groups), item['sections'])
    # Keep dedications, the Blue Train cast, and the periodical's original
    # introductory material on the first reading page, without extra routes.
    front = []
    for expression in item.get('frontXpaths', []):
        front.extend(doc.xpath(expression))
    groups[0]['nodes'] = front + groups[0]['nodes']
    return groups


def convert(node, item):
    if not isinstance(node.tag, str):
        return None
    if node.tag == 'img':
        src = node.get('src')
        record = next(f for f in item['figures'] if f['source'] == src)
        out = etree.Element(f'{{{NS}}}graphic', url=record['file'], n=node.get('alt') or 'Source figure')
        return out
    mapping = {'p':'p', 'div':'ab', 'blockquote':'quote', 'i':'hi', 'em':'hi', 'b':'hi', 'strong':'hi',
               'span':'seg', 'a':'seg', 'br':'lb', 'hr':'milestone', 'h2':'label', 'h3':'label', 'h4':'label',
               'table':'table', 'tr':'row', 'td':'cell', 'th':'cell', 'sup':'hi', 'sub':'hi',
               'ul':'list', 'ol':'list', 'li':'item', 'pre':'ab'}
    tag = mapping.get(node.tag,'seg')
    if node.tag == 'div' and node.xpath('.//p'):
        tag = 'quote'
    out = etree.Element(f'{{{NS}}}{tag}')
    if node.tag in {'i','em','b','strong','sup','sub'}:
        out.set('rend', {'b':'bold','strong':'bold','sup':'superscript','sub':'subscript'}.get(node.tag,'italic'))
    elif 'smcap' in node.get('class',''):
        out.set('rend','smallcaps')
    if node.tag == 'hr': out.set('unit','section')
    if node.tag == 'pre': out.set('rend','preformatted')
    out.text = node.text
    for child in node:
        converted = convert(child,item)
        if converted is not None:
            converted.tail = child.tail
            out.append(converted)
    return out


def build():
    manifest = json.loads((BASE / 'selection.json').read_text(encoding='utf8'))
    schema = etree.RelaxNG(etree.parse(str(ROOT / 'tei/tei_all.rng')))
    report = []
    for item in manifest:
        root = etree.Element(f'{{{NS}}}TEI', nsmap={None:NS})
        root.set(f'{{{XML}}}id', f'christie_{item["slug"]}_eng')
        header = add(root,'teiHeader'); desc = add(header,'fileDesc'); title = add(desc,'titleStmt')
        add(title,'title',item['title'],type='main'); add(title,'author','Agatha Christie')
        r = add(title,'respStmt'); add(r,'resp','Electronic source transcription'); add(r,'name',item['credits'])
        r = add(title,'respStmt'); add(r,'resp','TEI encoding and new AI-generated engraving-style sketches'); add(r,'name','Bookstacks, with OpenAI image generation')
        add(add(desc,'editionStmt'),'edition',item['edition'],n='1.0')
        pub = add(desc,'publicationStmt'); add(pub,'publisher','Bookstacks'); add(pub,'date','2026-10-28',when='2026-10-28')
        add(add(pub,'availability',status='free'),'p','The source text is public domain in the United States, as identified by Project Gutenberg. Source terms and contributor credits remain at the linked source. New sketches are AI-generated interpretations, not historical illustrations.')
        notes = add(desc,'notesStmt'); add(notes,'note',item['description'],type='source-description')
        source = add(add(desc,'sourceDesc'),'bibl'); add(source,'ref',f'Project Gutenberg {item["id"]}',type='source',target=f'https://www.gutenberg.org/ebooks/{item["id"]}'); add(source,'idno',item['sha256'],type='source-file-sha256')
        add(add(add(header,'profileDesc'),'langUsage'),'language','English',ident='en')
        text = add(root,'text'); text.set(f'{{{XML}}}lang','en'); body = add(text,'body')
        book_nodes = {}; entries = []; counters = {}
        for i, section in enumerate(sections(item),1):
            target = body
            if section['book']:
                bn = section['book']
                if bn not in book_nodes:
                    book_nodes[bn] = add(body,'div',type='book',n=str(bn)); book_nodes[bn].set(f'{{{XML}}}id',f'book-{bn}'); add(book_nodes[bn],'head',item['bookTitles'][bn-1])
                target = book_nodes[bn]
            key = (section['kind'], section['book'])
            counters[key] = counters.get(key, 0) + 1
            div = add(target,'div',type=section['kind'],n=str(counters[key])); div.set(f'{{{XML}}}id',section['slug']); add(div,'head',section['title'])
            fig = add(div,'figure',type='engraving'); add(fig,'graphic',url=f'img/{section["slug"]}.jpg'); add(fig,'figDesc',f'An engraving-style sketch for {item["title"]}, {section["title"]}.')
            blocks = []
            for node in section['nodes']:
                converted = convert(node,item)
                if converted is None: continue
                if converted.tag == f'{{{NS}}}seg':
                    converted.tag = f'{{{NS}}}ab'
                expected = norm(''.join(node.itertext())); actual = norm(''.join(converted.itertext()))
                assert expected == actual, (item['id'],section['title'],expected[:80],actual[:80])
                div.append(converted); blocks.append(expected)
            assert section['excerpt'], section['slug']
            entries.append(dict(slug=section['slug'],title=section['title'],blocks=len(blocks),normalized_text_sha256=hashlib.sha256('\n'.join(blocks).encode()).hexdigest()))
        for i,p in enumerate(text.iter(f'{{{NS}}}p'),1): p.set(f'{{{XML}}}id',f'p-{i:05d}')
        tree = etree.ElementTree(root)
        if not schema.validate(tree):
            tree.write(str(ROOT/'tmp/christie-invalid.xml'),encoding='UTF-8',pretty_print=True)
            raise ValueError(f'{item["id"]}: {schema.error_log}')
        for f in item['figures']: assert hashlib.sha256((BASE/f['file']).read_bytes()).hexdigest() == f['sha256']
        tree.write(str(BASE/f'christie_{item["slug"]}_eng.xml'),encoding='UTF-8',xml_declaration=True,pretty_print=True)
        report.append(dict(id=item['id'],title=item['title'],sections=entries))
    (BASE/'import-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(f'Imported {len(report)} editions, {sum(len(r["sections"]) for r in report)} reading units; all source block text preserved.')


if __name__ == '__main__':
    build()
