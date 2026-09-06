# EndeavourOS website

The endeavouros.com website. Static HTML built with [Astro](https://astro.build) — no
runtime, no database, no admin panel, nothing writable in the webroot.

Three tasks cover most of what people come here for:

- Editing content — a TOML edit under `data/` followed by `make check`; see "The shared data
  directory".
- Building the site on your own machine — see "Building".
- Putting a release on the server — see "Deploying to production".

## Layout

- `astro/` — the main site: home, download, news, ARM, and the info section.
- `data/` — the content that is not markup: release, mirrors, nav, packages, ARM images.
- `brand/` — the logo SVGs and the colour tokens the site's CSS derives from.
- `deploy/` — `nginx-production.conf` is the live site. Everything else is the preview
  host's and sits in `deploy/preview/`: `nginx-preview.conf` and `docker-compose.yml`.
- `scripts/` — the data validators, the link check, the WordPress importer. The
  build-output gates live in `astro/scripts/`, where the build can run them.

Discovery, the wiki, lives in its own repository at
`https://github.com/endeavouros-team/discovery.endeavouros.com`, laid out the same way.

News currently holds the release announcements from Mercury onward. They were imported from
the WordPress REST API before the cutover. That API is gone with the WordPress install, so
`scripts/import-news.py` can no longer fetch anything; it is kept for its link-rewriting
rules and as the record of how the import was done. Widening the archive would need another
source for the post bodies.

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
checksum and signature URLs are built from that plus the filename in `release.toml`. Bumping
a release edits one file — `release.toml`'s `[current]` fields plus the magnet and torrent
links — and regenerates all 78 mirror URLs, so a checksum link cannot drift away from the
image it verifies. `data/arm-images.toml` works the same way.

`make check` validates the field contract, `make mirrors` and `make arm` confirm every
composed URL still resolves. Those two warn rather than fail — a mirror that is briefly
down should not block a build — so read the output. Pass `--strict`
(`python3 scripts/check-mirrors.py --strict`) to make an unreachable URL an error instead.

See `data/README.md` for the field contract.

## Building

Node 22.12 or later and the dependencies, once per checkout. The `.nvmrc` pins the
version and the lockfile is committed:

    (cd astro && nvm use && npm ci)

`npm ci` rather than `npm install`: it installs exactly what the lockfile pins. The main
site's `npm run build` then runs `astro/scripts/audit-lock.mjs` before anything else, which
refuses a package that executes an install script, resolves off-registry, or ships without
an integrity hash unless it is in the allowlist there — the control the WordPress plugin
system never had.

Then:

    make check          # validate data/ against the field contract
    make links          # every internal link in astro/dist/ resolves
    make mirrors        # check every composed mirror URL is reachable
    make arm            # check every composed ARM image URL is reachable

    make dev-astro      # astro dev on :4321
    make build-astro    # -> astro/dist/

    make verify         # build, then run the build-output gate
    make serve          # serve astro/dist/ on :8812 for LAN review
    make deploy-preview # build, rsync to the preview host
    make clean          # drop the dist/ and .astro/ trees

There is no separate asset step. Everything under `astro/dist/_astro/` is produced by the
build — the images in `astro/src/assets/` come out fingerprinted, resized and converted. That
output is gitignored, so a clean checkout and `make build-astro` reproduces it exactly.

## Deploying to production

The build does not happen on the server, and the server needs no toolchain — no runtime, no
interpreter, no build step. CI builds it and attaches a tarball to a GitHub Release; the
deploy is downloading that and unpacking it into the webroot.

### 1. Cut a release

Tags are `vYYYY.MM.DD`, the day of the release, with `.1`, `.2` and so on appended for a
further release on the same day. `v2026.09.06` was the launch, so the next one that day
would be:

    git tag -a v2026.09.06.1 -m "mirror list and news update"
    git push origin v2026.09.06.1

Pushing a `v*` tag is what triggers a build. **Pushing to `main` does not** — ordinary
commits are checked by `.github/workflows/check.yml` and publish nothing, so refactors and
doc edits never produce a release.

The release job (`.github/workflows/build.yml`) validates `data/`, audits the lockfile,
builds with `PUBLIC_INDEXABLE=true`, runs the build-output gate and the link check, then
asserts the result is actually indexable: `robots.txt` allows crawling and names the
sitemap, and no page carries `noindex`. A build with that flag missing fails here rather
than being published — the last section explains why that matters.

    gh run watch --repo endeavouros-team/endeavouros.com

To rebuild a tag that already exists — a CI fix, or a run that failed halfway — start the
*Build site* workflow by hand (Actions → Build site → Run workflow) and give it the tag
name. It checks that tag out, builds it, and replaces the asset on that release.

### 2. Get the tarball

    gh release download v2026.09.06.1 --repo endeavouros-team/endeavouros.com

Or from the Releases page. The filename carries the tag and the short commit it was built
from — `eos-site-<tag>-<short sha>.tar.gz`, so the launch build was
`eos-site-v2026.09.06-4a92b64.tar.gz`.

### 3. Put it on the server

    tar -xzf eos-site-v2026.09.06.1-*.tar.gz -C /var/www/endeavouros.com/

If you would rather rsync an extracted copy, use `--delete`. It is load-bearing. The first
deploy replaced a compromised WordPress install, and `--delete` is what keeps the webroot
holding this site and nothing else; anything left beside it stays reachable, and the
static-site argument buys nothing. The target must therefore hold **only** this site —
check before running it.

### 4. Install the nginx config

`deploy/nginx-production.conf`. The lines marked `CONFIRM` are what has to be checked
against the box: the `server_name`s and whether www DNS points here, the webroot, the TLS
certificate paths, and the `arm.endeavouros.com` block at the end. That last one is two
checks. The certificate must cover `arm.`, and the WordPress vhost still answering for that
name has to be disabled as this config loads.

The certificate must cover all three names — `endeavouros.com`, `www.endeavouros.com` and
`arm.endeavouros.com` — because `www` and `arm` are HTTPS redirects, and a redirect cannot
be sent until the handshake succeeds. The `www` block's comment carries the `certbot
--expand` command; at launch the lineage covered only the bare name, and browsers that go
HTTPS-first refused `www` outright.

    sudo cp deploy/nginx-production.conf /etc/nginx/sites-available/endeavouros.com
    sudo ln -sf /etc/nginx/sites-available/endeavouros.com /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx

It sends the CSP, HSTS, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
`Permissions-Policy` and `Cross-Origin-Opener-Policy`. It also sets permanent caching for
`/_astro/*` and carries the five redirects and one 410 (`/comments/feed/`) that keep old
WordPress URLs from breaking.

Access logs are deliberately left on. `/privacy-policy/` tells visitors we keep request logs
for no more than 90 days, so logrotate on the host must be set to match that promise.

### 5. Verify the deploy

    curl -sI https://endeavouros.com/ | grep -iE 'content-security-policy|strict-transport|x-content-type|x-frame|referrer-policy'
    curl -s  https://endeavouros.com/robots.txt          # must Allow: / and name the sitemap
    curl -sI https://endeavouros.com/feed/               # 301 -> /news/feed.xml
    curl -sI https://endeavouros.com/comments/feed/      # 410
    curl -sI https://endeavouros.com/endeavouros-arm-install/   # 301 -> /endeavouros-arm/
    curl -sI https://endeavouros.com/privacy-policy-2/          # 301 -> /privacy-policy/
    curl -sI https://arm.endeavouros.com/                       # 301 -> /endeavouros-arm/
    curl -sI https://www.endeavouros.com/                       # 301 -> https://endeavouros.com/, no TLS error

    make spam-check

`make spam-check` fetches the live site as a browser, as Googlebot and as a click arriving
from Google, and reports any divergence between them plus any gambling vocabulary. It needs
no access to the host. Run it after every deploy. A clean result is not an all-clear: Google
verifies Googlebot by IP rather than user-agent, so a cloak keyed to real crawler ranges
cannot be seen from outside at all — only Search Console's URL Inspection settles that.

### Building by hand, if CI is unavailable

    PUBLIC_INDEXABLE=true make verify          # -> astro/dist/

One command, not two. `make verify` builds before it runs the gate, so building first and
then calling `make verify` separately rebuilds without the flag and overwrites the indexable
output with a `noindex` one.

**`PUBLIC_INDEXABLE=true` is not optional and it fails silently.** Without it every page
ships `<meta name="robots" content="noindex, nofollow">` and `/robots.txt` serves
`Disallow: /` — see `astro/src/layouts/Base.astro` and `astro/src/pages/robots.txt.ts`. The
site would look perfect and be invisible to search. The flag is unset by default so that
every preview build is noindex, and letting CI set it is the reason to prefer the release
tarball over a hand-rolled build.

