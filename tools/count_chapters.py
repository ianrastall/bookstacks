import xml.etree.ElementTree as ET
import os
NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for lang in ['ru', 'en', 'es']:
    path = os.path.join(REPO, 'tei-source', 'tolstoy-leo_war-and-peace_' + lang + '.xml')
    root = ET.parse(path).getroot()
    chapters = root.findall('.//tei:div[@type="chapter"]', NS)
    nums = sorted(int(c.get('n')) for c in chapters if c.get('n'))
    print(lang.upper() + ': ' + str(len(nums)) + ' chapters, n=' + str(min(nums)) + '-' + str(max(nums)))
