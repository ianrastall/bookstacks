import { isLocale, type Locale } from '../lib/i18n';
import { preferredLocale, text } from '../lib/interface';
const root = document.documentElement;
const choice = document.querySelector<HTMLSelectElement>('#interface-language')!;
let saved: string | null = null;
try { saved = localStorage.getItem('bookstacks-interface-language'); } catch { /* Optional storage. */ }
const explicit = new URLSearchParams(location.search).get('ui');
let override = explicit === 'auto' ? null : explicit && isLocale(explicit) ? explicit : saved && isLocale(saved) ? saved : null;
function apply() {
 const locale: Locale = override && isLocale(override) ? override : preferredLocale(navigator.languages?.length ? navigator.languages : [navigator.language]);
 root.lang = locale;
 choice.value = override || 'auto';
 for (const node of document.querySelectorAll<HTMLElement>('[data-i18n]')) {
  node.textContent = text(locale, node.dataset.i18n!, JSON.parse(node.dataset.i18nArgs || '[]'));
 }
 for (const attribute of ['aria-label','title']) {
  for (const node of document.querySelectorAll<HTMLElement>(`[data-i18n-${attribute}]`)) {
   node.setAttribute(attribute, text(locale, node.getAttribute(`data-i18n-${attribute}`)!));
  }
 }
 for (const note of document.querySelectorAll<HTMLElement>('.tei-note')) {
  const reference = note.querySelector<HTMLElement>('.tei-note-ref');
  const label = `${text(locale,'footnote')} ${reference?.textContent || ''}`;
  reference?.setAttribute('aria-label',label);
  const heading=note.querySelector<HTMLElement>('.tei-note-label');
  if (heading) { heading.textContent=label; heading.lang=locale; }
  const close=note.querySelector<HTMLElement>('.tei-note-close');
  close?.setAttribute('aria-label',text(locale,'closeFootnote'));
  if(close) close.lang=locale;
 }
 const titleKey = root.dataset.titleKey;
 if (titleKey) document.title = `${text(locale,titleKey)} · Bookstacks`;
 document.dispatchEvent(new CustomEvent('interfacechange', { detail: locale }));
}
function remember() {
 try { if (override) localStorage.setItem('bookstacks-interface-language',override); else localStorage.removeItem('bookstacks-interface-language'); }
 catch { document.querySelector<HTMLElement>('#interface-feedback')!.textContent = text(root.lang as Locale,'c.11'); }
}
if (explicit === 'auto' || (explicit && isLocale(explicit))) remember();
choice.disabled = false;
choice.addEventListener('change', () => {
 override = isLocale(choice.value) ? choice.value : null;
 apply(); remember();
 // A URL override is useful for shared links and for storage-restricted browsers.
 const url = new URL(location.href);
 if (override) url.searchParams.set('ui',override); else url.searchParams.delete('ui');
 history.replaceState(null,'',url);
});
// Carry an explicit choice through ordinary internal navigation, including when storage is unavailable.
document.addEventListener('click', event => {
 const link = (event.target as Element).closest<HTMLAnchorElement>('a[href]');
 if (!override || !link || link.hasAttribute('download')) return;
 const url = new URL(link.href);
 if (url.origin !== location.origin || /\.(xml|pdf)$/i.test(url.pathname) || link.getAttribute('href')?.startsWith('#')) return;
 url.searchParams.set('ui',override); link.href = url.href;
});
window.addEventListener('languagechange', () => { if (!override) apply(); });
window.addEventListener('storage', event => {
 if (event.key !== 'bookstacks-interface-language' && event.key !== null) return;
 override = event.newValue && isLocale(event.newValue) ? event.newValue : null; apply();
});
apply();
