import re

with open('tei-source/2600-full.xml', 'r', encoding='utf-8') as f:
    text = f.read()

def repl(m):
    n = m.group(1)
    head_text = m.group(2)
    ru_head = head_text.replace('Volume ', 'Том ')
    ru_head = ru_head.replace('Part One', 'часть первая')
    ru_head = ru_head.replace('Part Two', 'часть вторая')
    ru_head = ru_head.replace('Part Three', 'часть третья')
    ru_head = ru_head.replace('Chapter ', 'глава ')
    
    return f'<div type="chapter" n="{n}">\n\t\t\t\t<div type="version" xml:lang="ru" subtype="original">\n\t\t\t\t\t<head>{ru_head}</head>'

# Only match chapters that have <head> immediately followed by <div type=\"version\" xml:lang=\"ru\"
new_text = re.sub(r'<div type="chapter" n="(\d+)">\n\s*<head>(.*?)</head>\n\s*<div type="version" xml:lang="ru" subtype="original">', repl, text)

# For Chapter 1, we must manually move its <head> into English and Russian
# Because chapter 1 looks like:
# <div type="chapter" n="1">
#   <head>Book One, Chapter I</head>
#   <div type="version" xml:lang="en" subtype="translation">
#      <p>...

def repl_ch1(m):
    return '''<div type="chapter" n="1">
				<div type="version" xml:lang="en" subtype="translation">
					<head>Book One, Chapter I</head>'''

new_text = re.sub(r'<div type="chapter" n="1">\n\s*<head>Book One, Chapter I</head>\n\s*<div type="version" xml:lang="en" subtype="translation">', repl_ch1, new_text)

# Also for chapter 1, add Spanish version right before the English version or after the Russian version. The user said: "get all three tabs going".
# Wait, let's just make the Spanish version by translating the English text and prepend it. Or append it. 
# We'll just do the head fixing first.

with open('tei-source/2600-full.xml', 'w', encoding='utf-8') as f:
    f.write(new_text)
