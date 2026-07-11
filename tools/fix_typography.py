import os
import re

def fix_typography(directory):
    token_re = re.compile(r'(<[^>]+>)|([^<]+)')
    
    files_modified = 0
    
    for filename in os.listdir(directory):
        if not filename.endswith('.xml'):
            continue
            
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content_parts = []
        changed = False
        
        for match in token_re.finditer(content):
            tag = match.group(1)
            text = match.group(2)
            
            if tag:
                new_content_parts.append(tag)
            elif text:
                new_text = text
                
                # Replace the broken entities we introduced previously
                if '&mdash;' in new_text:
                    new_text = new_text.replace('&mdash;', '—')
                if '&hellip;' in new_text:
                    new_text = new_text.replace('&hellip;', '…')
                
                # Also replace any remaining plain text versions
                if re.search(r'(?<!-)--(?!-)', new_text):
                    new_text = re.sub(r'(?<!-)--(?!-)', '—', new_text)
                    
                if '...' in new_text:
                    new_text = new_text.replace('...', '…')
                    
                # Replace _words_ with <emph>words</emph>
                if re.search(r'(?<![a-zA-Z0-9_])_([^_\n]+)_(?![a-zA-Z0-9_])', new_text):
                    new_text = re.sub(r'(?<![a-zA-Z0-9_])_([^_\n]+)_(?![a-zA-Z0-9_])', r'<emph>\1</emph>', new_text)
                    
                if new_text != text:
                    changed = True
                    
                new_content_parts.append(new_text)
                
        if changed:
            new_content = ''.join(new_content_parts)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            files_modified += 1

    print(f"Fixed typography in {files_modified} files.")

if __name__ == '__main__':
    fix_typography('tei-source')
