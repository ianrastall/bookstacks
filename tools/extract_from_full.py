"""
Extract EN and ES chapters from 2600-full.xml and rebuild the separate
tolstoy-leo_war-and-peace_en.xml and tolstoy-leo_war-and-peace_es.xml files.

The full file has chapters with nested version divs:
  <div type="chapter" n="X">
    <div type="version" xml:lang="en" subtype="translation">
      <head>...</head>
      <p>...</p>
    </div>
    ...
  </div>

The separate files use a slightly different layout where <head> is promoted
to a direct child of the chapter div:
  <div type="chapter" n="X">
    <head>...</head>
    <div type="version" xml:lang="en" subtype="translation">
      <p>...</p>
    </div>
  </div>

This script reads 2600-full.xml, extracts chapters that have EN or ES
versions, and rebuilds the separate files while preserving the existing
teiHeader from each file.
"""

import xml.etree.ElementTree as ET
import copy
import os
import sys

TEI_NS = 'http://www.tei-c.org/ns/1.0'
XML_NS = 'http://www.w3.org/XML/1998/namespace'

NS = {'tei': TEI_NS}

ET.register_namespace('', TEI_NS)
ET.register_namespace('xml', XML_NS)


def find_version_div(chapter, lang):
    """Return the version div for the given language, or None."""
    for d in chapter.findall(f'{{{TEI_NS}}}div'):
        if (d.get('type') == 'version' and
                d.get(f'{{{XML_NS}}}lang') == lang):
            return d
    return None


def rebuild_chapter_div(chapter, lang):
    """
    Build a chapter div for the separate-file format.

    Promotes <head> from inside the version div to be a direct child of
    the chapter div (before the version div).
    """
    version_div = find_version_div(chapter, lang)
    if version_div is None:
        return None

    new_chapter = ET.Element(f'{{{TEI_NS}}}div')
    new_chapter.set('type', 'chapter')
    n = chapter.get('n')
    if n:
        new_chapter.set('n', n)

    # Pull <head> out of version div if present
    head_elem = version_div.find(f'{{{TEI_NS}}}head')
    if head_elem is not None:
        new_chapter.append(copy.deepcopy(head_elem))

    # Build a clean version div without the head
    new_version = copy.deepcopy(version_div)
    for h in new_version.findall(f'{{{TEI_NS}}}head'):
        new_version.remove(h)
    new_chapter.append(new_version)

    return new_chapter


def extract_body_chapters(full_xml_path, lang):
    """Return a list of rebuilt chapter elements for the given language."""
    tree = ET.parse(full_xml_path)
    root = tree.getroot()
    chapters = []
    for chapter in root.findall(f'.//{{{TEI_NS}}}div[@type="chapter"]'):
        rebuilt = rebuild_chapter_div(chapter, lang)
        if rebuilt is not None:
            chapters.append(rebuilt)
    return chapters


def rebuild_file(template_path, chapters, output_path):
    """
    Rebuild a TEI file by replacing the <body> content with new chapters
    while keeping the original teiHeader intact.
    """
    tree = ET.parse(template_path)
    root = tree.getroot()

    text_elem = root.find(f'{{{TEI_NS}}}text')
    if text_elem is None:
        print(f"  ERROR: <text> element not found in {template_path}")
        return

    body_elem = text_elem.find(f'{{{TEI_NS}}}body')
    if body_elem is None:
        print(f"  ERROR: <body> element not found in {template_path}")
        return

    # Clear existing chapters and replace
    for child in list(body_elem):
        body_elem.remove(child)

    for ch in chapters:
        body_elem.append(ch)

    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    print(f"  Wrote {len(chapters)} chapters to {output_path}")


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_xml = os.path.join(repo_root, 'tei-source', '2600-full.xml')
    en_file = os.path.join(repo_root, 'tei-source', 'tolstoy-leo_war-and-peace_en.xml')
    es_file = os.path.join(repo_root, 'tei-source', 'tolstoy-leo_war-and-peace_es.xml')

    if not os.path.exists(full_xml):
        print(f"ERROR: {full_xml} not found")
        sys.exit(1)

    print(f"Extracting EN chapters from {os.path.basename(full_xml)}...")
    en_chapters = extract_body_chapters(full_xml, 'en')
    print(f"  Found {len(en_chapters)} EN chapters")

    print(f"Extracting ES chapters from {os.path.basename(full_xml)}...")
    es_chapters = extract_body_chapters(full_xml, 'es')
    print(f"  Found {len(es_chapters)} ES chapters")

    print(f"\nRebuilding {os.path.basename(en_file)}...")
    rebuild_file(en_file, en_chapters, en_file)

    print(f"Rebuilding {os.path.basename(es_file)}...")
    rebuild_file(es_file, es_chapters, es_file)

    print("\nDone.")


if __name__ == '__main__':
    main()
