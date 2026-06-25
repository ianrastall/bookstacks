import xml.etree.ElementTree as ET
import os

NS = {
    'tei': 'http://www.tei-c.org/ns/1.0',
    'xml': 'http://www.w3.org/XML/1998/namespace'
}

def register_all_namespaces(filepath):
    # Hack to keep namespaces standard when writing
    ET.register_namespace('', 'http://www.tei-c.org/ns/1.0')
    ET.register_namespace('xml', 'http://www.w3.org/XML/1998/namespace')

def get_chapter_stats(root):
    stats = {}
    for chapter in root.findall('.//tei:div[@type="chapter"]', NS):
        chap_n = chapter.get('n')
        if not chap_n:
            continue
        
        foreign_tags = chapter.findall('.//tei:foreign[@xml:lang=”fr”]', NS)
        foreign_tags += chapter.findall('.//tei:foreign[@{http://www.w3.org/XML/1998/namespace}lang=”fr”]', NS)

        text_content = “”.join(chapter.itertext())
        has_curly_quotes = '”' in text_content or '”' in text_content
        has_straight_quotes = '”' in text_content
        p_count = len(chapter.findall('.//tei:p', NS))

        stats[chap_n] = {
            'foreign_fr_count': len(foreign_tags),
            'has_curly_quotes': has_curly_quotes,
            'has_straight_quotes': has_straight_quotes,
            'p_count': p_count
        }
    return stats

def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ru_file = os.path.join(repo_root, 'tei-source', 'tolstoy-leo_war-and-peace_ru.xml')
    en_file = os.path.join(repo_root, 'tei-source', 'tolstoy-leo_war-and-peace_en.xml')
    es_file = os.path.join(repo_root, 'tei-source', 'tolstoy-leo_war-and-peace_es.xml')
    
    register_all_namespaces(ru_file)
    ru_tree = ET.parse(ru_file)
    ru_stats = get_chapter_stats(ru_tree.getroot())
    
    for lang_file in [en_file, es_file]:
        print(f"Purging {lang_file}...")
        tree = ET.parse(lang_file)
        root = tree.getroot()
        stats = get_chapter_stats(root)
        
        body = root.find('.//tei:body', NS)
        chapters = list(body.findall('tei:div[@type="chapter"]', NS))
        
        lang = os.path.basename(lang_file).rsplit('_', 1)[-1].replace('.xml', '')
        removed_count = 0
        for chapter in chapters:
            chap_n = chapter.get('n')
            if chap_n not in ru_stats:
                continue

            ru_data = ru_stats[chap_n]
            data = stats[chap_n]

            is_shoddy = False
            if ru_data['foreign_fr_count'] > 0 and data['foreign_fr_count'] < ru_data['foreign_fr_count']:
                is_shoddy = True
            # Curly quotes are a quality flag for all languages
            if data['has_curly_quotes']:
                is_shoddy = True
            # Straight double quotes are wrong for ES dialogue (should be em-dash)
            if lang == 'es' and data['has_straight_quotes']:
                is_shoddy = True
            if abs(ru_data['p_count'] - data['p_count']) > max(2, ru_data['p_count'] * 0.1):
                is_shoddy = True
                
            if is_shoddy:
                # Remove the chapter completely from the translation file
                body.remove(chapter)
                removed_count += 1
                
        print(f"Removed {removed_count} shoddy chapters from {lang_file}")
        
        # Save the file back
        tree.write(lang_file, encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    main()
