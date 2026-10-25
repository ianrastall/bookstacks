"""Explicit offline assembly of two Holmes editions; never run by site builds.

Original TEI files remain immutable, including their routes and downloads.
Run with --allow-missing-art only while preparing illustrations.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, re
from pathlib import Path
from lxml import etree

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'tei/doyle'
NS='http://www.tei-c.org/ns/1.0'
N={'t':NS}
X='{http://www.w3.org/XML/1998/namespace}'
def add(p,tag,text=None,**attrs):
 e=etree.SubElement(p,f'{{{NS}}}{tag}',attrs); e.text=text; return e
def norm(s): return ' '.join(s.split())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def story_n(story):
 candidate=story['slug'].removeprefix('the-adventure-of-')
 aliases={
  'the-story-of-the-lost-special':'lost-special',
  'charles-augustus-milverton':'charles-milverton',
  'the-disappearance-of-lady-frances-carfax':'lady-frances-carfax',
  'the-problem-of-thor-bridge':'thor-bridge',
  'how-watson-learned-the-trick':'watson-learned-the-trick',
 }
 candidate=aliases.get(candidate,candidate)
 if len(candidate)>24:candidate=candidate.removeprefix('the-')
 assert re.fullmatch('[a-z0-9-]{1,24}',candidate),candidate
 return candidate
def pointer_prefix(node,prefix):
 ids={e.get(X+'id') for e in node.iter() if e.get(X+'id')}
 for e in node.iter():
  if e.get(X+'id'):e.set(X+'id',prefix+e.get(X+'id'))
  for attr,value in list(e.attrib.items()):
   if attr==X+'id':continue
   e.set(attr,' '.join('#'+prefix+p[1:] if p.startswith('#') and p[1:] in ids else p for p in value.split()) if '#' in value else value)

def build(allow_missing_art=False):
 config=json.loads((BASE/'holmes/selection.json').read_text(encoding='utf8'))
 descriptions_path=BASE/'holmes/descriptions.json'
 descriptions=json.loads(descriptions_path.read_text(encoding='utf8')) if descriptions_path.exists() else {}
 docs={}
 for filename,checksum in config['sources'].items():
  f=BASE/filename
  assert sha(f)==checksum,f'Source changed: {f}'
  docs[filename]=etree.parse(str(f))
 pieces={}; art=[]; verification=[]
 for story in config['stories']:
  if 'source' in story:
   original=docs[story['source']].xpath('//*[@xml:id=$id]',id=story['sourceId'],namespaces={'xml':X[1:-1]})[0]
   piece=copy.deepcopy(original)
   pointer_prefix(piece,story['slug']+'-')
   if story['kind']=='novel':
    piece.set('type','part'); piece.set('n',{'a-study-in-scarlet':'stud','the-sign-of-four':'sign','the-hound-of-the-baskervilles':'houn','the-valley-of-fear':'vall'}[story['slug']])
    head=etree.Element(f'{{{NS}}}head');head.text=story['title'];piece.insert(0,head)
   else:
    piece.set('type','story');piece.set('n',story_n(story))
    piece.find('t:head',N).text=story['title']
    # Keep complete stories together; internal divisions remain in their text.
    for div in piece.xpath('.//t:div',namespaces=N):div.set('type','textual-section')
  else:
   piece=etree.Element(f'{{{NS}}}div',type='story',n=story_n(story));piece.set(X+'id',story['slug'])
   add(piece,'head',story['title'])
   for i,p in enumerate(story['paragraphs'],1):add(piece,'p',p).set(X+'id',f'{story["slug"]}-p-{i}')
  units=piece.xpath('.//t:div[@type="chapter" or @type="epilogue"]',namespaces=N) if story['kind']=='novel' else [piece]
  for i,unit in enumerate(units,1):
   ident=story['slug']+(f'-{i:02}' if story['kind']=='novel' else '')
   title=norm(''.join(unit.find('t:head',N).itertext()))
   excerpt=norm(' '.join(unit.xpath('.//t:p/text()',namespaces=N)))[:850]
   art.append(dict(slug=ident,title=story['title']+' — '+title if story['kind']=='novel' else title,file=f'img/holmes/{ident}.jpg',excerpt=excerpt))
   unit.set('corresp','#plate-'+ident)
  pieces[story['slug']]=piece
  if 'source' in story:
   original_paragraphs=[norm(''.join(p.itertext())) for p in original.xpath('.//t:p',namespaces=N)]
   collected_paragraphs=[norm(''.join(p.itertext())) for p in piece.xpath('.//t:p',namespaces=N)]
   assert original_paragraphs==collected_paragraphs,f'Text changed in {story["slug"]}'
   original_graphics=original.xpath('.//t:graphic/@url',namespaces=N)
   assert original_graphics==piece.xpath('.//t:graphic/@url',namespaces=N)
   original_notes=[norm(''.join(p.itertext())) for p in original.xpath('.//t:note',namespaces=N)]
   assert original_notes==[norm(''.join(p.itertext())) for p in piece.xpath('.//t:note',namespaces=N)]
   original_text=original.xpath('.//text()[not(ancestor::t:head)]',namespaces=N)
   assert original_text==piece.xpath('.//text()[not(ancestor::t:head)]',namespaces=N),f'Non-heading text changed in {story["slug"]}'
   verification.append(dict(slug=story['slug'],paragraphs=len(original_paragraphs),notes=len(original_notes),documentaryFigures=len(original_graphics),textSha256=hashlib.sha256('\n'.join(original_paragraphs).encode()).hexdigest()))
 art.sort(key=lambda a:a['slug'])
 (BASE/'holmes/illustration-plan.json').write_text(json.dumps(art,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 report=[]
 for order,title,slug in [('publication','The Complete Sherlock Holmes','the-complete-sherlock-holmes'),('career','The Chronological Sherlock Holmes','the-chronological-sherlock-holmes')]:
  root=etree.Element(f'{{{NS}}}TEI',nsmap={None:NS});root.set(X+'id',f'doyle_{slug}_eng')
  header=add(root,'teiHeader');fd=add(header,'fileDesc');ts=add(fd,'titleStmt')
  add(ts,'title',title,type='main');add(ts,'author','Arthur Conan Doyle')
  rs=add(ts,'respStmt');add(rs,'resp','Compilation, chronology, TEI encoding and new AI-generated engraving-style illustrations');add(rs,'name','Bookstacks, with OpenAI image generation')
  rs=add(ts,'respStmt');add(rs,'resp','Source transcriptions for The Field Bazaar and How Watson Learned the Trick');add(rs,'name','The Arthur Conan Doyle Encyclopedia')
  for filename,doc in docs.items():
   for resp in doc.xpath('//t:titleStmt/t:respStmt',namespaces=N):
    cloned=copy.deepcopy(resp);pointer_prefix(cloned,filename[:-4]+'-');ts.append(cloned)
  add(add(fd,'editionStmt'),'edition','Bookstacks illustrated collected edition',n='1.0')
  pub=add(fd,'publicationStmt');add(pub,'publisher','Bookstacks');add(pub,'date','25 October 2026',when='2026-10-25');add(add(pub,'availability',status='free'),'p','Doyle’s texts are public domain in the United States. New illustrations are AI-generated interpretations, not historical engravings. Original source credits are retained below.')
  notes=add(fd,'notesStmt')
  description='Four complete novels, fifty-six canonical stories, The Field Bazaar, How Watson Learned the Trick, and The Story of the Lost Special. The latter has an unnamed reasoner commonly associated with Holmes and is included as a related tale outside the usual sixty-work canon. '
  description+=('Ordered by first UK or US publication, whichever came earlier, using dated magazine issues; serial novels are placed at their first instalment and kept intact. Dates with no recorded day retain month precision.' if order=='publication' else 'Ordered by William S. Baring-Gould’s Holmes career chronology, an editorial reconstruction with disputed dates. Novels stay intact at their Holmes case dates, including retrospective passages. The Lost Special is placed at its 3 June 1890 disappearance. The two undated brief pieces are editorially placed in 1890 and 1902 during the Baker Street partnership; those placements are approximate.')
  add(notes,'note',description,type='source-description')
  sd=add(fd,'sourceDesc')
  for filename,doc in docs.items():
   for bibl in doc.xpath('//t:sourceDesc/*',namespaces=N):
    b=copy.deepcopy(bibl);pointer_prefix(b,filename[:-4]+'-')
    for ref in b.xpath('.//t:ref',namespaces=N):ref.set('type','source')
    sd.append(b)
  for label,url in [('Publication dates',config['publicationSource']),('Baring-Gould chronology',config['chronologySource']),('The Lost Special: publication and text','https://www.arthur-conan-doyle.com/wiki/The_Story_of_the_Lost_Special')]+[(s['title'],s['sourceUrl']) for s in config['stories'] if 'sourceUrl' in s]:
   add(add(sd,'bibl'),'ref',label,type='source',target=url)
  add(add(add(header,'profileDesc'),'langUsage'),'language','English',ident='en')
  body=add(add(root,'text'),'body');root.find('t:text',N).set(X+'lang','en')
  edition=add(body,'div',type='edition');edition.set(X+'id',slug+'-text')
  ordered=sorted(config['stories'],key=lambda s:(s[order],s['slug']))
  for story in ordered: edition.append(copy.deepcopy(pieces[story['slug']]))
  back=add(root.find('t:text',N),'back');plates=add(back,'div',type='illustrations');plates.set(X+'id','illustrations')
  add(plates,'head','Illustration credits')
  for item in art:
   if not (BASE/item['file']).exists():
    assert allow_missing_art,f'Missing illustration: {item["file"]}'
   figure=add(plates,'figure',type='engraving');figure.set(X+'id','plate-'+item['slug'])
   description=descriptions.get(item['slug'],f'Illustration for {item["title"]}.')
   add(figure,'graphic',url=item['file']);add(figure,'figDesc',f'{description} AI-generated nineteenth-century engraving-style plate.')
  filename=BASE/f'doyle_{slug}_eng.xml'
  # Never pretty-print literary mixed content: indentation can add spaces
  # between adjacent inline elements. Format only the new metadata and plates.
  etree.indent(header,space='  ');etree.indent(plates,space='  ')
  etree.ElementTree(root).write(str(filename),encoding='UTF-8',xml_declaration=True)
  saved=etree.parse(str(filename))
  for story in ordered:
   expected=pieces[story['slug']]
   actual=saved.xpath('//*[@xml:id=$id]',id=expected.get(X+'id'),namespaces={'xml':X[1:-1]})[0]
   assert [norm(''.join(p.itertext())) for p in expected.xpath('.//t:p',namespaces=N)]==[norm(''.join(p.itertext())) for p in actual.xpath('.//t:p',namespaces=N)],f'Serialized text changed: {story["slug"]}'
  report.append(dict(file=filename.name,works=len(ordered),illustrations=len(art),order=[s['slug'] for s in ordered],sha256=sha(filename)))
 (BASE/'holmes/import-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
 (BASE/'holmes/text-verification.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf8')
 print(json.dumps([dict(file=r['file'],works=r['works'],illustrations=r['illustrations']) for r in report]))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--allow-missing-art',action='store_true');args=parser.parse_args();build(args.allow_missing_art)
