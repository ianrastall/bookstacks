import { defineCollection, z } from 'astro:content';
import fs from 'node:fs';
import path from 'node:path';
import { bookStatusForSlugs } from './utils/bookStatus';
import { parseTeiBook, slugify, slugifyAuthor } from './utils/teiParser';

function hasFile(filesLower: Set<string>, fileName: string) {
  return filesLower.has(fileName.toLowerCase());
}

function getCanonicalTeiFiles(files: string[]) {
  const xmlFiles = files
    .filter((file) => file.toLowerCase().endsWith('.xml'))
    .sort((a, b) => a.localeCompare(b));

  const filesLower = new Set(xmlFiles.map((file) => file.toLowerCase()));

  return xmlFiles.filter((file) => {
    const fullMatch = file.match(/^(.*?)([-_.])full\.xml$/i);
    if (fullMatch) {
      const [, prefix, separator] = fullMatch;
      return !hasFile(filesLower, `${prefix}${separator}ru.xml`);
    }

    const langMatch = file.match(/^(.*?)([-_.])(grc|en|es|fr|pt|ru|de|it|la)\.xml$/i);
    if (!langMatch) return true;

    const [, prefix, separator, lang] = langMatch;
    const normalizedLang = lang.toLowerCase();

    // Dynamically determine the base text by checking for the most canonical language file
    const possibleBases = ['grc', 'en', 'ru', 'de', 'fr', 'es', 'pt', 'it', 'la'];
    for (const base of possibleBases) {
      if (hasFile(filesLower, `${prefix}${separator}${base}.xml`)) {
        return normalizedLang === base;
      }
    }

    return true;
  });
}

function cloneTocTreeForStore(nodes: any[]): any[] {
  return (Array.isArray(nodes) ? nodes : []).map((node) => {
    const labels = Array.isArray(node.labels)
      ? node.labels.filter(Boolean)
      : Array.from(node.labels || []).filter(Boolean);

    const cloned: any = {
      key: node.key,
      labels,
      labelByLang: node.labelByLang || {},
      children: cloneTocTreeForStore(node.children || [])
    };

    if (node.chapter?.id) {
      cloned.chapter = { id: node.chapter.id };
    } else if (node.chapter?.href) {
      cloned.chapter = { href: node.chapter.href };
    }

    return cloned;
  });
}

function chapterSortValue(chapter: any, fallback: number) {
  if (Number.isFinite(chapter.sortKey)) return chapter.sortKey;
  const parsed = Number.parseFloat(chapter.n || '');
  return Number.isFinite(parsed) ? parsed : fallback + 1;
}

const teiLoader = () => {
  return {
    name: 'tei-loader',
    load: async ({ store }: any) => {
      // Clear the persisted store so content removed from the TEI sources
      // (e.g. a dropped chapter) doesn't linger from a previous build.
      store.clear();

      const teiDir = path.resolve('./tei-source');
      if (!fs.existsSync(teiDir)) return;

      const files = getCanonicalTeiFiles(fs.readdirSync(teiDir));
      const authorProcessed = new Set<string>();

      for (const file of files) {
        const filePath = path.join(teiDir, file);
        const bookData = parseTeiBook(filePath);

        const authorSlug = slugifyAuthor(bookData.author);
        const bookSlug = slugify(bookData.title);

        if (!authorProcessed.has(authorSlug)) {
          authorProcessed.add(authorSlug);
          store.set({
            id: `${authorSlug}/index`,
            data: {
              layout: 'author_index',
              title: bookData.author,
              author_name: bookData.author,
              author_dates: bookData.authorDates || ''
            }
          });
        }

        const chapters = [...bookData.chapters]
          .sort((a: any, b: any) => chapterSortValue(a, 0) - chapterSortValue(b, 0));

        for (const chap of chapters) {
          chap.id = `${authorSlug}/${bookSlug}/${chap.slugPath || `chapter-${chap.n}`}`;
        }

        const tocTree = cloneTocTreeForStore(bookData.tocTree || []);
        const bookStatus = bookStatusForSlugs(authorSlug, bookSlug);

        store.set({
          id: `${authorSlug}/${bookSlug}/index`,
          data: {
            layout: 'book_index',
            title: bookData.title,
            book_title: bookData.title,
            author: bookData.author,
            book_status: bookStatus.state,
            book_status_label: bookStatus.label,
            book_status_description: bookStatus.description,
            book_status_icon: bookStatus.icon,
            persons: bookData.persons,
            places: bookData.places,
            tocTree
          }
        });

        for (let i = 0; i < chapters.length; i++) {
          const chap = chapters[i];

          let chapterHtml = chap.html;
          if (chap.versions && chap.versions.length > 0) {
            const enVersion = chap.versions.find((v: any) => v.lang === 'en' || v.id === 'translation');
            chapterHtml = enVersion?.html || chap.versions[0].html;
          }

          store.set({
            id: chap.id,
            data: {
              layout: 'book',
              title: chap.title,
              chapter_order: chapterSortValue(chap, i),
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
    author_dates: z.string().optional(),
    book_title: z.string().optional(),
    author: z.string().optional(),
    book: z.string().optional(),
    book_status: z.enum(['unfinished', 'finished', 'fully-tagged']).optional(),
    book_status_label: z.string().optional(),
    book_status_description: z.string().optional(),
    book_status_icon: z.string().optional(),
    chapter_order: z.number().optional(),
    toc_section: z.string().optional(),
    toc_title: z.string().optional(),
    tocTree: z.array(z.any()).optional(),
    html: z.string().optional(),
    versions: z.array(z.any()).optional(),
    persons: z.record(z.any()).optional(),
    places: z.record(z.any()).optional()
  })
});

export const collections = { authors };
