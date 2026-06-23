import { defineCollection, z } from 'astro:content';
import fs from 'node:fs';
import path from 'node:path';
import { parseTeiBook, slugify, slugifyAuthor } from './utils/teiParser';

const teiLoader = () => {
  return {
    name: 'tei-loader',
    load: async ({ store, logger }: any) => {
      const teiDir = path.resolve('./tei-source');
      if (!fs.existsSync(teiDir)) return;
      
      const files = fs.readdirSync(teiDir).filter(f => f.endsWith('.xml'));
      
      const authorProcessed = new Set();

      for (const file of files) {
        const filePath = path.join(teiDir, file);
        const bookData = parseTeiBook(filePath);
        
        const authorSlug = slugifyAuthor(bookData.author);
        const bookSlug = slugify(bookData.title);
        
        // Add author index if not already added
        if (!authorProcessed.has(authorSlug)) {
          authorProcessed.add(authorSlug);
          store.set({
            id: `${authorSlug}/index`,
            data: {
              layout: 'author_index',
              title: bookData.author,
              author_name: bookData.author
            }
          });
        }
        
        // Add book index
        store.set({
          id: `${authorSlug}/${bookSlug}/index`,
          data: {
            layout: 'book_index',
            title: bookData.title,
            book_title: bookData.title,
            author: bookData.author
          }
        });
        
        // Add chapters
        for (let i = 0; i < bookData.chapters.length; i++) {
          const chap = bookData.chapters[i];
          store.set({
            id: `${authorSlug}/${bookSlug}/chapter-${chap.n}`,
            data: {
              layout: 'book',
              title: chap.title,
              chapter_order: parseInt(chap.n || '', 10) || (i + 1),
              book: bookData.title,
              author: bookData.author,
              html: chap.html
            }
          });
        }
      }
    }
  };
};

const authors = defineCollection({
  loader: teiLoader(),
  schema: z.object({
    title: z.string().optional(),
    layout: z.string().optional(),
    author_name: z.string().optional(),
    book_title: z.string().optional(),
    author: z.string().optional(),
    book: z.string().optional(),
    chapter_order: z.number().optional(),
    toc_section: z.string().optional(),
    toc_title: z.string().optional(),
    html: z.string().optional()
  })
});

export const collections = { authors };
