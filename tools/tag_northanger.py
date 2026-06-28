import re
import os

FILE_PATH = 'tei-source/austen-jane_northanger-abbey_en.xml'

def main():
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    body_start = content.find('<body>')
    if body_start == -1:
        print("Could not find <body>")
        return
        
    header = content[:body_start]
    body = content[body_start:]

    # Map of plain text -> tagged text
    # Order is extremely important: longer phrases must come first to prevent partial matches.
    replacements = {
        r'\bCaptain Frederick Tilney\b': '<persName ref="#frederick-tilney">Captain Frederick Tilney</persName>',
        r'\bCatherine Morland\b': '<persName ref="#catherine">Catherine Morland</persName>',
        r'\bGeneral Tilney\b': '<persName ref="#general-tilney">General Tilney</persName>',
        r'\bIsabella Thorpe\b': '<persName ref="#isabella-thorpe">Isabella Thorpe</persName>',
        r'\bEleanor Tilney\b': '<persName ref="#eleanor-tilney">Eleanor Tilney</persName>',
        r'\bCaptain Tilney\b': '<persName ref="#frederick-tilney">Captain Tilney</persName>',
        r'\bFrederick Tilney\b': '<persName ref="#frederick-tilney">Frederick Tilney</persName>',
        r'\bNorthanger Abbey\b': '<placeName ref="#northanger-abbey">Northanger Abbey</placeName>',
        r'\bJames Morland\b': '<persName ref="#james-morland">James Morland</persName>',
        r'\bPulteney Street\b': '<placeName ref="#pulteney-street">Pulteney Street</placeName>',
        r'\bBlaize Castle\b': '<placeName ref="#blaize-castle">Blaize Castle</placeName>',
        r'\bMiss Morland\b': '<persName ref="#catherine">Miss Morland</persName>',
        r'\bHenry Tilney\b': '<persName ref="#henry-tilney">Henry Tilney</persName>',
        r'\bJohn Thorpe\b': '<persName ref="#john-thorpe">John Thorpe</persName>',
        r'\bMrs\. Morland\b': '<persName ref="#mrs-morland">Mrs. Morland</persName>',
        r'\bMr\. Morland\b': '<persName ref="#mr-morland">Mr. Morland</persName>',
        r'\bMiss Tilney\b': '<persName ref="#eleanor-tilney">Miss Tilney</persName>',
        r'\bMr\. Tilney\b': '<persName ref="#henry-tilney">Mr. Tilney</persName>',
        r'\bMiss Thorpe\b': '<persName ref="#isabella-thorpe">Miss Thorpe</persName>',
        r'\bMr\. Thorpe\b': '<persName ref="#john-thorpe">Mr. Thorpe</persName>',
        r'\bMrs\. Thorpe\b': '<persName ref="#mrs-thorpe">Mrs. Thorpe</persName>',
        r'\bMrs\. Allen\b': '<persName ref="#mrs-allen">Mrs. Allen</persName>',
        r'\bMr\. Allen\b': '<persName ref="#mr-allen">Mr. Allen</persName>',
        r'\bGloucestershire\b': '<placeName ref="#gloucestershire">Gloucestershire</placeName>',
        r'\bNorthanger\b': '<placeName ref="#northanger-abbey">Northanger</placeName>',
        r'\bFullerton\b': '<placeName ref="#fullerton">Fullerton</placeName>',
        r'\bCatherine\b': '<persName ref="#catherine">Catherine</persName>',
        r'\bWiltshire\b': '<placeName ref="#wiltshire">Wiltshire</placeName>',
        r'\bIsabella\b': '<persName ref="#isabella-thorpe">Isabella</persName>',
        r'\bEleanor\b': '<persName ref="#eleanor-tilney">Eleanor</persName>',
        r'\bWoodston\b': '<placeName ref="#woodston">Woodston</placeName>',
        r'\bBristol\b': '<placeName ref="#bristol">Bristol</placeName>',
        r'\bLondon\b': '<placeName ref="#london">London</placeName>',
        r'\bOxford\b': '<placeName ref="#oxford">Oxford</placeName>',
        r'\bJames\b': '<persName ref="#james-morland">James</persName>',
        r'\bHenry\b': '<persName ref="#henry-tilney">Henry</persName>',
        r'\bBath\b': '<placeName ref="#bath">Bath</placeName>',
        r'\bJohn\b': '<persName ref="#john-thorpe">John</persName>',
    }

    # Compile a single regex that matches any of the keys
    pattern = re.compile('|'.join(f'({k})' for k in replacements.keys()))
    
    # We will build a function to replace a match with its corresponding value
    def replacer(match):
        matched_str = match.group(0)
        # Find which key matched
        for k, v in replacements.items():
            if re.match(k, matched_str):
                return v
        return matched_str

    # Tokenize the body to separate XML tags from text
    # <[^>]+> matches any XML tag
    tokens = re.split(r'(<[^>]+>)', body)
    
    new_tokens = []
    for i, token in enumerate(tokens):
        if i % 2 == 0:
            # It's a text node. Apply replacements.
            new_token = pattern.sub(replacer, token)
            new_tokens.append(new_token)
        else:
            # It's an XML tag. Leave it alone.
            new_tokens.append(token)
            
    new_body = ''.join(new_tokens)
    
    new_content = header + new_body
    
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("Tagging complete. Modifed file saved.")

if __name__ == '__main__':
    main()
