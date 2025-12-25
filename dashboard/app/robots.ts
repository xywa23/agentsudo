import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/dashboard/', '/profile/', '/playground/', '/api/'],
    },
    sitemap: 'https://agentsudo.dev/sitemap.xml',
  }
}
