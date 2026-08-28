import { getCollection, getEntry, type CollectionEntry } from 'astro:content';
import { CONTINENTS } from '../content.config';

export type Mirror = CollectionEntry<'mirrors'>['data'];
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
