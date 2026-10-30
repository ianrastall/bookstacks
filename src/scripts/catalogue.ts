import { currentLocale, text } from '../lib/interface';
import { matchesSearch } from '../lib/catalogue';

const get = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const search = get<HTMLInputElement>('book-search');
const language = get<HTMLSelectElement>('book-language');
const author = get<HTMLSelectElement>('book-author');
const sizeChoice = get<HTMLSelectElement>('book-page-size');
const rows = [...document.querySelectorAll<HTMLTableRowElement>('[data-book-row]')];
const params = new URLSearchParams(location.search);
search.value = params.get('q') || '';
author.value = params.get('author') || '';
// Only an explicit catalogue choice filters edition languages.
const requestedLanguage = params.get('language');
language.value = requestedLanguage === 'all' ? '' : requestedLanguage || '';
let savedSize: string | null = null;
try { savedSize = localStorage.getItem('bookstacks-page-size'); } catch { /* Optional storage. */ }
const requestedSize = params.get('size') ?? savedSize ?? '16';
sizeChoice.value = ['16', '32', '64', 'all'].includes(requestedSize) ? requestedSize : '16';
const requestedPage = Number(params.get('page'));
let page = Number.isSafeInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1;

function render(reset = false) {
 if (reset) page = 1;
 const size = sizeChoice.value === 'all' ? Math.max(1, rows.length) : Number(sizeChoice.value);
 const filtered = rows.filter(row =>
  (!language.value || row.dataset.language === language.value) &&
  (!author.value || row.dataset.author === author.value) &&
  matchesSearch(row.dataset.search || '', search.value));
 const pages = Math.max(1, Math.ceil(filtered.length / size));
 page = Math.min(page, pages);
 const visible = new Set(filtered.slice((page - 1) * size, page * size));
 rows.forEach(row => row.hidden = !visible.has(row));
 const locale = currentLocale();
 if (locale) get('book-count').textContent = text(locale, 'editionCount', [filtered.length]);
 get('book-empty').hidden = !!filtered.length;
 get('book-pagination').hidden = filtered.length <= size;
 get('book-page').textContent = `${page} / ${pages}`;
 get<HTMLButtonElement>('book-previous').disabled = page <= 1;
 get<HTMLButtonElement>('book-next').disabled = page >= pages;
 const url = new URL(location.href);
 for (const [key, value] of [
  ['q', search.value], ['language', language.value || 'all'],
  ['author', author.value], ['size', sizeChoice.value], ['page', page > 1 ? String(page) : ''],
 ]) {
  if (value) url.searchParams.set(key, value);
  else url.searchParams.delete(key);
 }
 history.replaceState(null, '', url);
}

sizeChoice.disabled = search.disabled = language.disabled = author.disabled = false;
sizeChoice.addEventListener('change', () => {
 try { localStorage.setItem('bookstacks-page-size', sizeChoice.value); } catch { /* Optional storage. */ }
 render(true);
});
search.addEventListener('input', () => render(true));
language.addEventListener('change', () => render(true));
author.addEventListener('change', () => render(true));
get('book-previous').addEventListener('click', () => { page--; render(); });
get('book-next').addEventListener('click', () => { page++; render(); });
document.addEventListener('interfacechange', () => render());
render();
