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
        print('Error parsing ' + filepath + ': ' + str(e))
        return stats

    root = tree.getroot()
    for chapter in root.findall('.//tei:div[@type="chapter"]', NS):
        chap_n = chapter.get('n')
        if not chap_n:
            continue

        foreign_tags = chapter.findall('.//tei:foreign[@xml:lang="fr"]', NS)
        foreign_tags += chapter.findall(
            './/tei:foreign[@{http://www.w3.org/XML/1998/namespace}lang="fr"]', NS)

        text_content = ''.join(chapter.itertext())
        # Curly/smart quotes: quality flag for all languages (automated translation marker)
        has_curly_quotes = ('“' in text_content or '”' in text_content)
        # Straight double quote: expected in EN dialogue, wrong in ES (should be em-dash)
        has_straight_quotes = ('"' in text_content)

        # Count <p> elements plus <l> verse-line elements so that chapters
        # whose EN uses <lg>/<l> verse markup (instead of <p>) are not
        # flagged as truncated due to the different element type.
        p_count = len(chapter.findall('.//tei:p', NS))
        l_count = len(chapter.findall('.//tei:l', NS))
        content_count = p_count + l_count

        stats[chap_n] = {
            'foreign_fr_count': len(foreign_tags),
            'has_curly_quotes': has_curly_quotes,
            'has_straight_quotes': has_straight_quotes,
            'p_count': content_count
        }
    return stats


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ru_file = os.path.join(repo_root, 'tei-source', 'tolstoy-leo_war-and-peace_ru.xml')
    en_file = os.path.join(repo_root, 'tei-source', 'tolstoy-leo_war-and-peace_en.xml')
    es_file = os.path.join(repo_root, 'tei-source', 'tolstoy-leo_war-and-peace_es.xml')

    print('Loading Russian Original Stats...')
    ru_stats = get_chapter_stats(ru_file)

    for lang_file in [en_file, es_file]:
        lang = os.path.basename(lang_file).rsplit('_', 1)[-1].replace('.xml', '')
        print('\n--- Auditing ' + lang.upper() + ' Translations ---')
        stats = get_chapter_stats(lang_file)

        flagged_chapters = []
        for chap_n, data in stats.items():
            if chap_n not in ru_stats:
                continue

            ru_data = ru_stats[chap_n]
            issues = []

            # 1. Missing French tags
            if ru_data['foreign_fr_count'] > 0 and data['foreign_fr_count'] < ru_data['foreign_fr_count']:
                issues.append(
                    'Missing <foreign xml:lang=\'fr\'> tags. Expected '
                    + str(ru_data['foreign_fr_count'])
                    + ', found ' + str(data['foreign_fr_count']))

            # 2. Quote style checks (language-aware)
            if data['has_curly_quotes']:
                issues.append('Contains curly/smart quotes (automated translation marker)')
            if lang == 'es' and data['has_straight_quotes']:
                issues.append('Contains straight double quotes (ES dialogue should use em-dash)')

            # 3. Paragraph count mismatch
            if abs(ru_data['p_count'] - data['p_count']) > max(2, ru_data['p_count'] * 0.1):
                issues.append(
                    'Paragraph count mismatch. RU: ' + str(ru_data['p_count'])
                    + ', ' + lang.upper() + ': ' + str(data['p_count']))

            if issues:
                flagged_chapters.append((chap_n, issues))

        if not flagged_chapters:
            print('No issues found! All chapters look clean.')
        else:
            print('Found ' + str(len(flagged_chapters)) + ' chapters with issues:')
            for chap_n, issues in flagged_chapters:
                print('  Chapter ' + chap_n + ':')
                for issue in issues:
                    print('    - ' + issue)


if __name__ == '__main__':
    main()
