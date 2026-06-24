import re
import time
from deep_translator import GoogleTranslator
import sys

def translate_html_aware(text, target_lang):
    # Split text into tags and non-tags
    parts = re.split(r'(<[^>]+>)', text)
    translator = GoogleTranslator(source='de', target=target_lang)
    
    translated_parts = []
    for p in parts:
        if p.startswith('<') and p.endswith('>'):
            translated_parts.append(p)
        else:
            if not p.strip():
                translated_parts.append(p)
                continue
            
            # translate p
            if len(p) > 4000:
                sentences = re.split(r'(?<=\.) ', p)
                trans_sents = []
                chunk = ""
                for s in sentences:
                    if len(chunk) + len(s) < 4000:
                        chunk += s + " "
                    else:
                        trans_sents.append(translator.translate(chunk.strip()))
                        chunk = s + " "
                        time.sleep(0.5)
                if chunk:
                    trans_sents.append(translator.translate(chunk.strip()))
                translated_p = " ".join(trans_sents)
            else:
                try:
                    translated_p = translator.translate(p)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Error translating: {e}")
                    translated_p = p
            
            # preserve original leading/trailing whitespace
            leading_ws = re.match(r'^\s*', p).group(0)
            trailing_ws = re.search(r'\s*$', p).group(0)
            translated_p = leading_ws + translated_p.strip() + trailing_ws
            translated_parts.append(translated_p)
            
    return "".join(translated_parts)

def translate_file(target_lang):
    print(f"Reading German source file...")
    with open('tei-source/22367-de.xml', 'r', encoding='utf-8') as f:
        de_xml = f.read()

    # We need to preserve the teiHeader
    header_match = re.search(r'(<teiHeader>.*?</teiHeader>)', de_xml, re.DOTALL)
    if not header_match:
        print("Error: Could not find teiHeader")
        sys.exit(1)
    
    tei_header = header_match.group(1)
    # Update lang in header
    tei_header = tei_header.replace('<language ident="de">German</language>', f'<language ident="{target_lang}">Target</language>')

    # Extract chapters
    chapters_matches = re.finditer(r'(<div type="chapter" n="([^"]+)">)(.*?)(</div><!-- end chapter)', de_xml, re.DOTALL)
    
    # If the file doesn't have <!-- end chapter -->, let's just use regex for </div> correctly
    # Actually, the 22367-de.xml does not have end chapter comments.
    chapters = re.split(r'(<div type="chapter" n="[^"]+">)', de_xml)
    
    output_xml = f"<?xml version='1.0' encoding='UTF-8'?>\n<TEI xmlns=\"http://www.tei-c.org/ns/1.0\" xml:lang=\"{target_lang}\">\n"
    output_xml += tei_header + "\n\t<text>\n\t\t<body>\n"

    # Because chapters list splits like: [0] before, [1] div start, [2] body, [3] div start, [4] body
    # Let's extract the actual chapters safely
    chapter_blocks = []
    
    # A safer way to parse chapters:
    # We find all <div type="chapter" ...> until the next <div type="chapter" or </body>
    matches = list(re.finditer(r'<div type="chapter" n="([^"]+)">', de_xml))
    
    for i, match in enumerate(matches):
        start_idx = match.end()
        end_idx = matches[i+1].start() if i+1 < len(matches) else de_xml.find('</body>')
        chapter_content = de_xml[start_idx:end_idx].strip()
        ch_num = match.group(1)
        
        # strip the trailing </div> if it exists at the end
        if chapter_content.endswith('</div>'):
            chapter_content = chapter_content[:-6].strip()
        
        print(f"Translating Chapter {ch_num} to {target_lang}...")
        
        # Extract <head>
        head_match = re.search(r'(<head>.*?</head>)', chapter_content, re.DOTALL)
        if head_match:
            head_str = head_match.group(1)
            body_str = chapter_content.replace(head_str, '').strip()
        else:
            head_str = ''
            body_str = chapter_content
        
        # Translate the body
        translated_body = translate_html_aware(body_str, target_lang)
        
        ch_out = f"\t\t\t<div type=\"chapter\" n=\"{ch_num}\">\n\t\t\t\t{head_str}\n"
        ch_out += f"\t\t\t\t<div type=\"version\" xml:lang=\"{target_lang}\" subtype=\"translation\">\n"
        # Add indentation
        trans_indented = "\n".join(["\t\t\t\t\t" + line for line in translated_body.split('\n')])
        ch_out += f"{trans_indented}\n"
        ch_out += "\t\t\t\t</div>\n\t\t\t</div>\n"
        
        output_xml += ch_out

    output_xml += "\t\t</body>\n\t</text>\n</TEI>"
    
    output_filename = f'tei-source/22367-{target_lang}.xml'
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(output_xml)
        
    print(f"Successfully wrote {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python translate_metamorphosis.py <target_lang>")
        sys.exit(1)
    translate_file(sys.argv[1])
