"""Show first few paragraphs of a chapter in RU, EN, ES side by side."""
import xml.etree.ElementTree as ET
import os
import sys

NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_paras(lang, n, limit=4):
    path = os.path.join(REPO, 'tei-source', f'tolstoy-leo_war-and-peace_{lang}.xml')
    root = ET.parse(path).getroot()
    for ch in root.findall('.//tei:div[@type="chapter"]', NS):
        if ch.get('n') == str(n):
            paras = []
            for p in ch.findall('.//tei:p', NS):
                text = ''.join(p.itertext()).strip()
                if text:
                    paras.append(text)
            return paras[:limit]
    return []

n = int(sys.argv[1]) if len(sys.argv) > 1 else 66
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 3

print(f'\n=== Chapter {n} ===\n')
for lang in ['ru', 'en', 'es']:
    print(f'--- {lang.upper()} ---')
    for i, p in enumerate(get_paras(lang, n, limit), 1):
        print(f'[{i}] {p[:300]}')
    print()
