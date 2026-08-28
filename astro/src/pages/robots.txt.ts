import type { APIRoute } from 'astro';

// Mirrors the noindex meta in Base.astro. Until PUBLIC_INDEXABLE is set for
// launch, this build refuses crawlers outright so it cannot compete with the
// live site in search.
export const GET: APIRoute = ({ site }) => {
  const indexable = import.meta.env.PUBLIC_INDEXABLE === 'true';
  const body = indexable
    ? `User-agent: *\nAllow: /\nSitemap: ${new URL('sitemap-index.xml', site)}\n`
    : `User-agent: *\nDisallow: /\n`;
  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
