"""Check ES chapters for real dialogue double-quote issues (paragraph starts with quote)."""
import xml.etree.ElementTree as ET
import os

NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root = ET.parse(os.path.join(REPO, 'tei-source', 'tolstoy-leo_war-and-peace_es.xml')).getroot()

bad = {}
for ch in root.findall('.//tei:div[@type="chapter"]', NS):
    n = int(ch.get('n', 0))
    if n < 46:
        continue
    for p in ch.findall('.//tei:p', NS):
        text = ''.join(p.itertext()).strip()
        if text.startswith('"'):
            bad.setdefault(n, []).append(text[:120])

print('ES chapters 46+ with paragraphs opening with double-quote (real dialogue issues):')
if bad:
    for n, lines in sorted(bad.items()):
        print('  Ch.' + str(n) + ': ' + str(len(lines)) + ' instance(s)')
        for line in lines[:2]:
            print('    ' + repr(line[:80]))
else:
    print('  None found.')
