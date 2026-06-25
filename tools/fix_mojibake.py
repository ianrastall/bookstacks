"""
Fix CP437 mojibake in the Russian original sections of 2600-full.xml.

What happened: Cyrillic UTF-8 bytes (e.g. D0 9D D0 B0 = "На") were
passed through a CP437 decoder (0xD0 → ╨, 0x9D → ¥, 0xD0 → ╨, 0xB0 → ░)
and then stored as UTF-8. The result is "╨¥╨░" where "На" should be.

Fix: encode each corrupted Unicode character back to its CP437 byte value;
those bytes are the original UTF-8; decode as UTF-8.

Only the xml:lang="ru" version divs are processed — EN/ES text is untouched.
"""

import xml.etree.ElementTree as ET
import os
import sys

TEI_NS = 'http://www.tei-c.org/ns/1.0'
XML_NS  = 'http://www.w3.org/XML/1998/namespace'

ET.register_namespace('', TEI_NS)
ET.register_namespace('xml', XML_NS)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fix_text(text):
    """Try to reverse CP437 mojibake. Return fixed text, or original if it fails."""
    if not text:
        return text
    try:
        fixed = text.encode('cp437').decode('utf-8')
        # Sanity: if fix produced Cyrillic where there was none, it's real.
        # If it produced the same string (pure ASCII), that's fine too.
        return fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def fix_element(elem):
    """Recursively fix all text content in an element and its descendants."""
    if elem.text:
        elem.text = fix_text(elem.text)
    if elem.tail:
        elem.tail = fix_text(elem.tail)
    for child in elem:
        fix_element(child)


def main():
    full_xml = os.path.join(REPO_ROOT, 'tei-source', '2600-full.xml')

    print(f"Parsing {os.path.basename(full_xml)}...")
    tree = ET.parse(full_xml)
    root = tree.getroot()

    # Fix all xml:lang="ru" version divs
    fixed_count = 0
    for div in root.findall(f'.//{{{TEI_NS}}}div[@type="version"]'):
        if div.get(f'{{{XML_NS}}}lang') == 'ru':
            fix_element(div)
            fixed_count += 1

    print(f"Fixed {fixed_count} Russian version divs.")

    tree.write(full_xml, encoding='UTF-8', xml_declaration=True)
    print(f"Saved {os.path.basename(full_xml)}.")

    # Write a sample of the fixed text to a file for verification
    verify_path = os.path.join(REPO_ROOT, 'tools', '_mojibake_fix_sample.txt')
    with open(verify_path, 'w', encoding='utf-8') as vf:
        for div in root.findall(f'.//{{{TEI_NS}}}div[@type="version"]'):
            if div.get(f'{{{XML_NS}}}lang') == 'ru':
                sample = "".join(div.itertext())[:200].strip()
                has_cyr = any('Ѐ' <= c <= 'ӿ' for c in sample)
                if has_cyr:
                    vf.write(sample[:120] + "\n---\n")
                    break
    print(f"Sample written to {verify_path}")


if __name__ == '__main__':
    main()
