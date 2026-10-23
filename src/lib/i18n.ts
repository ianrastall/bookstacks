// Edition languages are the languages of literary texts in the corpus. They own
// the reading routes (/fr/authors/...). Interface locales only translate the
// site controls and never select, filter or substitute an edition.
export const EDITION_LANGUAGES = [
  { code: 'en', teiCode: 'eng', name: 'English', nativeName: 'English', dir: 'ltr' },
  { code: 'fr', teiCode: 'fra', name: 'French', nativeName: 'Français', dir: 'ltr' },
  { code: 'es', teiCode: 'spa', name: 'Spanish', nativeName: 'Español', dir: 'ltr' },
  { code: 'grc', teiCode: 'grc', name: 'Ancient Greek', nativeName: 'Ἑλληνική', dir: 'ltr' },
  { code: 'ru', teiCode: 'rus', name: 'Russian', nativeName: 'Русский', dir: 'ltr' },
  { code: 'zh-Hans', teiCode: 'zho', name: 'Simplified Chinese', nativeName: '简体中文', dir: 'ltr' },
] as const;

export type EditionLanguage = typeof EDITION_LANGUAGES[number]['code'];

export function isEditionLanguage(value: string): value is EditionLanguage {
  return EDITION_LANGUAGES.some((language) => language.code === value);
}

export function editionLanguageData(code: EditionLanguage) {
  return EDITION_LANGUAGES.find((language) => language.code === code)!;
}

export function editionLanguageName(edition: { code: string; languageName: string }): string {
  return isEditionLanguage(edition.code) ? editionLanguageData(edition.code).nativeName : edition.languageName;
}

export function editionDirection(code: string): 'ltr' | 'rtl' {
  return isEditionLanguage(code) ? editionLanguageData(code).dir : 'ltr';
}

// Ordered by BCP 47 tag. Every edition language is also an interface locale.
export const INTERFACE_LOCALES = [
  { code: 'ar', name: 'Arabic', nativeName: 'العربية', dir: 'rtl' },
  { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', dir: 'ltr' },
  { code: 'cs', name: 'Czech', nativeName: 'Čeština', dir: 'ltr' },
  { code: 'da', name: 'Danish', nativeName: 'Dansk', dir: 'ltr' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', dir: 'ltr' },
  { code: 'el', name: 'Greek', nativeName: 'Ελληνικά', dir: 'ltr' },
  { code: 'en', name: 'English', nativeName: 'English', dir: 'ltr' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', dir: 'ltr' },
  { code: 'fa', name: 'Persian', nativeName: 'فارسی', dir: 'rtl' },
  { code: 'fi', name: 'Finnish', nativeName: 'Suomi', dir: 'ltr' },
  { code: 'fil', name: 'Filipino', nativeName: 'Filipino', dir: 'ltr' },
  { code: 'fr', name: 'French', nativeName: 'Français', dir: 'ltr' },
  { code: 'grc', name: 'Ancient Greek', nativeName: 'Ἑλληνική', dir: 'ltr' },
  { code: 'he', name: 'Hebrew', nativeName: 'עברית', dir: 'rtl' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', dir: 'ltr' },
  { code: 'hu', name: 'Hungarian', nativeName: 'Magyar', dir: 'ltr' },
  { code: 'id', name: 'Indonesian', nativeName: 'Bahasa Indonesia', dir: 'ltr' },
  { code: 'it', name: 'Italian', nativeName: 'Italiano', dir: 'ltr' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語', dir: 'ltr' },
  { code: 'ko', name: 'Korean', nativeName: '한국어', dir: 'ltr' },
  { code: 'mr', name: 'Marathi', nativeName: 'मराठी', dir: 'ltr' },
  { code: 'ms', name: 'Malay', nativeName: 'Bahasa Melayu', dir: 'ltr' },
  { code: 'nb', name: 'Norwegian Bokmål', nativeName: 'Norsk bokmål', dir: 'ltr' },
  { code: 'nl', name: 'Dutch', nativeName: 'Nederlands', dir: 'ltr' },
  { code: 'pl', name: 'Polish', nativeName: 'Polski', dir: 'ltr' },
  { code: 'pt-BR', name: 'Portuguese (Brazil)', nativeName: 'Português (Brasil)', dir: 'ltr' },
  { code: 'pt-PT', name: 'Portuguese (Portugal)', nativeName: 'Português (Portugal)', dir: 'ltr' },
  { code: 'ro', name: 'Romanian', nativeName: 'Română', dir: 'ltr' },
  { code: 'ru', name: 'Russian', nativeName: 'Русский', dir: 'ltr' },
  { code: 'sv', name: 'Swedish', nativeName: 'Svenska', dir: 'ltr' },
  { code: 'sw', name: 'Swahili', nativeName: 'Kiswahili', dir: 'ltr' },
  { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்', dir: 'ltr' },
  { code: 'te', name: 'Telugu', nativeName: 'తెలుగు', dir: 'ltr' },
  { code: 'th', name: 'Thai', nativeName: 'ไทย', dir: 'ltr' },
  { code: 'tr', name: 'Turkish', nativeName: 'Türkçe', dir: 'ltr' },
  { code: 'uk', name: 'Ukrainian', nativeName: 'Українська', dir: 'ltr' },
  { code: 'ur', name: 'Urdu', nativeName: 'اردو', dir: 'rtl' },
  { code: 'vi', name: 'Vietnamese', nativeName: 'Tiếng Việt', dir: 'ltr' },
  { code: 'zh-Hans', name: 'Simplified Chinese', nativeName: '简体中文', dir: 'ltr' },
  { code: 'zh-Hant', name: 'Traditional Chinese', nativeName: '繁體中文', dir: 'ltr' },
] as const;

export type Locale = typeof INTERFACE_LOCALES[number]['code'];

// Compile-time guarantee that each edition language has an interface translation.
const editionLocalesAreInterfaceLocales: readonly Locale[] = EDITION_LANGUAGES.map((language) => language.code);
void editionLocalesAreInterfaceLocales;

export function isLocale(value: string): value is Locale {
  return INTERFACE_LOCALES.some((locale) => locale.code === value);
}

export function localeDirection(locale: Locale): 'ltr' | 'rtl' {
  return INTERFACE_LOCALES.find((item) => item.code === locale)!.dir;
}
