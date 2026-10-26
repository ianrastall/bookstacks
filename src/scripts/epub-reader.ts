import {readingMode,type ReadingMode} from './reading-mode';
import type {EpubPublication} from '../lib/library';

const root=document.documentElement;
const read=(key:string)=>{try{return localStorage.getItem(key);}catch{return null;}};
const save=(key:string,value:string)=>{try{localStorage.setItem(key,value);}catch{/* Reading works without storage. */}};
const parse=(value:string)=>{const doc=new DOMParser().parseFromString(value,'application/xml');if(doc.querySelector('parsererror'))throw new Error('Invalid EPUB XML');return doc;};
const nodes=(doc:Document,tag:string)=>Array.from(doc.getElementsByTagNameNS('*',tag));
const pathFor=(base:string,href:string)=>decodeURIComponent(new URL(href,`https://epub.invalid/${base}`).pathname.slice(1));

for(const panel of document.querySelectorAll<HTMLElement>('[data-epub-pane]')){
  const publication:EpubPublication=JSON.parse(panel.dataset.epubPublication!);
  const host=panel.querySelector<HTMLElement>('[data-epub-host]')!,contents=panel.querySelector<HTMLSelectElement>('[data-epub-contents]')!;
  const previous=panel.querySelector<HTMLButtonElement>('[data-epub-previous]')!,next=panel.querySelector<HTMLButtonElement>('[data-epub-next]')!;
  const loading=panel.querySelector<HTMLElement>('[data-epub-loading]')!,error=panel.querySelector<HTMLElement>('[data-epub-error]')!,noMatches=panel.querySelector<HTMLElement>('[data-epub-no-match]')!;
  const key=`bookstacks-epub-location:${publication.revision}`;
  let saved:{path?:string;fraction?:number}={};try{saved=JSON.parse(read(key)??'{}');}catch{/* Ignore invalid saved locations. */}
  const start=publication.sections.find(s=>s.path===panel.dataset.epubStart)?.href;
  let current=saved.path??`EPUB/${start}`,fraction=Math.max(0,Math.min(1,Number(saved.fraction)||0));
  let scale=Number(read('bookstacks-epub-scale'))||1,request=0,active=false;
  let archive:Record<string,Uint8Array>|undefined,spine:string[]=[],frame:HTMLIFrameElement|undefined,observer:ResizeObserver|undefined;
  let initialization:Promise<void>|undefined;
  const blobs=new Map<string,string>(),chapterText=new Map<string,string>();
  let lastQuery='',lastSearchChapter='',searchOffset=0,searchVersion=0;
  const decode=(name:string)=>{if(!archive?.[name])throw new Error(`Missing EPUB resource: ${name}`);return new TextDecoder().decode(archive[name]);};
  const blobFor=(name:string):string=>{
    if(blobs.has(name))return blobs.get(name)!;
    const extension=name.split('.').pop()?.toLowerCase();let bytes=archive?.[name];if(!bytes)throw new Error('Missing EPUB asset');
    const mime=({css:'text/css',otf:'font/otf',ttf:'font/ttf',png:'image/png',jpg:'image/jpeg',jpeg:'image/jpeg',svg:'image/svg+xml',webp:'image/webp',gif:'image/gif'} as Record<string,string>)[extension??''];
    if(!mime)throw new Error('Unsupported EPUB asset');
    if(extension==='css')bytes=new TextEncoder().encode(decode(name).replace(/url\(['"]?([^'"\)]+)['"]?\)/g,(_,href)=>`url("${blobFor(pathFor(name,href))}")`));
    const url=URL.createObjectURL(new Blob([bytes.slice().buffer as ArrayBuffer],{type:mime}));blobs.set(name,url);return url;
  };
  async function initialize(){
    if(initialization)return initialization;
    initialization=(async()=>{
      const url=new URL(publication.href,location.href);url.searchParams.set('revision',publication.revision);
      const response=await fetch(url);if(!response.ok)throw new Error('EPUB download failed');
      const bytes=new Uint8Array(await response.arrayBuffer());
      const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(b=>b.toString(16).padStart(2,'0')).join('');
      if(digest!==publication.revision)throw new Error('EPUB checksum mismatch');
      const {unzip}=await import('fflate');archive=await new Promise((resolve,reject)=>unzip(bytes,{filter:file=>file.originalSize<150_000_000},(err,data)=>err?reject(err):resolve(data)));
      const container=parse(decode('META-INF/container.xml')),packagePath=nodes(container,'rootfile')[0]?.getAttribute('full-path');if(!packagePath)throw new Error('Missing EPUB package');
      const packageDoc=parse(decode(packagePath)),items=new Map(nodes(packageDoc,'item').map(item=>[item.id,item]));
      spine=nodes(packageDoc,'itemref').map(ref=>items.get(ref.getAttribute('idref')!)).filter(Boolean).map(item=>pathFor(packagePath,item!.getAttribute('href')!));
      if(!spine.length)throw new Error('Empty EPUB spine');if(!spine.includes(current))current=spine[0];
      contents.replaceChildren();
      const navItem=nodes(packageDoc,'item').find(item=>item.getAttribute('properties')?.split(/\s+/).includes('nav'));
      if(navItem){const navPath=pathFor(packagePath,navItem.getAttribute('href')!),nav=parse(decode(navPath));
        const toc=nodes(nav,'nav').find(n=>n.getAttributeNS('http://www.idpf.org/2007/ops','type')==='toc');
        if(toc)for(const link of Array.from(toc.getElementsByTagNameNS('*','a'))){const target=pathFor(navPath,link.getAttribute('href')!);if(spine.includes(target))contents.add(new Option(link.textContent??'',target));}
      }
      for(const section of spine)if(!Array.from(contents.options).some(o=>o.value===section)){const doc=parse(decode(section));contents.add(new Option(nodes(doc,'title')[0]?.textContent??section,section));}
      contents.lang=publication.language;contents.translate=false;contents.disabled=false;
    })().catch(cause=>{initialization=undefined;throw cause;});
    return initialization;
  }
  function theme(){
    const doc=frame?.contentDocument;if(!doc)return;
    const style=getComputedStyle(root),target=doc.documentElement.style;
    for(const [name,token] of [['--paper','--bg'],['--ink','--text'],['--muted','--muted'],['--accent','--accent'],['--rule','--border']])target.setProperty(name,style.getPropertyValue(token));
    target.colorScheme=root.dataset.theme==='light'?'light':'dark';target.fontSize=`${20*scale}px`;
    doc.documentElement.dataset.theme=root.dataset.theme;
    panel.querySelector<HTMLOutputElement>('[data-epub-size]')!.value=`${Math.round(scale*100)}%`;
  }
  function remember(){
    if(!active||!frame)return;
    const top=frame.getBoundingClientRect().top+scrollY;
    fraction=Math.max(0,Math.min(1,(scrollY-top)/Math.max(1,frame.offsetHeight)));
    save(key,JSON.stringify({path:current,fraction}));
  }
  async function render(target=current,anchor='',restore=false){
    const id=++request;loading.hidden=false;error.hidden=true;noMatches.hidden=true;
    try{
      await initialize();if(id!==request||!active)return;if(!spine.includes(target))target=current;
      const doc=parse(decode(target));
      doc.documentElement.setAttribute('translate','no');
      // Publications are generated locally; embedded documents still have no scripting,
      // forms, nested frames or permission to navigate the surrounding site.
      for(const el of Array.from(doc.querySelectorAll('script,iframe,object,embed,form,base')))el.remove();
      for(const el of Array.from(doc.querySelectorAll('*')))for(const attr of Array.from(el.attributes))if(attr.name.startsWith('on'))el.removeAttribute(attr.name);
      for(const el of Array.from(doc.querySelectorAll('[src]')))el.setAttribute('src',blobFor(pathFor(target,el.getAttribute('src')!)));
      for(const el of Array.from(doc.querySelectorAll('link[rel=stylesheet]')))el.setAttribute('href',blobFor(pathFor(target,el.getAttribute('href')!)));
      const csp=doc.createElementNS('http://www.w3.org/1999/xhtml','meta');csp.setAttribute('http-equiv','Content-Security-Policy');csp.setAttribute('content',"default-src 'none'; img-src blob: data:; font-src blob:; style-src 'unsafe-inline' blob:");nodes(doc,'head')[0].prepend(csp);
      const newFrame=document.createElement('iframe');newFrame.className='epub-loading-frame';newFrame.style.cssText='position:absolute;visibility:hidden;inset:0;width:100%;border:0';newFrame.translate=false;newFrame.title=nodes(doc,'title')[0]?.textContent??'EPUB';newFrame.setAttribute('sandbox','allow-same-origin');newFrame.setAttribute('scrolling','no');
      newFrame.srcdoc=new XMLSerializer().serializeToString(doc);
      await new Promise<void>((resolve,reject)=>{newFrame.onload=()=>resolve();newFrame.onerror=()=>reject(new Error('EPUB chapter failed'));host.append(newFrame);});
      if(id!==request||!active){newFrame.remove();return;}
      observer?.disconnect();frame?.remove();frame=newFrame;frame.className='epub-reading-frame';frame.style.cssText='';current=target;theme();
      await frame.contentDocument!.fonts.ready;
      const resize=()=>{if(!frame?.contentDocument)return;const body=frame.contentDocument.body;const height=Math.ceil(body.getBoundingClientRect().height+parseFloat(getComputedStyle(body).marginTop)+parseFloat(getComputedStyle(body).marginBottom));const value=`${height+2}px`;if(frame.style.height!==value)frame.style.height=value;};
      observer=new ResizeObserver(()=>requestAnimationFrame(resize));observer.observe(frame.contentDocument!.body);resize();
      frame.contentDocument!.addEventListener('click',event=>{
        const link=(event.target as Element).closest('a');if(!link)return;event.preventDefault();const href=link.getAttribute('href')??'';
        if(/^https?:\/\//.test(href)){window.open(href,'_blank','noopener,noreferrer');return;}
        const url=new URL(href,`https://epub.invalid/${current}`),path=decodeURIComponent(url.pathname.slice(1)),anchor=decodeURIComponent(url.hash.slice(1));
        if(path===current){const el=frame?.contentDocument?.getElementById(anchor);if(el)scrollTo({top:scrollY+frame!.getBoundingClientRect().top+el.getBoundingClientRect().top});}
        else if(spine.includes(path))void render(path,anchor);
      });
      const index=spine.indexOf(current);previous.disabled=index===0;next.disabled=index===spine.length-1;contents.value=current;
      panel.dataset.epubReady='true';panel.dataset.epubChapter=current;
      if(anchor){const el=frame.contentDocument!.getElementById(anchor);if(el)scrollTo({top:scrollY+frame.getBoundingClientRect().top+el.getBoundingClientRect().top});}
      else if(restore&&fraction>0)scrollTo({top:scrollY+frame.getBoundingClientRect().top+fraction*frame.offsetHeight,behavior:'instant'});
      else if(!restore)panel.scrollIntoView({block:'start',behavior:'instant'});
      save(key,JSON.stringify({path:current,fraction:restore?fraction:0}));
    }catch(cause){if(id===request){error.hidden=false;console.error('EPUB rendering failed',cause);}}
    finally{if(id===request)loading.hidden=true;}
  }
  function activate(mode:ReadingMode){active=mode==='epub';searchVersion++;if(active)void render(current,'',true);else request++;}
  previous.addEventListener('click',()=>{searchVersion++;void render(spine[Math.max(0,spine.indexOf(current)-1)]);});next.addEventListener('click',()=>{searchVersion++;void render(spine[Math.min(spine.length-1,spine.indexOf(current)+1)]);});
  contents.addEventListener('change',()=>{searchVersion++;void render(contents.value);});
  for(const [attribute,delta] of [['smaller',-.1],['larger',.1]] as const)panel.querySelector(`[data-epub-${attribute}]`)!.addEventListener('click',()=>{scale=Math.max(.8,Math.min(2,Math.round((scale+delta)*10)/10));save('bookstacks-epub-scale',String(scale));theme();});
  panel.querySelector('form')!.addEventListener('submit',async event=>{
    event.preventDefault();const query=panel.querySelector<HTMLInputElement>('[data-epub-find]')!.value.trim().toLocaleLowerCase();if(!query)return;
    const version=++searchVersion;
    try{
      await initialize();if(version!==searchVersion||!active)return;
      const start=spine.indexOf(current),resume=lastQuery===query&&lastSearchChapter===current?searchOffset:0;
      for(let offset=0;offset<=spine.length;offset++){
        if(offset===spine.length&&resume===0)break;
        const target=spine[(start+offset)%spine.length];if(!chapterText.has(target))chapterText.set(target,nodes(parse(decode(target)),'body')[0].textContent?.toLocaleLowerCase()??'');
        const index=chapterText.get(target)!.indexOf(query,offset===0?resume:0);
        if(index<0||(offset===spine.length&&index>=resume))continue;
        await render(target);if(version!==searchVersion||!active)return;
        const doc=frame?.contentDocument;if(!doc)return;
        const walker=doc.createTreeWalker(doc.body,NodeFilter.SHOW_TEXT),range=doc.createRange();let node:Node|null,position=0,started=false;
        while((node=walker.nextNode())){
          const length=node.textContent?.length??0;
          if(!started&&position+length>index){range.setStart(node,index-position);started=true;}
          if(started&&position+length>=index+query.length){range.setEnd(node,index+query.length-position);break;}
          position+=length;
        }
        if(started&&node){const mark=doc.createElement('mark');mark.append(range.extractContents());range.insertNode(mark);scrollTo({top:scrollY+frame!.getBoundingClientRect().top+mark.getBoundingClientRect().top-80});}
        lastQuery=query;lastSearchChapter=current;searchOffset=index+query.length;return;
      }
      noMatches.hidden=false;
    }catch(cause){if(version===searchVersion){error.hidden=false;console.error('EPUB search failed',cause);}}
  });
  new MutationObserver(theme).observe(root,{attributes:true,attributeFilter:['data-theme','style']});
  let timer:ReturnType<typeof setTimeout>|undefined;window.addEventListener('scroll',()=>{clearTimeout(timer);timer=setTimeout(remember,150);},{passive:true});
  window.addEventListener('pagehide',remember);window.addEventListener('bookstacks:reading-mode',event=>activate((event as CustomEvent<ReadingMode>).detail));
  activate(readingMode());
}
