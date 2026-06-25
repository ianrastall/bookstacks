"""Find exactly where curly/straight quotes appear within each flagged chapter."""
import xml.etree.ElementTree as ET
import re

TEI_NS = 'http://www.tei-c.org/ns/1.0'
XML_NS = 'http://www.w3.org/XML/1998/namespace'

import os
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
en_file = os.path.join(repo_root, 'tei-source', 'tolstoy-leo_war-and-peace_en.xml')

tree = ET.parse(en_file)
root = tree.getroot()

QUOTE_RE = re.compile(r'["“”]')

for chapter in root.findall(f'.//{{{TEI_NS}}}div[@type="chapter"]'):
    n = chapter.get('n')
    text = "".join(chapter.itertext())
    quotes = QUOTE_RE.findall(text)
    if quotes:
        # Show the first instance with context
        idx = QUOTE_RE.search(text).start()
        snippet = text[max(0, idx-60):idx+60].replace('\n', ' ')
        print(f"Ch.{n:>3}: {len(quotes)} quotes  first: ...{snippet}...")
        if int(n) > 10:
            break
