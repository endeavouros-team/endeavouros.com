import type { APIRoute } from 'astro';
import { newsPosts, siteData } from '../../lib/site';

/**
 * RSS 2.0 by hand, deliberately.
 *
 * @astrojs/rss would do this, but it pulls nine transitive packages -- eight of
 * them from a single maintainer -- to emit seven <item> elements. On a site
 * that is being rebuilt precisely because a plugin ecosystem was compromised,
 * that is the wrong trade for a fixed, 30-line document we fully control.
 *
 * Everything below is escaped and every URL is absolute, which is all RSS 2.0
 * actually requires of us.
 */
const escape = (s: string) =>
  s.replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

export const GET: APIRoute = async ({ site }) => {
  if (!site) throw new Error('astro.config.mjs must set `site` for the feed to build absolute URLs');
  const s = await siteData();
  const posts = await newsPosts();
  const self = new URL('/news/feed.xml', site).href;

  const items = posts.map((post) => {
    const url = new URL(`/news/${post.id}/`, site).href;
    return `    <item>
      <title>${escape(post.data.title)}</title>
      <link>${url}</link>
      <guid isPermaLink="true">${url}</guid>
      <pubDate>${post.data.date.toUTCString()}</pubDate>
      <author>${escape(post.data.author)}</author>
      <description>${escape(post.data.description)}</description>
    </item>`;
  }).join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>${escape(s.name)} News</title>
    <link>${new URL('/news/', site).href}</link>
    <description>Release announcements from the ${escape(s.name)} team.</description>
    <language>en</language>
    <atom:link href="${self}" rel="self" type="application/rss+xml" />
${items}
  </channel>
</rss>
`;

  return new Response(xml, { headers: { 'Content-Type': 'application/rss+xml; charset=utf-8' } });
};
