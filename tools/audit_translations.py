import xml.etree.ElementTree as ET
import sys
import os

NS = {
    'tei': 'http://www.tei-c.org/ns/1.0',
    'xml': 'http://www.w3.org/XML/1998/namespace'
}
def get_chapter_stats(filepath):
    stats = {}
    try:
        tree = ET.parse(filepath)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return stats
    
    root = tree.getroot()
    # Find all chapters
    for chapter in root.findall('.//tei:div[@type="chapter"]', NS):
        chap_n = chapter.get('n')
        if not chap_n:
            continue
        
        # Count foreign fr tags
        foreign_tags = chapter.findall('.//tei:foreign[@xml:lang="fr"]', NS)
        # also check if the xml:lang without namespace is used just in case
        foreign_tags += chapter.findall('.//tei:foreign[@{http://www.w3.org/XML/1998/namespace}lang="fr"]', NS)
        
        # Extract text to check for quotes
        text_content = "".join(chapter.itertext())
        has_quotes = '"' in text_content or '“' in text_content or '”' in text_content
        
        # Count paragraphs as a length check
        p_count = len(chapter.findall('.//tei:p', NS))
        
        stats[chap_n] = {
            'foreign_fr_count': len(foreign_tags),
            'has_quotes': has_quotes,
            'p_count': p_count
        }
    return stats

def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ru_file = os.path.join(repo_root, 'tei-source', '2600-ru.xml')
    en_file = os.path.join(repo_root, 'tei-source', '2600-en.xml')
    es_file = os.path.join(repo_root, 'tei-source', '2600-es.xml')
    
    print("Loading Russian Original Stats...")
    ru_stats = get_chapter_stats(ru_file)
    
    for lang_file in [en_file, es_file]:
        lang = os.path.basename(lang_file).replace('2600-', '').replace('.xml', '')
        print(f"\n--- Auditing {lang.upper()} Translations ---")
        stats = get_chapter_stats(lang_file)
        
        flagged_chapters = []
        for chap_n, data in stats.items():
            if chap_n not in ru_stats:
                continue
            
            ru_data = ru_stats[chap_n]
            issues = []
            
            # 1. Missing French Tags
            if ru_data['foreign_fr_count'] > 0 and data['foreign_fr_count'] < ru_data['foreign_fr_count']:
                issues.append(f"Missing <foreign xml:lang='fr'> tags. Expected {ru_data['foreign_fr_count']}, found {data['foreign_fr_count']}")
                
            # 2. Quotation Marks
            if data['has_quotes']:
                issues.append("Contains forbidden quotation marks (should use em-dash)")
                
            # 3. Paragraph Count Mismatch (loose heuristic)
            if abs(ru_data['p_count'] - data['p_count']) > max(2, ru_data['p_count'] * 0.1):
                issues.append(f"Paragraph count mismatch. RU: {ru_data['p_count']}, {lang.upper()}: {data['p_count']}")
                
            if issues:
                flagged_chapters.append((chap_n, issues))
                
        if not flagged_chapters:
            print("No issues found! All chapters look clean.")
        else:
            print(f"Found {len(flagged_chapters)} shoddy chapters:")
            for chap_n, issues in flagged_chapters:
                print(f"  Chapter {chap_n}:")
                for issue in issues:
                    print(f"    - {issue}")

if __name__ == '__main__':
    main()
