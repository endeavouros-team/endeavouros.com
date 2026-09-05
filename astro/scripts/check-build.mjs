#!/usr/bin/env node
/**
 * Build-output integrity gate — the WordPress lesson, mechanised.
 *
 * The site was compromised by injected markup in served pages. This asserts
 * that dist/ contains no script we did not write and no outbound origin we did
 * not put there. It fails the build; it does not warn.
 *
 * Mirror origins are derived from ../data/mirrors.toml, so adding a mirror to
 * the shared data permits its origin automatically and the allowlist cannot
 * drift away from the content.
 */
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, extname, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse as parseToml } from 'smol-toml';

const root = fileURLToPath(new URL('..', import.meta.url));
const dist = join(root, 'dist');
const dataDir = join(root, '..', 'data');

/** Inline scripts we intend to ship. Regenerate with --update when they change. */
const EXPECTED = new Set(JSON.parse(readFileSync(join(root, 'scripts/inline-scripts.json'), 'utf8')));

const mirrors = parseToml(readFileSync(join(dataDir, 'mirrors.toml'), 'utf8')).mirrors;
const site = parseToml(readFileSync(join(dataDir, 'site.toml'), 'utf8'));
const release = parseToml(readFileSync(join(dataDir, 'release.toml'), 'utf8')).current;

const allowed = new Set([
  ...mirrors.map((m) => new URL(m.base).origin),
  new URL(release.torrent).origin,
  new URL(site.url).origin,
  ...site.nav.filter((n) => n.external).map((n) => new URL(n.url).origin),
  ...site.footer.flatMap((c) => c.links.map((l) => new URL(l.url).origin)),
  // Imported news bodies link out to hosts that are in no other data file.
  // Hand-maintained on purpose; see data/site.toml.
  ...(site.contentOrigins ?? []).map((u) => new URL(u).origin),
]);
// Package links are editorial and change with packages.toml.
for (const p of parseToml(readFileSync(join(dataDir, 'packages.toml'), 'utf8')).packages) {
  if (p.url) allowed.add(new URL(p.url).origin);
}

const walk = (dir) => readdirSync(dir).flatMap((e) => {
  const p = join(dir, e);
  return statSync(p).isDirectory() ? walk(p) : [p];
});

const fails = [];
const seen = new Set();
const update = process.argv.includes('--update');

for (const file of walk(dist)) {
  if (extname(file) !== '.html') continue;
  const rel = relative(dist, file);
  const html = readFileSync(file, 'utf8');

  for (const m of html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/gi)) {
    const [, attrs, body] = m;
    if (/\ssrc=/i.test(attrs)) {
      const src = /src=["']?([^"'\s>]+)/i.exec(attrs)?.[1] ?? '';
      if (/^https?:/i.test(src)) fails.push(`${rel}: external <script src=${src}>`);
      continue;
    }
    if (/type=["']?application\/ld\+json/i.test(attrs)) continue; // data, not code
    const hash = 'sha256-' + createHash('sha256').update(body, 'utf8').digest('base64');
    seen.add(hash);
    if (!update && !EXPECTED.has(hash)) fails.push(`${rel}: unexpected inline <script> ${hash}`);
  }

  for (const m of html.matchAll(/(?:src|href|action|poster)=["']?(https?:\/\/[^"'\s>]+)/gi)) {
    const { origin } = new URL(m[1]);
    if (!allowed.has(origin)) fails.push(`${rel}: unexpected external origin ${origin}`);
  }

  for (const bad of ['eval(', 'document.write(', 'atob(']) {
    if (html.includes(bad)) fails.push(`${rel}: dynamic-code construct ${bad}`);
  }

  /*
   * Astro trims the newline and indent before an element that starts a line, so
   * a link wrapped onto its own line renders as "through the<a>forum</a>" --
   * "theforum" on the page. It is invisible in the source, survives review, and
   * we shipped seven of them in one sitting building the info section.
   *
   * Only inline elements that carry visible text count. An sr-only <span> holds
   * its own leading space inside the element and is correct as written.
   */
  const body = html.split('<main')[1] ?? '';
  for (const m of body.matchAll(/\w<(a|code|strong|em)\b/g)) {
    const at = body.slice(Math.max(0, m.index - 40), m.index + m[0].length);
    fails.push(`${rel}: missing space before <${m[1]}> — ...${at.replace(/\s+/g, ' ')}...`);
  }
}

if (update) {
  const { writeFileSync } = await import('node:fs');
  writeFileSync(join(root, 'scripts/inline-scripts.json'), JSON.stringify([...seen].sort(), null, 2) + '\n');
  console.log(`  recorded ${seen.size} inline script hash(es)`);
  process.exit(0);
}

// The CSP and the hash allowlist must agree, or one silently drifts. The policy
// is restated in two places — _headers for Cloudflare Pages, the nginx conf for
// the preview host — and only checking one lets the other rot. A stale nginx
// conf blocks the theme bootstrap, which shows up as a flash of the wrong theme
// on the preview and nowhere else.
const policies = {
  'public/_headers': join(root, 'public/_headers'),
  '../deploy/nginx-preview.conf': join(root, '..', 'deploy', 'nginx-preview.conf'),
};
for (const [label, path] of Object.entries(policies)) {
  const text = readFileSync(path, 'utf8');
  for (const h of EXPECTED) {
    if (!text.includes(`'${h}'`)) fails.push(`${label}: CSP is missing ${h}`);
  }
}

if (fails.length) {
  console.error(`\n  check-build: ${fails.length} problem(s)\n`);
  for (const f of fails) console.error(`    ${f}`);
  console.error('\n  If an inline script changed on purpose: npm run check:build -- --update,');
  console.error('  then paste the new hashes into public/_headers AND deploy/nginx-preview.conf.\n');
  process.exit(1);
}

console.log(`  check-build ok — ${seen.size} inline scripts all expected, every external origin allowlisted`);
