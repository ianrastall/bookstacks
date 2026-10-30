"""Import the two reviewed Spanish EMOTHE editions offline, without changing text.

The source XML snapshots and their upstream commit are pinned in the manifest.
Only encoding, structural tag names, navigation numbers and missing IDs change.
No site build invokes this importer. Use --verify-only to check reproducibility.
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

from lxml import etree
from validate_tei import validate_file

ROOT = Path(__file__).resolve().parent
TEI = 'http://www.tei-c.org/ns/1.0'
NS = {'t': TEI}
XML_ID = '{http://www.w3.org/XML/1998/namespace}id'
XML_LANG = '{http://www.w3.org/XML/1998/namespace}lang'


def node(tag, value=None, **attrs):
    result = etree.Element(f'{{{TEI}}}{tag}', **attrs)
    result.text = value
    return result


def characters(element):
    return re.sub(r'\s+', '', ''.join(element.itertext()))


def build(record, raw):
    source = etree.fromstring(raw)
    root = deepcopy(source)
    root.set(XML_ID, f"shakespeare-{record['slug']}-spa")
    root.set(XML_LANG, 'es')
    header = root.find('t:teiHeader', NS)
    desc = header.find('t:fileDesc', NS)
    title_stmt = desc.find('t:titleStmt', NS)
    # The second author is an inverted sorting label, not a coauthor.
    for author in title_stmt.findall('t:author[@key="orden"]', NS):
        title_stmt.remove(author)
    resp = node('respStmt'); resp.set(XML_ID, 'bookstacks-encoding')
    resp.append(node('resp', 'Technical TEI format normalization; literary text unchanged'))
    resp.append(node('name', 'Bookstacks project')); title_stmt.append(resp)
    # Retain the entire original availability statement and licence.
    source_desc = desc.find('t:sourceDesc', NS)
    for language in source_desc.findall('.//t:lang', NS):
        language.tag = f'{{{TEI}}}textLang'
        language.set('mainLang', 'es')
    # A paragraph makes print provenance and reuse terms visible on the book page.
    source_desc.insert(0, node('p', record['source_description']))
    for label, href in [
        ('EMOTHE digital edition', record['edition_url']),
        ('Recorded upstream XML', record['source_url']),
        ('CC BY-NC-ND 4.0', record['licence']),
    ]:
        paragraph = node('p'); paragraph.append(node('ref', label, target=href, type='source'))
        source_desc.append(paragraph)
    bibliography = source_desc.find('t:bibl', NS)
    bibliography.append(node('ref', 'EMOTHE digital edition', target=record['edition_url']))
    bibliography.append(node('ref', 'CC BY-NC-ND 4.0', target=record['licence']))
    citation_text = ' '.join(bibliography.find('t:note', NS).itertext()).strip()
    encoder = record['encoder']
    bibliography.append(node('note', f'{citation_text} Oleza, Joan et al. EMOTHE: The Classics of Early Modern European Theatre. Valencia: ARTELOPE/EMOTHE Universitat de València, 2010–. Digital encoding: {encoder}.', type='source-attribution'))
    source_desc.remove(bibliography)
    citation = node('p'); citation.append(bibliography); source_desc.append(citation)
    revision = header.find('t:revisionDesc', NS)
    change = node('change', 'Bookstacks technical format normalization from the recorded EMOTHE XML; no literary wording changed.', when=record['import_date'], who='#bookstacks-encoding')
    revision.append(change)
    text = root.find('t:text', NS); text.set(XML_LANG, 'es')
    counters = Counter()
    used = set(root.xpath('//@xml:id'))
    for element in text.iter():
        if not isinstance(element.tag, str):
            continue
        tag = etree.QName(element).localname
        if tag in {'div1', 'div2'}:
            element.tag = f'{{{TEI}}}div'; tag = 'div'
        if tag == 'div' and element.get('type') in {'nota_edicion_digital', 'elenco'}:
            element.set('type', {'nota_edicion_digital': 'publication-note', 'elenco': 'characters'}[element.get('type')])
        if tag == 'div' and element.get('type') == 'scene':
            element.set('n', str(1 + len(element.xpath('preceding-sibling::t:div[@type="scene"]', namespaces=NS))))
        if tag in {'div', 'p', 'sp', 'stage', 'lg', 'l'} and not element.get(XML_ID):
            counters[tag] += 1
            identifier = f"emothe-{record['id']}-{tag}-{counters[tag]:05d}"
            if identifier in used:
                raise ValueError(f'Duplicate generated ID: {identifier}')
            element.set(XML_ID, identifier); used.add(identifier)
        # EMOTHE's stylesheet supplies these boundaries; retain them as spacing
        # when its adjacent XML elements are rendered outside that stylesheet.
        if tag == 'role' and element.getnext() is not None and etree.QName(element.getnext()).localname == 'roleDesc':
            element.tail = (element.tail or '') + ' '
        if tag == 'stage' and element.tail and not element.tail[0].isspace():
            element.tail = ' ' + element.tail
    original_text = source.find('t:text', NS)
    if characters(original_text) != characters(text):
        raise ValueError('Literary text or order changed during normalization')
    for tag in ('sp', 'speaker', 'p', 'stage', 'lg', 'l', 'castItem', 'seg', 'lb'):
        if len(original_text.findall('.//t:' + tag, NS)) != len(text.findall('.//t:' + tag, NS)):
            raise ValueError(f'Source {tag} boundaries changed')
    acts = text.findall('.//t:div[@type="act"]', NS)
    scenes = [len(act.findall('t:div[@type="scene"]', NS)) for act in acts]
    if scenes != record['scenes_per_act']:
        raise ValueError(f'Unexpected act/scene structure: {scenes}')
    for tag, count in record['counts'].items():
        if len(text.findall('.//t:' + tag, NS)) != count:
            raise ValueError(f'Unexpected {tag} count')
    for who in text.xpath('.//t:sp/@who', namespaces=NS):
        if any(pointer[1:] not in used for pointer in who.split()):
            raise ValueError(f'Unresolved character: {who}')
    return etree.ElementTree(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    records = json.loads((ROOT / 'emothe-shakespeare-sources.json').read_text(encoding='utf-8'))
    schema = etree.RelaxNG(etree.parse(str(ROOT / 'tei_all.rng')))
    for record in records:
        raw = gzip.decompress((ROOT / record['snapshot']).read_bytes())
        if hashlib.sha256(raw).hexdigest() != record['sha256']:
            raise ValueError('Source snapshot checksum mismatch')
        document = build(record, raw)
        if not schema.validate(document):
            raise ValueError(str(schema.error_log))
        output = ROOT / 'shakespeare' / f"shakespeare_{record['slug']}_spa.xml"
        serialized = etree.tostring(document, encoding='utf-8', xml_declaration=True, pretty_print=True)
        if args.verify_only:
            if output.read_bytes() != serialized:
                raise ValueError(f'Import differs from {output}')
        else:
            output.write_bytes(serialized)
        errors = validate_file(output, schema)
        if errors:
            raise ValueError('\n'.join(errors))
        print(f"OK {output.name}: {record['scenes_per_act']}; all source text and literary boundaries preserved")


if __name__ == '__main__':
    main()
