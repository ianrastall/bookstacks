import {describe,it,expect} from 'vitest';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {DOMParser} from '@xmldom/xmldom';
import {unzipSync,strFromU8} from 'fflate';
import {portableChapter} from '../../scripts/build_epubs';
import publications from '../data/epub-publications.json';

describe('EPUB publication',()=>{
  it('converts site popovers to linked, portable footnotes without losing verse or emphasis',()=>{
    const document=portableChapter({path:'chapter',segments:['chapter'],title:'Chapter',context:['Part I'],html:'<p class="tei-paragraph">Don’t <em>change</em> this<span class="tei-note"><button class="tei-note-ref">1</button><span class="tei-note-popover" hidden><span class="tei-note-text">The <em>original</em> note.</span><button>×</button></span></span>.</p><div class="tei-line-group"><span class="tei-line">First line</span><span class="tei-line">Second line</span></div>'},'en');
    expect(document).toContain('epub:type="noteref"');expect(document).toContain('epub:type="footnote"');expect(document).toContain('href="#noteref-1"');
    expect(document).toContain('Don’t <em>change</em>');expect(document).toContain('The <em>original</em> note.');expect(document).toContain('tei-line-group');expect(document).not.toContain('<button');expect(document).not.toContain(' hidden');
  });
  for(const[stem,publication]of Object.entries(publications))it(`${stem}: source-pinned, complete EPUB container with one file for both themes`,()=>{
    const data=fs.readFileSync('public'+publication.href),archive=unzipSync(data),source=fs.readFileSync(`tei/${stem.split('_')[0]}/${stem}.xml`);
    expect(createHash('sha256').update(data).digest('hex')).toBe(publication.revision);expect(createHash('sha256').update(source).digest('hex')).toBe(publication.source_sha256);
    expect(data.readUInt16LE(8)).toBe(0);expect(data.subarray(30,38).toString()).toBe('mimetype');expect(strFromU8(archive.mimetype)).toBe('application/epub+zip');
    const xml=(name:string)=>new DOMParser().parseFromString(strFromU8(archive[name]),'application/xml');
    const packageDoc=xml('EPUB/package.opf');expect(packageDoc.getElementsByTagName('dc:language')[0].textContent).toBe(publication.language);
    expect(packageDoc.getElementsByTagName('itemref').length).toBe(publication.sections.length+1);
    for(const section of publication.sections){const doc=xml('EPUB/'+section.href);expect(doc.getElementsByTagName('h1')[0].textContent).toBe(section.title);expect(doc.documentElement!.getAttribute('lang')).toBe(publication.language);}
    for(const[name,bytes]of Object.entries(archive))if(name.endsWith('.xhtml')){
      const doc=xml(name);expect(doc.getElementsByTagName('script')).toHaveLength(0);expect(doc.getElementsByTagName('button')).toHaveLength(0);
      for(const tag of ['img','link','a'])for(const node of Array.from(doc.getElementsByTagName(tag))){
        const href=node.getAttribute(tag==='img'?'src':'href');if(!href||/^https?:/.test(href))continue;
        const target=new URL(href,`https://epub.invalid/${name}`),file=decodeURIComponent(target.pathname.slice(1));expect(archive[file],`${name} → ${href}`).toBeDefined();
        if(target.hash){const targetDoc=xml(file);expect(Array.from(targetDoc.getElementsByTagName('*')).some(n=>n.getAttribute('id')===target.hash.slice(1))).toBe(true);}
      }
      expect(strFromU8(bytes)).not.toContain('src="/tei/');
    }
    expect(strFromU8(archive['EPUB/publication.xhtml'])).toContain('Publication and rights');expect(strFromU8(archive['EPUB/publication.xhtml'])).toContain('Font license');
    expect(strFromU8(archive['EPUB/styles/book.css'])).toContain('prefers-color-scheme:dark');
  });
});
