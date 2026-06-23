with open('tei-source/2600-full.xml', 'r', encoding='utf-8') as f:
    text = f.read()

for i in range(3, 6):
    ch = text[text.find(f'<div type="chapter" n="{i}">'):text.find(f'<div type="chapter" n="{i+1}">')]
    with open(f'ch{i}.txt', 'w', encoding='utf-8') as f2:
        f2.write(ch)
