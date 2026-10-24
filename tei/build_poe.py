"""Explicit offline import of the Poe selection; never invoked by site deployment.

Fetch the six checksum-pinned HTML sources into assets/source-poe first.
The selection and illustration subjects are maintained in poe/selection.json.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from lxml import etree, html

ROOT = Path(__file__).resolve().parent.parent
NS = 'http://www.tei-c.org/ns/1.0'
XML = 'http://www.w3.org/XML/1998/namespace'
CONFIG = ROOT / 'tei/poe/selection.json'


def add(parent, tag, text=None, **attrs):
    node = etree.SubElement(parent, f'{{{NS}}}{tag}', attrs)
    node.text = text
    return node


def norm(value):
    return ' '.join(value.split())


def convert(node):
    # Preserve every source character, inline emphasis and explicit line break.
    if node.tag == 'img':
        image = etree.Element(f'{{{NS}}}graphic')
        index = re.fullmatch(r'images/(\d+)\.jpg', node.get('src', ''))
        if not index:
            raise ValueError(f'Unexpected source image: {node.get("src")}')
        image.set('url', f'img/pym-source-{index[1]}.jpg')
        image.set('n', node.get('alt', 'Source diagram'))
        if node.getparent().tag == 'sub': image.set('rend', 'inline')
        return image
    mapping = {'p': 'p', 'div': 'ab', 'blockquote': 'quote', 'pre': 'p',
               'i': 'hi', 'em': 'hi', 'b': 'hi', 'strong': 'hi', 'span': 'seg',
               'a': 'seg', 'br': 'lb', 'hr': 'milestone', 'h3': 'label',
               'table': 'table', 'tr': 'row', 'td': 'cell', 'th': 'cell',
               'sup': 'hi', 'sub': 'hi'}
    tag = mapping.get(node.tag, 'seg')
    out = etree.Element(f'{{{NS}}}{tag}')
    if tag == 'milestone':
        out.set('unit', 'section')
    if node.tag == 'pre':
        out.set('rend', 'preformatted cipher')
    if node.tag in {'i', 'em', 'b', 'strong', 'sup', 'sub'}:
        out.set('rend', {'b': 'bold', 'strong': 'bold', 'sup': 'superscript', 'sub': 'subscript'}.get(node.tag, 'italic'))
    out.text = node.text
    for child in node:
        if not isinstance(child.tag, str):
            continue
        converted = convert(child)
        converted.tail = child.tail
        out.append(converted)
    return out


def build():
    config = json.loads(CONFIG.read_text(encoding='utf8'))
    documents = {}
    for number, source in config['sources'].items():
        raw = (ROOT / f'assets/source-poe/{number}.html').read_bytes()
        if hashlib.sha256(raw).hexdigest() != source['sha256']:
            raise ValueError(f'Source {number} changed; review before importing.')
        documents[int(number)] = html.fromstring(raw.decode('utf8'))
    for figure in config['sourceFigures']:
        if hashlib.sha256((ROOT / 'tei/poe' / figure['file']).read_bytes()).hexdigest() != figure['sha256']:
            raise ValueError(f'Source figure changed: {figure["file"]}')
    root = etree.Element(f'{{{NS}}}TEI', nsmap={None: NS})
    root.set(f'{{{XML}}}id', 'poe_collected-works-of-mystery-and-horror_eng')
    header = add(root, 'teiHeader')
    desc = add(header, 'fileDesc')
    title = add(desc, 'titleStmt')
    add(title, 'title', config['title'], type='main')
    add(title, 'author', 'Edgar Allan Poe')
    resp = add(title, 'respStmt')
    add(resp, 'resp', 'Electronic source transcription')
    add(resp, 'name', 'Project Gutenberg; David Widger; Carlo Traverso (Raven volume I); Ron Swanson (1838 Pym edition)')
    resp = add(title, 'respStmt')
    add(resp, 'resp', 'Selection, TEI encoding, and new AI-generated engraving-style illustrations')
    add(resp, 'name', 'Bookstacks, with OpenAI image generation')
    add(add(desc, 'editionStmt'), 'edition', 'Bookstacks selected illustrated collection, including the complete Arthur Gordon Pym', n='1.0')
    pub = add(desc, 'publicationStmt')
    add(pub, 'publisher', 'Bookstacks')
    add(pub, 'date', '2026-10-24', when='2026-10-24')
    add(add(pub, 'availability', status='free'), 'p', 'Poe’s texts are public domain in the United States. New illustrations are AI-generated for this edition, not historical engravings. Project Gutenberg source terms and contributor credits remain at the linked sources.')
    notes = add(desc, 'notesStmt')
    add(notes, 'note', 'Selected mystery, detection, psychological horror and supernatural tales from the Raven Edition, plus the complete Narrative of Arthur Gordon Pym of Nantucket from the New York 1838 edition transcribed by Ron Swanson (Project Gutenberg 51060), including its original diagrams and glyphs. Source wording, embedded verse, epigraphs and notes are retained; standalone poems, critical essays and unrelated comic or speculative sketches are excluded. This is an editorial selection, not a claim to all of Poe’s writings. The 36 new sidebar illustrations are AI-generated interpretations in nineteenth-century engraving style; the seven Pym source images are original textual figures.', type='source-description')
    sources = add(desc, 'sourceDesc')
    for number, source in config['sources'].items():
        b = add(sources, 'bibl')
        label = 'The Narrative of Arthur Gordon Pym of Nantucket, New York 1838' if number == '51060' else f'The Works of Edgar Allan Poe, Raven Edition, volume {int(number)-2146}'
        add(b, 'ref', f'Project Gutenberg {number}, {label}', type='source', target=source['url'])
        add(b, 'idno', source['sha256'], type='source-file-sha256')
    add(add(add(header, 'profileDesc'), 'langUsage'), 'language', 'English', ident='en')
    text = add(root, 'text'); text.set(f'{{{XML}}}lang', 'en')
    body = add(text, 'body')
    report = []
    for index, story in enumerate(config['stories'], 1):
        doc = documents[story['volume']]
        if story['slug'].startswith('the-narrative-of-'):
            containers = []
            current = None
            chapter_number = 0
            for node in doc.xpath('//body/*'):
                if node.tag == 'footer': break
                value = norm(''.join(node.itertext()))
                if (node.tag == 'h2' and value == 'PREFACE.') or node.tag == 'h3':
                    if value == 'PREFACE.': heading = 'Preface'
                    elif value == 'NOTE.': heading = 'Concluding note'
                    else:
                        chapter_number += 1
                        heading = f'CHAPTER {chapter_number}'
                    current = etree.Element('div')
                    etree.SubElement(current, 'h2').text = heading
                    containers.append(current)
                elif current is not None and value != 'NARRATIVE OF':
                    if value or node.xpath('.//img'):
                        current.append(copy.deepcopy(node))
            assert chapter_number == 25 and len(containers) == 27
        else:
            def key(s): return re.sub(r'[^A-Z]', '', s.upper()).replace('DOCTOR', 'DR')
            expected = key(story['title'])
            candidates = [h for h in doc.xpath('//div[@class="chapter"]/h2') if key(h.text_content()).split('FOOTNOTES')[0].startswith(expected)]
            if len(candidates) != 1:
                raise ValueError(f'Cannot uniquely find {story["title"]}: {len(candidates)}')
            containers = [candidates[0].getparent()]
        is_pym = len(containers) > 1
        div = add(body, 'div', type='part' if is_pym else 'story', n='pym' if is_pym else str(index))
        div.set(f'{{{XML}}}id', story['slug'])
        add(div, 'head', story['title'])
        if not is_pym:
            figure = add(div, 'figure', type='engraving')
            add(figure, 'graphic', url=f'img/{story["slug"]}.png')
            add(figure, 'figDesc', story['description'])
        expected_blocks = []
        actual_blocks = []
        for ci, container in enumerate(containers):
            target = div
            if is_pym:
                heading = norm(container.xpath('string(h2)'))
                number = re.fullmatch(r'CHAPTER (\d+)', heading)
                kind = 'chapter' if number else ('preface' if ci == 0 else 'notes')
                target = add(div, 'div', type=kind, n=number[1] if number else kind)
                target.set(f'{{{XML}}}id', f'pym-section-{ci+1}')
                target.set('corresp', '#pym-antarctic' if (number and int(number[1]) >= 23) or kind == 'notes' else '#pym-voyage')
                add(target, 'head', 'Preface' if ci == 0 else heading)
                if ci in {0, 1}:
                    figure = add(target, 'figure', type='engraving')
                    figure.set(f'{{{XML}}}id', 'pym-antarctic' if ci == 0 else 'pym-voyage')
                    add(figure, 'graphic', url=f'img/{story["slug"]}.png' if ci == 0 else 'img/pym-grampus.png')
                    add(figure, 'figDesc', story['description'] if ci == 0 else 'The storm-damaged brig Grampus rolling in heavy seas, its broken rigging above the waves.')
            for node in container:
                if not isinstance(node.tag, str) or node.tag == 'h2': continue
                converted = convert(node)
                target.append(converted)
                expected_blocks.append(norm(''.join(node.itertext())))
                actual_blocks.append(norm(''.join(converted.itertext())))
        # Volume II stores several notes outside the story containers.
        note_terms = {'A Descent into the Maelstrom': 'Maelstrom', 'Berenice': 'Berenice'}
        if story['title'] in note_terms:
            heading = next(h for h in doc.xpath('//h3') if note_terms[story['title']] in h.text_content())
            add(div, 'label', norm(heading.text_content()))
            for node in heading.itersiblings():
                if node.tag in {'h2', 'h3'}: break
                if not isinstance(node.tag, str): continue
                converted = convert(node); div.append(converted)
                expected_blocks.append(norm(''.join(node.itertext())))
                actual_blocks.append(norm(''.join(converted.itertext())))
        if expected_blocks != actual_blocks or not expected_blocks:
            raise ValueError(f'Text preservation failed: {story["title"]}')
        if is_pym:
            assert len([c for c in containers if re.fullmatch(r'CHAPTER \d+', norm(c.xpath('string(h2)')))]) == 25
        report.append({'title': story['title'], 'source_blocks': len(expected_blocks), 'normalized_text_sha256': hashlib.sha256('\n'.join(expected_blocks).encode()).hexdigest()})
    for i, node in enumerate(text.iter(), 1):
        if node.tag == f'{{{NS}}}p': node.set(f'{{{XML}}}id', f'poe-p-{i:05d}')
    tree = etree.ElementTree(root)
    etree.RelaxNG(etree.parse(str(ROOT / 'tei/tei_all.rng'))).assertValid(tree)
    output = ROOT / 'tei/poe/poe_collected-works-of-mystery-and-horror_eng.xml'
    tree.write(str(output), encoding='UTF-8', xml_declaration=True, pretty_print=True)
    (ROOT / 'tei/poe/import-report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(f'{output}: {len(report)} works; source block text preserved')


if __name__ == '__main__':
    build()
