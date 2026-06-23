import re

with open('tei-source/2600-full.xml', 'r', encoding='utf-8') as f:
    text = f.read()

ch1 = text[text.find('<div type="chapter" n="1">'):text.find('<div type="chapter" n="2">')]

ru_text = ch1[ch1.find('<div type="version" xml:lang="ru"'):]
en_text = ch1[ch1.find('<div type="version" xml:lang="en"'):ch1.find('<div type="version" xml:lang="es"')]

ru_foreigns = re.findall(r'<foreign xml:lang="fr">(.*?)</foreign>', ru_text)
en_segs = re.findall(r'<seg type="origfr">(.*?)</seg>', en_text)

with open('align.txt', 'w', encoding='utf-8') as f:
    f.write("RU:\n")
    for i, r in enumerate(ru_foreigns):
        f.write(f"{i}: {r}\n")
    
    f.write("\nEN:\n")
    for i, e in enumerate(en_segs):
        f.write(f"{i}: {e}\n")
