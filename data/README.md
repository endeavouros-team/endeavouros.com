# The shared data directory

This is the single source of truth for the site. The Astro content layer reads
these files directly from `../data`, so there is no second copy to drift.

Nothing here is markup, so editing a file in this directory needs no toolchain
installed. That is the point of the split: a mirror maintainer can add a mirror
without building the site.

Run `make check` after any edit. It checks every file here against the field
contract below, and it is fast. CI runs it on every push and every pull request
as well, so an edit made without the toolchain gets the same answer without
waiting on anyone.

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
| `signing.name` | Key owner, as shown on the download page |
| `signing.email` | Key owner's address, must parse as an email address |
| `signing.fingerprint` | 40 hex characters in 10 space-separated groups of 4 |
| `signing.shortKey` | 8 uppercase hex characters, must be the tail of the fingerprint |
| `signing.keyserver` | Hostname the key can be fetched from, e.g. `keyserver.ubuntu.com` |
| `requirements.diskGb` | Positive integer, free disk space |
| `requirements.ramGb` | Positive integer |
| `requirements.cpu` | One line, e.g. `64-bit dual-core Intel or AMD processor` |
| `requirements.note` | One sentence of caveat, shown under the table |

Both `[current.signing]` and `[current.requirements]` are whole tables: every
field above is required, and a missing one fails the build. `make check` covers
most of them and the Astro schema in `astro/src/content.config.ts` covers the
rest, so run a build as well as `make check` if you change either table.

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

| Field | Contract |
|---|---|
| `name` / `tagline` / `subtitle` / `description` | Required, non-empty |
| `url` | The canonical site origin, https |
| `nav[].name` | Required, the label shown |
| `nav[].url` | Required. Root-relative (`/download/`) unless `external` |
| `nav[].external` | Optional, default `false`. `true` requires an https URL |
| `nav[].cta` | Optional, default `false`. Renders as the highlighted button; only Download uses it |
| `footer[].heading` | Required, the column heading |
| `footer[].links[].name` / `.url` | Required. One `[[footer.links]]` stanza per link, at least one per column |

Nav and footer render in file order, so moving a stanza moves the item.

One link to an `https://forum.` host is required somewhere in nav or footer:
the discuss-this link on every news post is resolved from it by origin, and
`make check` fails if none is left.

`contentOrigins` is the allowlist of outbound hosts that imported news bodies may
link to. The build-output gate reads it, and nothing else grants an origin to
post content. It is hand-maintained on purpose: deriving it from the content
would let an injected link authorise itself, which is precisely what the gate
exists to catch. Adding a host is a reviewed one-line diff; each entry must be a
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
lives here so it can be corrected without touching the site's markup.

| Field | Contract |
|---|---|
| `packages[].name` | Required, the package as users would name it |
| `packages[].desc` | Required, one sentence |
| `packages[].url` | Optional. Upstream project page; must be a full URL |
| `bootloaders[].name` | Required |
| `bootloaders[].desc` | Required, one sentence on when to pick it |

One `[[packages]]` stanza per package and one `[[bootloaders]]` stanza per
option, both rendered in file order. `make check` requires at least one package
and at least two bootloaders — a single option is not a choice, and the homepage
presents it as one.
