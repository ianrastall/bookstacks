import { defineCollection, z } from 'astro:content';
import fs from 'node:fs';
import path from 'node:path';
import { parseTeiBook, slugify, slugifyAuthor } from './utils/teiParser';

const teiLoader = () => {
  return {
    name: 'tei-loader',
    load: async ({ store }: any) => {
      // Clear the persisted store so content removed from the TEI sources
      // (e.g. a dropped chapter) doesn't linger from a previous build.
      store.clear();

      const teiDir = path.resolve('./tei-source');
      if (!fs.existsSync(teiDir)) return;

      const files = fs.readdirSync(teiDir).filter(f => f.endsWith('.xml'));
      
      const authorProcessed = new Set();
      const booksBySlug = new Map<string, any>();

      // First pass: parse all files and group by book
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

        if (!booksBySlug.has(bookSlug)) {
          booksBySlug.set(bookSlug, {
            authorSlug,
            bookSlug,
            bookData: {
              ...bookData,
              persons: { ...bookData.persons },
              places: { ...bookData.places },
              chaptersMap: new Map() // n -> chapter
            }
          });
        }

        const aggregated = booksBySlug.get(bookSlug).bookData;
        Object.assign(aggregated.persons, bookData.persons);
        Object.assign(aggregated.places, bookData.places);

        for (const chap of bookData.chapters) {
          if (!aggregated.chaptersMap.has(chap.n)) {
            aggregated.chaptersMap.set(chap.n, { ...chap, versions: [...chap.versions] });
          } else {
            const existingChap = aggregated.chaptersMap.get(chap.n);
            // Append versions from this file
            existingChap.versions.push(...chap.versions);
            // If the current file is the 'en' translation or 'translation' subtype, 
            // use its HTML as the default chapter HTML (optional, but good for base layout)
            if (chap.versions.some((v: any) => v.lang === 'en' || v.id === 'translation')) {
              existingChap.html = chap.html;
            }
          }
        }
      }

      // Second pass: emit book indexes and chapters
      for (const [bookSlug, bookGroup] of booksBySlug.entries()) {
        const { authorSlug, bookData } = bookGroup;
        
        // Add book index
        store.set({
          id: `${authorSlug}/${bookSlug}/index`,
          data: {
            layout: 'book_index',
            title: bookData.title,
            book_title: bookData.title,
            author: bookData.author,
            persons: bookData.persons,
            places: bookData.places
          }
        });
        
        // Add chapters
        const chapters = Array.from(bookData.chaptersMap.values()) as any[];
        // Sort chapters just in case (assuming n can be sorted numerically, though some are strings)
        // chapter_order logic will handle the actual sorting in Astro pages.
        for (let i = 0; i < chapters.length; i++) {
          const chap = chapters[i];
          // We set html to the first version's html if we have versions, to ensure there's a fallback.
          let chapterHtml = chap.html;
          if (chap.versions && chap.versions.length > 0) {
              const enVersion = chap.versions.find((v: any) => v.lang === 'en' || v.id === 'translation');
              if (enVersion) chapterHtml = enVersion.html;
              else chapterHtml = chap.versions[0].html;
          }

          store.set({
            id: `${authorSlug}/${bookSlug}/chapter-${chap.n}`,
            data: {
              layout: 'book',
              title: chap.title,
              chapter_order: parseInt(chap.n || '', 10) || (i + 1),
              book: bookData.title,
              author: bookData.author,
              html: chapterHtml,
              versions: chap.versions || []
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
    html: z.string().optional(),
    versions: z.array(z.any()).optional(),
    persons: z.record(z.any()).optional(),
    places: z.record(z.any()).optional()
  })
});

export const collections = { authors };
