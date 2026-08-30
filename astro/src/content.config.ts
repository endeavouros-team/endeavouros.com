import { defineCollection, z } from 'astro:content';
import { file, glob } from 'astro/loaders';
import { parse as parseToml } from 'smol-toml';

/**
 * The shared ../data directory is the single source of truth and is read by the
 * Zola build too, so neither track owns it. Astro's file() loader reads paths
 * outside the project root, which Zola's load_data() refuses to do.
 *
 * TOML's top level is always a table, so `[[mirrors]]` parses to
 * { mirrors: [...] }. The loader wants one entry per row carrying an `id`.
 *
 * smol-toml is already a direct dependency of astro, so declaring it adds no
 * packages to the lockfile.
 */
const tomlRows = (path: string, key: string) =>
  file(path, {
    parser: (text) => {
      const doc = parseToml(text) as Record<string, unknown>;
      const rows = (doc[key] ?? []) as Record<string, unknown>[];
      // getCollection() returns entries sorted by id, which would silently
      // reorder editorial lists (Firefox first, systemd-boot before GRUB).
      // Carry the declaration index so callers can restore file order.
      return rows.map((row, order) => ({ ...row, order, id: String(row.id ?? row.name) }));
    },
  });

export const CONTINENTS = [
  'Africa', 'Asia', 'Europe', 'North America', 'South America', 'Oceania',
] as const;

const mirrors = defineCollection({
  loader: tomlRows('../data/mirrors.toml', 'mirrors'),
  schema: z.object({
    id: z.string().regex(/^[a-z0-9-]+$/, 'id must be lowercase alphanumeric and hyphens'),
    continent: z.enum(CONTINENTS),
    country: z.string().min(2),
    countryCode: z.string().regex(/^[A-Z]{2}$/, 'countryCode must be two uppercase letters'),
    order: z.number().int(),
    name: z.string().min(2),
    // The directory holding the ISO. The three per-mirror URLs are composed
    // from this plus release.iso, never stored.
    base: z.string().url()
      .refine((u) => u.startsWith('https://'), 'mirrors must be served over https')
      .refine((u) => !u.endsWith('/'), 'drop the trailing slash, URLs are composed'),
    active: z.boolean().default(true),
  }),
});

/**
 * A truncated or mistyped checksum must fail the build rather than ship: it is
 * the value users verify their download against.
 */
const release = defineCollection({
  loader: file('../data/release.toml'),
  schema: z.object({
    codename: z.string().min(2),
    date: z.coerce.date(),
    iso: z.string().regex(
      /^EndeavourOS_[A-Za-z][A-Za-z-]*-\d{4}\.\d{2}\.\d{2}\.iso$/,
      'iso must match the release naming convention',
    ),
    sha512: z.string().regex(/^[0-9a-f]{128}$/, 'sha512 must be 128 lowercase hex characters'),
    sizeBytes: z.number().int().positive(),
    sha512Suffix: z.string().startsWith('.'),
    sigSuffix: z.string().startsWith('.'),
    magnet: z.string().startsWith('magnet:?xt=urn:btih:'),
    torrent: z.string().url(),
    signing: z.object({
      name: z.string(),
      email: z.string().email(),
      fingerprint: z.string().regex(
        /^([0-9A-F]{4} ){9}[0-9A-F]{4}$/,
        'fingerprint must be 40 hex characters in 10 space-separated groups',
      ),
      shortKey: z.string().regex(/^[0-9A-F]{8}$/),
      keyserver: z.string(),
    }),
    requirements: z.object({
      diskGb: z.number().int().positive(),
      ramGb: z.number().int().positive(),
      cpu: z.string(),
      note: z.string(),
    }),
  }),
});

/**
 * site.toml is a flat table, and the file() loader would otherwise split each
 * top-level key into its own entry. Wrap it as a single row instead.
 */
const navItem = z.object({
  name: z.string(),
  url: z.string(),
  external: z.boolean().default(false),
  wip: z.boolean().default(false),
  cta: z.boolean().default(false),
});

const site = defineCollection({
  loader: file('../data/site.toml', {
    parser: (text) => [{ id: 'site', ...(parseToml(text) as Record<string, unknown>) }],
  }),
  schema: z.object({
    id: z.string(),
    name: z.string(),
    tagline: z.string(),
    subtitle: z.string(),
    description: z.string(),
    url: z.string().url(),
    contentOrigins: z.array(z.string().url()).default([]),
    nav: z.array(navItem).min(1),
    footer: z.array(z.object({
      heading: z.string(),
      links: z.array(z.object({ name: z.string(), url: z.string().url() })).min(1),
    })).min(1),
  })
    .superRefine((s, ctx) => {
      for (const n of s.nav) {
        const ok = n.external ? n.url.startsWith('https://') : n.url.startsWith('/');
        if (!ok) ctx.addIssue({ code: z.ZodIssueCode.custom,
          message: `nav "${n.name}": ${n.external ? 'external links must be https' : 'internal links must be root-relative'}` });
      }
    }),
});

const packages = defineCollection({
  loader: tomlRows('../data/packages.toml', 'packages'),
  schema: z.object({
    id: z.string(),
    order: z.number().int(),
    name: z.string(),
    desc: z.string(),
    url: z.string().url().optional(),
  }),
});

const bootloaders = defineCollection({
  loader: tomlRows('../data/packages.toml', 'bootloaders'),
  schema: z.object({ id: z.string(), order: z.number().int(), name: z.string(), desc: z.string() }),
});

/**
 * News announcements, imported from WordPress by scripts/import-news.py.
 *
 * The only authored-Markdown collection on the site; everything else is TOML
 * out of ../data. Hero images go through image() so Astro's pipeline owns the
 * resizing and format negotiation rather than shipping the 2560px original.
 *
 * heroAlt is deliberately not .min(1): every alt attribute in the WordPress
 * source is empty, so requiring it would have held the import hostage to
 * copywriting. The empty strings are visible in review and are the team's to
 * fill; the importer reads back anything authored here and preserves it.
 */
const news = defineCollection({
  loader: glob({ pattern: '*.md', base: './src/content/news' }),
  schema: ({ image }) => z.object({
    title: z.string().min(4),
    description: z.string().min(20).max(200),
    date: z.coerce.date(),
    author: z.string().min(2),
    hero: image(),
    heroAlt: z.string(),
  }),
});

export const collections = { mirrors, release, site, packages, bootloaders, news };
