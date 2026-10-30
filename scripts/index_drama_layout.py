"""Explicitly index Shakespeare character labels for the shared web/PDF layout.

This is derived presentation metadata, not a corpus import. Site deployment
reads the committed index and never runs this command or regenerates TEI/PDFs.
"""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
RULES = json.loads((ROOT / 'src/data/drama-layout-rules.json').read_text(encoding='utf-8'))
NS = {'t': 'http://www.tei-c.org/ns/1.0'}


def name_candidate(value):
    value = ' '.join(value.split()).strip(' ,.:;()[]{}—–-')
    value = re.sub(r'\d+$', '', value).strip()
    if len(value) < 2 or len(value) > 65 or value.lower() in RULES['excludeNames']:
        return None
    if re.fullmatch('[IVXLCDM]+', value) or value.lower() in {'chanson','canto','canción','prologue','epilogue'}:
        return None
    if any(re.search(pattern, value, re.I) for kind in ['entrance', 'exit'] for pattern in RULES[kind].values()):
        return None
    return value


def main():
    index = {}
    for path in sorted((ROOT / 'tei/shakespeare').glob('*.xml')):
        root = ET.parse(path).getroot()
        parents = {child: parent for parent in root.iter() for child in parent}
        def ancestors(element):
            while element in parents:
                element=parents[element]
                yield element
        cast_divisions={element for element in root.iter() if element.tag.endswith('}div') and
                        any(' '.join(''.join(child.itertext()).split()).upper().strip(' :.') in
                            {'PERSONNAGES','PERSONAJES','DRAMATIS PERSONAE'} for child in element)}
        candidates = []
        for element in root.iter():
            tag = element.tag.rsplit('}', 1)[-1]
            value = ' '.join(''.join(element.itertext()).split())
            rendition = element.get('rend', '').split()
            if tag in {'speaker', 'role'}:
                candidates.append(value.split(',')[0])
            elif tag in {'name', 'persName'} and element.get('type') in {'character', 'person'}:
                candidates.append(value)
            elif tag in {'hi', 'seg'} and set(rendition) & {'sc', 'smallcaps', 'small-caps'} and any(
                a.tag.endswith('}stage') or a.get('type')=='characters' for a in ancestors(element)
            ):
                candidates.append(value)
            # Older French cast lists are verse lines; retain their uppercase labels.
            if tag in {'castItem', 'l', 'p'} and any(a in cast_divisions or a.get('type')=='characters' or a.tag.endswith('}castList') for a in ancestors(element)):
                prefix = re.split(r'[,—–{}(]', value, maxsplit=1)[0].strip()
                if prefix and prefix.isupper(): candidates.append(prefix)
        names = {}
        for value in candidates:
            if name := name_candidate(value): names.setdefault(name.lower(), name)
        index[path.name] = {'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'names': sorted(names.values(), key=lambda v: (-len(v), v.lower()))}
    target = ROOT / 'src/data/drama-layout-index.json'
    target.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Indexed character labels for {len(index)} Shakespeare editions.')


if __name__ == '__main__': main()
