import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const authors = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./authors" }),
  schema: z.object({
    title: z.string().optional(),
    layout: z.string().optional(),
    author_name: z.string().optional(),
    book_title: z.string().optional(),
    author: z.string().optional(),
    book: z.string().optional(),
    chapter_order: z.number().optional(),
    toc_section: z.string().optional(),
    toc_title: z.string().optional()
  })
});

export const collections = { authors };
