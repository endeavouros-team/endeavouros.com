# The shared data directory

This is the single source of truth for the site. **Both** the Zola and the Astro
build read these files, so the two cannot disagree, and neither one owns them.

Nothing here is markup, so editing a file in this directory needs no toolchain
installed — that is the point of the split, and it is what lets a mirror
maintainer add a mirror without cloning the site.

Validation is `make check`, run by whoever holds the repo. Run it after any
edit: it is fast and it will catch you. Once the repo is hosted somewhere the
team can send changes to, that check belongs in CI so a contributor without the
toolchain gets the same answer without waiting on anyone.

## `release.toml`

The current ISO. **This is the file a release bump edits**, and it is the only
one.

| Field | Contract |
|---|---|
| `codename` | Release name, e.g. `Titan Neo` |
| `date` | Release date, TOML date literal |
| `iso` | Filename, must match `EndeavourOS_<Name>-YYYY.MM.DD.iso` |
| `sha512` | Exactly 128 lowercase hex characters |
| `sizeBytes` | Positive integer, from `Content-Length` on any mirror |
| `sha512Suffix` / `sigSuffix` | Appended to `iso` to build the other two URLs |
| `magnet` | A `magnet:?xt=urn:btih:` URI |
| `torrent` | https URL |
| `signing.fingerprint` | 40 hex characters in 10 space-separated groups of 4 |
| `signing.shortKey` | Must be the tail of the fingerprint |

The checksum and the fingerprint are what users verify a download against, so
both are rendered verbatim and both are format-checked on every build. A
truncated or uppercased checksum fails the build rather than shipping.

## `mirrors.toml`

One `[[mirrors]]` stanza per mirror.

**Download URLs are composed, never stored:**

    {base}/{release.iso}
    {base}/{release.iso}{release.sha512Suffix}
    {base}/{release.iso}{release.sigSuffix}

That is the whole point of this file. 26 mirrors x 3 links = 78 URLs that
regenerate from one edit to `release.toml`. The old WordPress page hardcoded all
78, and hand-editing them was how it ended up linking one mirror over plain
`http` and omitting another mirror's checksum link entirely.

| Field | Contract |
|---|---|
| `id` | Unique, lowercase, `[a-z0-9-]` |
| `continent` | One of Africa, Asia, Europe, North America, South America, Oceania |
| `country` | Display name |
| `countryCode` | Two uppercase letters (ISO 3166-1 alpha-2) |
| `name` | The mirror operator's name, as they would like it shown |
| `base` | Directory holding the ISO. **https, no trailing slash** |
| `active` | Optional, default `true`. Set `false` to hide without deleting |

### Adding a mirror

Append a stanza, then:

    make check      # field contract
    make mirrors    # is the ISO actually there?

`make mirrors` reports non-200 as a warning rather than an error. Some mirrors
reject scripted requests while serving browsers fine, and a mirror being briefly
down should never block a build. Check any warning by hand before acting on it.

## `site.toml`

Identity, navigation and footer.

Nav entries marked `wip = true` point at the current WordPress site because that
section is not migrated yet. They render muted with a tooltip, so an internal
reviewer sees the real nav shape without us pretending the pages exist. Clear
`wip` and `external` as each section lands — as News, EndeavourOS ARM, Info and
Support us have.

That fallback stopped being safe on 2026-09-05, when the WordPress host began
returning 500 site-wide. A `wip` entry now points at a page that does not
answer, so anything still marked `wip` is a dead link rather than a degraded
one.

`contentOrigins` is the allowlist of outbound hosts that imported news bodies may
link to. Both build-output gates read it, and nothing else grants an origin to
post content. It is hand-maintained on purpose: deriving it from the content
would let an injected link authorise itself, which is precisely what the gates
exist to catch. Adding a host is a reviewed one-line diff; each entry must be a
bare `https://` origin with no path or trailing slash, which
`scripts/validate-data.py` enforces.

## `arm-images.toml`

The EndeavourOS ARM images, one `[[devices]]` stanza per device.

| Field | Contract |
|---|---|
| `base` | Release-download root, https, no trailing slash |
| `sha512Suffix` | Appended to `image` to build the checksum URL |
| `devices[].id` | Lowercase alphanumeric and hyphens |
| `devices[].name` | Shown in the Device column |
| `devices[].tag` | Upstream release tag |
| `devices[].image` | Asset filename, must end `.img.xz` |
| `devices[].server` | `true` for the headless images, which render in their own table |

Same composition rule as `mirrors.toml`: no full URL is ever stored. The download
and checksum URLs are built from `base` + `tag` + `image`, so a checksum link
cannot drift away from the image it verifies.

The upstream tags end in `-latest` and are reused across image rebuilds, which is
what keeps this file stable — and also what makes `make arm` necessary. A device
dropped upstream, or a tag renamed, changes nothing here and would ship as a dead
download link. `make arm` HEADs all of them; it is the ARM counterpart of
`make mirrors` and should be run for the same reasons.

## `packages.toml`

The preset software list and the bootloader options shown on the homepage. Copy
lives here so it can be corrected without touching either site's markup.
