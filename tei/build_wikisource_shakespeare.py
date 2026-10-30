"""Explicit, offline Shakespeare imports from reviewed Wikisource snapshots.

Snapshots contain only scan-backed text containers, not the site's interface.
The source manifest pins their hashes and upstream revision links. Nothing in
the site build invokes this importer. Unrecognized literary blocks fail closed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import re

from lxml import etree, html

from build_gutenberg_drama_epub import TEI, XML_ID, XML_LANG, append_text, tei
from validate_tei import validate_file

ROOT = Path(__file__).resolve().parent
NS = {'t': TEI}


def compact(value: str) -> str:
    return re.sub(r'\s+', ' ', re.sub('[\u200b\u200c\ufeff]', '', value)).strip()


def letters(value: str) -> str:
    return re.sub(r'\s+', '', compact(value))


def text(element) -> str:
    return compact(''.join(element.itertext()))


def has_class(element, name: str) -> bool:
    return name in element.get('class', '').split()


def clean_source(root):
    root = deepcopy(root)
    for element in list(root.iter()):
        if not isinstance(element.tag, str):
            element.getparent().remove(element)
        elif element.tag in {'style', 'script', 'link', 'figure', 'math'} or any(
            has_class(element, cls) for cls in ('pagenum', 'mw-editsection', 'ws-noexport')
        ) or element.tag == 'a' and element.get('href', '').startswith('#OCSH_16_haut_'):
            element.drop_tree()
        else:
            # Wikisource uses invisible placeholders for indentation/page breaks.
            if element.text: element.text = re.sub('[\u200b\u200c\ufeff]', '', element.text)
            if element.tail: element.tail = re.sub('[\u200b\u200c\ufeff]', '', element.tail)
    return root


class Importer:
    def __init__(self, record):
        self.record = record
        self.counts = Counter()
        self.act = None
        self.scene = None
        self.speech = None

    def node(self, tag, value=None, **attrs):
        self.counts[tag] += 1
        if tag in {'div', 'p', 'sp', 'stage', 'lg', 'l', 'note'}:
            attrs.setdefault('xml_id', f"{self.record['language3']}-{tag}-{self.counts[tag]:06d}")
        return tei(tag, value, **attrs)

    def inline(self, source, target):
        append_text(target, source.text)
        for child in source:
            converted = None
            if child.tag == 'br':
                converted = tei('lb')
            elif child.tag in {'i', 'em', 'b', 'strong', 'sup', 'sub'}:
                converted = tei('hi', rend={'i': 'italic', 'em': 'italic', 'b': 'bold', 'strong': 'bold'}.get(child.tag, child.tag))
                self.inline(child, converted)
            elif child.tag == 'a':
                href = child.get('href', '')
                converted = tei('ref', target=(href if not href.startswith('#') else '#' + href[1:]))
                self.inline(child, converted)
            else:
                converted = tei('seg')
                if child.get('class'):
                    converted.set('rend', child.get('class'))
                self.inline(child, converted)
            if converted is not None:
                target.append(converted)
            append_text(target, child.tail)

    def header(self):
        r = self.record
        root = etree.Element(f'{{{TEI}}}TEI', nsmap={None: TEI})
        root.set(XML_ID, f"shakespeare-{r['slug']}-{r['language3']}")
        root.set(XML_LANG, r['language'])
        header = tei('teiHeader')
        desc = tei('fileDesc')
        title = tei('titleStmt')
        title.append(tei('title', r['title'], xml_lang=r['language']))
        for name in r['authors']:
            author = tei('author'); author.append(tei('persName', name)); title.append(author)
        for role, name in [('French translation and notes', r['translator']), ('Wikisource transcription', 'Wikisource contributors')]:
            resp = tei('respStmt'); resp.append(tei('resp', role)); resp.append(tei('name', name)); title.append(resp)
        resp = tei('respStmt', xml_id='bookstacks-encoding')
        resp.append(tei('resp', 'HTML-to-TEI conversion and source verification'))
        resp.append(tei('name', 'Bookstacks project')); title.append(resp)
        desc.append(title)
        edition = tei('editionStmt'); edition.append(tei('edition', 'Bookstacks TEI edition', n='1.0')); desc.append(edition)
        publication = tei('publicationStmt')
        publication.append(tei('publisher', 'Bookstacks project'))
        publication.append(tei('date', r['import_date'], when=r['import_date']))
        availability = tei('availability', status='free')
        availability.append(tei('licence', 'Historical translation in the public domain. Wikisource transcription and this derived TEI are available under CC BY-SA 4.0; attribution and revision history are linked in sourceDesc.', target='https://creativecommons.org/licenses/by-sa/4.0/'))
        publication.append(availability); desc.append(publication)
        source = tei('sourceDesc')
        source.append(tei('p', r['print_source']))
        source.append(tei('p', r['source_note']))
        source.append(tei('p', f"Reviewed text snapshot SHA-256: {r['sha256']}."))
        bibliography = tei('bibl')
        bibliography.append(tei('title', r['title']))
        bibliography.append(tei('publisher', 'Paris : Pagnerre'))
        bibliography.append(tei('date', '1866', when='1866'))
        bibliography.append(tei('ref', 'Recorded transcription', target='https://fr.wikisource.org/?oldid=15966643', type='source'))
        for child in bibliography: child.tail = ' '
        citation = tei('p'); citation.append(bibliography); source.append(citation)
        for label, href in [('Wikisource transcription (recorded revision)', r['url']), ('Source scan', r['scan_url']), ('Transcription history and contributors', r['history_url'])]:
            p = tei('p'); p.append(tei('ref', label, target=href, type='source')); source.append(p)
        desc.append(source); header.append(desc)
        encoding = tei('encodingDesc'); project = tei('projectDesc')
        project.append(tei('p', 'Scan-backed text containers converted in source order. All literary characters are verified against the snapshot after whitespace normalization. Acts, scenes, speaker labels, stage directions, verse line breaks, inline typography, title/cast matter, prologue, epilogue and translator notes are retained. Decorative images, page markers and website controls are omitted. No alignment with another language is imposed.'))
        encoding.append(project); header.append(encoding)
        profile = tei('profileDesc'); usage = tei('langUsage'); usage.append(tei('language', 'French', ident=r['language'])); profile.append(usage); header.append(profile)
        revision = tei('revisionDesc'); revision.append(tei('change', 'Imported from the recorded Wikisource snapshot; verified complete source text, hierarchy and note targets.', when=r['import_date'], who='#bookstacks-encoding')); header.append(revision)
        root.append(header)
        literary = tei('text', xml_lang=r['language']); self.body = tei('body'); literary.append(self.body); root.append(literary)
        return etree.ElementTree(root)

    def division(self, parent, kind, heading, number=None):
        attrs = {'type': kind}
        if number is not None: attrs['n'] = str(number)
        result = self.node('div', **attrs); result.append(tei('head', heading)); parent.append(result)
        self.speech = None
        return result

    def poem(self, source, target):
        group = self.node('lg')
        # Preserve all inline markup while splitting at explicit source breaks.
        line = self.node('l')
        def walk(element, output):
            nonlocal line
            append_text(output, element.text)
            for child in element:
                if etree.QName(child).localname == 'lb':
                    if text(line): group.append(line)
                    line = self.node('l'); output = line
                else:
                    # Source poem typography is inline; keep nested emphasis.
                    clone = deepcopy(child); clone.tail = None; output.append(clone)
                append_text(output, child.tail)
        # poem wrappers contain p; flatten wrapper boundaries into line breaks.
        # The source uses direct p/br with inline spans, not nested line breaks.
        for p in source:
            if p.tag != 'p': raise ValueError('Unexpected poem wrapper')
            scratch = tei('seg'); self.inline(p, scratch); walk(scratch, line)
            if text(line): group.append(line)
            line = self.node('l')
        target.append(group)

    def build(self, roots):
        document = self.header()
        current = self.division(self.body, 'title-page', 'Page de titre')
        mode = 'title'
        act_number = scene_number = 0
        for source in roots[0]:
            value = text(source)
            if not value: continue
            act_match = re.fullmatch(r'ACTE ([IVX]+)\.?', value)
            scene_match = re.fullmatch(r'SCÈNE ([IVX]+)\.?', value)
            if act_match:
                act_number += 1; scene_number = 0
                self.act = self.division(self.body, 'act', value, act_number)
                self.scene = None; current = self.act; mode = 'drama'; continue
            if scene_match:
                if self.act is None: raise ValueError('Scene before act')
                scene_number += 1
                current = self.scene = self.division(self.act, 'scene', value, scene_number); continue
            if value in {'PROLOGUE.', 'ÉPILOGUE.'}:
                current = self.division(self.body, 'prologue' if value == 'PROLOGUE.' else 'epilogue', value)
                mode = 'supplement'; continue
            if value == 'PERSONNAGES :':
                current = self.division(self.body, 'characters', value); mode = 'cast'; continue
            speaker = source.xpath('./span[contains(concat(" ",normalize-space(@class)," ")," personnage ")]')
            if speaker:
                if len(speaker) != 1 or self.scene is None: raise ValueError('Unexpected speaker location')
                self.speech = self.node('sp'); current.append(self.speech)
                label = tei('speaker'); self.inline(speaker[0], label); self.speech.append(label)
                # Qualifying directions are explicitly marked by Wikisource.
                for qualifier in source.xpath('./span[@class="didascalie"]'):
                    stage = self.node('stage', type='business'); self.inline(qualifier, stage); self.speech.append(stage)
                continue
            poems = source.xpath('.//div[@class="poem"]')
            if source.tag == 'div' and has_class(source, 'poem'): poems = [source]
            if poems:
                for poem in poems:
                    self.poem(poem, self.speech if self.speech is not None else current)
                continue
            if source.tag not in {'p', 'div', 'table'}:
                raise ValueError(f'Unrecognized literary block {source.tag}: {value[:80]}')
            if mode == 'drama' and source.tag == 'div' and 'font-size:90%' in source.get('style', '') and not value.startswith('fin des'):
                output = self.node('stage', type='business')
                target = self.speech if self.speech is not None else current
            else:
                output = self.node('p')
                target = self.speech if self.speech is not None and mode == 'drama' else current
            # Decorative nested table cells carry cast/title words, not speech.
            self.inline(source, output); target.append(output)
        notes = self.division(self.body, 'notes', 'Notes du traducteur')
        for source in roots[1]:
            if not text(source): continue
            if source.tag != 'p': raise ValueError('Unexpected note block')
            note = self.node('note', type='editorial', place='end')
            markers = source.xpath('.//*[@id]')
            marker = next((e for e in markers if e.get('id', '').startswith('OCSH_16_bas_')), None)
            if marker is None: raise ValueError('Note without source identifier')
            note.set(XML_ID, marker.get('id'))
            note.set('n', marker.get('id').rsplit('_', 1)[-1])
            self.inline(source, note); notes.append(note)
        actual = letters(''.join(self.body.itertext()))
        # Added navigation headings aren't source text; exclude them here.
        for heading in [self.body[0][0], notes[0]]:
            actual = actual.replace(letters(heading.text), '', 1)
        expected = letters(''.join(''.join(r.itertext()) for r in roots))
        if actual != expected:
            mismatch = next((i for i, (a,b) in enumerate(zip(actual, expected)) if a != b), min(len(actual), len(expected)))
            raise ValueError(f'Source text mismatch at {mismatch}: {actual[mismatch:mismatch+100]!r} vs {expected[mismatch:mismatch+100]!r}')
        return document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'shakespeare')
    parser.add_argument('--verify-only', action='store_true', help='Compare imports with committed TEI without writing files')
    args = parser.parse_args()
    records = json.loads((ROOT / 'shakespeare-sources.json').read_text(encoding='utf-8'))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    schema = etree.RelaxNG(etree.parse(str(ROOT / 'tei_all.rng')))
    for record in records:
        raw = gzip.decompress((ROOT / record['snapshot']).read_bytes())
        if hashlib.sha256(raw).hexdigest() != record['sha256']: raise ValueError('Snapshot hash mismatch')
        source = html.fromstring(raw.decode('utf-8'))
        roots = [clean_source(root) for root in source.xpath('//div[@class="prp-pages-output"]')]
        if len(roots) != 2: raise ValueError('Expected play and note containers')
        document = Importer(record).build(roots)
        acts = document.findall('.//{' + TEI + '}div[@type="act"]')
        scenes = [len(a.findall('./{' + TEI + '}div[@type="scene"]')) for a in acts]
        if scenes != record['scenes_per_act']: raise ValueError(f'Unexpected scene sequence: {scenes}')
        for tag, expected in [('speaker', 835), ('lg', 7), ('note', 3)]:
            actual = len(document.findall('.//{' + TEI + '}text//{' + TEI + '}' + tag))
            if actual != expected: raise ValueError(f'Unexpected {tag} count: {actual}, expected {expected}')
        ids = set(document.xpath('//@xml:id'))
        for target in document.xpath('//t:text//t:ref/@target', namespaces=NS):
            if target.startswith('#') and target[1:] not in ids: raise ValueError(f'Unresolved note target: {target}')
        if not schema.validate(document): raise ValueError(str(schema.error_log))
        output = args.output_dir / f"shakespeare_{record['slug']}_{record['language3']}.xml"
        serialized = etree.tostring(document, encoding='utf-8', xml_declaration=True, pretty_print=True)
        if args.verify_only:
            if not output.exists() or output.read_bytes() != serialized:
                raise ValueError(f'{output} does not match its reviewed source import')
        else:
            output.write_bytes(serialized)
        errors = validate_file(output, schema)
        if errors: raise ValueError('\n'.join(errors))
        print(f'OK {output.name}: {scenes}; all source characters preserved')


if __name__ == '__main__':
    main()
