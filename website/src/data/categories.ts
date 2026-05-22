export const CATEGORIES = [
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
] as const;

export type CategorySlug = (typeof CATEGORIES)[number]['slug'];
