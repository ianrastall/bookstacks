import xml.etree.ElementTree as ET
import os

NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_stats(path):
    root = ET.parse(path).getroot()
    stats = {}
    for ch in root.findall('.//tei:div[@type="chapter"]', NS):
        n = ch.get('n')
        if n:
            p = len(ch.findall('.//tei:p', NS)) + len(ch.findall('.//tei:l', NS))
            stats[int(n)] = p
    return stats

ru = load_stats(os.path.join(REPO, 'tei-source', 'tolstoy-leo_war-and-peace_ru.xml'))
en = load_stats(os.path.join(REPO, 'tei-source', 'tolstoy-leo_war-and-peace_en.xml'))
es = load_stats(os.path.join(REPO, 'tei-source', 'tolstoy-leo_war-and-peace_es.xml'))

print('Ch  RU  EN  ES  flags')
for n in range(46, 93):
    r = ru.get(n, 0)
    e = en.get(n, 0)
    s = es.get(n, 0)
    flags = []
    if abs(r - e) > max(2, r * 0.1):
        flags.append('EN')
    if abs(r - s) > max(2, r * 0.1):
        flags.append('ES')
    flag_str = ' *** ' + '+'.join(flags) if flags else ''
    print(str(n).rjust(2) + '  ' + str(r).rjust(2) + '  ' + str(e).rjust(2) + '  ' + str(s).rjust(2) + flag_str)
