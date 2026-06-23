with open('tei-source/2600-full.xml', 'r', encoding='utf-8') as f:
    text = f.read()

with open('es.txt', 'r', encoding='utf-8') as f:
    es_text = f.read()

en_end = 'apprenticeship as an old maid.</seg></p>\n\t\t\t\t</div>\n'
if en_end in text:
    text = text.replace(en_end, en_end + es_text + '\n')
else:
    print("Could not find end of English tab")

ru_start = '<div type="version" xml:lang="ru" subtype="original">\n\t\t\t\t\t<p><foreign xml:lang="fr">— Eh bien, mon prince.'
ru_head_start = '<div type="version" xml:lang="ru" subtype="original">\n\t\t\t\t\t<head>Том I, часть первая, глава I</head>\n\t\t\t\t\t<p><foreign xml:lang="fr">— Eh bien, mon prince.'
if ru_start in text:
    text = text.replace(ru_start, ru_head_start)
else:
    print("Could not find start of Russian tab")

with open('tei-source/2600-full.xml', 'w', encoding='utf-8') as f:
    f.write(text)
