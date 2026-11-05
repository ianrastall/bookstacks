import { currentLocale, text } from '../lib/interface';
import { accentForeground, readableAccent } from '../lib/appearance';

const root = document.documentElement;
const dialog = document.querySelector<HTMLDialogElement>('#appearance-dialog')!;
const picker = document.querySelector<HTMLInputElement>('#accent-picker')!;
const theme = document.querySelector<HTMLSelectElement>('#theme-choice')!;
const illustrations = document.querySelector<HTMLSelectElement>('#illustration-choice')!;
const radios = [...document.querySelectorAll<HTMLInputElement>('input[name="accent-mode"]')];
const feedback = document.querySelector<HTMLElement>('#appearance-feedback')!;
function read(key: string) { try { return localStorage.getItem(key); } catch { return null; } }
function save(key: string, value: string | null) {
  try { if (value === null) localStorage.removeItem(key); else localStorage.setItem(key, value); }
  catch { feedback.textContent = text(currentLocale() ?? 'en','preferenceNotSaved'); }
}
let custom = read('bookstacks-accent');
if (!custom || !/^#[0-9a-f]{6}$/i.test(custom)) custom = null;
// CSS system colors remain live. Poll only the resolved value while visible so
// custom text/focus contrast also follows an OS/browser accent change.
const probe = document.createElement('span');
probe.className = 'accent-probe';
probe.setAttribute('aria-hidden', 'true');
document.body.append(probe);
let previous = '';
function apply() {
  const isDark = root.dataset.theme !== 'light';
  const source = custom || getComputedStyle(probe).color;
  if (source === previous && root.dataset.appearanceTheme === root.dataset.theme) return;
  previous = source;
  root.dataset.appearanceTheme = root.dataset.theme;
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d')!;
  ctx.fillStyle = source;
  const resolved = ctx.fillStyle;
  const hex = /^#[0-9a-f]{6}$/i.test(resolved) ? resolved : '#c8a96b';
  if (custom) root.style.setProperty('--accent', custom); else root.style.removeProperty('--accent');
  root.style.setProperty('--on-accent', accentForeground(hex));
  root.style.setProperty('--accent-strong', readableAccent(hex, isDark ? '#2b2824' : '#eae6de'));
  picker.value = custom || hex;
  document.querySelector('#accent-value')!.textContent = picker.value.toUpperCase();
  picker.disabled = !custom;
  radios.forEach(radio => radio.checked = radio.value === (custom ? 'custom' : 'system'));
}
theme.value = root.dataset.theme || 'dark';
function linkedIllustrations() {
  const value = new URLSearchParams(location.search).get('illustrations');
  return value === 'photos' || value === 'sketches' ? value : null;
}
function syncIllustrations() {
  const value = linkedIllustrations() ?? (read('bookstacks-illustrations') === 'photos' ? 'photos' : 'sketches');
  root.dataset.illustrations = illustrations.value = value;
}
syncIllustrations();
apply();
document.querySelector<HTMLButtonElement>('#appearance-open')!.disabled = false;
document.querySelector('#appearance-open')!.addEventListener('click', () => dialog.showModal());
document.querySelector('#appearance-close')!.addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => { if (event.target === dialog) { const b = dialog.getBoundingClientRect(); const e = event as MouseEvent; if (e.clientX < b.left || e.clientX > b.right || e.clientY < b.top || e.clientY > b.bottom) dialog.close(); } });
theme.addEventListener('change', () => { root.dataset.theme = theme.value; save('bookstacks-theme', theme.value); apply(); });
illustrations.addEventListener('change', () => {
  root.dataset.illustrations = illustrations.value;
  const url = new URL(location.href);
  try {
    localStorage.setItem('bookstacks-illustrations', illustrations.value);
    url.searchParams.delete('illustrations');
    feedback.textContent = text(currentLocale() ?? 'en', 'settingsSaved');
  } catch {
    url.searchParams.set('illustrations', illustrations.value);
    feedback.textContent = '';
  }
  if (url.href !== location.href) history.replaceState(history.state, '', url);
});
// Carry the choice through ordinary site links when it lives in the URL.
document.addEventListener('click', event => {
  const value = linkedIllustrations();
  if (!value) return;
  const link = (event.target as Element).closest<HTMLAnchorElement>('a[href]');
  if (!link || link.hasAttribute('download') || link.getAttribute('href')?.startsWith('#')) return;
  const url = new URL(link.href);
  if (url.origin !== location.origin || /\.(xml|pdf|epub)$/i.test(url.pathname)) return;
  url.searchParams.set('illustrations', value);
  link.href = url.href;
});
window.addEventListener('pageshow', event => { if (event.persisted) syncIllustrations(); });
picker.addEventListener('input', () => { custom = picker.value; save('bookstacks-accent', custom); apply(); });
function reset() { custom = null; previous = ''; save('bookstacks-accent', null); save('bookstacks-palette',null); apply(); }
radios.forEach(radio => radio.addEventListener('change', () => { if (radio.value === 'system') reset(); else { custom = picker.value; save('bookstacks-accent', custom); apply(); } }));
document.querySelector('#accent-reset')!.addEventListener('click', reset);
window.addEventListener('storage', event => {
  const savedTheme = read('bookstacks-theme');
  root.dataset.theme = savedTheme === 'light' ? 'light' : 'dark'; theme.value = root.dataset.theme;
  if (event.key === 'bookstacks-illustrations' || event.key === null) syncIllustrations();
  const saved = read('bookstacks-accent'); custom = saved && /^#[0-9a-f]{6}$/i.test(saved) ? saved : null;
  previous = ''; apply();
});
window.setInterval(() => { if (!document.hidden && !custom) apply(); }, 1500);
