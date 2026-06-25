"""
Replace curly/smart double quotes with straight double quotes in EN and ES files.

Curly quotes ( U+201C and U+201D ) are the most visible automated-translation
marker. Straight quotes are the correct EN dialogue standard and are also
acceptable for Spanish prose quoting.

Operates at the raw XML text level so no namespace or element logic is needed.
"""
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES = [
    os.path.join(REPO_ROOT, 'tei-source', 'tolstoy-leo_war-and-peace_en.xml'),
    os.path.join(REPO_ROOT, 'tei-source', 'tolstoy-leo_war-and-peace_es.xml'),
]

# Also replace curly single quotes that appear in inner-monologue passages
# (some tools generate ‘ / ’ for apostrophes / single-quote dialogue)
REPLACEMENTS = [
    ('“', '"'),   # " LEFT DOUBLE QUOTATION MARK  -> straight "
    ('”', '"'),   # " RIGHT DOUBLE QUOTATION MARK -> straight "
    ('‘', "'"),   # ' LEFT SINGLE QUOTATION MARK  -> straight '
    ('’', "'"),   # ' RIGHT SINGLE QUOTATION MARK -> straight '
]


def fix_file(path):
    with open(path, encoding='utf-8') as f:
        content = f.read()

    original = content
    for bad, good in REPLACEMENTS:
        content = content.replace(bad, good)

    changed = sum(original.count(bad) for bad, _ in REPLACEMENTS)

    if changed:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        print(f'{os.path.basename(path)}: replaced {changed} curly quote characters')
    else:
        print(f'{os.path.basename(path)}: no curly quotes found')

    return changed


if __name__ == '__main__':
    total = sum(fix_file(p) for p in FILES)
    print(f'\nTotal curly quote characters replaced: {total}')
