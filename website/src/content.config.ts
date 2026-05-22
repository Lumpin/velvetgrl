import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';
import { CATEGORIES } from './data/categories.ts';

const categorySlugs = CATEGORIES.map(c => c.slug) as [string, ...string[]];

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    category: z.enum(categorySlugs),
    tags: z.array(z.string()),
    pinterest_title: z.string(),
    date: z.coerce.date(),
    draft: z.boolean().default(false),
    featured_image: z.string().optional(),
  }),
});

export const collections = { blog };
