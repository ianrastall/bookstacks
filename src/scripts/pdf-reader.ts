// Render PDF pages directly into the existing reading column.
import '../styles/pdf-text-layer.css';
interface PdfFile {theme:string;href:string;revision:string}
interface Outline {title:string;dest:string|unknown[]|null;items:Outline[]}
interface PdfPage {getViewport(options:{scale:number}):{width:number;height:number};render(options:unknown):{promise:Promise<void>};getTextContent():Promise<{items:Array<{str?:string}>}>}
interface PdfDocument {numPages:number;getPage(page:number):Promise<PdfPage>;getOutline():Promise<Outline[]|null>;getDestination(name:string):Promise<unknown[]|null>;getPageIndex(ref:unknown):Promise<number>}
const root=document.documentElement;
const read=(key:string)=>{try{return localStorage.getItem(key);}catch{return null;}};
const save=(key:string,value:string)=>{try{localStorage.setItem(key,value);}catch{/* Storage is optional. */}};
const normalize=(value:string)=>value.normalize('NFKC').toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu,'');
let library:Promise<any>|undefined;
function loadLibrary(){
  return library??=new Promise<any>((resolve,reject)=>{
    const script=document.createElement('script');script.type='module';script.src='/vendor/pdfjs/build/pdf.mjs';
    script.onload=()=>{const module=(window as Window&{pdfjsLib?:any}).pdfjsLib;module.GlobalWorkerOptions.workerSrc='/vendor/pdfjs/build/pdf.worker.mjs';resolve(module);};
    script.onerror=()=>{library=undefined;script.remove();reject(new Error('PDF.js could not be loaded'));};
    document.head.append(script);
  });
}
for(const panel of document.querySelectorAll<HTMLElement>('[data-pdf-files]')){
  const files:PdfFile[]=JSON.parse(panel.dataset.pdfFiles!);
  const online=document.querySelector<HTMLElement>('[data-online-content]')!;
  const host=panel.querySelector<HTMLElement>('[data-pdf-page-host]')!;
  const input=panel.querySelector<HTMLInputElement>('[data-pdf-page]')!;
  const count=panel.querySelector<HTMLOutputElement>('[data-pdf-count]')!;
  const previous=panel.querySelector<HTMLButtonElement>('[data-pdf-previous]')!;
  const next=panel.querySelector<HTMLButtonElement>('[data-pdf-next]')!;
  const outlineSelect=panel.querySelector<HTMLSelectElement>('[data-pdf-outline]')!;
  const download=panel.querySelector<HTMLAnchorElement>('[data-pdf-download]')!;
  const loading=panel.querySelector<HTMLProgressElement>('[data-pdf-loading]')!;
  const error=panel.querySelector<HTMLElement>('[data-pdf-error]')!;
  const noMatches=panel.querySelector<HTMLElement>('[data-pdf-no-match]')!;
  const search=panel.querySelector<HTMLInputElement>('[data-pdf-find]')!;
  const pageKey=`bookstacks-pdf-page:${files.map(file=>file.revision).join(':')}`;
  const saved=Number(read(pageKey));
  let page=Number.isSafeInteger(saved)&&saved>0?saved:1;
  let mode='online',version=0,searchVersion=0,lastWidth=0;
  let currentDocument:PdfDocument|undefined;
  let outlines:Outline[]=[];
  const documents=new Map<string,Promise<PdfDocument>>();
  const textCache=new Map<number,string>();
  const file=()=>files.find(file=>file.theme===root.dataset.theme)??files[0];
  async function documentFor(file:PdfFile):Promise<PdfDocument>{
    if(!documents.has(file.href)){
      const publicationUrl=new URL(file.href,location.href);publicationUrl.searchParams.set('revision',file.revision);
      const loading=loadLibrary().then(pdfjs=>pdfjs.getDocument({url:publicationUrl.href,standardFontDataUrl:'/vendor/pdfjs/web/standard_fonts/',cMapUrl:'/vendor/pdfjs/web/cmaps/',cMapPacked:true,wasmUrl:'/vendor/pdfjs/web/wasm/',useSystemFonts:false}).promise);
      documents.set(file.href,loading);void loading.catch(()=>documents.delete(file.href));
    }
    return documents.get(file.href)!;
  }
  async function destinationPage(document:PdfDocument,item:Outline){
    const destination=typeof item.dest==='string'?await document.getDestination(item.dest):item.dest;
    if(!destination)return 1;
    return typeof destination[0]==='number'?destination[0]+1:(await document.getPageIndex(destination[0]))+1;
  }
  async function populateOutline(document:PdfDocument){
    const tree=await document.getOutline()??[];
    outlines=[];outlineSelect.replaceChildren(new Option('—',''));
    function visit(items:Outline[],depth=0){for(const item of items){const index=outlines.push(item)-1;outlineSelect.add(new Option('— '.repeat(depth)+item.title,String(index)));visit(item.items??[],depth+1);}}
    visit(tree);outlineSelect.disabled=outlines.length===0;outlineSelect.lang=panel.lang;outlineSelect.translate=false;
    if(!saved){
      const title=normalize(panel.dataset.pdfTitle??'');
      const context:string[]=JSON.parse(panel.dataset.pdfContext??'[]');
      let best:Outline|undefined;
      function find(items:Outline[],ancestors:string[]=[]){for(const item of items){if(normalize(item.title)===title&&(!best||context.every(part=>ancestors.some(parent=>normalize(parent)===normalize(part)))))best=item;find(item.items??[],[...ancestors,item.title]);}}
      find(tree);if(best){outlineSelect.value=String(outlines.indexOf(best));page=await destinationPage(document,best);}
    }
  }
  async function render(){
    if(mode!=='pdf')return;
    const request=++version;loading.hidden=false;error.hidden=true;noMatches.hidden=true;
    try{
      const selected=file();download.href=selected.href;download.download=selected.href.split('/').pop()!;
      const document=await documentFor(selected);
      if(request!==version||mode!=='pdf')return;
      if(!currentDocument)await populateOutline(document);
      currentDocument=document;
      if(request!==version||mode!=='pdf')return;
      page=Math.min(document.numPages,Math.max(1,page));input.value=String(page);input.max=String(document.numPages);count.value=` / ${document.numPages}`;
      previous.disabled=page===1;next.disabled=page===document.numPages;
      const pdfPage=await document.getPage(page),natural=pdfPage.getViewport({scale:1});
      const width=host.clientWidth;if(width<1)return;
      const scale=width/natural.width,viewport=pdfPage.getViewport({scale}),ratio=Math.min(devicePixelRatio||1,2);
      const canvas=window.document.createElement('canvas');canvas.width=Math.ceil(viewport.width*ratio);canvas.height=Math.ceil(viewport.height*ratio);
      canvas.style.width='100%';canvas.style.height='auto';canvas.setAttribute('aria-label',`${page} / ${document.numPages}`);
      await pdfPage.render({canvasContext:canvas.getContext('2d')!,canvas,viewport,transform:ratio===1?null:[ratio,0,0,ratio,0,0]}).promise;
      if(request!==version||mode!=='pdf')return;
      const wrapper=window.document.createElement('div');wrapper.className='pdf-rendered-page';wrapper.dataset.pageNumber=String(page);
      wrapper.style.setProperty('--total-scale-factor',String(scale));wrapper.style.setProperty('--scale-factor',String(scale));wrapper.append(canvas);
      const textLayer=window.document.createElement('div');textLayer.className='pdf-text-layer';wrapper.append(textLayer);
      const pdfjs=await loadLibrary();await new pdfjs.TextLayer({textContentSource:await pdfPage.getTextContent(),container:textLayer,viewport}).render();
      if(request!==version||mode!=='pdf')return;
      host.replaceChildren(wrapper);save(pageKey,String(page));lastWidth=width;panel.dataset.pdfReady='true';panel.dataset.pdfTheme=selected.theme;
    }catch(cause){if(request===version){error.hidden=false;console.error('PDF rendering failed',cause);}}
    finally{if(request===version)loading.hidden=true;}
  }
  function setMode(value:string,changeUrl=true){
    mode=value==='pdf'?'pdf':'online';root.dataset.readingMode=mode;online.hidden=mode==='pdf';panel.hidden=mode!=='pdf';
    if(mode==='pdf')document.querySelector<HTMLButtonElement>('.reader-expanded .reader-fullscreen')?.click();
    const title=document.querySelector<HTMLElement>('[data-reader-title]');
    if(title)title.textContent=(mode==='pdf'?title.dataset.pdfTitle:title.dataset.onlineTitle)??'';
    document.querySelectorAll<HTMLElement>('[data-online-only]').forEach(node=>node.hidden=mode==='pdf');
    document.querySelectorAll<HTMLElement>('[data-pdf-only]').forEach(node=>node.hidden=mode!=='pdf');
    document.querySelectorAll<HTMLButtonElement>('[data-reading-mode]').forEach(button=>{button.disabled=false;button.setAttribute('aria-pressed',String(button.dataset.readingMode===mode));});
    if(changeUrl){const url=new URL(location.href);if(mode==='pdf')url.searchParams.set('view','pdf');else url.searchParams.delete('view');if(url.hash==='#pdf-reader')url.hash='';history.replaceState(null,'',url);}
    if(mode==='pdf')void render();else{version++;searchVersion++;}
  }
  document.querySelectorAll<HTMLButtonElement>('[data-reading-mode]').forEach(button=>button.addEventListener('click',()=>setMode(button.dataset.readingMode!)));
  previous.addEventListener('click',()=>{page--;void render();});next.addEventListener('click',()=>{page++;void render();});
  input.addEventListener('change',()=>{const value=Number(input.value);if(Number.isSafeInteger(value)){page=value;void render();}});
  input.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();input.dispatchEvent(new Event('change'));}});
  outlineSelect.addEventListener('change',async()=>{const item=outlines[Number(outlineSelect.value)];if(item&&currentDocument){page=await destinationPage(currentDocument,item);void render();}});
  panel.querySelector('form')!.addEventListener('submit',async event=>{
    event.preventDefault();const query=search.value.trim().toLocaleLowerCase();if(!query||!currentDocument)return;
    const request=++searchVersion;loading.hidden=false;noMatches.hidden=true;
    for(let offset=0;offset<currentDocument.numPages;offset++){
      const candidate=(page-1+offset)%currentDocument.numPages+1;
      if(!textCache.has(candidate)){const content=await(await currentDocument.getPage(candidate)).getTextContent();textCache.set(candidate,content.items.map(item=>item.str??'').join(' ').toLocaleLowerCase());}
      if(request!==searchVersion||mode!=='pdf')return;
      if(textCache.get(candidate)!.includes(query)){page=candidate;await render();host.querySelectorAll<HTMLElement>('.pdf-text-layer span').forEach(span=>{if(span.textContent?.toLocaleLowerCase().includes(query))span.classList.add('pdf-find-match');});return;}
      if(offset%8===0)await new Promise(resolve=>setTimeout(resolve,0));
    }
    if(request===searchVersion){noMatches.hidden=false;loading.hidden=true;}
  });
  new ResizeObserver(()=>{if(mode==='pdf'&&Math.abs(host.clientWidth-lastWidth)>1)void render();}).observe(host);
  new MutationObserver(()=>{if(mode==='pdf')void render();}).observe(root,{attributes:true,attributeFilter:['data-theme']});
  window.addEventListener('popstate',()=>setMode(new URLSearchParams(location.search).get('view')==='pdf'?'pdf':'online',false));
  setMode(new URLSearchParams(location.search).get('view')==='pdf'||location.hash==='#pdf-reader'?'pdf':'online',false);
}
