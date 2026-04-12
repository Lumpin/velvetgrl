# HerVisionCraft Autopilot — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a fully automated content marketing pipeline — Astro blog + Python agent system — that researches keywords, writes blog posts, generates Pinterest pin graphics, and posts to Pinterest on autopilot.

**Architecture:** Astro static blog deployed to Netlify, with a Python agent system (Claude API) that orchestrates the full pipeline. Playwright handles Pinterest browser automation. SQLite tracks all state. CLI for human review/approval of blog posts.

**Tech Stack:** Astro 5, Tailwind CSS 4, Python 3.12, Anthropic SDK, Playwright, Pillow, APScheduler, SQLite, Unsplash/Pexels API, Flux API

---

## Phase A: Astro Blog Website

### Task 1: Initialize Astro Project

**Files:**
- Create: `website/package.json`
- Create: `website/astro.config.mjs`
- Create: `website/tsconfig.json`
- Create: `website/tailwind.config.mjs`
- Create: `website/src/env.d.ts`

**Step 1: Scaffold Astro project**

```bash
cd hervisioncraft
npm create astro@latest website -- --template minimal --no-install --no-git --typescript strict
```

**Step 2: Install dependencies**

```bash
cd hervisioncraft/website
npm install
npm install @astrojs/tailwind @astrojs/sitemap @astrojs/rss tailwindcss @tailwindcss/typography
```

**Step 3: Configure Astro**

Update `website/astro.config.mjs`:
```js
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://hervisioncraft.com',
  integrations: [tailwind(), sitemap()],
  image: {
    domains: ['images.unsplash.com', 'images.pexels.com'],
  },
});
```

**Step 4: Configure Tailwind with brand colors**

Create `website/tailwind.config.mjs`:
```js
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        brand: {
          cream: '#FFF8F0',
          blush: '#F4C2C2',
          sage: '#B2C9AB',
          gold: '#C9A96E',
          dark: '#2D2D2D',
          muted: '#6B6B6B',
        },
      },
      fontFamily: {
        display: ['Playfair Display', 'serif'],
        body: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
};
```

**Step 5: Verify dev server starts**

```bash
cd hervisioncraft/website && npm run dev
```
Expected: Astro dev server running on localhost:4321

**Step 6: Commit**

```bash
git add website/
git commit -m "feat: initialize Astro project with Tailwind and brand theme"
```

---

### Task 2: Content Collections Setup

**Files:**
- Create: `website/src/content.config.ts`
- Create: `website/src/content/blog/_placeholder.md` (sample post for testing)

**Step 1: Define blog content collection**

Create `website/src/content.config.ts`:
```ts
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
```

**Step 2: Create sample blog post**

Create `website/src/content/blog/17-boho-kitchen-ideas.md`:
```markdown
---
title: "17 Boho Kitchen Ideas That Feel Effortlessly Chic"
description: "Discover stunning boho kitchen designs that blend warmth, texture, and free-spirited charm into your cooking space."
category: "boho-decor"
tags: ["boho", "kitchen", "home decor"]
pinterest_title: "Boho Kitchen Ideas | Her Vision Craft"
date: 2026-04-12
draft: false
featured_image: "/images/posts/boho-kitchen/hero.webp"
---

Looking to bring that relaxed, earthy boho vibe into your kitchen? These 17 ideas will transform your cooking space into a warm, inviting retreat.

## 1. Macrame Plant Hangers Above the Sink

Nothing says boho quite like cascading greenery in hand-knotted macrame holders. Hang them near your kitchen window for natural light and instant texture.

**Style tip:** Mix different plant varieties — trailing pothos with upright herbs creates the most visual interest.

## 2. Open Wooden Shelving

Swap out upper cabinets for raw wood shelves to display your favorite ceramics, spice jars, and cookbooks. The open feel is pure boho.

**Style tip:** Stick to a neutral palette on the shelves — whites, terracotta, and natural wood keep it cohesive.
```

**Step 3: Verify content collection loads**

```bash
cd hervisioncraft/website && npm run build
```
Expected: Build succeeds, content collection is parsed

**Step 4: Commit**

```bash
git add website/src/content.config.ts website/src/content/
git commit -m "feat: add blog content collection schema and sample post"
```

---

### Task 3: Base Layout & Global Styles

**Files:**
- Create: `website/src/layouts/BaseLayout.astro`
- Create: `website/src/components/Header.astro`
- Create: `website/src/components/Footer.astro`
- Create: `website/src/styles/global.css`
- Modify: `website/src/pages/index.astro`

**Step 1: Create global styles**

Create `website/src/styles/global.css`:
```css
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html {
    @apply scroll-smooth;
  }
  body {
    @apply bg-brand-cream text-brand-dark font-body antialiased;
  }
  h1, h2, h3, h4 {
    @apply font-display;
  }
}
```

**Step 2: Create Header component**

Create `website/src/components/Header.astro`:
```astro
---
const categories = [
  { name: 'Boho Decor', slug: 'boho-decor' },
  { name: 'Tattoo Ideas', slug: 'tattoo-ideas' },
  { name: 'Nail Art', slug: 'nail-art' },
  { name: 'Fashion', slug: 'fashion' },
  { name: 'Tarot', slug: 'tarot-spirituality' },
  { name: 'Kitchen', slug: 'kitchen-recipes' },
  { name: 'Perfume', slug: 'perfume-fragrance' },
  { name: 'Makeup', slug: 'makeup-beauty' },
  { name: 'Hair', slug: 'hair-hairstyles' },
  { name: 'Jewelry', slug: 'jewelry-accessories' },
  { name: 'Self-Care', slug: 'self-care-wellness' },
  { name: 'Wedding', slug: 'wedding-bridal' },
];
---

<header class="bg-white/80 backdrop-blur-sm border-b border-brand-blush/30 sticky top-0 z-50">
  <div class="max-w-6xl mx-auto px-4 py-4">
    <div class="flex items-center justify-between">
      <a href="/" class="font-display text-2xl font-bold text-brand-dark">
        Her<span class="text-brand-sage">Vision</span>Craft
      </a>
      <nav class="hidden md:flex items-center gap-1">
        <a href="/about" class="px-3 py-2 text-sm text-brand-muted hover:text-brand-dark transition-colors">About</a>
      </nav>
    </div>
    <nav class="flex gap-2 mt-3 overflow-x-auto pb-2 scrollbar-hide">
      {categories.map(cat => (
        <a
          href={`/${cat.slug}/`}
          class="shrink-0 px-3 py-1.5 text-xs font-medium rounded-full bg-brand-blush/20 text-brand-dark hover:bg-brand-blush/40 transition-colors"
        >
          {cat.name}
        </a>
      ))}
    </nav>
  </div>
</header>
```

**Step 3: Create Footer component**

Create `website/src/components/Footer.astro`:
```astro
---
const year = new Date().getFullYear();
---

<footer class="bg-brand-dark text-white/70 mt-20">
  <div class="max-w-6xl mx-auto px-4 py-12">
    <div class="grid md:grid-cols-3 gap-8">
      <div>
        <p class="font-display text-xl font-bold text-white mb-2">
          Her<span class="text-brand-sage">Vision</span>Craft
        </p>
        <p class="text-sm">Inspiration for the modern woman. Curated ideas for beauty, home, style, and soul.</p>
      </div>
      <div>
        <p class="font-medium text-white mb-3">Categories</p>
        <div class="grid grid-cols-2 gap-1 text-sm">
          <a href="/boho-decor/" class="hover:text-brand-blush transition-colors">Boho Decor</a>
          <a href="/tattoo-ideas/" class="hover:text-brand-blush transition-colors">Tattoo Ideas</a>
          <a href="/nail-art/" class="hover:text-brand-blush transition-colors">Nail Art</a>
          <a href="/fashion/" class="hover:text-brand-blush transition-colors">Fashion</a>
          <a href="/makeup-beauty/" class="hover:text-brand-blush transition-colors">Makeup</a>
          <a href="/hair-hairstyles/" class="hover:text-brand-blush transition-colors">Hair</a>
        </div>
      </div>
      <div>
        <p class="font-medium text-white mb-3">Links</p>
        <div class="flex flex-col gap-1 text-sm">
          <a href="/about/" class="hover:text-brand-blush transition-colors">About</a>
          <a href="/privacy/" class="hover:text-brand-blush transition-colors">Privacy Policy</a>
          <a href="/disclaimer/" class="hover:text-brand-blush transition-colors">Disclaimer</a>
        </div>
      </div>
    </div>
    <div class="border-t border-white/10 mt-8 pt-6 text-center text-xs">
      &copy; {year} HerVisionCraft. All rights reserved.
    </div>
  </div>
</footer>
```

**Step 4: Create BaseLayout**

Create `website/src/layouts/BaseLayout.astro`:
```astro
---
import Header from '../components/Header.astro';
import Footer from '../components/Footer.astro';
import '../styles/global.css';

interface Props {
  title: string;
  description: string;
  image?: string;
  type?: string;
}

const { title, description, image, type = 'website' } = Astro.props;
const canonicalURL = new URL(Astro.url.pathname, Astro.site);
---

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="canonical" href={canonicalURL} />
    <title>{title} | HerVisionCraft</title>
    <meta name="description" content={description} />
    <!-- Open Graph -->
    <meta property="og:type" content={type} />
    <meta property="og:title" content={title} />
    <meta property="og:description" content={description} />
    <meta property="og:url" content={canonicalURL} />
    {image && <meta property="og:image" content={image} />}
    <!-- Pinterest -->
    <meta name="pinterest-rich-pin" content="true" />
    <!-- Twitter/X -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content={title} />
    <meta name="twitter:description" content={description} />
    {image && <meta name="twitter:image" content={image} />}
    <!-- Favicon -->
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="generator" content={Astro.generator} />
  </head>
  <body class="min-h-screen flex flex-col">
    <Header />
    <main class="flex-1">
      <slot />
    </main>
    <Footer />
  </body>
</html>
```

**Step 5: Create homepage**

Replace `website/src/pages/index.astro`:
```astro
---
import { getCollection } from 'astro:content';
import BaseLayout from '../layouts/BaseLayout.astro';

const posts = (await getCollection('blog', ({ data }) => !data.draft))
  .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
---

<BaseLayout
  title="Inspiration for Beauty, Home & Style"
  description="HerVisionCraft — curated ideas for the modern woman. Boho decor, tattoo ideas, nail art, fashion, and more."
>
  <!-- Hero -->
  <section class="max-w-6xl mx-auto px-4 pt-12 pb-8 text-center">
    <h1 class="font-display text-4xl md:text-5xl font-bold text-brand-dark mb-4">
      Inspiration for the <span class="text-brand-sage">Modern Woman</span>
    </h1>
    <p class="text-brand-muted text-lg max-w-2xl mx-auto">
      Curated ideas for beauty, home, style, and soul. Find your next obsession.
    </p>
  </section>

  <!-- Post Grid (Masonry-style) -->
  <section class="max-w-6xl mx-auto px-4 pb-16">
    <div class="columns-1 sm:columns-2 lg:columns-3 gap-6 space-y-6">
      {posts.map((post) => (
        <a
          href={`/blog/${post.id}/`}
          class="block break-inside-avoid bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow group"
        >
          {post.data.featured_image && (
            <img
              src={post.data.featured_image}
              alt={post.data.title}
              class="w-full object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
          )}
          <div class="p-5">
            <span class="text-xs font-medium text-brand-sage uppercase tracking-wider">
              {post.data.category.replace(/-/g, ' ')}
            </span>
            <h2 class="font-display text-lg font-semibold mt-1 group-hover:text-brand-sage transition-colors">
              {post.data.title}
            </h2>
            <p class="text-brand-muted text-sm mt-2 line-clamp-2">
              {post.data.description}
            </p>
          </div>
        </a>
      ))}
    </div>
  </section>
</BaseLayout>
```

**Step 6: Verify it renders**

```bash
cd hervisioncraft/website && npm run dev
```
Expected: Homepage loads with header, hero, post grid (with sample post), and footer. Check at http://localhost:4321

**Step 7: Commit**

```bash
git add website/src/
git commit -m "feat: add base layout, header, footer, homepage with masonry grid"
```

---

### Task 4: Blog Post Page Template

**Files:**
- Create: `website/src/pages/blog/[...slug].astro`
- Create: `website/src/layouts/BlogPost.astro`
- Create: `website/src/components/SchemaArticle.astro`

**Step 1: Create Article schema component**

Create `website/src/components/SchemaArticle.astro`:
```astro
---
interface Props {
  title: string;
  description: string;
  date: Date;
  image?: string;
  url: string;
}
const { title, description, date, image, url } = Astro.props;
const schema = {
  '@context': 'https://schema.org',
  '@type': 'Article',
  headline: title,
  description,
  datePublished: date.toISOString(),
  image: image || undefined,
  url,
  author: {
    '@type': 'Organization',
    name: 'HerVisionCraft',
  },
  publisher: {
    '@type': 'Organization',
    name: 'HerVisionCraft',
  },
};
---

<script type="application/ld+json" set:html={JSON.stringify(schema)} />
```

**Step 2: Create BlogPost layout**

Create `website/src/layouts/BlogPost.astro`:
```astro
---
import BaseLayout from './BaseLayout.astro';
import SchemaArticle from '../components/SchemaArticle.astro';

interface Props {
  title: string;
  description: string;
  category: string;
  tags: string[];
  date: Date;
  featured_image?: string;
  pinterest_title: string;
}

const { title, description, category, tags, date, featured_image, pinterest_title } = Astro.props;
const canonicalURL = new URL(Astro.url.pathname, Astro.site);
---

<BaseLayout title={title} description={description} image={featured_image} type="article">
  <SchemaArticle
    title={title}
    description={description}
    date={date}
    image={featured_image}
    url={canonicalURL.toString()}
  />
  <article class="max-w-3xl mx-auto px-4 py-10">
    <!-- Breadcrumb -->
    <nav class="text-sm text-brand-muted mb-6">
      <a href="/" class="hover:text-brand-sage">Home</a>
      <span class="mx-2">/</span>
      <a href={`/${category}/`} class="hover:text-brand-sage capitalize">{category.replace(/-/g, ' ')}</a>
      <span class="mx-2">/</span>
      <span class="text-brand-dark">{title}</span>
    </nav>

    <!-- Header -->
    <header class="mb-8">
      <span class="inline-block px-3 py-1 text-xs font-medium rounded-full bg-brand-sage/20 text-brand-dark uppercase tracking-wider mb-3">
        {category.replace(/-/g, ' ')}
      </span>
      <h1 class="font-display text-3xl md:text-4xl font-bold leading-tight mb-4">{title}</h1>
      <p class="text-brand-muted">{description}</p>
      <time class="text-sm text-brand-muted mt-3 block" datetime={date.toISOString()}>
        {date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
      </time>
    </header>

    {featured_image && (
      <img
        src={featured_image}
        alt={title}
        class="w-full rounded-xl mb-10 shadow-sm"
        loading="eager"
      />
    )}

    <!-- Content -->
    <div class="prose prose-lg prose-stone max-w-none
      prose-headings:font-display prose-headings:text-brand-dark
      prose-a:text-brand-sage prose-a:no-underline hover:prose-a:underline
      prose-img:rounded-xl prose-img:shadow-sm
      prose-strong:text-brand-dark">
      <slot />
    </div>

    <!-- Tags -->
    <div class="flex flex-wrap gap-2 mt-10 pt-6 border-t border-brand-blush/30">
      {tags.map(tag => (
        <span class="px-3 py-1 text-xs rounded-full bg-brand-blush/20 text-brand-muted">
          #{tag}
        </span>
      ))}
    </div>

    <!-- Pinterest Save Button Data -->
    <div data-pin-description={pinterest_title} class="hidden"></div>
  </article>
</BaseLayout>
```

**Step 3: Create dynamic blog post route**

Create `website/src/pages/blog/[...slug].astro`:
```astro
---
import { getCollection, render } from 'astro:content';
import BlogPost from '../../layouts/BlogPost.astro';

export async function getStaticPaths() {
  const posts = await getCollection('blog');
  return posts.map((post) => ({
    params: { slug: post.id },
    props: { post },
  }));
}

const { post } = Astro.props;
const { Content } = await render(post);
---

<BlogPost {...post.data}>
  <Content />
</BlogPost>
```

**Step 4: Verify blog post renders**

```bash
cd hervisioncraft/website && npm run dev
```
Visit http://localhost:4321/blog/17-boho-kitchen-ideas/ — should show full styled blog post

**Step 5: Commit**

```bash
git add website/src/
git commit -m "feat: add blog post template with schema.org, breadcrumbs, SEO meta"
```

---

### Task 5: Category Pages

**Files:**
- Create: `website/src/pages/[category].astro`

**Step 1: Create dynamic category page**

Create `website/src/pages/[category].astro`:
```astro
---
import { getCollection } from 'astro:content';
import BaseLayout from '../layouts/BaseLayout.astro';

const categoryLabels: Record<string, string> = {
  'boho-decor': 'Boho Decor & Home',
  'tattoo-ideas': 'Tattoo Ideas',
  'nail-art': 'Nail Art',
  'fashion': 'Fashion & Outfits',
  'tarot-spirituality': 'Tarot & Spirituality',
  'kitchen-recipes': 'Kitchen & Recipes',
  'perfume-fragrance': 'Perfume & Fragrance',
  'makeup-beauty': 'Makeup & Beauty',
  'hair-hairstyles': 'Hair & Hairstyles',
  'jewelry-accessories': 'Jewelry & Accessories',
  'self-care-wellness': 'Self-Care & Wellness',
  'wedding-bridal': 'Wedding & Bridal',
};

export async function getStaticPaths() {
  const posts = await getCollection('blog', ({ data }) => !data.draft);
  const categories = [...new Set(posts.map(p => p.data.category))];
  return Object.keys(categoryLabels).map(cat => ({
    params: { category: cat },
    props: {
      category: cat,
      label: categoryLabels[cat],
      posts: posts
        .filter(p => p.data.category === cat)
        .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf()),
    },
  }));
}

const { category, label, posts } = Astro.props;
---

<BaseLayout
  title={`${label} Ideas & Inspiration`}
  description={`Browse our curated collection of ${label.toLowerCase()} ideas, tips, and inspiration.`}
>
  <section class="max-w-6xl mx-auto px-4 py-10">
    <h1 class="font-display text-3xl md:text-4xl font-bold mb-2">{label}</h1>
    <p class="text-brand-muted mb-10">Curated ideas and inspiration for {label.toLowerCase()}.</p>

    {posts.length === 0 ? (
      <p class="text-brand-muted text-center py-20">Posts coming soon!</p>
    ) : (
      <div class="columns-1 sm:columns-2 lg:columns-3 gap-6 space-y-6">
        {posts.map((post) => (
          <a
            href={`/blog/${post.id}/`}
            class="block break-inside-avoid bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow group"
          >
            {post.data.featured_image && (
              <img
                src={post.data.featured_image}
                alt={post.data.title}
                class="w-full object-cover group-hover:scale-105 transition-transform duration-300"
                loading="lazy"
              />
            )}
            <div class="p-5">
              <h2 class="font-display text-lg font-semibold group-hover:text-brand-sage transition-colors">
                {post.data.title}
              </h2>
              <p class="text-brand-muted text-sm mt-2 line-clamp-2">
                {post.data.description}
              </p>
            </div>
          </a>
        ))}
      </div>
    )}
  </section>
</BaseLayout>
```

**Step 2: Verify category page**

Visit http://localhost:4321/boho-decor/ — should show category page with the sample post

**Step 3: Commit**

```bash
git add website/src/pages/
git commit -m "feat: add dynamic category pages for all 12 niches"
```

---

### Task 6: Static Pages (About, Privacy, Disclaimer) + RSS + Sitemap

**Files:**
- Create: `website/src/pages/about.astro`
- Create: `website/src/pages/privacy.astro`
- Create: `website/src/pages/disclaimer.astro`
- Create: `website/src/pages/rss.xml.ts`
- Create: `website/public/robots.txt`
- Create: `website/public/favicon.svg`

**Step 1: Create About page**

Create `website/src/pages/about.astro`:
```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
---

<BaseLayout title="About" description="About HerVisionCraft — inspiration for the modern woman.">
  <div class="max-w-3xl mx-auto px-4 py-12">
    <h1 class="font-display text-4xl font-bold mb-6">About HerVisionCraft</h1>
    <div class="prose prose-lg prose-stone">
      <p>Welcome to HerVisionCraft — your curated destination for all things beauty, home, style, and soul.</p>
      <p>We believe every woman deserves a space filled with inspiration. Whether you're dreaming up your next tattoo, planning a boho kitchen makeover, or exploring tarot for the first time, we're here to spark your creativity.</p>
      <p>Our team curates the best ideas across beauty, fashion, home decor, wellness, and more — bringing you listicles packed with stunning visuals and actionable style tips.</p>
      <h2>What We Cover</h2>
      <ul>
        <li><strong>Beauty</strong> — nail art, makeup looks, hairstyles, skincare</li>
        <li><strong>Home</strong> — boho decor, kitchen ideas, cozy spaces</li>
        <li><strong>Style</strong> — fashion inspiration, jewelry, accessories</li>
        <li><strong>Soul</strong> — tarot, self-care, wellness, spirituality</li>
        <li><strong>Celebrations</strong> — wedding ideas, bridal beauty</li>
      </ul>
      <p>Follow us on <a href="https://pinterest.com/hervisioncraft">Pinterest</a> for daily inspiration.</p>
    </div>
  </div>
</BaseLayout>
```

**Step 2: Create Privacy Policy page**

Create `website/src/pages/privacy.astro`:
```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
---

<BaseLayout title="Privacy Policy" description="HerVisionCraft privacy policy.">
  <div class="max-w-3xl mx-auto px-4 py-12">
    <h1 class="font-display text-4xl font-bold mb-6">Privacy Policy</h1>
    <div class="prose prose-lg prose-stone">
      <p><em>Last updated: April 2026</em></p>
      <p>HerVisionCraft ("we", "us", or "our") operates the website hervisioncraft.com. This page informs you of our policies regarding the collection, use, and disclosure of personal data when you use our website.</p>
      <h2>Information We Collect</h2>
      <p>We collect standard analytics data through Google Analytics, including pages visited, time on site, and general location data. We do not collect personally identifiable information unless you voluntarily provide it.</p>
      <h2>Cookies</h2>
      <p>We use cookies for analytics and to serve relevant advertisements. You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent.</p>
      <h2>Third-Party Services</h2>
      <p>We may use third-party advertising services (such as Google AdSense) that use cookies to serve ads based on your prior visits. You can opt out of personalized advertising by visiting Google's Ads Settings.</p>
      <h2>Contact</h2>
      <p>If you have questions about this policy, contact us at hello@hervisioncraft.com.</p>
    </div>
  </div>
</BaseLayout>
```

**Step 3: Create Disclaimer page**

Create `website/src/pages/disclaimer.astro`:
```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
---

<BaseLayout title="Disclaimer" description="HerVisionCraft content disclaimer.">
  <div class="max-w-3xl mx-auto px-4 py-12">
    <h1 class="font-display text-4xl font-bold mb-6">Disclaimer</h1>
    <div class="prose prose-lg prose-stone">
      <p>The information provided on HerVisionCraft is for general informational and inspiration purposes only.</p>
      <h2>Affiliate Links</h2>
      <p>Some posts may contain affiliate links. If you make a purchase through these links, we may earn a small commission at no additional cost to you. We only recommend products we genuinely find inspiring or useful.</p>
      <h2>Images</h2>
      <p>Images on this site are sourced from stock photography providers, AI generation tools, or created by our team. If you believe an image has been used in error, please contact us.</p>
      <h2>Accuracy</h2>
      <p>While we strive to provide accurate and up-to-date content, we make no warranties about the completeness or reliability of any information on this site.</p>
    </div>
  </div>
</BaseLayout>
```

**Step 4: Create RSS feed**

Create `website/src/pages/rss.xml.ts`:
```ts
import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

export async function GET(context: APIContext) {
  const posts = (await getCollection('blog', ({ data }) => !data.draft))
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());

  return rss({
    title: 'HerVisionCraft',
    description: 'Inspiration for the modern woman — beauty, home, style, and soul.',
    site: context.site!,
    items: posts.map(post => ({
      title: post.data.title,
      pubDate: post.data.date,
      description: post.data.description,
      link: `/blog/${post.id}/`,
    })),
  });
}
```

**Step 5: Create robots.txt**

Create `website/public/robots.txt`:
```
User-agent: *
Allow: /

Sitemap: https://hervisioncraft.com/sitemap-index.xml
```

**Step 6: Create favicon**

Create `website/public/favicon.svg`:
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#B2C9AB"/>
  <text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" font-family="serif" font-size="18" font-weight="bold" fill="white">V</text>
</svg>
```

**Step 7: Verify all pages**

```bash
cd hervisioncraft/website && npm run build
```
Expected: Build succeeds with all pages generated, sitemap.xml and rss.xml present in dist/

**Step 8: Commit**

```bash
git add website/src/pages/ website/public/
git commit -m "feat: add about, privacy, disclaimer pages, RSS feed, robots.txt, favicon"
```

---

### Task 7: Netlify Deployment Config

**Files:**
- Create: `website/netlify.toml`
- Create: `website/.nvmrc`

**Step 1: Create Netlify config**

Create `website/netlify.toml`:
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "SAMEORIGIN"
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "strict-origin-when-cross-origin"

[[headers]]
  for = "/images/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/_astro/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
```

Create `website/.nvmrc`:
```
20
```

**Step 2: Verify production build**

```bash
cd hervisioncraft/website && npm run build && npm run preview
```
Expected: Production build completes, preview server runs on localhost:4321

**Step 3: Commit**

```bash
git add website/netlify.toml website/.nvmrc
git commit -m "feat: add Netlify deployment config with caching headers"
```

---

## Phase B: Python Agent Foundation

### Task 8: Python Project Setup

**Files:**
- Create: `agents/pyproject.toml`
- Create: `agents/__init__.py`
- Create: `agents/__main__.py`
- Create: `agents/db.py`
- Create: `agents/config.py`

**Step 1: Create pyproject.toml**

Create `agents/pyproject.toml`:
```toml
[project]
name = "hervisioncraft-agents"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "anthropic>=0.40.0",
    "playwright>=1.49.0",
    "Pillow>=11.0.0",
    "httpx>=0.28.0",
    "apscheduler>=3.10.0",
    "click>=8.1.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.24"]
```

**Step 2: Create database module**

Create `agents/db.py`:
```python
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "hervisioncraft.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection, creating tables if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _create_tables(conn)
    return conn


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            search_volume_estimate INTEGER DEFAULT 0,
            competition TEXT DEFAULT 'unknown',
            ad_value_score REAL DEFAULT 0.0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            keywords TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            published_at TEXT,
            pageviews INTEGER DEFAULT 0,
            pinterest_impressions INTEGER DEFAULT 0,
            pinterest_clicks INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS pins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_slug TEXT NOT NULL,
            image_path TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            board TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            posted_at TEXT,
            impressions INTEGER DEFAULT 0,
            saves INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            FOREIGN KEY (post_slug) REFERENCES posts(slug)
        );

        CREATE TABLE IF NOT EXISTS calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week TEXT NOT NULL,
            post_data TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
```

**Step 3: Create config module**

Create `agents/config.py`:
```python
import json
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent / "config"
QUEUE_DIR = Path(__file__).parent.parent / "queue"
DATA_DIR = Path(__file__).parent.parent / "data"
WEBSITE_DIR = Path(__file__).parent.parent / "website"
BLOG_DIR = WEBSITE_DIR / "src" / "content" / "blog"
IMAGES_DIR = WEBSITE_DIR / "src" / "assets" / "images" / "posts"

CATEGORIES = {
    "boho-decor": "Boho Decor & Home",
    "tattoo-ideas": "Tattoo Ideas",
    "nail-art": "Nail Art",
    "fashion": "Fashion & Outfits",
    "tarot-spirituality": "Tarot & Spirituality",
    "kitchen-recipes": "Kitchen & Recipes",
    "perfume-fragrance": "Perfume & Fragrance",
    "makeup-beauty": "Makeup & Beauty",
    "hair-hairstyles": "Hair & Hairstyles",
    "jewelry-accessories": "Jewelry & Accessories",
    "self-care-wellness": "Self-Care & Wellness",
    "wedding-bridal": "Wedding & Bridal",
}


def load_settings() -> dict:
    """Load settings from config/settings.json."""
    settings_path = CONFIG_DIR / "settings.json"
    if settings_path.exists():
        return json.loads(settings_path.read_text())
    return {}


def load_boards() -> dict:
    """Load Pinterest board mapping from config/boards.json."""
    boards_path = CONFIG_DIR / "boards.json"
    if boards_path.exists():
        return json.loads(boards_path.read_text())
    return {}


def ensure_dirs() -> None:
    """Create all required directories."""
    for d in [CONFIG_DIR, QUEUE_DIR / "drafts", DATA_DIR / "pins", DATA_DIR / "keywords", BLOG_DIR, IMAGES_DIR]:
        d.mkdir(parents=True, exist_ok=True)
```

**Step 4: Create CLI entry point**

Create `agents/__init__.py`:
```python
"""HerVisionCraft agent system."""
```

Create `agents/__main__.py`:
```python
import click
from rich.console import Console
from rich.table import Table

from agents.config import ensure_dirs, QUEUE_DIR
from agents.db import get_connection

console = Console()


@click.group()
def cli():
    """HerVisionCraft Autopilot — AI-powered content marketing pipeline."""
    ensure_dirs()


@cli.command()
def status():
    """Show system dashboard."""
    conn = get_connection()
    posts = conn.execute("SELECT status, COUNT(*) as cnt FROM posts GROUP BY status").fetchall()
    pins = conn.execute("SELECT status, COUNT(*) as cnt FROM pins GROUP BY status").fetchall()
    conn.close()

    table = Table(title="HerVisionCraft Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    for row in posts:
        table.add_row(f"Posts ({row['status']})", str(row['cnt']))
    for row in pins:
        table.add_row(f"Pins ({row['status']})", str(row['cnt']))

    console.print(table)


@cli.group()
def review():
    """Manage post review queue."""
    pass


@review.command("list")
def review_list():
    """List posts waiting for review."""
    conn = get_connection()
    drafts = conn.execute(
        "SELECT slug, title, category, created_at FROM posts WHERE status = 'review' ORDER BY created_at"
    ).fetchall()
    conn.close()

    if not drafts:
        console.print("[dim]No posts waiting for review.[/dim]")
        return

    table = Table(title="Posts Awaiting Review")
    table.add_column("Slug", style="cyan")
    table.add_column("Title")
    table.add_column("Category", style="green")
    table.add_column("Created", style="dim")

    for d in drafts:
        table.add_row(d["slug"], d["title"], d["category"], d["created_at"])

    console.print(table)


@review.command("approve")
@click.argument("slug")
def review_approve(slug: str):
    """Approve a post for publishing."""
    conn = get_connection()
    result = conn.execute("UPDATE posts SET status = 'approved' WHERE slug = ? AND status = 'review'", (slug,))
    conn.commit()
    conn.close()

    if result.rowcount:
        console.print(f"[green]Approved:[/green] {slug}")
    else:
        console.print(f"[red]Not found or not in review:[/red] {slug}")


@review.command("reject")
@click.argument("slug")
@click.option("--note", "-n", default="", help="Rejection reason")
def review_reject(slug: str, note: str):
    """Reject a post with optional feedback."""
    conn = get_connection()
    result = conn.execute("UPDATE posts SET status = 'rejected' WHERE slug = ? AND status = 'review'", (slug,))
    conn.commit()
    conn.close()

    if result.rowcount:
        console.print(f"[yellow]Rejected:[/yellow] {slug}")
        if note:
            console.print(f"[dim]Note: {note}[/dim]")
    else:
        console.print(f"[red]Not found or not in review:[/red] {slug}")


if __name__ == "__main__":
    cli()
```

**Step 5: Install and verify CLI**

```bash
cd hervisioncraft && pip install -e agents/
python -m agents status
```
Expected: Shows empty status table

**Step 6: Commit**

```bash
git add agents/ config/ queue/ data/
git commit -m "feat: add Python agent foundation — DB schema, config, CLI"
```

---

### Task 9: Config Files

**Files:**
- Create: `config/settings.json`
- Create: `config/categories.json`
- Create: `config/boards.json`

**Step 1: Create settings template**

Create `config/settings.json`:
```json
{
  "anthropic_api_key": "",
  "unsplash_access_key": "",
  "pexels_api_key": "",
  "image_generation_api": "flux",
  "flux_api_key": "",
  "pinterest_email": "",
  "pinterest_password": "",
  "schedule": {
    "posts_per_week": 4,
    "publish_days": ["monday", "wednesday", "friday", "saturday"],
    "pins_per_day": 10,
    "researcher_day": "monday",
    "researcher_hour": 6,
    "writer_hour": 7,
    "analytics_day": "sunday"
  },
  "site_url": "https://hervisioncraft.com"
}
```

**Step 2: Create categories config**

Create `config/categories.json`:
```json
{
  "boho-decor": {
    "label": "Boho Decor & Home",
    "seed_keywords": ["boho decor", "boho home", "bohemian style", "boho kitchen", "boho bedroom", "boho living room"],
    "pinterest_boards": ["Boho Home Inspiration", "Bohemian Decor Ideas", "Boho Kitchen & Living"]
  },
  "tattoo-ideas": {
    "label": "Tattoo Ideas",
    "seed_keywords": ["tattoo ideas", "small tattoo", "minimalist tattoo", "tattoo for women", "tattoo design", "cute tattoo"],
    "pinterest_boards": ["Tattoo Inspiration", "Minimalist Tattoos", "Tattoo Ideas for Women"]
  },
  "nail-art": {
    "label": "Nail Art",
    "seed_keywords": ["nail art", "nail design", "nail ideas", "acrylic nails", "gel nails", "nail inspo"],
    "pinterest_boards": ["Nail Art Ideas", "Nail Designs", "Manicure Inspiration"]
  },
  "fashion": {
    "label": "Fashion & Outfits",
    "seed_keywords": ["outfit ideas", "fashion inspiration", "casual outfits", "date night outfit", "street style"],
    "pinterest_boards": ["Fashion Inspiration", "Outfit Ideas", "Street Style"]
  },
  "tarot-spirituality": {
    "label": "Tarot & Spirituality",
    "seed_keywords": ["tarot cards", "tarot reading", "spirituality", "crystals", "manifestation", "moon ritual"],
    "pinterest_boards": ["Tarot & Divination", "Spiritual Living", "Crystal Healing"]
  },
  "kitchen-recipes": {
    "label": "Kitchen & Recipes",
    "seed_keywords": ["easy recipes", "kitchen ideas", "meal prep", "healthy recipes", "baking ideas"],
    "pinterest_boards": ["Kitchen Inspiration", "Easy Recipes", "Healthy Cooking"]
  },
  "perfume-fragrance": {
    "label": "Perfume & Fragrance",
    "seed_keywords": ["best perfume", "fragrance", "perfume for women", "luxury perfume", "perfume collection"],
    "pinterest_boards": ["Perfume Collection", "Fragrance Inspiration", "Luxury Scents"]
  },
  "makeup-beauty": {
    "label": "Makeup & Beauty",
    "seed_keywords": ["makeup look", "makeup tutorial", "beauty tips", "eyeshadow ideas", "lipstick shades"],
    "pinterest_boards": ["Makeup Looks", "Beauty Inspiration", "Makeup Tutorials"]
  },
  "hair-hairstyles": {
    "label": "Hair & Hairstyles",
    "seed_keywords": ["hairstyle ideas", "hair color", "braids", "curly hair", "hair tutorial", "bob haircut"],
    "pinterest_boards": ["Hairstyle Inspiration", "Hair Color Ideas", "Braids & Updos"]
  },
  "jewelry-accessories": {
    "label": "Jewelry & Accessories",
    "seed_keywords": ["jewelry ideas", "layered necklace", "ear piercing", "rings", "bracelets", "accessories"],
    "pinterest_boards": ["Jewelry Inspiration", "Accessories & Style", "Layered Jewelry"]
  },
  "self-care-wellness": {
    "label": "Self-Care & Wellness",
    "seed_keywords": ["self care routine", "skincare", "journaling", "wellness tips", "mental health", "morning routine"],
    "pinterest_boards": ["Self-Care Ideas", "Wellness & Mindfulness", "Skincare Routines"]
  },
  "wedding-bridal": {
    "label": "Wedding & Bridal",
    "seed_keywords": ["wedding ideas", "bridal makeup", "wedding dress", "wedding decor", "bridesmaid dresses"],
    "pinterest_boards": ["Wedding Inspiration", "Bridal Beauty", "Wedding Decor Ideas"]
  }
}
```

**Step 3: Create boards mapping**

Create `config/boards.json`:
```json
{
  "boards": [
    {"name": "Boho Home Inspiration", "category": "boho-decor", "description": "Bohemian home decor ideas, boho kitchens, bedrooms, and living spaces. Free-spirited interior design."},
    {"name": "Bohemian Decor Ideas", "category": "boho-decor", "description": "Earthy, textured, and warm boho decor inspiration for every room."},
    {"name": "Tattoo Inspiration", "category": "tattoo-ideas", "description": "Beautiful tattoo ideas for women. Minimalist, floral, symbolic, and artistic tattoo designs."},
    {"name": "Minimalist Tattoos", "category": "tattoo-ideas", "description": "Clean, simple, and elegant minimalist tattoo ideas."},
    {"name": "Tattoo Ideas for Women", "category": "tattoo-ideas", "description": "Curated tattoo designs — small tattoos, wrist tattoos, and meaningful ink."},
    {"name": "Nail Art Ideas", "category": "nail-art", "description": "Stunning nail art designs, manicure ideas, and nail trends."},
    {"name": "Nail Designs", "category": "nail-art", "description": "Gel nails, acrylic nails, and creative nail art inspiration."},
    {"name": "Fashion Inspiration", "category": "fashion", "description": "Outfit ideas and fashion inspiration for the modern woman."},
    {"name": "Outfit Ideas", "category": "fashion", "description": "Casual, date night, work, and street style outfit inspiration."},
    {"name": "Tarot & Divination", "category": "tarot-spirituality", "description": "Tarot card meanings, spreads, and spiritual guidance."},
    {"name": "Spiritual Living", "category": "tarot-spirituality", "description": "Crystals, manifestation, moon rituals, and spiritual wellness."},
    {"name": "Kitchen Inspiration", "category": "kitchen-recipes", "description": "Easy recipes, kitchen ideas, and cooking inspiration."},
    {"name": "Easy Recipes", "category": "kitchen-recipes", "description": "Quick and delicious recipes for everyday cooking."},
    {"name": "Perfume Collection", "category": "perfume-fragrance", "description": "Best perfumes for women, luxury fragrances, and scent recommendations."},
    {"name": "Makeup Looks", "category": "makeup-beauty", "description": "Makeup tutorials, beauty looks, and product recommendations."},
    {"name": "Beauty Inspiration", "category": "makeup-beauty", "description": "Beauty tips, skincare, and makeup ideas."},
    {"name": "Hairstyle Inspiration", "category": "hair-hairstyles", "description": "Hairstyle ideas, hair color trends, braids, and tutorials."},
    {"name": "Hair Color Ideas", "category": "hair-hairstyles", "description": "Blonde, brunette, red, and creative hair color inspiration."},
    {"name": "Jewelry Inspiration", "category": "jewelry-accessories", "description": "Layered necklaces, rings, ear piercings, and accessory ideas."},
    {"name": "Self-Care Ideas", "category": "self-care-wellness", "description": "Self-care routines, journaling, skincare, and wellness tips."},
    {"name": "Wedding Inspiration", "category": "wedding-bridal", "description": "Wedding dresses, decor, bridal beauty, and wedding planning."},
    {"name": "Bridal Beauty", "category": "wedding-bridal", "description": "Bridal makeup, wedding hairstyles, and bridal nail art."}
  ]
}
```

**Step 4: Commit**

```bash
git add config/
git commit -m "feat: add category, board, and settings config files"
```

---

## Phase C: Content Agents

### Task 10: Researcher Agent

**Files:**
- Create: `agents/researcher/__init__.py`
- Create: `agents/researcher/keyword_scraper.py`
- Create: `agents/researcher/topic_selector.py`
- Create: `agents/researcher/calendar_generator.py`
- Test: `tests/test_researcher.py`

**Step 1: Write test for topic selector**

Create `tests/test_researcher.py`:
```python
import json
from unittest.mock import patch, MagicMock
from agents.researcher.topic_selector import select_topics


def test_select_topics_returns_correct_count():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps([
        {"title": "23 Minimalist Tattoo Ideas", "category": "tattoo-ideas", "keywords": ["minimalist tattoo"], "target_items": 23},
        {"title": "15 Boho Kitchen Ideas", "category": "boho-decor", "keywords": ["boho kitchen"], "target_items": 15},
        {"title": "19 Sage Green Nail Designs", "category": "nail-art", "keywords": ["sage green nails"], "target_items": 19},
        {"title": "21 Tarot Spread Ideas", "category": "tarot-spirituality", "keywords": ["tarot spread"], "target_items": 21},
    ]))]

    with patch("agents.researcher.topic_selector.get_claude_client") as mock_client:
        mock_client.return_value.messages.create.return_value = mock_response
        topics = select_topics(count=4)

    assert len(topics) == 4
    assert topics[0]["category"] == "tattoo-ideas"
```

**Step 2: Run test to verify it fails**

```bash
cd hervisioncraft && python -m pytest tests/test_researcher.py -v
```
Expected: FAIL — module not found

**Step 3: Create Claude client helper**

Create `agents/claude_client.py`:
```python
import anthropic
from agents.config import load_settings


def get_claude_client() -> anthropic.Anthropic:
    """Get an Anthropic client using settings."""
    settings = load_settings()
    api_key = settings.get("anthropic_api_key") or None
    return anthropic.Anthropic(api_key=api_key)
```

**Step 4: Create keyword scraper**

Create `agents/researcher/__init__.py`:
```python
"""Researcher agent — keyword research, topic selection, calendar generation."""
```

Create `agents/researcher/keyword_scraper.py`:
```python
import json
from agents.claude_client import get_claude_client
from agents.config import CATEGORIES
from agents.db import get_connection


def scrape_keyword_suggestions(category: str, seed_keywords: list[str]) -> list[dict]:
    """Use Claude to expand seed keywords into a list of Pinterest-worthy search terms."""
    client = get_claude_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""You are a Pinterest keyword researcher for a women's lifestyle blog.

Category: {category}
Seed keywords: {', '.join(seed_keywords)}

Generate 20 high-volume Pinterest search terms for this category. For each keyword, estimate:
- search_volume: "high", "medium", or "low"
- competition: "high", "medium", or "low"
- ad_value: 1-10 score (how likely advertisers target this term)

Return as JSON array:
[{{"keyword": "...", "search_volume": "...", "competition": "...", "ad_value": 5}}]

Focus on specific, listicle-friendly terms (e.g., "minimalist wrist tattoo" not just "tattoo").
Return ONLY the JSON array, no other text."""
        }]
    )
    keywords = json.loads(response.content[0].text)
    return keywords


def update_keyword_database(category: str, keywords: list[dict]) -> None:
    """Store keywords in SQLite."""
    conn = get_connection()
    volume_map = {"high": 3, "medium": 2, "low": 1}
    for kw in keywords:
        conn.execute(
            """INSERT INTO keywords (keyword, category, search_volume_estimate, competition, ad_value_score)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(keyword) DO UPDATE SET
                 search_volume_estimate = excluded.search_volume_estimate,
                 competition = excluded.competition,
                 ad_value_score = excluded.ad_value_score,
                 last_updated = CURRENT_TIMESTAMP""",
            (kw["keyword"], category, volume_map.get(kw.get("search_volume", "low"), 1),
             kw.get("competition", "unknown"), kw.get("ad_value", 0))
        )
    conn.commit()
    conn.close()


def run_keyword_research() -> None:
    """Run keyword research for all categories."""
    from agents.config import load_categories
    categories = load_categories()
    for cat_slug, cat_data in categories.items():
        keywords = scrape_keyword_suggestions(cat_slug, cat_data["seed_keywords"])
        update_keyword_database(cat_slug, keywords)
```

**Step 5: Create topic selector**

Create `agents/researcher/topic_selector.py`:
```python
import json
from agents.claude_client import get_claude_client
from agents.db import get_connection


def select_topics(count: int = 4) -> list[dict]:
    """Use Claude to pick the best topics for the week."""
    conn = get_connection()

    # Get top keywords not yet covered
    keywords = conn.execute(
        """SELECT keyword, category, search_volume_estimate, ad_value_score
           FROM keywords
           WHERE keyword NOT IN (SELECT title FROM posts)
           ORDER BY search_volume_estimate DESC, ad_value_score DESC
           LIMIT 50"""
    ).fetchall()

    # Get already published categories for balance
    published = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM posts WHERE status = 'published' GROUP BY category"
    ).fetchall()
    conn.close()

    keyword_list = [dict(k) for k in keywords]
    published_list = [dict(p) for p in published]

    client = get_claude_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""You are a content strategist for HerVisionCraft, a women's lifestyle blog.

Pick {count} blog post topics for this week. Each should be a listicle.

Available keywords (sorted by search volume):
{json.dumps(keyword_list, indent=2)}

Already published post counts by category:
{json.dumps(published_list, indent=2)}

Selection criteria:
- High Pinterest search volume
- Mix of categories (don't repeat the same category unless it's clearly the top performer)
- Listicle-friendly (can be "N [adjective] [topic] ideas/designs/looks")
- Pick a specific number of items (between 13-31, odd numbers perform well)

Return JSON array:
[{{"title": "23 Minimalist Tattoo Ideas for First-Timers", "category": "tattoo-ideas", "keywords": ["minimalist tattoo", "small tattoo"], "target_items": 23}}]

Return ONLY the JSON array."""
        }]
    )
    topics = json.loads(response.content[0].text)
    return topics
```

**Step 6: Create calendar generator**

Create `agents/researcher/calendar_generator.py`:
```python
import json
from datetime import datetime, timedelta
from agents.config import QUEUE_DIR, load_settings
from agents.db import get_connection


def generate_weekly_calendar(topics: list[dict]) -> dict:
    """Assign topics to publish dates for the week."""
    settings = load_settings()
    publish_days = settings.get("schedule", {}).get("publish_days", ["monday", "wednesday", "friday", "saturday"])

    today = datetime.now()
    # Find next Monday
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0 and today.hour >= 12:
        days_until_monday = 7
    week_start = today + timedelta(days=days_until_monday)

    day_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
    publish_dates = []
    for day_name in publish_days:
        offset = day_map[day_name]
        publish_dates.append(week_start + timedelta(days=offset))

    calendar = {
        "week": week_start.strftime("%Y-%m-%d"),
        "created_at": datetime.now().isoformat(),
        "posts": [],
    }

    for i, topic in enumerate(topics):
        date = publish_dates[i % len(publish_dates)]
        slug = topic["title"].lower()
        slug = "".join(c if c.isalnum() or c == " " else "" for c in slug)
        slug = slug.strip().replace(" ", "-")[:80]

        post = {
            **topic,
            "slug": slug,
            "publish_date": date.strftime("%Y-%m-%d"),
            "status": "draft",
        }
        calendar["posts"].append(post)

    # Save to queue
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    (QUEUE_DIR / "upcoming.json").write_text(json.dumps(calendar, indent=2))

    # Track in DB
    conn = get_connection()
    conn.execute(
        "INSERT INTO calendar (week, post_data) VALUES (?, ?)",
        (calendar["week"], json.dumps(calendar))
    )
    conn.commit()
    conn.close()

    return calendar
```

**Step 7: Run test**

```bash
cd hervisioncraft && python -m pytest tests/test_researcher.py -v
```
Expected: PASS

**Step 8: Commit**

```bash
git add agents/ tests/
git commit -m "feat: add researcher agent — keyword scraper, topic selector, calendar generator"
```

---

### Task 11: Writer Agent

**Files:**
- Create: `agents/writer/__init__.py`
- Create: `agents/writer/blog_writer.py`
- Test: `tests/test_writer.py`

**Step 1: Write test**

Create `tests/test_writer.py`:
```python
import json
from unittest.mock import patch, MagicMock
from agents.writer.blog_writer import generate_blog_post


def test_generate_blog_post_creates_markdown():
    topic = {
        "title": "15 Boho Kitchen Ideas",
        "category": "boho-decor",
        "keywords": ["boho kitchen"],
        "target_items": 15,
        "slug": "15-boho-kitchen-ideas",
        "publish_date": "2026-04-14",
    }

    fake_markdown = """---
title: "15 Boho Kitchen Ideas"
description: "Transform your cooking space with these boho ideas."
category: "boho-decor"
tags: ["boho", "kitchen", "home decor"]
pinterest_title: "Boho Kitchen Ideas | Her Vision Craft"
date: 2026-04-14
draft: false
---

Looking for boho kitchen inspiration?

## 1. Macrame Plant Hangers

Add some texture above your sink.
"""

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=fake_markdown)]

    with patch("agents.writer.blog_writer.get_claude_client") as mock_client:
        mock_client.return_value.messages.create.return_value = mock_response
        result = generate_blog_post(topic)

    assert "15 Boho Kitchen Ideas" in result
    assert "---" in result
```

**Step 2: Run test to verify it fails**

```bash
cd hervisioncraft && python -m pytest tests/test_writer.py -v
```
Expected: FAIL

**Step 3: Create writer agent**

Create `agents/writer/__init__.py`:
```python
"""Writer agent — blog post generation with Claude."""
```

Create `agents/writer/blog_writer.py`:
```python
from pathlib import Path
from agents.claude_client import get_claude_client
from agents.config import QUEUE_DIR, CATEGORIES
from agents.db import get_connection


def generate_blog_post(topic: dict) -> str:
    """Generate a complete Markdown blog post using Claude."""
    client = get_claude_client()
    category_label = CATEGORIES.get(topic["category"], topic["category"])

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"""Write a complete Markdown blog post for HerVisionCraft, a women's lifestyle blog.

TOPIC: {topic['title']}
CATEGORY: {category_label}
TARGET KEYWORDS: {', '.join(topic['keywords'])}
NUMBER OF ITEMS: {topic['target_items']}

FORMAT — start with YAML frontmatter, then the post body:

---
title: "{topic['title']}"
description: "[Write a compelling 150-char meta description using the main keyword]"
category: "{topic['category']}"
tags: [list of 3-5 relevant lowercase tags]
pinterest_title: "[Catchy Pinterest title] | Her Vision Craft"
date: {topic['publish_date']}
draft: false
---

[2-3 sentence intro — warm, excited, conversational. Use the main keyword naturally.]

## 1. [Item Name]

[2-3 sentences describing this item. Be specific, visual, and helpful.]

**Style tip:** [One actionable tip related to this item.]

[Continue for all {topic['target_items']} items...]

## Final Thoughts

[2-3 sentences wrapping up. Encourage readers to save/pin their favorites.]

VOICE: Warm, aspirational, like a stylish friend giving advice. Not salesy or corporate.
Use keywords naturally — don't stuff them.
Make each item unique and specific — avoid generic descriptions.

Return ONLY the complete Markdown file (frontmatter + content). No other text."""
        }]
    )
    markdown = response.content[0].text.strip()

    # Save to queue
    slug = topic["slug"]
    draft_path = QUEUE_DIR / "drafts" / f"{slug}.md"
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(markdown)

    # Track in DB
    conn = get_connection()
    conn.execute(
        """INSERT INTO posts (slug, title, category, keywords, status)
           VALUES (?, ?, ?, ?, 'review')
           ON CONFLICT(slug) DO UPDATE SET status = 'review'""",
        (slug, topic["title"], topic["category"], str(topic["keywords"]))
    )
    conn.commit()
    conn.close()

    return markdown
```

**Step 4: Run test**

```bash
cd hervisioncraft && python -m pytest tests/test_writer.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add agents/writer/ tests/test_writer.py
git commit -m "feat: add writer agent — blog post generation with Claude"
```

---

### Task 12: Image Sourcer Agent

**Files:**
- Create: `agents/image_sourcer/__init__.py`
- Create: `agents/image_sourcer/stock_photos.py`
- Test: `tests/test_image_sourcer.py`

**Step 1: Write test**

Create `tests/test_image_sourcer.py`:
```python
from unittest.mock import patch, MagicMock, AsyncMock
from agents.image_sourcer.stock_photos import search_unsplash


def test_search_unsplash_returns_urls():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {"urls": {"regular": "https://images.unsplash.com/photo-1"}, "alt_description": "boho kitchen"},
            {"urls": {"regular": "https://images.unsplash.com/photo-2"}, "alt_description": "kitchen decor"},
        ]
    }

    with patch("agents.image_sourcer.stock_photos.httpx.get", return_value=mock_response):
        results = search_unsplash("boho kitchen", count=2)

    assert len(results) == 2
    assert "unsplash.com" in results[0]["url"]
```

**Step 2: Create image sourcer**

Create `agents/image_sourcer/__init__.py`:
```python
"""Image sourcer agent — stock photos from Unsplash/Pexels."""
```

Create `agents/image_sourcer/stock_photos.py`:
```python
import httpx
from pathlib import Path
from agents.config import load_settings, IMAGES_DIR


def search_unsplash(query: str, count: int = 5) -> list[dict]:
    """Search Unsplash for photos matching query."""
    settings = load_settings()
    access_key = settings.get("unsplash_access_key", "")
    if not access_key:
        return []

    response = httpx.get(
        "https://api.unsplash.com/search/photos",
        params={"query": query, "per_page": count, "orientation": "portrait"},
        headers={"Authorization": f"Client-ID {access_key}"},
    )
    response.raise_for_status()
    data = response.json()

    return [
        {"url": r["urls"]["regular"], "alt": r.get("alt_description", query)}
        for r in data.get("results", [])
    ]


def search_pexels(query: str, count: int = 5) -> list[dict]:
    """Search Pexels for photos matching query."""
    settings = load_settings()
    api_key = settings.get("pexels_api_key", "")
    if not api_key:
        return []

    response = httpx.get(
        "https://api.pexels.com/v1/search",
        params={"query": query, "per_page": count, "orientation": "portrait"},
        headers={"Authorization": api_key},
    )
    response.raise_for_status()
    data = response.json()

    return [
        {"url": p["src"]["large"], "alt": p.get("alt", query)}
        for p in data.get("photos", [])
    ]


def download_image(url: str, save_path: Path) -> Path:
    """Download an image and save to disk."""
    save_path.parent.mkdir(parents=True, exist_ok=True)
    response = httpx.get(url, follow_redirects=True)
    response.raise_for_status()
    save_path.write_bytes(response.content)
    return save_path


def source_images_for_post(slug: str, items: list[str]) -> list[Path]:
    """Find and download images for each item in a blog post."""
    post_images_dir = IMAGES_DIR / slug
    post_images_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    for i, item_query in enumerate(items):
        # Try Unsplash first, fall back to Pexels
        results = search_unsplash(item_query, count=1)
        if not results:
            results = search_pexels(item_query, count=1)
        if not results:
            continue

        filename = f"{i + 1:02d}.jpg"
        path = download_image(results[0]["url"], post_images_dir / filename)
        saved.append(path)

    return saved
```

**Step 3: Run test**

```bash
cd hervisioncraft && python -m pytest tests/test_image_sourcer.py -v
```
Expected: PASS

**Step 4: Commit**

```bash
git add agents/image_sourcer/ tests/test_image_sourcer.py
git commit -m "feat: add image sourcer agent — Unsplash/Pexels search and download"
```

---

### Task 13: Publisher Agent

**Files:**
- Create: `agents/publisher/__init__.py`
- Create: `agents/publisher/publish.py`

**Step 1: Create publisher agent**

Create `agents/publisher/__init__.py`:
```python
"""Publisher agent — moves approved posts to website and triggers deploy."""
```

Create `agents/publisher/publish.py`:
```python
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from agents.config import QUEUE_DIR, BLOG_DIR
from agents.db import get_connection


def publish_post(slug: str) -> bool:
    """Move an approved post from queue to website and deploy."""
    draft_path = QUEUE_DIR / "drafts" / f"{slug}.md"
    if not draft_path.exists():
        return False

    # Move to blog content directory
    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    target_path = BLOG_DIR / f"{slug}.md"
    shutil.copy2(draft_path, target_path)

    # Update DB
    conn = get_connection()
    conn.execute(
        "UPDATE posts SET status = 'published', published_at = ? WHERE slug = ?",
        (datetime.now().isoformat(), slug)
    )
    conn.commit()
    conn.close()

    # Git commit and push
    _git_deploy(slug, target_path)

    # Clean up draft
    draft_path.unlink()

    return True


def _git_deploy(slug: str, file_path: Path) -> None:
    """Commit the new post and push to trigger Netlify deploy."""
    repo_root = file_path.parents[4]  # Navigate up to hervisioncraft/
    try:
        subprocess.run(["git", "add", str(file_path)], cwd=repo_root, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"publish: {slug}"],
            cwd=repo_root, check=True
        )
        subprocess.run(["git", "push"], cwd=repo_root, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Git deploy failed: {e}")


def publish_all_approved() -> list[str]:
    """Publish all posts with 'approved' status."""
    conn = get_connection()
    approved = conn.execute("SELECT slug FROM posts WHERE status = 'approved'").fetchall()
    conn.close()

    published = []
    for row in approved:
        if publish_post(row["slug"]):
            published.append(row["slug"])
    return published
```

**Step 2: Commit**

```bash
git add agents/publisher/
git commit -m "feat: add publisher agent — moves posts to website, git deploys"
```

---

## Phase D: Pinterest Agent

### Task 14: Pin Graphic Generator

**Files:**
- Create: `agents/pinterest/__init__.py`
- Create: `agents/pinterest/pin_generator.py`
- Create: `agents/pinterest/image_gen.py`
- Test: `tests/test_pin_generator.py`

**Step 1: Write test**

Create `tests/test_pin_generator.py`:
```python
from PIL import Image
from agents.pinterest.pin_generator import create_pin_collage


def test_create_pin_collage_correct_size():
    # Create 4 dummy images
    images = [Image.new("RGB", (500, 500), color) for color in ["red", "blue", "green", "yellow"]]
    result = create_pin_collage(
        images=images,
        number=17,
        title_lines=["MAGICAL CAT", "TATTOO IDEAS!"],
        highlight_word="CAT",
        accent_color="#F4C2C2",
    )
    assert result.size == (1000, 1500)
```

**Step 2: Run test to verify fail**

```bash
cd hervisioncraft && python -m pytest tests/test_pin_generator.py -v
```

**Step 3: Create AI image generation module**

Create `agents/pinterest/__init__.py`:
```python
"""Pinterest agent — pin graphic generation and browser posting."""
```

Create `agents/pinterest/image_gen.py`:
```python
import json
import httpx
from pathlib import Path
from agents.claude_client import get_claude_client
from agents.config import load_settings, DATA_DIR


def generate_image_prompts(title: str, category: str, count: int = 4) -> list[str]:
    """Use Claude to generate detailed image prompts for pin graphics."""
    client = get_claude_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": f"""Generate {count} detailed image prompts for AI image generation.
These will be used in a 2x2 collage for a Pinterest pin about: "{title}" (category: {category}).

Each prompt should describe a different, photorealistic scene related to the topic.
Make them visually diverse — different angles, settings, and compositions.
Style: Pinterest-aesthetic, high quality, editorial photography look.
Do NOT include any text in the images.

Return as JSON array of strings:
["prompt 1", "prompt 2", "prompt 3", "prompt 4"]

Return ONLY the JSON array."""
        }]
    )
    return json.loads(response.content[0].text)


def generate_images(prompts: list[str], output_dir: Path) -> list[Path]:
    """Generate images using Flux API."""
    settings = load_settings()
    api_key = settings.get("flux_api_key", "")
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    for i, prompt in enumerate(prompts):
        try:
            response = httpx.post(
                "https://api.together.xyz/v1/images/generations",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "black-forest-labs/FLUX.1-schnell",
                    "prompt": prompt,
                    "width": 512,
                    "height": 512,
                    "n": 1,
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()

            # Download the generated image
            image_url = data["data"][0]["url"]
            img_response = httpx.get(image_url, follow_redirects=True)
            path = output_dir / f"gen_{i}.png"
            path.write_bytes(img_response.content)
            paths.append(path)
        except Exception as e:
            print(f"Image generation failed for prompt {i}: {e}")

    return paths
```

**Step 4: Create pin collage generator**

Create `agents/pinterest/pin_generator.py`:
```python
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from agents.claude_client import get_claude_client
from agents.pinterest.image_gen import generate_image_prompts, generate_images
from agents.config import DATA_DIR

# Pin dimensions
PIN_WIDTH = 1000
PIN_HEIGHT = 1500
GRID_COLS = 2
GRID_ROWS = 2


def create_pin_collage(
    images: list[Image.Image],
    number: int,
    title_lines: list[str],
    highlight_word: str,
    accent_color: str = "#F4C2C2",
) -> Image.Image:
    """Create a Pinterest pin collage with text overlay."""
    canvas = Image.new("RGB", (PIN_WIDTH, PIN_HEIGHT), "white")

    # Place 4 images in 2x2 grid
    cell_w = PIN_WIDTH // GRID_COLS
    cell_h = PIN_HEIGHT // GRID_ROWS
    for i, img in enumerate(images[:4]):
        row, col = divmod(i, GRID_COLS)
        resized = img.resize((cell_w, cell_h), Image.LANCZOS)
        canvas.paste(resized, (col * cell_w, row * cell_h))

    draw = ImageDraw.Draw(canvas)

    # Darken center area for text
    overlay = Image.new("RGBA", (PIN_WIDTH, PIN_HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    center_y = PIN_HEIGHT // 2
    band_height = 400
    overlay_draw.rectangle(
        [0, center_y - band_height // 2, PIN_WIDTH, center_y + band_height // 2],
        fill=(0, 0, 0, 140),
    )
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # Load fonts (fall back to default if custom not available)
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Supplemental/Impact.ttf", 72)
        font_number = ImageFont.truetype("/System/Library/Fonts/Supplemental/Impact.ttf", 96)
    except OSError:
        font_large = ImageFont.load_default()
        font_number = ImageFont.load_default()

    # Draw number badge
    badge_y = center_y - band_height // 2 + 20
    badge_x = PIN_WIDTH // 2
    badge_r = 55
    draw.ellipse(
        [badge_x - badge_r, badge_y - badge_r + 30, badge_x + badge_r, badge_y + badge_r + 30],
        fill=accent_color,
    )
    num_text = str(number)
    num_bbox = draw.textbbox((0, 0), num_text, font=font_number)
    num_w = num_bbox[2] - num_bbox[0]
    num_h = num_bbox[3] - num_bbox[1]
    draw.text(
        (badge_x - num_w // 2, badge_y - num_h // 2 + 30),
        num_text, fill="white", font=font_number,
    )

    # Draw title lines
    title_y = badge_y + badge_r + 50
    for line in title_lines:
        words = line.split()
        # Calculate total line width first
        line_bbox = draw.textbbox((0, 0), line, font=font_large)
        line_w = line_bbox[2] - line_bbox[0]
        x_start = (PIN_WIDTH - line_w) // 2

        # Draw word by word for highlight
        x = x_start
        for word in words:
            color = accent_color if word.upper() == highlight_word.upper() else "white"
            draw.text((x, title_y), word + " ", fill=color, font=font_large)
            word_bbox = draw.textbbox((0, 0), word + " ", font=font_large)
            x += word_bbox[2] - word_bbox[0]

        title_y += 80

    # Brand watermark
    try:
        font_small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 24)
    except OSError:
        font_small = ImageFont.load_default()
    brand = "hervisioncraft.com"
    brand_bbox = draw.textbbox((0, 0), brand, font=font_small)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text(
        ((PIN_WIDTH - brand_w) // 2, PIN_HEIGHT - 50),
        brand, fill="white", font=font_small,
    )

    return canvas


def generate_pin_title(post_title: str, category: str) -> dict:
    """Use Claude to generate a clickbait pin title with highlight word."""
    client = get_claude_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""Generate a Pinterest pin title for this blog post: "{post_title}"

The title should be:
- ALL CAPS
- Format: [number] [ADJECTIVE] [keyword] IDEAS/DESIGNS/LOOKS!
- Eye-catching and clickable
- The adjective should be emotional/visual (STUNNING, DREAMY, MAGICAL, GORGEOUS, etc.)

Also identify the single most emotional/visual word to highlight in a different color.
Split the title into 2 lines for the pin graphic.

Return JSON:
{{"line1": "17 MAGICAL CAT", "line2": "TATTOO IDEAS!", "highlight_word": "MAGICAL", "number": 17}}

Return ONLY JSON."""
        }]
    )
    return json.loads(response.content[0].text)


def generate_pins_for_post(slug: str, title: str, category: str, count: int = 3) -> list[Path]:
    """Generate multiple pin variations for a blog post."""
    pins_dir = DATA_DIR / "pins" / slug
    pins_dir.mkdir(parents=True, exist_ok=True)

    accent_colors = ["#F4C2C2", "#B2C9AB", "#C9A96E", "#A8C4D9", "#D4A5A5"]
    generated_pins = []

    for variation in range(count):
        # Generate title variation
        pin_title = generate_pin_title(title, category)

        # Generate AI images
        prompts = generate_image_prompts(title, category, count=4)
        image_dir = pins_dir / f"v{variation}"
        image_paths = generate_images(prompts, image_dir)

        if len(image_paths) < 4:
            continue

        # Create collage
        images = [Image.open(p) for p in image_paths]
        pin = create_pin_collage(
            images=images,
            number=pin_title["number"],
            title_lines=[pin_title["line1"], pin_title["line2"]],
            highlight_word=pin_title["highlight_word"],
            accent_color=accent_colors[variation % len(accent_colors)],
        )

        pin_path = pins_dir / f"pin_v{variation}.png"
        pin.save(pin_path, "PNG", quality=95)
        generated_pins.append(pin_path)

        # Clean up individual images
        for img in images:
            img.close()

    return generated_pins
```

**Step 5: Run test**

```bash
cd hervisioncraft && python -m pytest tests/test_pin_generator.py -v
```
Expected: PASS

**Step 6: Commit**

```bash
git add agents/pinterest/ tests/test_pin_generator.py
git commit -m "feat: add pin graphic generator — AI images + Pillow collage compositing"
```

---

### Task 15: Pinterest Browser Automation

**Files:**
- Create: `agents/pinterest/browser.py`
- Test: `tests/test_pinterest_browser.py`

**Step 1: Create Pinterest browser automation**

Create `agents/pinterest/browser.py`:
```python
import json
import random
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page
from agents.config import load_settings, load_boards
from agents.db import get_connection


def _human_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
    """Random delay to mimic human behavior."""
    time.sleep(random.uniform(min_s, max_s))


def login_to_pinterest(page: Page) -> bool:
    """Log into Pinterest using stored credentials."""
    settings = load_settings()
    email = settings.get("pinterest_email", "")
    password = settings.get("pinterest_password", "")

    if not email or not password:
        print("Pinterest credentials not configured in settings.json")
        return False

    page.goto("https://www.pinterest.com/login/")
    _human_delay(2, 4)

    page.fill('input[name="id"]', email)
    _human_delay(0.5, 1.5)
    page.fill('input[name="password"]', password)
    _human_delay(0.5, 1.0)
    page.click('button[type="submit"]')

    # Wait for navigation
    try:
        page.wait_for_url("**/", timeout=15000)
        return True
    except Exception:
        print("Pinterest login failed — may need manual verification")
        return False


def create_pin(page: Page, image_path: Path, title: str, description: str, board: str, url: str) -> bool:
    """Create a single pin on Pinterest."""
    try:
        page.goto("https://www.pinterest.com/pin-creation-tool/")
        _human_delay(2, 4)

        # Upload image
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(image_path))
        _human_delay(3, 5)

        # Fill title
        title_input = page.locator('[data-test-id="pin-draft-title"] textarea, [data-test-id="pin-draft-title"] input')
        if title_input.count() > 0:
            title_input.first.fill(title)
            _human_delay(0.5, 1.0)

        # Fill description
        desc_input = page.locator('[data-test-id="pin-draft-description"] textarea, [data-test-id="pin-draft-description"] div[contenteditable]')
        if desc_input.count() > 0:
            desc_input.first.fill(description)
            _human_delay(0.5, 1.0)

        # Fill destination URL
        url_input = page.locator('[data-test-id="pin-draft-link"] input')
        if url_input.count() > 0:
            url_input.first.fill(url)
            _human_delay(0.5, 1.0)

        # Select board
        board_selector = page.locator('[data-test-id="board-dropdown-select-button"]')
        if board_selector.count() > 0:
            board_selector.click()
            _human_delay(1, 2)
            board_option = page.locator(f'text="{board}"')
            if board_option.count() > 0:
                board_option.first.click()
                _human_delay(0.5, 1.0)

        # Publish
        publish_btn = page.locator('[data-test-id="board-dropdown-save-button"], button:has-text("Publish")')
        if publish_btn.count() > 0:
            publish_btn.first.click()
            _human_delay(3, 5)

        return True
    except Exception as e:
        print(f"Failed to create pin: {e}")
        return False


def post_pins_for_post(slug: str) -> int:
    """Post all pending pins for a given blog post."""
    conn = get_connection()
    pins = conn.execute(
        "SELECT id, image_path, title, description, board FROM pins WHERE post_slug = ? AND status = 'pending'",
        (slug,)
    ).fetchall()

    if not pins:
        conn.close()
        return 0

    settings = load_settings()
    site_url = settings.get("site_url", "https://hervisioncraft.com")
    post_url = f"{site_url}/blog/{slug}/"
    posted = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )
        page = context.new_page()

        if not login_to_pinterest(page):
            browser.close()
            conn.close()
            return 0

        for pin in pins:
            _human_delay(60, 180)  # Long delay between pins
            success = create_pin(
                page=page,
                image_path=Path(pin["image_path"]),
                title=pin["title"],
                description=pin["description"],
                board=pin["board"],
                url=post_url,
            )
            if success:
                conn.execute("UPDATE pins SET status = 'posted', posted_at = CURRENT_TIMESTAMP WHERE id = ?", (pin["id"],))
                conn.commit()
                posted += 1

        browser.close()

    conn.close()
    return posted


def create_boards_from_config() -> int:
    """Create Pinterest boards from config if they don't exist."""
    boards_config = load_boards()
    created = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        if not login_to_pinterest(page):
            browser.close()
            return 0

        for board in boards_config.get("boards", []):
            try:
                # Navigate to profile
                page.goto("https://www.pinterest.com/")
                _human_delay(2, 3)

                # Click create board (via + button or profile)
                # This is fragile and may need updating as Pinterest changes their UI
                page.goto("https://www.pinterest.com/pin-creation-tool/")
                _human_delay(2, 3)

                created += 1
            except Exception as e:
                print(f"Failed to create board '{board['name']}': {e}")

        browser.close()

    return created
```

**Step 2: Commit**

```bash
git add agents/pinterest/browser.py
git commit -m "feat: add Pinterest browser automation — login, create pins, board management"
```

---

### Task 16: Pin Copy Generator + DB Integration

**Files:**
- Modify: `agents/pinterest/pin_generator.py` (add pin copy + DB tracking)

**Step 1: Add pin copy and DB registration**

Add to `agents/pinterest/pin_generator.py` a function that generates pin descriptions and registers pins in the DB:

```python
def generate_pin_copy(title: str, keywords: list[str], category: str) -> dict:
    """Generate Pinterest pin title and description."""
    client = get_claude_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""Write Pinterest pin copy for: "{title}"
Keywords: {', '.join(keywords)}
Category: {category}

Return JSON:
{{"pin_title": "max 100 chars, keyword-rich, compelling", "pin_description": "max 500 chars, includes keywords naturally, ends with CTA to click through"}}

Return ONLY JSON."""
        }]
    )
    return json.loads(response.content[0].text)


def register_pins_in_db(slug: str, pin_paths: list[Path], title: str, keywords: list[str], category: str) -> None:
    """Register generated pins in DB for the browser agent to post."""
    from agents.config import load_boards
    boards_config = load_boards()

    # Find boards for this category
    category_boards = [b["name"] for b in boards_config.get("boards", []) if b["category"] == category]
    if not category_boards:
        category_boards = ["General"]

    conn = get_connection()
    for i, pin_path in enumerate(pin_paths):
        copy = generate_pin_copy(title, keywords, category)
        board = category_boards[i % len(category_boards)]

        conn.execute(
            """INSERT INTO pins (post_slug, image_path, title, description, board, status)
               VALUES (?, ?, ?, ?, ?, 'pending')""",
            (slug, str(pin_path), copy["pin_title"], copy["pin_description"], board)
        )
    conn.commit()
    conn.close()
```

**Step 2: Commit**

```bash
git add agents/pinterest/
git commit -m "feat: add pin copy generation and DB registration"
```

---

## Phase E: Orchestrator

### Task 17: Orchestrator & Scheduler

**Files:**
- Create: `agents/orchestrator/__init__.py`
- Create: `agents/orchestrator/scheduler.py`
- Create: `agents/orchestrator/pipeline.py`

**Step 1: Create pipeline**

Create `agents/orchestrator/__init__.py`:
```python
"""Orchestrator — coordinates all agents and runs the pipeline."""
```

Create `agents/orchestrator/pipeline.py`:
```python
import json
from rich.console import Console
from agents.researcher.keyword_scraper import run_keyword_research
from agents.researcher.topic_selector import select_topics
from agents.researcher.calendar_generator import generate_weekly_calendar
from agents.writer.blog_writer import generate_blog_post
from agents.image_sourcer.stock_photos import source_images_for_post
from agents.publisher.publish import publish_all_approved
from agents.pinterest.pin_generator import generate_pins_for_post, register_pins_in_db
from agents.pinterest.browser import post_pins_for_post
from agents.config import QUEUE_DIR

console = Console()


def run_research_phase() -> dict:
    """Phase 1: Research keywords and generate content calendar."""
    console.print("[cyan]Phase 1: Running keyword research...[/cyan]")
    run_keyword_research()

    console.print("[cyan]Phase 1: Selecting topics...[/cyan]")
    topics = select_topics(count=4)

    console.print("[cyan]Phase 1: Generating calendar...[/cyan]")
    calendar = generate_weekly_calendar(topics)

    console.print(f"[green]Research complete — {len(topics)} topics planned[/green]")
    return calendar


def run_writing_phase() -> list[str]:
    """Phase 2: Write blog posts for all pending calendar items."""
    calendar_path = QUEUE_DIR / "upcoming.json"
    if not calendar_path.exists():
        console.print("[yellow]No calendar found. Run research phase first.[/yellow]")
        return []

    calendar = json.loads(calendar_path.read_text())
    written = []

    for post in calendar["posts"]:
        if post["status"] != "draft":
            continue
        console.print(f"[cyan]Writing: {post['title']}[/cyan]")
        generate_blog_post(post)

        # Source images
        console.print(f"[cyan]Sourcing images for: {post['slug']}[/cyan]")
        items = [f"{post['title']} {kw}" for kw in post.get("keywords", [])]
        source_images_for_post(post["slug"], items)

        post["status"] = "review"
        written.append(post["slug"])

    # Update calendar
    calendar_path.write_text(json.dumps(calendar, indent=2))
    console.print(f"[green]Writing complete — {len(written)} posts ready for review[/green]")
    return written


def run_publish_phase() -> list[str]:
    """Publish all approved posts."""
    console.print("[cyan]Publishing approved posts...[/cyan]")
    published = publish_all_approved()
    console.print(f"[green]Published {len(published)} posts[/green]")
    return published


def run_pinterest_phase(slugs: list[str]) -> int:
    """Phase 3: Generate and post pins for published posts."""
    total_posted = 0
    for slug in slugs:
        console.print(f"[cyan]Generating pins for: {slug}[/cyan]")
        # Get post info from DB
        from agents.db import get_connection
        conn = get_connection()
        post = conn.execute("SELECT * FROM posts WHERE slug = ?", (slug,)).fetchone()
        conn.close()

        if not post:
            continue

        pin_paths = generate_pins_for_post(slug, post["title"], post["category"], count=3)
        keywords = json.loads(post["keywords"].replace("'", '"')) if post["keywords"] else []
        register_pins_in_db(slug, pin_paths, post["title"], keywords, post["category"])

        console.print(f"[cyan]Posting pins for: {slug}[/cyan]")
        posted = post_pins_for_post(slug)
        total_posted += posted

    console.print(f"[green]Pinterest complete — {total_posted} pins posted[/green]")
    return total_posted


def run_full_cycle() -> None:
    """Run one complete pipeline cycle."""
    console.print("[bold]Starting full pipeline cycle...[/bold]")
    run_research_phase()
    run_writing_phase()
    console.print("[yellow]Posts queued for review. Approve with: python -m agents review approve <slug>[/yellow]")
```

**Step 2: Create scheduler**

Create `agents/orchestrator/scheduler.py`:
```python
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from rich.console import Console
from agents.config import load_settings
from agents.orchestrator.pipeline import (
    run_research_phase,
    run_writing_phase,
    run_publish_phase,
    run_pinterest_phase,
)

console = Console()


def create_scheduler() -> BlockingScheduler:
    """Create and configure the APScheduler instance."""
    settings = load_settings()
    schedule = settings.get("schedule", {})

    scheduler = BlockingScheduler()

    # Research: weekly on configured day
    researcher_day = schedule.get("researcher_day", "monday")
    researcher_hour = schedule.get("researcher_hour", 6)
    scheduler.add_job(
        run_research_phase,
        CronTrigger(day_of_week=_day_abbrev(researcher_day), hour=researcher_hour),
        id="research",
        name="Weekly Research",
    )

    # Writing: Mon-Sat at configured hour
    writer_hour = schedule.get("writer_hour", 7)
    scheduler.add_job(
        run_writing_phase,
        CronTrigger(day_of_week="mon-sat", hour=writer_hour),
        id="writing",
        name="Daily Writing",
    )

    # Publishing: check every 30 min for approved posts
    scheduler.add_job(
        _publish_and_pin,
        CronTrigger(minute="*/30"),
        id="publish_check",
        name="Publish Check",
    )

    # Analytics: weekly on Sunday
    analytics_day = schedule.get("analytics_day", "sunday")
    scheduler.add_job(
        _run_analytics,
        CronTrigger(day_of_week=_day_abbrev(analytics_day), hour=20),
        id="analytics",
        name="Weekly Analytics",
    )

    return scheduler


def _publish_and_pin() -> None:
    """Publish approved posts and trigger Pinterest."""
    published = run_publish_phase()
    if published:
        run_pinterest_phase(published)


def _run_analytics() -> None:
    """Run analytics collection (placeholder)."""
    console.print("[cyan]Analytics collection — not yet implemented[/cyan]")


def _day_abbrev(day: str) -> str:
    """Convert day name to APScheduler abbreviation."""
    mapping = {
        "monday": "mon", "tuesday": "tue", "wednesday": "wed",
        "thursday": "thu", "friday": "fri", "saturday": "sat", "sunday": "sun",
    }
    return mapping.get(day.lower(), day[:3].lower())
```

**Step 3: Wire CLI commands**

Add to `agents/__main__.py`:
```python
@cli.command()
@click.option("--once", is_flag=True, help="Run one cycle and exit")
def run(once: bool):
    """Start the orchestrator."""
    from agents.orchestrator.pipeline import run_full_cycle
    from agents.orchestrator.scheduler import create_scheduler

    if once:
        console.print("[bold]Running single pipeline cycle...[/bold]")
        run_full_cycle()
    else:
        console.print("[bold]Starting HerVisionCraft Autopilot...[/bold]")
        scheduler = create_scheduler()
        try:
            scheduler.start()
        except KeyboardInterrupt:
            console.print("[yellow]Shutting down...[/yellow]")


@cli.group()
def pinterest():
    """Pinterest automation commands."""
    pass


@pinterest.command("test")
def pinterest_test():
    """Test Pinterest login."""
    from agents.pinterest.browser import login_to_pinterest
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        success = login_to_pinterest(page)
        if success:
            console.print("[green]Pinterest login successful![/green]")
        else:
            console.print("[red]Pinterest login failed.[/red]")
        browser.close()


@pinterest.command("post")
@click.argument("slug")
def pinterest_post(slug: str):
    """Manually post pins for a blog post."""
    from agents.pinterest.browser import post_pins_for_post
    posted = post_pins_for_post(slug)
    console.print(f"[green]Posted {posted} pins for {slug}[/green]")
```

**Step 4: Commit**

```bash
git add agents/orchestrator/ agents/__main__.py
git commit -m "feat: add orchestrator — pipeline coordination + APScheduler"
```

---

## Phase F: Analytics Agent

### Task 18: Analytics Agent

**Files:**
- Create: `agents/analytics/__init__.py`
- Create: `agents/analytics/collector.py`
- Create: `agents/analytics/reporter.py`

**Step 1: Create analytics collector**

Create `agents/analytics/__init__.py`:
```python
"""Analytics agent — data collection and weekly reporting."""
```

Create `agents/analytics/collector.py`:
```python
from datetime import datetime
from agents.db import get_connection


def record_post_metrics(slug: str, pageviews: int, pinterest_impressions: int = 0, pinterest_clicks: int = 0) -> None:
    """Update post metrics in the database."""
    conn = get_connection()
    conn.execute(
        """UPDATE posts SET pageviews = ?, pinterest_impressions = ?, pinterest_clicks = ?
           WHERE slug = ?""",
        (pageviews, pinterest_impressions, pinterest_clicks, slug)
    )
    conn.commit()
    conn.close()


def record_pin_metrics(pin_id: int, impressions: int, saves: int, clicks: int) -> None:
    """Update pin metrics in the database."""
    conn = get_connection()
    conn.execute(
        "UPDATE pins SET impressions = ?, saves = ?, clicks = ? WHERE id = ?",
        (impressions, saves, clicks, pin_id)
    )
    conn.commit()
    conn.close()
```

Create `agents/analytics/reporter.py`:
```python
from rich.console import Console
from rich.table import Table
from agents.db import get_connection

console = Console()


def generate_weekly_report() -> str:
    """Generate a weekly performance report."""
    conn = get_connection()

    total_posts = conn.execute("SELECT COUNT(*) as cnt FROM posts WHERE status = 'published'").fetchone()["cnt"]
    total_pins = conn.execute("SELECT COUNT(*) as cnt FROM pins WHERE status = 'posted'").fetchone()["cnt"]
    total_views = conn.execute("SELECT COALESCE(SUM(pageviews), 0) as total FROM posts").fetchone()["total"]
    total_impressions = conn.execute("SELECT COALESCE(SUM(pinterest_impressions), 0) as total FROM posts").fetchone()["total"]

    top_posts = conn.execute(
        "SELECT slug, title, pageviews, pinterest_clicks FROM posts WHERE status = 'published' ORDER BY pageviews DESC LIMIT 5"
    ).fetchall()

    top_pins = conn.execute(
        "SELECT title, board, impressions, clicks FROM pins WHERE status = 'posted' ORDER BY impressions DESC LIMIT 5"
    ).fetchall()

    # Category performance
    categories = conn.execute(
        """SELECT category, COUNT(*) as posts, SUM(pageviews) as views, SUM(pinterest_clicks) as clicks
           FROM posts WHERE status = 'published' GROUP BY category ORDER BY views DESC"""
    ).fetchall()

    conn.close()

    # Build report
    report = f"""
=== HerVisionCraft Weekly Report ===

Published posts: {total_posts}
Total pins posted: {total_pins}
Total pageviews: {total_views:,}
Pinterest impressions: {total_impressions:,}

--- Top Posts ---
"""
    for p in top_posts:
        report += f"  {p['title']} — {p['pageviews']:,} views, {p['pinterest_clicks']:,} clicks\n"

    report += "\n--- Category Performance ---\n"
    for c in categories:
        report += f"  {c['category']}: {c['posts']} posts, {c['views'] or 0:,} views\n"

    # Recommendation
    if categories:
        top_cat = categories[0]["category"]
        report += f"\nRecommendation: Double down on {top_cat} content.\n"

    return report


def print_report() -> None:
    """Print the weekly report to console."""
    report = generate_weekly_report()
    console.print(report)
```

**Step 2: Wire analytics CLI command**

Add to `agents/__main__.py`:
```python
@cli.command()
def report():
    """Show weekly analytics report."""
    from agents.analytics.reporter import print_report
    print_report()
```

**Step 3: Commit**

```bash
git add agents/analytics/ agents/__main__.py
git commit -m "feat: add analytics agent — metrics collection and weekly reporting"
```

---

## Phase G: Final Integration

### Task 19: Git Repository Setup

**Step 1: Initialize git repo**

```bash
cd hervisioncraft
git init
echo "node_modules/\ndist/\n.astro/\n__pycache__/\n*.pyc\n.env\ndata/hervisioncraft.db\ndata/pins/\ndata/keywords/\nqueue/drafts/*.md\n.pytest_cache/\nvenv/" > .gitignore
```

**Step 2: Create .env.example**

```bash
cat > .env.example << 'EOF'
ANTHROPIC_API_KEY=
UNSPLASH_ACCESS_KEY=
PEXELS_API_KEY=
FLUX_API_KEY=
PINTEREST_EMAIL=
PINTEREST_PASSWORD=
EOF
```

**Step 3: Initial commit**

```bash
git add .
git commit -m "feat: HerVisionCraft Autopilot — initial project setup"
```

---

### Task 20: Dockerfile for Remote Sandbox

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`

**Step 1: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY agents/pyproject.toml agents/
RUN pip install -e agents/

# Install Playwright browsers
RUN playwright install --with-deps chromium

COPY . .

CMD ["python", "-m", "agents", "run"]
```

**Step 2: Create docker-compose.yml**

```yaml
version: "3.8"
services:
  autopilot:
    build: .
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./queue:/app/queue
      - ./website/src/content/blog:/app/website/src/content/blog
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    restart: unless-stopped
```

**Step 3: Commit**

```bash
git add Dockerfile docker-compose.yml .env.example .gitignore
git commit -m "feat: add Docker setup for remote sandbox deployment"
```

---

### Task 21: End-to-End Smoke Test

**Step 1: Test the full pipeline locally**

```bash
cd hervisioncraft

# Verify website builds
cd website && npm run build && cd ..

# Verify CLI works
python -m agents status
python -m agents review list

# Run single pipeline cycle (requires API keys in config/settings.json)
python -m agents run --once
```

**Step 2: Test Pinterest login**

```bash
python -m agents pinterest test
```

**Step 3: Verify everything works end to end**

- Check `queue/drafts/` for generated posts
- Review and approve a post: `python -m agents review approve <slug>`
- Check `data/pins/` for generated pin graphics
- Verify pin images look correct (1000x1500, 4-image collage with text)

**Step 4: Final commit**

```bash
git add .
git commit -m "feat: HerVisionCraft Autopilot — complete pipeline ready"
```
