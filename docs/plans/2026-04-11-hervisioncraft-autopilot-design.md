# HerVisionCraft Autopilot — System Design

**Date:** 2026-04-11
**Status:** Approved

## Overview

Automated content marketing pipeline for hervisioncraft.com — a women's lifestyle/aesthetics blog monetized through Pinterest traffic and display ads.

The system uses AI agents to research keywords, write blog posts, generate Pinterest pin graphics, and distribute content — running on near-full autopilot with human approval only for blog posts before publishing.

## Niche & Categories

Women's lifestyle/aesthetics with 12 categories:

1. Boho Decor / Home
2. Tattoo Ideas
3. Nail Art
4. Fashion / Outfits
5. Tarot / Spirituality
6. Kitchen / Recipes
7. Perfume / Fragrance
8. Makeup / Beauty
9. Hair / Hairstyles
10. Jewelry / Accessories
11. Self-care / Wellness
12. Wedding / Bridal

Target cadence: 3-4 posts/week (~1 post per category per month).

## Tech Stack

| Component | Technology |
|---|---|
| Blog | Astro (static site), Markdown content |
| Hosting | Netlify (auto-deploy from git) |
| Agents | Python, Claude API (Anthropic SDK) |
| Pinterest automation | Playwright (browser automation) |
| Pin graphics | Flux/DALL-E API + Pillow compositing |
| Stock images | Unsplash/Pexels API |
| Database | SQLite |
| Scheduler | APScheduler |
| Remote sandbox | VPS with Docker |
| Review workflow | CLI |

## Project Structure

```
hervisioncraft/
├── website/                  # Astro blog (deploys to Netlify)
│   ├── src/
│   │   ├── content/blog/     # Markdown posts (agents write here)
│   │   ├── pages/            # Home, category, about, privacy pages
│   │   ├── layouts/          # Base layout, blog post layout
│   │   ├── components/       # Nav, footer, post card, image grid
│   │   └── assets/images/    # Stock + generated images
│   ├── public/               # Favicons, robots.txt
│   └── astro.config.mjs
├── agents/                   # Python agent system
│   ├── researcher/           # Phase 1: keyword research + topic selection
│   ├── writer/               # Phase 2: blog post drafting
│   ├── image_sourcer/        # Phase 2: stock photos for blog posts
│   ├── publisher/            # Phase 2: git commit + deploy trigger
│   ├── pinterest/            # Phase 3: pin generation + browser posting
│   ├── analytics/            # Phase 6: data collection + reporting
│   ├── orchestrator/         # Scheduler + pipeline coordinator
│   └── __main__.py           # CLI entry point
├── queue/                    # Approval queue
│   ├── drafts/               # Posts awaiting review
│   └── upcoming.json         # Weekly content calendar
├── config/                   # Niche config, board mappings, schedules
│   ├── categories.json       # Category definitions + keywords
│   ├── boards.json           # Pinterest board → category mapping
│   ├── templates/            # Pin graphic templates
│   └── settings.json         # API keys, schedule config
├── data/                     # Persistent data
│   ├── hervisioncraft.db     # SQLite database
│   ├── pins/                 # Generated pin images
│   └── keywords/             # Keyword research cache
└── docs/
    └── plans/
```

## Phase 1: Research & Planning

### Researcher Agent

Runs weekly (Monday 6:00 AM).

**Keyword Research:**
- Uses Claude to analyze Pinterest trends by category
- Scrapes Pinterest search suggestions via Playwright (type keyword → capture autocomplete)
- Cross-references with Google Trends API and Pinterest Trends page
- Scores keywords: search volume estimate + ad revenue potential + competition
- Stores in SQLite `keywords` table

**Topic Selection:**
- Claude picks 3-4 topics from keyword pool
- Criteria: high Pinterest volume, not yet covered, good listicle potential
- Formats as listicle titles (e.g., "23 Minimalist Tattoo Ideas for Women")
- Assigns category and target keywords

**Content Calendar:**
- Slots topics into Mon/Wed/Fri/Sat publishing schedule
- Batches by theme when possible for topical authority
- Writes to `queue/upcoming.json`

**Output format:**
```json
{
  "week": "2026-04-13",
  "posts": [
    {
      "title": "23 Minimalist Tattoo Ideas for First-Timers",
      "category": "tattoo-ideas",
      "keywords": ["minimalist tattoo", "small tattoo ideas", "first tattoo"],
      "target_items": 23,
      "publish_date": "2026-04-14",
      "status": "draft"
    }
  ]
}
```

## Phase 2: Content Creation

### Writer Agent

Triggers for each topic on the calendar.

**Blog Post Drafting:**
- Takes topic, keywords, target item count from calendar
- Claude generates full Markdown post with frontmatter
- Tone: warm, aspirational, girlfriend-giving-advice
- Format: intro → numbered items (heading + 2-3 sentences + style tip) → conclusion
- Saves to `queue/drafts/{slug}.md`

**Blog post frontmatter:**
```yaml
title: "17 Boho Kitchen Ideas That Feel Effortlessly Chic"
description: "Discover stunning boho kitchen designs..."
category: "boho-decor"
tags: ["boho", "kitchen", "home decor"]
images: ["kitchen-1.webp", "kitchen-2.webp"]
pinterest_title: "Boho Kitchen Ideas | Her Vision Craft"
date: 2026-04-12
draft: false
```

### Image Sourcer Agent

- Searches Unsplash/Pexels API for each list item
- Downloads top match, optimizes to WebP
- Stores in `website/src/assets/images/posts/{slug}/`
- Inserts image references into Markdown draft
- Falls back gracefully if no good match found

### Review Workflow

Posts queue for human approval before publishing:

```bash
python -m agents review list                    # See what's waiting
python -m agents review show "slug"             # Preview a post
python -m agents review approve "slug"          # Approve for publishing
python -m agents review reject "slug" --note "" # Reject with feedback
```

### Publisher Agent

On approval:
- Moves post from `queue/drafts/` to `website/src/content/blog/`
- Commits to git and pushes → Netlify auto-deploys
- Updates post status in SQLite to `published`
- Triggers Pinterest agent

## Phase 3: Pinterest Distribution

### Pinterest Agent (Playwright Browser Automation)

Triggers after a post is published, runs in local or remote sandbox.

**Pin Graphic Generation:**

Style: 4-image grid collage with bold text overlay (Pinterest-native attention-grabbing style).

Process:
1. Claude writes 4 detailed image prompts based on the blog topic
2. Flux/DALL-E API generates 4 photorealistic images per prompt
3. Pillow assembles 2x2 collage on 1000x1500 canvas
4. Adds center title block:
   - Number badge (circle, bold font, contrasting color)
   - Large bold title (Impact/Montserrat Bold)
   - Key emotional word highlighted in accent color
   - Brand watermark at bottom
5. Creates 3-5 variations per post (different images, titles, accent colors)

**Title copy style:**
- Format: "{number} {ADJECTIVE} {keyword} IDEAS!"
- Claude picks the most emotional/visual word for color-pop highlight
- Examples: "23 STUNNING Boho Kitchen Ideas!", "31 MYSTICAL Tarot Tattoo Ideas!"

**Browser Posting (Playwright):**
- Logs into Pinterest in sandbox browser
- For each pin: upload image → set title → set description → set URL → select board → publish
- Spreads pins across the day (random 60-180s delays between actions)
- Posts to relevant boards based on category mapping in config

**Board Management:**
- Creates boards from config on first run
- Boards have keyword-rich names and descriptions
- Category → board mapping in `config/boards.json`

**Scheduling:**
- 5-15 pins/day spread across hours
- Mix of new post pins + reshares of older high-performers
- Top 20 posts get pins reshared on rotation indefinitely

## Phase 4: Website Design (Astro)

### Design Theme: "Her Vision Craft"

**Aesthetic:**
- Soft color palette: warm whites, blush pinks, sage greens, muted golds
- Large, tall images (mirrors Pinterest visual continuity)
- Mobile-first (80%+ of Pinterest traffic is mobile)
- Target < 1s LCP, zero JS by default (Astro)

**Pages:**
- **Home** — hero + latest posts in masonry grid (Pinterest-style)
- **Category pages** — `/boho-decor/`, `/tattoo-ideas/`, `/nail-art/`, etc.
- **Blog post** — listicle-optimized: intro → numbered image+text items → conclusion
- **About** — builds trust for future AdSense approval
- **Privacy / Disclaimer** — required for AdSense

**SEO:**
- Schema.org structured data (Article, ImageObject, BreadcrumbList)
- Auto-generated sitemap + RSS feed
- Open Graph + Pinterest-specific meta tags (rich pins)
- Canonical URLs, proper heading hierarchy
- Image optimization: WebP/AVIF via Astro built-in

## Phase 5: Monetization (Deferred)

Added later once traffic reaches threshold:
- **AdSense** — apply after ~20 posts are live with consistent traffic
- **Premium ads (Mediavine/Raptive)** — at 50k sessions/month
- **Affiliate links** — Amazon, Etsy product links within blog posts

Website layout will be designed with ad slot placeholders for easy integration later.

## Phase 6: Analytics & Optimization

### Analytics Agent

Runs weekly (Sunday).

**Data collection:**
- Pinterest: browser scrapes Pinterest analytics (impressions, saves, outbound clicks per pin)
- Website: Google Analytics Data API (pageviews, bounce rate, session duration, top posts)
- All metrics stored in SQLite with timestamps

**Weekly report:**
```
=== HerVisionCraft Weekly Report ===
Posts published: 4
Total pageviews: 2,340 (+18% vs last week)
Pinterest impressions: 45,200
Top pin: "23 Minimalist Tattoo Ideas" — 8,400 impressions, 312 clicks
Top post: "/boho-kitchen-ideas" — 890 pageviews

Recommendation: Double down on tattoo + boho content.
```

**Feedback loop:**
- Tags keywords/categories with performance scores
- Researcher agent weighs scores when picking next week's topics
- High performers → more content scheduled
- Low performers → experiment with title styles before dropping

**Auto-resharing:**
- Posts crossing pageview threshold get fresh pin variations automatically
- Evergreen top 20 posts reshared on rotation indefinitely

## Orchestrator & Scheduling

**Daily schedule:**
```
Monday 6:00 AM    → Researcher: generate weekly content plan
Mon-Sat 7:00 AM   → Writer: draft next post from calendar
Mon-Sat 7:30 AM   → Image Sourcer: fetch stock images for draft
                   → Notification: "Post ready for review"
(Human approves)   → Publisher: commit + deploy to Netlify
+30 min after pub  → Pinterest Agent: generate AI pin images
+60 min after pub  → Pinterest Agent: start posting pins (spread over day)
Daily ongoing      → Pinterest Agent: reshare older high-performing pins
Sunday             → Analytics Agent: weekly report
```

**Post state machine:**
```
research → draft → images_added → review → approved → published → pins_generated → pins_posted
                                    ↓
                                 rejected → redraft → review (loop)
```

**CLI:**
```bash
python -m agents status          # Dashboard
python -m agents review list     # Posts awaiting approval
python -m agents review approve  # Approve a post
python -m agents run             # Start orchestrator
python -m agents run --once      # Single cycle (testing)
python -m agents pinterest test  # Test Pinterest login
```

**Error handling:**
- Pinterest login fails → pause posting, notify user
- Claude API fails → retry 3x with backoff, skip + notify
- Image generation fails → fall back to stock photo collage
- All errors logged + surfaced in `agents status`

## Automation Level

- **Blog posts:** fully automated through draft, human approves before publish
- **Pinterest pins:** fully automated after post is published
- **Keywords/topics:** fully automated
- **Analytics:** fully automated with weekly report
