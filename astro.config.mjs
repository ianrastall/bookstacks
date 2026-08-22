import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://bookstacks.org',
  output: 'static',
  trailingSlash: 'never',
  redirects: {
    '/authors/austen-jane': '/authors/austen',
    '/authors/dickens-charles': '/authors/dickens',
    '/authors/dostoevsky-fyodor': '/authors/dostoevsky',
    '/authors/tolstoy-leo': '/authors/tolstoy',
  },
  build: {
    format: 'file',
  },
});
