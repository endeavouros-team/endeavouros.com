import type { APIRoute } from 'astro';

// Mirrors the noindex meta in Base.astro: while PUBLIC_INDEXABLE is unset, the
// internal review build refuses crawlers outright.
export const GET: APIRoute = ({ site }) => {
  const indexable = import.meta.env.PUBLIC_INDEXABLE === 'true';
  const body = indexable
    ? `User-agent: *\nAllow: /\nSitemap: ${new URL('sitemap-index.xml', site)}\n`
    : `# Internal review build. Set PUBLIC_INDEXABLE=true for launch.\nUser-agent: *\nDisallow: /\n`;
  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
