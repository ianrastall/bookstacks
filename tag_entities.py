import re
import sys
import os

def tag_entities(filepath, language):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Entities mapping per language
    # We will use regex to find these words and wrap them. 
    # To prevent tagging inside existing tags, we will split by tag first.
    
    entities = {
        'de': {
            r'\bGregor(s)?\b': '#gregor',
            r'\bGrete(s)?\b': '#grete',
            r'\bSchwester(n)?\b': '#grete',
            r'\bVater(s)?\b': '#vater',
            r'\bMutter\b': '#mutter',
            r'\bProkurist(en)?\b': '#prokurist',
            r'\bBedienerin\b': '#bedienerin',
            r'\bZimmerherr(en)?\b': '#zimmerherr1',
            r'\bWohnung\b': '#wohnung',
            r'\bZimmer(s)?\b': '#gregors-zimmer',
            r'\bWohnzimmer(s)?\b': '#wohnzimmer'
        },
        'en': {
            r'\bGregor(\'s)?\b': '#gregor',
            r'\bGrete(\'s)?\b': '#grete',
            r'\bsister(\'s)?\b': '#grete',
            r'\bfather(\'s)?\b': '#vater',
            r'\bmother(\'s)?\b': '#mutter',
            r'\bchief clerk(\'s)?\b': '#prokurist',
            r'\bmaid\b': '#bedienerin',
            r'\blodger(s)?\b': '#zimmerherr1',
            r'\bapartment\b': '#wohnung',
            r'\broom(s)?\b': '#gregors-zimmer',
            r'\bliving room\b': '#wohnzimmer'
        },
        'es': {
            r'\bGregor\b': '#gregor',
            r'\bGrete\b': '#grete',
            r'\bhermana\b': '#grete',
            r'\bpadre\b': '#vater',
            r'\bmadre\b': '#mutter',
            r'\bapoderado\b': '#prokurist',
            r'\bsirvienta\b': '#bedienerin',
            r'\basistenta\b': '#bedienerin',
            r'\binquilino(s)?\b': '#zimmerherr1',
            r'\bapartamento\b': '#wohnung',
            r'\bpiso\b': '#wohnung',
            r'\bhabitación\b': '#gregors-zimmer',
            r'\bsala de estar\b': '#wohnzimmer',
            r'\bsalón\b': '#wohnzimmer'
        },
        'fr': {
            r'\bGregor\b': '#gregor',
            r'\bGrete\b': '#grete',
            r'\bsœur\b': '#grete',
            r'\bsoeur\b': '#grete',
            r'\bpère\b': '#vater',
            r'\bmère\b': '#mutter',
            r'\bfondé de pouvoir\b': '#prokurist',
            r'\bdirecteur\b': '#prokurist',
            r'\bfemme de ménage\b': '#bedienerin',
            r'\bbonne\b': '#bedienerin',
            r'\blocataire(s)?\b': '#zimmerherr1',
            r'\bappartement\b': '#wohnung',
            r'\bchambre\b': '#gregors-zimmer',
            r'\bsalon\b': '#wohnzimmer'
        }
    }
    
    if language not in entities:
        print(f"Language {language} not supported.")
        return
        
    lang_rules = entities[language]
    
    # We only want to tag text inside <div type="chapter">...</div>
    # and specifically inside the <p> tags, avoiding existing <rs> tags.
    
    def replace_in_text(text):
        for pattern, ref_id in lang_rules.items():
            # Ensure we are not matching inside already tagged <rs> elements
            # A simple approach: 
            # find all matches, but ignore them if they are inside a tag.
            # Since we split by tags, `text` contains no tags!
            
            # Use a function to do replacement
            def replacement(match):
                word = match.group(0)
                return f'<rs ref="{ref_id}">{word}</rs>'
            
            # case insensitive? No, keep it case sensitive for proper nouns like Gregor.
            # Actually, father/mother could be lowercase in EN, FR, ES, but capitalized in DE.
            flags = 0 if language == 'de' else re.IGNORECASE
            
            text = re.sub(pattern, replacement, text, flags=flags)
        return text

    parts = re.split(r'(<[^>]+>)', content)
    tagged_parts = []
    
    in_body = False
    
    for p in parts:
        if p.startswith('<') and p.endswith('>'):
            if '<body' in p:
                in_body = True
            elif '</body' in p:
                in_body = False
            tagged_parts.append(p)
        else:
            if in_body and p.strip():
                # We are in the text content
                tagged_parts.append(replace_in_text(p))
            else:
                tagged_parts.append(p)
                
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("".join(tagged_parts))
        
    print(f"Successfully tagged entities in {filepath}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tag_entities.py <filepath> <language_code>")
        sys.exit(1)
    tag_entities(sys.argv[1], sys.argv[2])
