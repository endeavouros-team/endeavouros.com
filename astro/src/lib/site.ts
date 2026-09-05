import { getCollection, getEntry, type CollectionEntry } from 'astro:content';
import { CONTINENTS } from '../content.config';

export type Mirror = CollectionEntry<'mirrors'>['data'];
export type NewsPost = CollectionEntry<'news'>;
export type Release = CollectionEntry<'release'>['data'];

export async function release(): Promise<Release> {
  const e = await getEntry('release', 'current');
  if (!e) throw new Error('data/release.toml is missing the [current] table');
  return e.data;
}

export async function siteData() {
  const e = await getEntry('site', 'site');
  if (!e) throw new Error('data/site.toml failed to load');
  return e.data;
}

/** The URL composition rule, stated exactly once for the whole site. */
export function mirrorUrls(m: Mirror, rel: Release) {
  const iso = `${m.base}/${rel.iso}`;
  return { iso, sha512: iso + rel.sha512Suffix, sig: iso + rel.sigSuffix };
}

/** Grouped for rendering, in declared continent order, empty groups dropped. */
export async function mirrorsByContinent() {
  const all = (await getCollection('mirrors')).filter((m) => m.data.active);
  return CONTINENTS.map((continent) => ({
    continent,
    slug: continent.toLowerCase().replace(/\s+/g, '-'),
    items: all
      .map((e) => e.data)
      .filter((m) => m.continent === continent)
      .sort((a, b) => a.country.localeCompare(b.country) || a.name.localeCompare(b.name)),
  })).filter((g) => g.items.length > 0);
}

/** Consumed by scripts/check-build.mjs to allowlist outbound origins. */
export async function mirrorOrigins() {
  return [...new Set((await getCollection('mirrors')).map((m) => new URL(m.data.base).origin))];
}

export function formatBytes(n: number) {
  return `${(n / 1024 ** 3).toFixed(2)} GiB`;
}

/**
 * News, newest first. The ordering lives here rather than in a template so the
 * listing and the feed cannot quietly disagree about what "latest" means.
 */
export async function newsPosts(): Promise<NewsPost[]> {
  return (await getCollection('news')).sort(
    (a, b) => b.data.date.valueOf() - a.data.date.valueOf(),
  );
}

/**
 * Frontmatter dates are bare YYYY-MM-DD, which parse as UTC midnight. Format in
 * UTC too, or a reader west of Greenwich sees every announcement dated a day
 * early.
 */
export function formatDate(d: Date) {
  return d.toLocaleDateString('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
  });
}

/**
 * Where a post footer sends readers to discuss it. Resolved from data/site.toml
 * by origin rather than by link text, so renaming the nav entry cannot silently
 * drop the link, and a missing forum fails the build instead of shipping a
 * dead end.
 */
export async function forumUrl(): Promise<string> {
  const s = await siteData();
  const urls = [
    ...s.nav.map((n) => n.url),
    ...s.footer.flatMap((c) => c.links.map((l) => l.url)),
  ];
  const found = urls.find((u) => u.startsWith('https://forum.'));
  if (!found) throw new Error('data/site.toml has no forum link for news post footers');
  return found;
}

export type ArmDevice = { id: string; name: string; tag: string; image: string; server: boolean };

/**
 * ARM images, with their URLs composed the same way mirror URLs are: from a
 * base plus the parts, never stored. Stated once here so the table and the
 * build gate cannot disagree about where an image lives.
 */
export async function armImages() {
  const e = await getEntry('arm', 'arm');
  if (!e) throw new Error('data/arm-images.toml failed to load');
  const { base, sha512Suffix, devices } = e.data;
  return {
    devices: devices.map((d) => {
      const img = `${base}/${d.tag}/${d.image}`;
      return { ...d, img, sha512: img + sha512Suffix };
    }),
  };
}

/** Consumed by scripts/check-build.mjs to allowlist the ARM image origin. */
export async function armOrigin() {
  const e = await getEntry('arm', 'arm');
  return e ? new URL(e.data.base).origin : null;
}
