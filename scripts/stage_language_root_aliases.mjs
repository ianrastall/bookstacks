#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const outputRoot = path.join(root, 'dist');
const locales = ['en', 'fr', 'es', 'grc', 'ru'];

for (const locale of locales) {
  const source = path.join(outputRoot, `${locale}.html`);
  const destination = path.join(outputRoot, locale, 'index.html');
  const html = await fs.readFile(source, 'utf8');

  if (!html.includes(`<html lang="${locale}"`)) {
    throw new Error(`Unexpected language homepage output: ${source}`);
  }

  await fs.mkdir(path.dirname(destination), { recursive: true });
  await fs.writeFile(destination, html, 'utf8');
  console.log(`Added /${locale}/ alias.`);
}
