"""Find double quote characters in ES ch.51 paragraphs."""
import xml.etree.ElementTree as ET, os
NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root = ET.parse(os.path.join(REPO, 'tei-source', 'tolstoy-leo_war-and-peace_es.xml')).getroot()
for ch in root.findall('.//tei:div[@type="chapter"]', NS):
    if ch.get('n') != '51':
        continue
    for i, p in enumerate(ch.findall('.//tei:p', NS), 1):
        text = ''.join(p.itertext())
        if '"' in text:
            print(f'  Para {i}: {text[:200]}')
