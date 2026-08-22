import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://bookstacks.org',
  output: 'static',
  trailingSlash: 'never',
  build: {
    format: 'file',
  },
});
