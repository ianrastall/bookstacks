"""Compare French foreign tag content between RU and EN ch.1 to find missing ones."""
import xml.etree.ElementTree as ET, os
NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
XML_LANG = '{http://www.w3.org/XML/1998/namespace}lang'
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_fr_tags(lang):
    root = ET.parse(os.path.join(REPO, 'tei-source', f'tolstoy-leo_war-and-peace_{lang}.xml')).getroot()
    for ch in root.findall('.//tei:div[@type="chapter"]', NS):
        if ch.get('n') == '1':
            return [(t.text or '').strip()[:70]
                    for t in ch.findall('.//tei:foreign', NS)
                    if t.get(XML_LANG) == 'fr' or t.get('xml:lang') == 'fr']
    return []

ru_tags = get_fr_tags('ru')
en_tags = get_fr_tags('en')
es_tags = get_fr_tags('es')

print(f'RU ch.1: {len(ru_tags)} French tags')
print(f'EN ch.1: {len(en_tags)} French tags')
print(f'ES ch.1: {len(es_tags)} French tags')

# Find RU tags that have no close match in EN
print('\nRU tags not found in EN:')
for ru in ru_tags:
    key = ru[:30].lower()
    if not any(key in en.lower() for en in en_tags):
        print(f'  {repr(ru)}')

print('\nRU tags not found in ES:')
for ru in ru_tags:
    key = ru[:30].lower()
    if not any(key in es.lower() for es in es_tags):
        print(f'  {repr(ru)}')
