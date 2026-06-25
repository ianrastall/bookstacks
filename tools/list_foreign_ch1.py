"""List all French foreign tags in ch.1 for RU and EN to compare."""
import xml.etree.ElementTree as ET, os
NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
XML_LANG = '{http://www.w3.org/XML/1998/namespace}lang'
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_fr_tags(lang):
    root = ET.parse(os.path.join(REPO, 'tei-source', f'tolstoy-leo_war-and-peace_{lang}.xml')).getroot()
    for ch in root.findall('.//tei:div[@type="chapter"]', NS):
        if ch.get('n') == '1':
            return [(t.text or '').strip()
                    for t in ch.findall('.//tei:foreign', NS)
                    if t.get(XML_LANG) == 'fr' or t.get('xml:lang') == 'fr']
    return []

ru = get_fr_tags('ru')
en = get_fr_tags('en')

print(f'=== RU ch.1: {len(ru)} tags ===')
for i, t in enumerate(ru, 1):
    print(f'[{i:2}] {t[:90]}')

print(f'\n=== EN ch.1: {len(en)} tags ===')
for i, t in enumerate(en, 1):
    print(f'[{i:2}] {t[:90]}')
