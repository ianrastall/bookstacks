with open('tei-source/2600-full.xml', 'r', encoding='utf-8') as f:
    text = f.read()
start = text.find('<div type="chapter" n="1">')
end = text.find('<div type="chapter" n="2">')
with open('ch1.txt', 'w', encoding='utf-8') as f:
    f.write(text[start:end])
