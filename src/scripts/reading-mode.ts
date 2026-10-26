/** One shared column and URL state for HTML, PDF and EPUB renderers. */
export type ReadingMode='online'|'pdf'|'epub';
const root=document.documentElement;
let current:ReadingMode='online';
export const readingMode=()=>current;
export function setReadingMode(value:string,changeUrl=true){
  const requested=value==='pdf'||value==='epub'?value:'online';
  current=requested==='online'||document.querySelector(`[data-${requested}-pane]`)?requested:'online';
  if(current!=='online')document.querySelector<HTMLButtonElement>('.reader-expanded .reader-fullscreen')?.click();
  root.dataset.readingMode=current;
  const online=document.querySelector<HTMLElement>('[data-online-content]');if(online)online.hidden=current!=='online';
  for(const format of ['pdf','epub']){const panel=document.querySelector<HTMLElement>(`[data-${format}-pane]`);if(panel)panel.hidden=current!==format;}
  const title=document.querySelector<HTMLElement>('[data-reader-title]');
  if(title)title.textContent=(current==='online'?title.dataset.onlineTitle:title.dataset.pdfTitle)??'';
  document.querySelectorAll<HTMLElement>('[data-online-only]').forEach(el=>el.hidden=current!=='online');
  document.querySelectorAll<HTMLButtonElement>('[data-reading-mode]').forEach(button=>{button.disabled=false;button.setAttribute('aria-pressed',String(button.dataset.readingMode===current));});
  if(changeUrl){const url=new URL(location.href);if(current==='online')url.searchParams.delete('view');else url.searchParams.set('view',current);if(url.hash==='#pdf-reader')url.hash='';history.replaceState(null,'',url);}
  window.dispatchEvent(new CustomEvent('bookstacks:reading-mode',{detail:current}));
}
document.querySelectorAll<HTMLButtonElement>('[data-reading-mode]').forEach(button=>button.addEventListener('click',()=>setReadingMode(button.dataset.readingMode!)));
window.addEventListener('popstate',()=>setReadingMode(new URLSearchParams(location.search).get('view')??'online',false));
setReadingMode(new URLSearchParams(location.search).get('view')??(location.hash==='#pdf-reader'?'pdf':'online'),false);
