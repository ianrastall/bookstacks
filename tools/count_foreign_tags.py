"""Count French <foreign> tags in ch.90-92 per language."""
import xml.etree.ElementTree as ET, os
NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XML_LANG = '{http://www.w3.org/XML/1998/namespace}lang'

for lang in ['ru', 'en', 'es']:
    root = ET.parse(os.path.join(REPO, 'tei-source', f'tolstoy-leo_war-and-peace_{lang}.xml')).getroot()
    for ch in root.findall('.//tei:div[@type="chapter"]', NS):
        if ch.get('n') in ('90', '91', '92'):
            fr_tags = [t for t in ch.findall('.//tei:foreign', NS)
                       if t.get(XML_LANG) == 'fr' or t.get('xml:lang') == 'fr']
            print(f'{lang.upper()} ch.{ch.get("n")}: {len(fr_tags)} <foreign xml:lang="fr"> tags')
            for t in fr_tags:
                text = (t.text or '').strip()[:60]
                print(f'  {repr(text)}')
