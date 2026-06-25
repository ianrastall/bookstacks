"""
Merge chapters from git history into the current EN and ES files.

The current files already have chapters 1-45, 51-53, 65 from 2600-full.xml
(those are the high-quality translations). This script pulls chapters from
the last complete git snapshot (commit 7243418, before the purge) and adds
any chapters that are missing from the current files.

Priority: current file content wins (keeps 2600-full.xml quality); git fills
in the gaps for chapters not already present.
"""

import xml.etree.ElementTree as ET
import subprocess
import tempfile
import os
import sys

TEI_NS = 'http://www.tei-c.org/ns/1.0'
XML_NS = 'http://www.w3.org/XML/1998/namespace'

ET.register_namespace('', TEI_NS)
ET.register_namespace('xml', XML_NS)

# Commit that had the most complete EN/ES content before the purge
GIT_COMMIT = '7243418'

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_git_file(commit, git_path):
    """Return file contents from a git commit as a string."""
    result = subprocess.run(
        ['git', 'show', f'{commit}:{git_path}'],
        capture_output=True, text=True, encoding='utf-8',
        cwd=REPO_ROOT
    )
    if result.returncode != 0:
        print(f"  ERROR: git show failed for {git_path} at {commit}")
        return None
    return result.stdout


def parse_xml_string(xml_str):
    """Parse an XML string and return the root element."""
    return ET.fromstring(xml_str.encode('utf-8'))


def get_chapters_from_tree(root):
    """Return a dict of chapter_n -> chapter_element from a parsed TEI tree."""
    chapters = {}
    body = root.find(f'.//{{{TEI_NS}}}body')
    if body is None:
        return chapters
    for chapter in body.findall(f'{{{TEI_NS}}}div[@type="chapter"]'):
        n = chapter.get('n')
        if n:
            chapters[n] = chapter
    return chapters


def merge_chapters(current_path, git_chapters):
    """
    Add git_chapters to the current file, skipping any chapter numbers
    already present in the current file.
    """
    tree = ET.parse(current_path)
    root = tree.getroot()

    body = root.find(f'.//{{{TEI_NS}}}body')
    if body is None:
        print(f"  ERROR: <body> not found in {current_path}")
        return 0

    # Collect existing chapter numbers
    existing = set()
    for ch in body.findall(f'{{{TEI_NS}}}div[@type="chapter"]'):
        n = ch.get('n')
        if n:
            existing.add(n)

    # Determine which git chapters are missing
    missing = {n: ch for n, ch in git_chapters.items() if n not in existing}

    if not missing:
        print(f"  No missing chapters to add.")
        return 0

    print(f"  Adding {len(missing)} chapters: {sorted(missing.keys(), key=lambda x: int(x))}")

    # Append missing chapters in numeric order
    for n in sorted(missing.keys(), key=lambda x: int(x)):
        body.append(missing[n])

    tree.write(current_path, encoding='utf-8', xml_declaration=True)
    return len(missing)


def main():
    en_git_path = 'tei-source/2600-en.xml'
    es_git_path = 'tei-source/2600-es.xml'

    en_local = os.path.join(REPO_ROOT, 'tei-source', 'tolstoy-leo_war-and-peace_en.xml')
    es_local = os.path.join(REPO_ROOT, 'tei-source', 'tolstoy-leo_war-and-peace_es.xml')

    print(f"Fetching EN content from git {GIT_COMMIT}...")
    en_str = get_git_file(GIT_COMMIT, en_git_path)
    if not en_str:
        sys.exit(1)

    print(f"Fetching ES content from git {GIT_COMMIT}...")
    es_str = get_git_file(GIT_COMMIT, es_git_path)
    if not es_str:
        sys.exit(1)

    en_root = parse_xml_string(en_str)
    es_root = parse_xml_string(es_str)

    en_git_chapters = get_chapters_from_tree(en_root)
    es_git_chapters = get_chapters_from_tree(es_root)
    print(f"Git EN chapters: {len(en_git_chapters)}, Git ES chapters: {len(es_git_chapters)}")

    print(f"\nMerging EN chapters into {os.path.basename(en_local)}...")
    added_en = merge_chapters(en_local, en_git_chapters)

    print(f"\nMerging ES chapters into {os.path.basename(es_local)}...")
    added_es = merge_chapters(es_local, es_git_chapters)

    print(f"\nDone. Added {added_en} EN chapters, {added_es} ES chapters.")


if __name__ == '__main__':
    main()
