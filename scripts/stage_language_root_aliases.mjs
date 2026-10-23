#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const outputRoot = path.join(root, 'dist');
// A localized homepage is a top-level <locale>.html whose document language is that locale.
const pages = (await fs.readdir(outputRoot)).filter((name) => name.endsWith('.html'));
let count = 0;

for (const page of pages) {
  const locale = page.slice(0, -'.html'.length);
  const source = path.join(outputRoot, page);
  const html = await fs.readFile(source, 'utf8');
  if (!html.includes(`<html lang="${locale}"`)) continue;

  const destination = path.join(outputRoot, locale, 'index.html');
  await fs.mkdir(path.dirname(destination), { recursive: true });
  await fs.writeFile(destination, html, 'utf8');
  console.log(`Added /${locale}/ alias.`);
  count += 1;
}

if (count < 6) throw new Error(`Expected localized homepages in ${outputRoot}; found ${count}.`);
