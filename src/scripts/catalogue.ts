import { text } from '../lib/interface';
import type { Locale } from '../lib/i18n';
import { matchesSearch } from '../lib/catalogue';
const get=<T extends HTMLElement>(id:string)=>document.getElementById(id) as T;
const search=get<HTMLInputElement>('book-search'),language=get<HTMLSelectElement>('book-language'),author=get<HTMLSelectElement>('book-author');
const rows=[...document.querySelectorAll<HTMLTableRowElement>('[data-book-row]')];
const params=new URLSearchParams(location.search);search.value=params.get('q')||'';language.value=params.get('language')||'';author.value=params.get('author')||'';
let page=Math.max(1,Number(params.get('page'))||1);const size=16;
function render(reset=false){if(reset)page=1;const filtered=rows.filter(row=>(!language.value||row.dataset.language===language.value)&&(!author.value||row.dataset.author===author.value)&&matchesSearch(row.dataset.search||'',search.value));const pages=Math.max(1,Math.ceil(filtered.length/size));page=Math.min(page,pages);const visible=new Set(filtered.slice((page-1)*size,page*size));rows.forEach(row=>row.hidden=!visible.has(row));
 get<HTMLElement>('book-count').textContent=text(document.documentElement.lang as Locale,'editionCount',[filtered.length]);get<HTMLElement>('book-empty').hidden=!!filtered.length;get<HTMLElement>('book-pagination').hidden=filtered.length<=size;get<HTMLElement>('book-page').textContent=`${page} / ${pages}`;get<HTMLButtonElement>('book-previous').disabled=page<=1;get<HTMLButtonElement>('book-next').disabled=page>=pages;
 const url=new URL(location.href);for(const [key,value]of [['q',search.value],['language',language.value],['author',author.value],['page',page>1?String(page):'']]){if(value)url.searchParams.set(key,value);else url.searchParams.delete(key);}history.replaceState(null,'',url);
}
search.disabled=language.disabled=author.disabled=false;search.addEventListener('input',()=>render(true));language.addEventListener('change',()=>render(true));author.addEventListener('change',()=>render(true));get('book-previous').addEventListener('click',()=>{page--;render();});get('book-next').addEventListener('click',()=>{page++;render();});render();

document.addEventListener("interfacechange",()=>render());
