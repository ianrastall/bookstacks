export function foldSearch(value:string):string {return value.normalize('NFKD').replace(/\p{M}/gu,'').toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim();}
export function matchesSearch(haystack:string,query:string):boolean {const value=foldSearch(haystack);return foldSearch(query).split(/\s+/).every(word=>value.includes(word));}
import { EDITION_LANGUAGES, type EditionLanguage } from './i18n';

/** Initial book filter only; interface choices never call this. */
export function preferredBookLanguage(preferences: readonly string[]): EditionLanguage | '' {
 for (const preference of preferences) {
  try {
   const locale = new Intl.Locale(preference);
   const code = locale.language === 'zh' ? `zh-${locale.maximize().script}` : locale.language;
   if (EDITION_LANGUAGES.some(language => language.code === code)) return code as EditionLanguage;
  } catch { /* Ignore invalid browser language tags. */ }
 }
 return '';
}
