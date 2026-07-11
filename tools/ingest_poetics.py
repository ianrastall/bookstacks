import urllib.request
import re

url = 'https://www.gutenberg.org/cache/epub/6763/pg6763.txt'
html = urllib.request.urlopen(url).read().decode('utf-8')

# Find the start of the text (after the preface)
# Bywater's translation usually starts after the preface, around chapter 1
match = re.search(r'\n1\r?\n', html)
if not match:
    print("Could not find start")
    exit(1)

start_idx = match.start()

# Find the end of the text
end_match = re.search(r'\*\*\* END OF THE PROJECT GUTENBERG', html)
if not end_match:
    print("Could not find end")
    exit(1)

end_idx = end_match.start()

text = html[start_idx:end_idx]

# Split by chapters
chapters = re.split(r'\n(\d+)\r?\n', '\n' + text.strip())

# The first element is empty or whitespace
if chapters[0].strip() == '':
    chapters = chapters[1:]

tei_header = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:lang="en">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Aristotle on the Art of Poetry</title>
        <author>
          <persName>Aristotle<note type="dates">385 BCE-323 BCE</note></persName>
        </author>
      </titleStmt>
      <publicationStmt>
        <publisher>Bookstacks</publisher>
        <availability status="free">
          <p>Source text available under a Creative Commons Attribution-ShareAlike 4.0 International License.</p>
        </availability>
      </publicationStmt>
      <sourceDesc>
        <p>Translated by Ingram Bywater. Sourced from Project Gutenberg.</p>
      </sourceDesc>
    </fileDesc>
    <profileDesc>
      <langUsage>
        <language ident="en">English</language>
      </langUsage>
    </profileDesc>
  </teiHeader>
  <text>
    <body>"""

print(tei_header)

xml_chapters = []
for i in range(0, len(chapters), 2):
    chapter_num = chapters[i]
    chapter_text = chapters[i+1].strip()
    
    # Split chapter text into paragraphs
    paragraphs = re.split(r'\n\s*\n', chapter_text)
    
    p_tags = []
    for p in paragraphs:
        p = p.replace('\r', '').replace('\n', ' ').strip()
        if p:
            # Handle blockquotes or simple formatting if needed, but for now just wrap in p
            p = p.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            p_tags.append(f"        <p>{p}</p>")
    
    chapter_xml = f"""      <div type="chapter" n="{chapter_num}">
        <head>Chapter {chapter_num}</head>
{chr(10).join(p_tags)}
      </div>"""
    xml_chapters.append(chapter_xml)

tei_footer = """    </body>
  </text>
</TEI>
"""

with open('tei-source/aristotle_aristotle-on-the-art-of-poetry_en.xml', 'w', encoding='utf-8') as f:
    f.write(tei_header + '\n')
    f.write('\n'.join(xml_chapters) + '\n')
    f.write(tei_footer)

print("Created tei-source/aristotle_aristotle-on-the-art-of-poetry_en.xml")
