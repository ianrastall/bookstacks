import os
import re

def preview_typography(directory):
    dash_count = 0
    ellipsis_count = 0
    underscore_count = 0
    
    # Regex to match XML tags so we can ignore them, and match text separately
    # This splits the text into tokens of either a tag or text
    token_re = re.compile(r'(<[^>]+>)|([^<]+)')
    
    for filename in os.listdir(directory):
        if not filename.endswith('.xml'):
            continue
            
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = []
        for match in token_re.finditer(content):
            tag = match.group(1)
            text = match.group(2)
            
            if tag:
                # keep tags unchanged
                pass
            elif text:
                # Check for replacements in text
                dashes = len(re.findall(r'(?<!-)--(?!-)', text))
                if dashes > 0:
                    dash_count += dashes
                    
                ellipses = len(re.findall(r'\.\.\.', text))
                if ellipses > 0:
                    ellipsis_count += ellipses
                    
                # For words offset by underscores, like _word_ or _several words_
                # We need to make sure we don't match inside URLs or words like some_variable_name
                # Usually it is \b_([^_]+)_\b
                # Let's match space or punctuation before/after
                underscores = len(re.findall(r'(^|\W)_([^_]+)_(\W|$)', text))
                if underscores > 0:
                    underscore_count += underscores
                    
    print(f"Found {dash_count} instances of '--'")
    print(f"Found {ellipsis_count} instances of '...'")
    print(f"Found {underscore_count} instances of '_word_'")

if __name__ == '__main__':
    preview_typography('tei-source')
