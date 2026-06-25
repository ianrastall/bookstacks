"""
Replace chapter 51 in EN and ES files with ChatGPT translations.
The translations were pasted by the user and saved to a temp file.
"""
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EN_FILE = os.path.join(REPO_ROOT, 'tei-source', 'tolstoy-leo_war-and-peace_en.xml')
ES_FILE = os.path.join(REPO_ROOT, 'tei-source', 'tolstoy-leo_war-and-peace_es.xml')
TRANS_FILE = r'C:\Users\Ian\AppData\Local\Temp\ch51_translations.txt'


def chapter_span(content, n):
    marker = f'<div type="chapter" n="{n}">'
    start = content.find(marker)
    if start == -1:
        raise ValueError(f'Chapter {n} not found')
    nxt = content.find('<div type="chapter"', start + len(marker))
    if nxt == -1:
        raise ValueError(f'No chapter after {n} found')
    return start, nxt


def extract_paras(lines, lang_marker):
    """Extract <p> lines between a version div open tag and its </div>."""
    start = None
    for i, line in enumerate(lines):
        if lang_marker in line:
            start = i + 1
            break
    if start is None:
        raise ValueError(f'Lang marker not found: {lang_marker}')
    paras = []
    for i in range(start, len(lines)):
        stripped = lines[i].rstrip('\r\n')
        if stripped.strip() == '</div>':
            break
        if stripped.strip():
            paras.append('    ' + stripped.strip())
    return '\n'.join(paras) + '\n'


def replace_chapter(file_path, new_block, n=51):
    with open(file_path, encoding='utf-8') as f:
        content = f.read()
    start, end = chapter_span(content, n)
    old_len = end - start
    content = content[:start] + new_block + content[end:]
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print(f'  {os.path.basename(file_path)}: replaced {old_len} chars with {len(new_block)} chars')


with open(TRANS_FILE, encoding='utf-8') as f:
    lines = f.readlines()

en_paras = extract_paras(lines, 'xml:lang="en" subtype="translation"')
es_paras = extract_paras(lines, 'xml:lang="es" subtype="translation-es"')

en_p_count = en_paras.count('<p>')
es_p_count = es_paras.count('<p>')
print(f'Extracted: EN={en_p_count} paragraphs, ES={es_p_count} paragraphs')

new_en_ch51 = (
    '<div type="chapter" n="51">\n'
    '  <head>Volume I, Part Three, Chapter VI</head>\n'
    '  <div type="version" xml:lang="en" subtype="translation">\n'
    + en_paras
    + '  </div>\n'
    '</div>'
)

new_es_ch51 = (
    '<div type="chapter" n="51">\n'
    '  <head>Volume I, Part Three, Chapter VI</head>\n'
    '  <div type="version" xml:lang="es" subtype="translation-es">\n'
    + es_paras
    + '  </div>\n'
    '</div>'
)

print('Replacing EN ch.51...')
replace_chapter(EN_FILE, new_en_ch51, 51)

print('Replacing ES ch.51...')
replace_chapter(ES_FILE, new_es_ch51, 51)

print('Done.')
