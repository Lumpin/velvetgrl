import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    category: z.string(),
    tags: z.array(z.string()),
    pinterest_title: z.string(),
    date: z.coerce.date(),
    draft: z.boolean().default(false),
    featured_image: z.string().optional(),
  }),
});

export const collections = { blog };
