"""Prepare the reviewed Holmes manifest from local reference HTML snapshots.

Read assets/source-holmes/{publication,William_Stuart_Baring-Gould,
The_Field_Bazaar,How_Watson_Learned_the_Trick}.html. This explicit editorial
step is separate from site builds and does not fetch sources or create PDFs.
"""
from pathlib import Path
from lxml import etree, html
import hashlib, json, re, difflib, unicodedata
from datetime import date as calendar_date

ROOT=Path(__file__).resolve().parents[1]
NS={'t':'http://www.tei-c.org/ns/1.0'}
X='{http://www.w3.org/XML/1998/namespace}'
def norm(s): return ' '.join(s.split())
def key(s):
 s=s.split(":",1)[0]
 s=unicodedata.normalize('NFKD',s).lower().replace('’',"'")
 s=re.sub(r'^(adventures of sherlock holmes )?adventure [ivxlc]+ ', '',s)
 s=re.sub(r'^[ivxlc]+\. ', '',s)
 s=re.sub(r'^the (adventure of |problem of )?', '',s)
 return re.sub(r'[^a-z0-9]','',s).replace('squires','squire').replace('signofthefour','signoffour')
def slug(s): return re.sub('[^a-z0-9]+','-',s.lower().replace('’',"'").replace("'",'')).strip('-')
months={m:i+1 for i,m in enumerate('january february march april may june july august september october november december'.split())}
def date(s):
 p=s.lower().split()
 if not p or not p[-1].isdigit(): return None
 if len(p)==1:return p[0]
 result=f'{p[-1]}-{months[p[-2]]:02}'+(f'-{int(p[0]):02}' if len(p)==3 else '')
 calendar_date.fromisoformat(result if len(p)==3 else result+'-01')
 return result
publication=html.parse(str(ROOT/'assets/source-holmes/publication.html'))
stories=[]
for tr in publication.xpath('//tr'):
 cells=tr.xpath('./td')
 if len(cells)!=4 or not norm(cells[0].text_content()).rstrip('.').isdigit():continue
 title=norm(cells[1].text_content()); raw_dates=[norm(c.text_content()) for c in cells[2:]]
 # The summary table prints the impossible date 31 September. The dedicated
 # story page's Collier's illustration caption identifies 31 December 1904.
 if title=='The Adventure of the Abbey Grange':raw_dates[1]='31 december 1904'
 dates=[date(value) for value in raw_dates]
 stories.append(dict(title=title,slug=slug(title),publication=min(d for d in dates if d),publicationUK=dates[0],publicationUS=dates[1]))
 if title=='The Adventure of the Abbey Grange':stories[-1]['publicationUSSource']='https://www.arthur-conan-doyle.com/wiki/The_Adventure_of_the_Abbey_Grange#Illustrations'
assert len(stories)==62
chron=html.parse(str(ROOT/'assets/source-holmes/William_Stuart_Baring-Gould.html'))
chronology={}
code_titles=dict(zip('GLOR MUSG STUD SPEC RESI NOBL SECO REIG SCAN TWIS FIVE IDEN REDH DYIN BLUE VALL YELL GREE SIGN HOUN COPP BOSC STOC NAVA CARD ENGR CROO WIST SILV BERY FINA EMPT GOLD 3STU SOLI BLAC NORW BRUC VEIL SUSS MISS ABBE DEVI DANC RETI CHAS SIXN THOR PRIO SHOS 3GAR LADY ILLU REDC MAZA BLAN 3GAB CREE LION LAST'.split(), ['Gloria Scott','Musgrave Ritual','A Study in Scarlet','Speckled Band','Resident Patient','Noble Bachelor','Second Stain','Reigate Squire','A Scandal in Bohemia','Man with the Twisted Lip','Five Orange Pips','A Case of Identity','Red-Headed League','Dying Detective','Blue Carbuncle','Valley of Fear','Yellow Face','Greek Interpreter','Sign of Four','Hound of the Baskervilles','Copper Beeches','Boscombe Valley Mystery',"Stockbroker’s Clerk",'Naval Treaty','Cardboard Box',"Engineer’s Thumb",'Crooked Man','Wisteria Lodge','Silver Blaze','Beryl Coronet','Final Problem','Empty House','Golden Pince-Nez','Three Students','Solitary Cyclist','Black Peter','Norwood Builder','Bruce-Partington Plans','Veiled Lodger','Sussex Vampire','Missing Three-Quarter','Abbey Grange',"Devil’s Foot",'Dancing Men','Retired Colourman','Charles Augustus Milverton','Six Napoleons','Thor Bridge','Priory School','Shoscombe Old Place','Three Garridebs','Disappearance of Lady Frances Carfax','Illustrious Client','Red Circle','Mazarin Stone','Blanched Soldier','Three Gables','Creeping Man',"Lion’s Mane",'His Last Bow']))
for li in chron.xpath('//li'):
 s=norm(li.text_content()); a=li.find('a')
 if a is None or not re.match(r'^[A-Z0-9]{4}\s*:',s):continue
 chronology[key(code_titles[a.get('title')])]=date(s.split(':',1)[1].strip())
novels={'a-study-in-scarlet','the-sign-of-the-four','the-hound-of-the-baskervilles','the-valley-of-fear'}
collections={'the-adventures-of-sherlock-holmes','the-memoirs-of-sherlock-holmes','the-return-of-sherlock-holmes','his-last-bow','the-case-book-of-sherlock-holmes'}
sources={}
for f in sorted((ROOT/'tei/doyle').glob('*.xml')):
 work=f.stem[len('doyle_'):-len('_eng')]
 if work not in novels|collections:continue
 doc=etree.parse(str(f)); sources[f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
 divisions=doc.xpath('//t:body/t:div',namespaces=NS) if work in novels else doc.xpath('//t:body/t:div/t:div',namespaces=NS)
 for div in divisions:
  title=norm(doc.xpath('string(//t:titleStmt/t:title[1])',namespaces=NS)) if work in novels else norm(''.join(div.find('t:head',NS).itertext()))
  candidates=sorted(stories,key=lambda s:difflib.SequenceMatcher(None,key(title),key(s['title'])).ratio(),reverse=True)
  story=candidates[0]; score=difflib.SequenceMatcher(None,key(title),key(story['title'])).ratio()
  assert score>.73,(title,story['title'],score)
  if 'source' in story: continue # Cardboard Box occurs in both source collections.
  story.update(source=f.name,sourceId=div.get(X+'id'),kind='novel' if work in novels else 'story')
for s in stories:
 matches=sorted(chronology,key=lambda k:difflib.SequenceMatcher(None,key(s['title']),k).ratio(),reverse=True)
 if s['title']=='The Field Bazaar': s.update(career='1890-01',careerNote='Undated Baker Street vignette; editorial placement during the partnership, before the 1891 hiatus.')
 elif s['title']=='How Watson Learned the Trick':s.update(career='1902-01',careerNote='Undated Baker Street vignette; editorial placement during the later partnership, before retirement.')
 else:
  k=matches[0]; assert difflib.SequenceMatcher(None,key(s['title']),k).ratio()>.73,(s['title'],k)
  s['career']=chronology[k]
 if 'source' not in s:
  source=s['title'].replace(' ','_')+'.html'; raw=(ROOT/'assets/source-holmes'/source).read_bytes()
  d=html.fromstring(raw); heading=d.xpath('//*[@id="Text"]')[0].getparent()
  paragraphs=[]
  for node in heading.itersiblings():
   if node.tag=='hr':break
   if node.tag=='p' and norm(node.text_content()): paragraphs.append(norm(node.text_content()))
  assert len(paragraphs)>15
  s.update(kind='story',paragraphs=paragraphs,sourceUrl='https://www.arthur-conan-doyle.com/wiki/'+source[:-5],sourceSha256=hashlib.sha256(raw).hexdigest())
lost=etree.parse(str(ROOT/'tei/doyle/doyle_tales-of-terror-and-mystery_eng.xml'))
stories.append(dict(title='The Story of the Lost Special',slug='the-story-of-the-lost-special',publication='1898-08',career='1890-06-03',careerNote='Dated by the train disappearance within the story; the later confession is a retrospective frame. The unnamed amateur reasoner is an implied Holmes connection, outside the usual sixty-work canon.',kind='story',source='doyle_tales-of-terror-and-mystery_eng.xml',sourceId='eng-part-02-chapter-001'))
sources['doyle_tales-of-terror-and-mystery_eng.xml']=hashlib.sha256((ROOT/'tei/doyle/doyle_tales-of-terror-and-mystery_eng.xml').read_bytes()).hexdigest()
assert len(stories)==63
out=ROOT/'tei/doyle/holmes';out.mkdir(exist_ok=True)
manifest=dict(publicationSource='https://www.arthur-conan-doyle.com/wiki/The_62_Sherlock_Holmes_stories_written_by_Arthur_Conan_Doyle',chronologySource='https://www.arthur-conan-doyle.com/wiki/William_Stuart_Baring-Gould',sources=sources,stories=sorted(stories,key=lambda s:(s['publication'],s['slug'])))
manifest['referenceSnapshots']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (ROOT/'assets/source-holmes').glob('*.html')}
(out/'selection.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print([(s['title'],s.get('source'),s['publication'],s['career']) for s in manifest['stories']])
