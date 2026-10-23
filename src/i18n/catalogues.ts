// Server-side registration of every interface catalogue. Import this only from
// Astro frontmatter or Node code; browser scripts load catalogues on demand.
import { isLocale } from '../lib/i18n';
import { registerMessages } from '../lib/interface';
import type { Messages } from './types';

const modules = import.meta.glob<{ default: Messages }>('./locales/*.ts', { eager: true });

for (const [file, module] of Object.entries(modules)) {
  const locale = file.slice('./locales/'.length, -'.ts'.length);
  if (!isLocale(locale)) throw new Error(`Interface catalogue without a declared locale: ${file}`);
  registerMessages(locale, module.default);
}
