import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://bookstacks.org',
  output: 'static',
  build: {
    format: 'file'
  }
});
