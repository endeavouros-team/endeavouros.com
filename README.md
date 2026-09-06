# EndeavourOS website

The endeavouros.com website. Static HTML built with [Astro](https://astro.build) — no
runtime, no database, no admin panel, nothing writable in the webroot.

## Layout

- `astro/` — the main site: home, download, news, ARM, and the info section.
- `wiki/` — Discovery, on Starlight. Three converted articles so far, not a migration.
- `data/` — the content that is not markup: release, mirrors, nav, packages, ARM images.
- `deploy/` — the nginx configs for production and for the preview host.
- `scripts/` — data validators, the build-output gates, the WordPress importer.

News currently holds the release announcements from Mercury onward. `scripts/import-news.py`
is re-runnable and takes a slug list, so widening that is an edit rather than a rewrite.

> **Keep this repository private** until the old WordPress host is remediated.
> `docs/seo-recovery.md` assesses a production box that was compromised repeatedly and is not
> yet fixed, naming the endpoints still reachable on it. That is the right document for
> whoever fixes the server and a map for anyone else.

## The shared data directory

`data/` is the single source of truth. Nothing in it is markup, so adding a mirror or bumping
a release needs no toolchain installed — which is the point of the split.

| File | Holds |
|---|---|
| `data/release.toml` | The current ISO: filename, date, checksum, signing key, torrent |
| `data/mirrors.toml` | The 26 download mirrors |
| `data/site.toml` | Navigation, taglines, footer links |
| `data/packages.toml` | Preset packages and bootloader options |
| `data/arm-images.toml` | The 6 ARM device images |

Download URLs are **composed, never stored.** Each mirror carries a `base`, and the ISO,
checksum and signature URLs are built from that plus the filename in `release.toml`. Bumping a
release edits four lines in one file and regenerates all 78 mirror URLs; a checksum link
cannot drift away from the image it verifies. `data/arm-images.toml` works the same way.

`make check` validates the field contract, `make mirrors` and `make arm` confirm every
composed URL still resolves.

See `data/README.md` for the field contract.

## Building

    make check       # validate data/ against the field contract
    make mirrors     # check every composed mirror URL is reachable
    make arm         # check every composed ARM image URL is reachable

    make dev-astro   # astro dev on :4321
    make build-astro # -> astro/dist/
    make build-wiki  # -> wiki/dist/

    make verify      # build, then run the build-output gate
    make deploy-preview

## Deploying to production

The whole deploy is: build with one environment variable set, check it, rsync the output,
install one nginx config. Nothing is installed on the server — there is no runtime, no
interpreter and no build step there.

### 1. Build for production

    PUBLIC_INDEXABLE=true make build-astro

**`PUBLIC_INDEXABLE=true` is not optional and it fails silently.** Without it every page
ships `<meta name="robots" content="noindex, nofollow">` and `/robots.txt` serves
`Disallow: /` — see `astro/src/layouts/Base.astro` and `astro/src/pages/robots.txt.ts`.
The site would look perfect and be invisible to search, which is precisely the problem this
project exists to fix. It is unset by default so that every preview build is noindex and
cannot compete with the live site.

### 2. Check before copying anything

    make verify

Builds the site and runs the build-output gate, which asserts the output contains no script
we did not write and no outbound origin that is not in `data/`. This is the WordPress lesson
mechanised: the compromise showed up as injected markup in served pages, so this fails rather
than warns. **If it fails, do not deploy.**

### 3. Copy the build

    rsync -avz --delete astro/dist/ user@endeavouros.com:/var/www/endeavouros.com/

`--delete` is load-bearing. The webroot currently holds a compromised WordPress install;
without it, every old PHP file stays reachable beside the new site and the static-site
argument buys nothing. That also means the target must be a directory holding **only** this
site — check it before running with `--delete`.

### 4. Install the nginx config

`deploy/nginx-production.conf`. Three values are marked `CONFIRM` in the file and must be
checked against the box: the webroot, the `server_name`, and the TLS certificate paths.

    sudo cp deploy/nginx-production.conf /etc/nginx/sites-available/endeavouros.com
    sudo ln -sf /etc/nginx/sites-available/endeavouros.com /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx

It carries the CSP, HSTS and the other security headers — the live site currently sends
**none** of them — plus permanent caching for `/_astro/*` and the six redirects that keep
old WordPress URLs working.

Access logs are deliberately left on. `/privacy-policy/` tells visitors we keep request logs
for no more than 90 days, so logrotate on the host must be set to match that promise.

### 5. Verify the deploy

    curl -sI https://endeavouros.com/ | grep -iE 'content-security-policy|strict-transport|x-content-type|x-frame|referrer-policy'
    curl -s  https://endeavouros.com/robots.txt          # must Allow: / and name the sitemap
    curl -sI https://endeavouros.com/feed/               # 301 -> /news/feed.xml
    curl -sI https://endeavouros.com/comments/feed/      # 410
    curl -sI https://endeavouros.com/endeavouros-arm-install/   # 301 -> /endeavouros-arm/
    curl -sI https://endeavouros.com/privacy-policy-2/          # 301 -> /privacy-policy/

    make spam-check

`make spam-check` fetches the live site as a browser, as Googlebot and as a click arriving
from Google, and reports any divergence between them plus any gambling vocabulary. It needs
no access to the host. Run it after every deploy, and read `docs/seo-recovery.md` for what a
clean result does and does not prove.

## Documentation

- `docs/status.md` — where the work stands, what is open, what is next
- `docs/bake-off.md` — the Zola vs Astro comparison, written from measured output
- `docs/preview-hosting.md` — how the three previews are served, and what breaks them
- `docs/release-bump.md` — how to publish a new ISO release, written from the Titan Nova bump
- `docs/seo-recovery.md` — reclaiming the search index from the injected spam, and why the
  static launch does not do it on its own
