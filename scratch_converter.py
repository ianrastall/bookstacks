import re
import os

input_file = r"C:\Users\Ian\.gemini\antigravity-ide\brain\77c5fd43-6419-4fab-9d89-b3d3b880bcb2\.system_generated\steps\9\content.md"
output_file = r"d:\GitHub\bookstacks\tei-source\22367-de.xml"

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find start and end of actual text
start_idx = 0
for i, line in enumerate(lines):
    if "*** START OF THE PROJECT GUTENBERG" in line:
        start_idx = i + 1
        break

end_idx = len(lines)
for i, line in enumerate(lines):
    if "*** END OF THE PROJECT GUTENBERG" in line:
        end_idx = i
        break

content_lines = lines[start_idx:end_idx]

# Extract chapters
chapters = []
current_chapter_num = 0
current_chapter_text = []

# Find I., II., III.
for line in content_lines:
    stripped = line.strip()
    if stripped in ["I.", "II.", "III."]:
        if current_chapter_num > 0:
            chapters.append((current_chapter_num, current_chapter_text))
        current_chapter_num += 1
        current_chapter_text = []
    else:
        if current_chapter_num > 0:
            current_chapter_text.append(line)

if current_chapter_num > 0:
    chapters.append((current_chapter_num, current_chapter_text))

tei_header = """<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:lang="de">
	<teiHeader>
		<fileDesc>
			<titleStmt>
				<title>Die Verwandlung</title>
				<author>
					<persName>Franz Kafka</persName>
				</author>
			</titleStmt>
			<publicationStmt>
				<availability status="free">
					<p>This work is in the public domain.</p>
				</availability>
			</publicationStmt>
			<sourceDesc>
				<bibl>Digital source text from Project Gutenberg: <ref target="https://www.gutenberg.org/ebooks/22367">https://www.gutenberg.org/ebooks/22367</ref></bibl>
			</sourceDesc>
		</fileDesc>
		<profileDesc>
			<langUsage>
				<language ident="de">German</language>
			</langUsage>
			<particDesc>
				<listPerson>
					<person xml:id="gregor" sex="M">
						<persName>Gregor Samsa</persName>
						<note>Der Sohn, der sich in ein Ungeziefer verwandelt.</note>
					</person>
					<person xml:id="grete" sex="F">
						<persName>Grete Samsa</persName>
						<note>Gregors Schwester.</note>
					</person>
					<person xml:id="vater" sex="M">
						<persName>Herr Samsa</persName>
						<note>Gregors Vater.</note>
					</person>
					<person xml:id="mutter" sex="F">
						<persName>Frau Samsa</persName>
						<note>Gregors Mutter.</note>
					</person>
					<person xml:id="prokurist" sex="M">
						<persName>Der Prokurist</persName>
						<note>Gregors Vorgesetzter.</note>
					</person>
					<person xml:id="bedienerin" sex="F">
						<persName>Die Bedienerin</persName>
						<note>Die alte Witwe, die bei den Samsas aushilft.</note>
					</person>
					<person xml:id="zimmerherr1" sex="M">
						<persName>Zimmerherr</persName>
						<note>Einer der drei Zimmerherren.</note>
					</person>
				</listPerson>
			</particDesc>
			<settingDesc>
				<listPlace>
					<place xml:id="wohnung">
						<placeName>Die Wohnung der Familie Samsa</placeName>
					</place>
					<place xml:id="gregors-zimmer">
						<placeName>Gregors Zimmer</placeName>
					</place>
					<place xml:id="wohnzimmer">
						<placeName>Das Wohnzimmer</placeName>
					</place>
				</listPlace>
			</settingDesc>
		</profileDesc>
	</teiHeader>
	<text>
		<body>"""

def process_chapter_text(lines):
    # Join lines, separate by blank lines to form paragraphs
    text = "".join(lines)
    paragraphs = re.split(r'\n\s*\n', text)
    xml_paras = []
    for p in paragraphs:
        p = p.strip()
        if not p: continue
        # Escape XML chars
        p = p.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # Replace newlines with spaces within paragraph for clean TEI
        p = " ".join(p.split())
        
        # Simple inline markup logic could be added here, e.g. for French/dialogue
        # But we'll keep it basic for now
        xml_paras.append(f'\t\t\t\t<p>{p}</p>')
    return "\n".join(xml_paras)

xml_chapters = []
for chap_num, chap_lines in chapters:
    chap_xml = f'\n\t\t\t<div type="chapter" n="{chap_num}">\n\t\t\t\t<head>Kapitel {chap_num}</head>\n'
    chap_xml += process_chapter_text(chap_lines)
    chap_xml += '\n\t\t\t</div>'
    xml_chapters.append(chap_xml)

tei_footer = """
		</body>
	</text>
</TEI>
"""

with open(output_file, "w", encoding="utf-8") as f:
    f.write(tei_header)
    for c in xml_chapters:
        f.write(c)
    f.write(tei_footer)

print(f"Successfully wrote TEI XML to {output_file}")
