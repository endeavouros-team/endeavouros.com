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

Operational notes — the release runbook, the preview host, the search-index recovery — are
kept outside this repository.

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

Node 22 and the dependencies, once per checkout. Both `.nvmrc` files pin the version, and
both lockfiles are committed:

    (cd astro && nvm use && npm ci)
    (cd wiki  && nvm use && npm ci)

`npm ci` rather than `npm install`: it installs exactly what the lockfile pins. `npm run
build` then runs `scripts/audit-lock.mjs` before anything else, which refuses a package that
executes an install script, resolves off-registry, or ships without an integrity hash unless
it is in the allowlist there — the control the WordPress plugin system never had.

Then:

    make check       # validate data/ against the field contract
    make mirrors     # check every composed mirror URL is reachable
    make arm         # check every composed ARM image URL is reachable

    make dev-astro   # astro dev on :4321
    make build-astro # -> astro/dist/
    make build-wiki  # -> wiki/dist/

    make verify      # build, then run the build-output gate
    make deploy-preview

There is no separate asset step. Everything under `astro/dist/_astro/` is produced by the
build — the images in `astro/src/assets/` come out fingerprinted, resized and converted. That
output is gitignored, so a clean checkout and `make build-astro` reproduces it exactly.

## Deploying to production

The build does not happen on the server, and the server needs no toolchain — no runtime, no
interpreter, no build step. CI builds it and attaches a tarball to a GitHub Release; the
deploy is downloading that and unpacking it into the webroot.

### 1. Cut a release

    git tag -a v2026.09.06 -m "Titan Nova site launch"
    git push origin v2026.09.06

Pushing a `v*` tag is what triggers a build. **Pushing to `main` does not** — ordinary
commits are checked by `.github/workflows/check.yml` and publish nothing, so refactors and
doc edits never produce a release.

The release job (`.github/workflows/build.yml`) validates `data/`, audits the lockfile,
builds with `PUBLIC_INDEXABLE=true`, runs the build-output gate, then asserts the result is
actually indexable — `robots.txt` allows crawling and names the sitemap, and no page carries
`noindex`. It fails rather than publishing a build with that flag missing, which is the one
deploy mistake that is invisible in the output.

    gh run watch --repo endeavouros-team/endeavouros.com

### 2. Get the tarball

    gh release download v2026.09.06 --repo endeavouros-team/endeavouros.com

Or from the Releases page. The filename carries the tag and the short commit it was built
from, e.g. `eos-site-v2026.09.06-4a92b64.tar.gz`.

### 3. Put it on the server

    tar -xzf eos-site-v2026.09.06-*.tar.gz -C /var/www/endeavouros.com/

If you would rather rsync an extracted copy, use `--delete`. It is load-bearing: the webroot
holds a compromised WordPress install, and without it every old PHP file stays reachable
beside the new site and the static-site argument buys nothing. That also means the target
must hold **only** this site — check before running it.

### 4. Install the nginx config

`deploy/nginx-production.conf`. Four `CONFIRM` comments mark what must be checked against the
box: the `server_name` and whether www DNS points here, the webroot, and the TLS certificate
paths.

    sudo cp deploy/nginx-production.conf /etc/nginx/sites-available/endeavouros.com
    sudo ln -sf /etc/nginx/sites-available/endeavouros.com /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx

It carries the CSP, HSTS and the other security headers — the live site currently sends
**none** of them — plus permanent caching for `/_astro/*` and the six redirects that keep old
WordPress URLs working.

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
no access to the host. Run it after every deploy. A clean result is not an all-clear: Google
verifies Googlebot by IP rather than user-agent, so a cloak keyed to real crawler ranges
cannot be seen from outside at all — only Search Console's URL Inspection settles that.

### Building by hand, if CI is unavailable

    PUBLIC_INDEXABLE=true make build-astro     # -> astro/dist/
    make verify

**`PUBLIC_INDEXABLE=true` is not optional and it fails silently.** Without it every page
ships `<meta name="robots" content="noindex, nofollow">` and `/robots.txt` serves
`Disallow: /` — see `astro/src/layouts/Base.astro` and `astro/src/pages/robots.txt.ts`. The
site would look perfect and be invisible to search, which is precisely the problem this
project exists to fix. It is unset by default so every preview build is noindex. Letting CI
set it is the reason to prefer the release tarball over a hand-rolled build.

