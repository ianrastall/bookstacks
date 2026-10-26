/** Explicit offline EPUB publication. Never called by the website build. */
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {DOMParser,XMLSerializer} from '@xmldom/xmldom';
import {zipSync,strToU8,type Zippable} from 'fflate';
import {getLibrary,localizedEditionHref,type Author,type Work,type Edition,type ReadingUnit,type TocNode} from '../src/lib/library';
import {editionDirection} from '../src/lib/i18n';

const ROOT=process.cwd(),XHTML='http://www.w3.org/1999/xhtml',EPUB='http://www.idpf.org/2007/ops';
const escape=(s:string)=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const hash=(b:Uint8Array|string)=>createHash('sha256').update(b).digest('hex');
const elements=(node:any,tag:string):any[]=>node?Array.from(node.getElementsByTagName('*')).filter((n:any)=>tag==='*'||n.localName===tag):[];
const classed=(node:any,name:string)=>elements(node,'*').filter(n=>(n.getAttribute('class')||'').split(/\s+/).includes(name));
const text=(node:any)=>String(node?.textContent??'').replace(/\s+/g,' ').trim();
function xhtml(title:string,lang:string,body:string){return `<?xml version="1.0" encoding="utf-8"?><!DOCTYPE html><html xmlns="${XHTML}" xmlns:epub="${EPUB}" lang="${escape(lang)}" xml:lang="${escape(lang)}" dir="${editionDirection(lang)}"><head><meta charset="utf-8"/><title>${escape(title)}</title><link rel="stylesheet" type="text/css" href="styles/book.css"/></head><body>${body}</body></html>`;}

/** Turn the TEI reader's interactive notes into portable EPUB footnotes. */
export function portableChapter(unit:ReadingUnit,lang:string):string{
  const raw=`${unit.context.length?`<p class="context">${escape(unit.context.join(' · '))}</p>`:''}<h1>${escape(unit.title)}</h1>${unit.html}${unit.illustration?`<figure><img src="${escape(unit.illustration.previewSrc??unit.illustration.src)}" alt="${escape(unit.illustration.description)}"/><figcaption>${escape(unit.illustration.description)}</figcaption></figure>`:''}`;
  const doc=new DOMParser().parseFromString(xhtml(unit.title,lang,raw.replace(/\shidden(?=[ >])/g,' hidden="hidden"')),'application/xhtml+xml');
  const body=elements(doc,'body')[0],notes=doc.createElementNS(XHTML,'section');notes.setAttribute('class','footnotes');notes.setAttributeNS(EPUB,'epub:type','footnotes');
  for(const [index,note] of classed(doc,'tei-note').entries()){
    const content=classed(note,'tei-note-text')[0];if(!content)continue;
    const n=index+1,id=`footnote-${n}`,ref=`noteref-${n}`;
    const link=doc.createElementNS(XHTML,'a');link.setAttribute('id',ref);link.setAttribute('href',`#${id}`);link.setAttribute('class','noteref');link.setAttributeNS(EPUB,'epub:type','noteref');link.setAttribute('role','doc-noteref');
    const sup=doc.createElementNS(XHTML,'sup');sup.appendChild(doc.createTextNode(String(n)));link.appendChild(sup);
    const aside=doc.createElementNS(XHTML,'aside');aside.setAttribute('id',id);aside.setAttributeNS(EPUB,'epub:type','footnote');aside.setAttribute('role','doc-footnote');
    const back=doc.createElementNS(XHTML,'a');back.setAttribute('href',`#${ref}`);back.setAttribute('role','doc-backlink');back.appendChild(doc.createTextNode(`${n}. ↩ `));aside.appendChild(back);
    while(content.firstChild)aside.appendChild(content.firstChild);notes.appendChild(aside);note.parentNode.replaceChild(link,note);
  }
  if(notes.childNodes.length)body.appendChild(notes);
  for(const el of elements(doc,'*')){el.removeAttribute('loading');el.removeAttribute('decoding');}
  return new XMLSerializer().serializeToString(doc);
}

export function buildEpub(author:Author,work:Work,edition:Edition,outputRoot=path.join(ROOT,'public/downloads/epub')){
  const source=path.join(ROOT,'tei',author.slug,edition.sourceFile),sourceBytes=fs.readFileSync(source),sourceDoc=new DOMParser().parseFromString(sourceBytes.toString(),'application/xml');
  const files:Record<string,Uint8Array>={},assets=new Map<string,string>();
  const sections=edition.units.map((unit,i)=>({path:unit.path,href:`chapter-${String(i+1).padStart(4,'0')}.xhtml`,title:unit.title}));
  const media=new Map<string,string>();
  const addAsset=(src:string)=>{
    if(assets.has(src))return assets.get(src)!;
    const decoded=decodeURIComponent(src),physical=path.resolve(ROOT,'.'+decoded);
    if(!decoded.startsWith(`/tei/${author.slug}/img/`)||!physical.startsWith(path.resolve(ROOT,'tei',author.slug)+path.sep))throw new Error(`Invalid EPUB image: ${src}`);
    if(!fs.existsSync(physical))throw new Error(`Missing EPUB image: ${src}`);
    const bytes=fs.readFileSync(physical),ext=path.extname(physical).toLowerCase(),href=`images/${hash(bytes).slice(0,24)}${ext}`;
    const mime=({'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.gif':'image/gif','.svg':'image/svg+xml','.webp':'image/webp'} as Record<string,string>)[ext];
    if(!mime)throw new Error(`Unsupported EPUB image: ${src}`);
    files[`EPUB/${href}`]=bytes;media.set(href,mime);assets.set(src,href);return href;
  };
  for(const [i,unit] of edition.units.entries()){
    let document=portableChapter(unit,edition.code);
    document=document.replace(/src="(\/tei\/[^\"]+)"/g,(_,src)=>`src="${addAsset(src)}"`);
    files[`EPUB/${sections[i].href}`]=strToU8(document);media.set(sections[i].href,'application/xhtml+xml');
  }
  files['EPUB/styles/book.css']=fs.readFileSync(path.join(ROOT,'scripts/export/epub.css'));media.set('styles/book.css','text/css');
  // Western fonts are embedded once; other source scripts retain reader fallbacks.
  for(const name of ['NewCM10-Regular.otf','NewCM10-Italic.otf','NewCM10-Bold.otf','NewCM10-BoldItalic.otf']){files[`EPUB/fonts/${name}`]=fs.readFileSync(path.join(ROOT,'src/assets/fonts',name));media.set(`fonts/${name}`,'font/otf');}
  const fileDesc=elements(sourceDoc,'fileDesc')[0];
  const record=[['titleStmt','Title and responsibilities'],['editionStmt','Edition'],['publicationStmt','Publication and rights'],['sourceDesc','Sources'],['notesStmt','Editorial notes']].map(([tag,label])=>{
    const node=elements(fileDesc,tag)[0];if(!node)return '';
    const paragraphs=Array.from(node.childNodes).filter((n:any)=>n.nodeType===1).map((n:any)=>`<p>${escape(text(n))}</p>`).join('');
    return `<section><h2>${label}</h2>${paragraphs}</section>`;
  }).join('');
  const refs=elements(fileDesc,'ref').map(n=>n.getAttribute('target')).filter((s:string)=>/^https?:\/\//.test(s));
  const rights=text(elements(elements(fileDesc,'publicationStmt')[0],'availability')[0]);
  const fontLicense=fs.readFileSync(path.join(ROOT,'src/assets/fonts/NewComputerModern-LICENSE.txt'),'utf8');
  files['EPUB/publication.xhtml']=strToU8(xhtml('Publication record',edition.code,`<article class="publication-record"><h1>${escape(edition.sourceTitle)}</h1><p>${escape(author.name)} ${escape(author.dates)}</p>${record}<ul>${[...new Set(refs)].map(href=>`<li><a href="${escape(href)}">${escape(href)}</a></li>`).join('')}<li><a href="https://bookstacks.org${localizedEditionHref(work,edition)}">Bookstacks</a></li></ul><section lang="en" xml:lang="en"><h2>Font license</h2><pre class="font-license">${escape(fontLicense)}</pre></section></article>`));media.set('publication.xhtml','application/xhtml+xml');
  const routeBase=localizedEditionHref(work,edition);
  function toc(nodes:TocNode[]):string{return `<ol>${nodes.map(node=>{const section=sections.find(s=>node.href===`${routeBase}/${s.path}`);return `<li>${section?`<a href="${section.href}">${escape(node.label)}</a>`:`<span>${escape(node.label)}</span>`}${node.children.length?toc(node.children):''}</li>`;}).join('')}</ol>`;}
  files['EPUB/nav.xhtml']=strToU8(xhtml('Contents',edition.code,`<nav epub:type="toc" id="toc"><h1>Contents</h1>${toc(edition.toc)}</nav><nav epub:type="landmarks" hidden="hidden"><h2>Guide</h2><ol><li><a epub:type="bodymatter" href="${sections[0].href}">${escape(edition.sourceTitle)}</a></li><li><a epub:type="copyright-page" href="publication.xhtml">Publication record</a></li></ol></nav>`));media.set('nav.xhtml','application/xhtml+xml');
  const modified=(elements(sourceDoc,'change').map(n=>n.getAttribute('when')).filter((s:string)=>/^\d{4}-\d{2}-\d{2}$/.test(s)).sort().at(-1)??'2026-01-01')+'T00:00:00Z';
  const uid=`https://bookstacks.org${routeBase}`,items=[...media.entries()];
  files['EPUB/package.opf']=strToU8(`<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="book-id">${escape(uid)}</dc:identifier><dc:title>${escape(edition.sourceTitle)}</dc:title><dc:language>${escape(edition.code)}</dc:language><dc:creator>${escape(author.name)}</dc:creator><dc:publisher>Bookstacks</dc:publisher><dc:rights>${escape(rights)}</dc:rights><dc:source>${escape(uid)}</dc:source><meta property="dcterms:modified">${modified}</meta><meta property="rendition:layout">reflowable</meta></metadata><manifest>${items.map(([href,mime],i)=>`<item id="resource-${i}" href="${href}" media-type="${mime}"${href==='nav.xhtml'?' properties="nav"':''}/>`).join('')}</manifest><spine page-progression-direction="${editionDirection(edition.code)}">${[...sections.map(s=>s.href),'publication.xhtml'].map(href=>`<itemref idref="resource-${items.findIndex(([key])=>key===href)}"/>`).join('')}</spine></package>`);
  const archive:Zippable={mimetype:[strToU8('application/epub+zip'),{level:0}], 'META-INF/container.xml':strToU8('<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'),...files};
  // Stable ZIP timestamps make repeated builds byte-for-byte reproducible.
  const bytes=zipSync(archive,{level:6,mtime:new Date('2026-01-01T00:00:00Z')});
  const stem=edition.sourceFile.replace(/\.xml$/,''),target=path.join(outputRoot,author.slug,`${stem}.epub`);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,bytes);
  const metadata={source_sha256:hash(sourceBytes),href:`/downloads/epub/${author.slug}/${stem}.epub`,revision:hash(bytes),language:edition.code,sections,bytes:bytes.length};
  fs.writeFileSync(target.replace(/\.epub$/,'.manifest.json'),JSON.stringify(metadata,null,2)+'\n');
  return metadata;
}

export async function main(requested:string[]){
  if(!requested.length)throw new Error('Specify one or more canonical TEI filenames, or --all.');
  process.env.BOOKSTACKS_BUILD_EPUB='1';
  const indexPath=path.join(ROOT,'src/data/epub-publications.json'),index=JSON.parse(fs.readFileSync(indexPath,'utf8'));
  let count=0;
  for(const author of getLibrary().authors)for(const work of author.works)for(const edition of work.editions){
    if(!requested.includes('--all')&&!requested.some(s=>path.basename(s)===edition.sourceFile))continue;
    index[edition.sourceFile.replace(/\.xml$/,'')]=buildEpub(author,work,edition);count++;console.log(`Built ${edition.sourceFile}`);
  }
  if(!count)throw new Error('No matching published TEI editions.');
  fs.writeFileSync(indexPath,JSON.stringify(index,null,2)+'\n');console.log(`Published ${count} EPUB file(s).`);
}
