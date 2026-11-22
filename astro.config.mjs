import { defineConfig } from 'astro/config';

// Unnatural Death's chapters moved inside their parts on 22 November 2026.
const unnaturalDeath = '/en/authors/sayers/unnatural-death';
const unnaturalDeathParts = [[1, 1, 9], [2, 10, 18], [3, 19, 23]];
const unnaturalDeathRedirects = Object.fromEntries(unnaturalDeathParts.flatMap(([part, first, last]) => [
  [`${unnaturalDeath}/part-${part}`, `${unnaturalDeath}/part-${part}/chapter-${first}`],
  ...Array.from({ length: last - first + 1 }, (_, index) => [
    `${unnaturalDeath}/chapter-${first + index}`, `${unnaturalDeath}/part-${part}/chapter-${first + index}`,
  ]),
]));

export default defineConfig({
  site: 'https://bookstacks.org',
  output: 'static',
  trailingSlash: 'never',
  redirects: {
    '/authors/austen-jane': '/authors/austen',
    '/authors/dickens-charles': '/authors/dickens',
    '/authors/dostoevsky-fyodor': '/authors/dostoevsky',
    '/authors/tolstoy-leo': '/authors/tolstoy',
    ...unnaturalDeathRedirects,
  },
  build: {
    format: 'file',
  },
});
