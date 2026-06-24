import re
import time
from deep_translator import GoogleTranslator

def translate_html_aware(text, target_lang):
    tags = []
    
    def tag_replacer(match):
        tags.append(match.group(0))
        return f"__TAG{len(tags)-1}__"

    # Replace XML tags with placeholders
    ph_text = re.sub(r'<[^>]+>', tag_replacer, text)
    
    paragraphs = ph_text.split('\n')
    translated_paragraphs = []
    translator = GoogleTranslator(source='ru', target=target_lang)
    
    for p in paragraphs:
        if not p.strip():
            translated_paragraphs.append(p)
            continue
        
        # split long paragraphs if needed (Google Translate limit is 5000 chars)
        if len(p) > 4000:
            # simple split by sentences
            sentences = re.split(r'(?<=\.) ', p)
            trans_sents = []
            chunk = ""
            for s in sentences:
                if len(chunk) + len(s) < 4000:
                    chunk += s + " "
                else:
                    trans_sents.append(translator.translate(chunk.strip()))
                    chunk = s + " "
                    time.sleep(1)
            if chunk:
                trans_sents.append(translator.translate(chunk.strip()))
            translated_p = " ".join(trans_sents)
        else:
            try:
                translated_p = translator.translate(p)
                time.sleep(1) # rate limit prevention
            except Exception as e:
                print(f"Error translating: {e}")
                translated_p = p
        
        translated_paragraphs.append(translated_p)
        
    translated_text = '\n'.join(translated_paragraphs)
    
    # Put tags back
    # Google Translate often adds spaces around punctuation/digits, e.g. "__TAG 0 __"
    # We use regex to find and replace them safely
    for i, tag in enumerate(tags):
        pattern = re.compile(rf"__\s*TAG\s*{i}\s*__", re.IGNORECASE)
        translated_text = pattern.sub(tag, translated_text)
        
    return translated_text

with open('chaps_ru.txt', 'r', encoding='utf-8') as f:
    text = f.read()

chapters = re.split(r'--- CHAPTER (\d+) ---', text)[1:]
# chapters is a list: ['88', '\n<head...', '89', '\n<head...']
# We skip 88 because it's already done.

en_appends = []
es_appends = []

for i in range(0, len(chapters), 2):
    ch_num = int(chapters[i])
    if ch_num <= 88:
        continue
        
    ch_content = chapters[i+1].strip()
    
    print(f"Translating Chapter {ch_num}...")
    
    # Extract head and body
    head_match = re.search(r'(<head>.*?</head>)', ch_content, re.DOTALL)
    head_str = head_match.group(1) if head_match else ""
    
    # The body is inside <div type="version"...>...</div>
    body_match = re.search(r'<div type="version"[^>]*>(.*?)</div>', ch_content, re.DOTALL)
    body_str = body_match.group(1).strip() if body_match else ""
    
    # Translate EN
    print("  -> to English")
    en_body = translate_html_aware(body_str, 'en')
    en_full = f"""      <div type="chapter" n="{ch_num}">
        {head_str}
        <div type="version" xml:lang="en" subtype="translation">
          {en_body}
        </div>
      </div>
"""
    en_appends.append(en_full)
    
    # Translate ES
    print("  -> to Spanish")
    es_body = translate_html_aware(body_str, 'es')
    es_full = f"""      <div type="chapter" n="{ch_num}">
        {head_str}
        <div type="version" xml:lang="es" subtype="translation">
          {es_body}
        </div>
      </div>
"""
    es_appends.append(es_full)

print("Appending to files...")

# English
with open("tei-source/2600-en.xml", "r", encoding="utf-8") as f:
    en_xml = f.read()
en_xml = en_xml.replace("    </body>\n  </text>\n</TEI>", "\n".join(en_appends) + "    </body>\n  </text>\n</TEI>")
with open("tei-source/2600-en.xml", "w", encoding="utf-8") as f:
    f.write(en_xml)

# Spanish
with open("tei-source/2600-es.xml", "r", encoding="utf-8") as f:
    es_xml = f.read()
es_xml = es_xml.replace("    </body>\n  </text>\n</TEI>", "\n".join(es_appends) + "    </body>\n  </text>\n</TEI>")
with open("tei-source/2600-es.xml", "w", encoding="utf-8") as f:
    f.write(es_xml)

print("Done.")
