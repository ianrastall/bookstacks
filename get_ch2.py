with open('tei-source/2600-full.xml', 'r', encoding='utf-8') as f:
    text = f.read()

ch2 = text[text.find('<div type="chapter" n="2">'):text.find('<div type="chapter" n="3">')]

with open('ch2.txt', 'w', encoding='utf-8') as f:
    f.write(ch2)
