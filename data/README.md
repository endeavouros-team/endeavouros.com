# The shared data directory

This is the single source of truth for the site. **Both** the Zola and the Astro
build read these files, so the two cannot disagree, and neither one owns them.

Nothing here is markup. Editing a file in this directory is a normal pull
request that needs no toolchain installed — CI validates it and rebuilds the
site.

Run `make check` after any edit. It is fast and it will catch you.

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
`wip` and `external` as each section lands.

`contentOrigins` is the allowlist of outbound hosts that imported news bodies may
link to. Both build-output gates read it, and nothing else grants an origin to
post content. It is hand-maintained on purpose: deriving it from the content
would let an injected link authorise itself, which is precisely what the gates
exist to catch. Adding a host is a reviewed one-line diff; each entry must be a
bare `https://` origin with no path or trailing slash, which
`scripts/validate-data.py` enforces.

## `packages.toml`

The preset software list and the bootloader options shown on the homepage. Copy
lives here so it can be corrected without touching either site's markup.
