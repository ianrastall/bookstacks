with open('tei-source/2600-full.xml', 'r', encoding='utf-8') as f:
    text = f.read()

for i in range(6, 11):
    start = text.find(f'<div type="chapter" n="{i}">')
    end = text.find(f'<div type="chapter" n="{i+1}">')
    ch = text[start:end]
    with open(f'ch{i}.txt', 'w', encoding='utf-8') as f2:
        f2.write(ch)
