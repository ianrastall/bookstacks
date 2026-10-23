import { isLocale, type Locale } from './i18n';
import en from '../i18n/locales/en';
import type { Message, MessageKey, Messages, Plural } from '../i18n/types';

// Interface locales are independent of the languages of literary editions.
// English is always bundled as the fallback; other catalogues are registered
// eagerly on the server (src/i18n/catalogues.ts) and on demand in the browser.
const catalogues = new Map<Locale, Messages>([['en', en]]);
let current: Locale | undefined;

export type TranslationArg = string | number;

export function registerMessages(locale: Locale, messages: Messages): void {
  catalogues.set(locale, messages);
}

export function hasMessages(locale: Locale): boolean {
  return catalogues.has(locale);
}

/** The interface locale applied in the browser, once its catalogue has loaded. */
export function currentLocale(): Locale | undefined {
  return current;
}

export function setCurrentLocale(locale: Locale): void {
  current = locale;
}

export function text(locale: Locale, key: string, args: TranslationArg[] = []): string {
  const catalogue = catalogues.get(locale);
  const effective = catalogue ? locale : 'en';
  const message = (catalogue ?? en)[key as MessageKey] ?? en[key as MessageKey];
  return message === undefined ? '' : format(effective, catalogue ?? en, message, args);
}

function format(locale: Locale, catalogue: Messages, message: Message, args: TranslationArg[]): string {
  if (typeof message !== 'string') return plural(locale, message, Number(args[0] ?? 0));
  return message.replace(/\{(\d+)(?:\|(\w+))?\}/g, (_, index: string, nested?: string) => {
    const value = args[Number(index)];
    if (nested) {
      const forms = catalogue[nested as MessageKey] ?? en[nested as MessageKey];
      return typeof forms === 'string' ? forms : plural(locale, forms, Number(value ?? 0));
    }
    return typeof value === 'number' ? formatNumber(locale, value) : String(value ?? '');
  });
}

// Ancient Greek has no CLDR data; Modern Greek rules give the same singular/plural split.
const FORMAT_LOCALE: Partial<Record<Locale, string>> = { grc: 'el' };
const pluralRules = new Map<Locale, Intl.PluralRules>();
const numberFormats = new Map<Locale, Intl.NumberFormat>();

function plural(locale: Locale, forms: Plural, count: number): string {
  let rules = pluralRules.get(locale);
  if (!rules) pluralRules.set(locale, rules = new Intl.PluralRules(FORMAT_LOCALE[locale] ?? locale));
  const category = rules.select(count) as keyof Plural;
  return (forms[category] ?? forms.other).replaceAll('#', formatNumber(locale, count));
}

function formatNumber(locale: Locale, value: number): string {
  let formatter = numberFormats.get(locale);
  if (!formatter) numberFormats.set(locale, formatter = new Intl.NumberFormat(FORMAT_LOCALE[locale] ?? locale));
  return formatter.format(value);
}

/** Matches browser language preferences, in order, to a supported interface locale. */
export function preferredLocale(preferences: readonly string[]): Locale {
  for (const preference of preferences) {
    const match = matchLocale(preference);
    if (match) return match;
  }
  return 'en';
}

function matchLocale(tag: string): Locale | undefined {
  let locale: Intl.Locale;
  try {
    locale = new Intl.Locale(Intl.getCanonicalLocales(tag)[0]);
  } catch {
    return undefined;
  }
  const { language } = locale;
  // Script decides Chinese; region only implies a script (zh-TW → Hant, zh-SG → Hans).
  if (language === 'zh') return locale.maximize().script === 'Hant' ? 'zh-Hant' : 'zh-Hans';
  if (language === 'pt') return locale.maximize().region === 'BR' ? 'pt-BR' : 'pt-PT';
  if (language === 'no' || language === 'nn') return 'nb';
  if (language === 'tl') return 'fil';
  // Modern Greek (el) and Ancient Greek (grc) are distinct locales; neither stands in for the other.
  return isLocale(language) ? language : undefined;
}
