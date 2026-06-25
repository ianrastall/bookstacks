import xml.etree.ElementTree as ET
import os

TEI_NS = 'http://www.tei-c.org/ns/1.0'
XML_NS = 'http://www.w3.org/XML/1998/namespace'

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
full_xml = os.path.join(repo_root, 'tei-source', '2600-full.xml')

tree = ET.parse(full_xml)
root = tree.getroot()

# Build a map of chapter number -> direct-child EN/ES divs
chapters_with_en = {}
chapters_with_es = {}
for chapter in root.findall(f'.//{{{TEI_NS}}}div[@type="chapter"]'):
    n = chapter.get('n')
    for d in chapter.findall(f'{{{TEI_NS}}}div[@type="version"]'):
        lang = d.get(f'{{{XML_NS}}}lang')
        if lang == 'en':
            chapters_with_en[n] = d
        elif lang == 'es':
            chapters_with_es[n] = d

print(f"Chapters with EN (direct child): {sorted(chapters_with_en.keys(), key=lambda x: int(x))}")
print(f"\nChapters with ES (direct child): {sorted(chapters_with_es.keys(), key=lambda x: int(x))}")

# Find all EN divs anywhere - check their parent context
body = root.find(f'.//{{{TEI_NS}}}body')
all_body_children = list(body) if body is not None else []
print(f"\nDirect children of <body>: {len(all_body_children)}")
for child in all_body_children[:5]:
    print(f"  {child.tag} type={child.get('type')} n={child.get('n')}")
