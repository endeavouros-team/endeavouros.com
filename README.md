# EndeavourOS website

A statically generated replacement for endeavouros.com.

The current site runs WordPress and was affected by a compromise originating upstream in the
WordPress plugin ecosystem, not on our own infrastructure. A static site has no interpreter,
no admin panel and no writable webroot, so that entire class of attack disappears.

## Status

Phase 1, in progress: a vertical slice of the **homepage and download section**, built twice
so the team can compare real output before committing to a toolchain.

- `zola/` — Zola track. One static binary, `pacman -S zola`, no npm.
- `astro/` — Astro track. Better image pipeline and a typed data contract, at the cost of a
  Node toolchain.

Migration of the 106 existing news posts is deferred pending a scope decision.

## The shared data directory

`data/` is the single source of truth and is read by **both** tracks, so the comparison is
honest and the two sites cannot drift.

| File | Holds |
|---|---|
| `data/release.toml` | The current ISO: filename, date, checksum, signing key, torrent |
| `data/mirrors.toml` | The 26 download mirrors |
| `data/site.toml` | Navigation, taglines, footer links |
| `data/packages.toml` | Preset packages and bootloader options |

Mirror download URLs are **composed**, never stored. Each mirror carries a `base`; the ISO,
checksum and signature URLs are built from `base` + the ISO filename in `release.toml`.
Bumping a release therefore edits four lines in one file and regenerates all 78 mirror URLs.

See `data/README.md` for the field contract.

## Building

    make check       # validate data/ against the field contract
    make mirrors     # check every composed mirror URL is reachable

    make dev-zola    # zola serve on :1111
    make build-zola  # -> zola/public/

    make dev-astro   # astro dev on :4321
    make build-astro # -> astro/dist/

Zola is in the Arch `extra` repository: `sudo pacman -S zola`.

## Documentation

- `docs/bake-off.md` — the Zola vs Astro comparison, written from measured output
- `docs/release-bump.md` — how to publish a new ISO release
- `docs/seo-recovery.md` — reclaiming the search index from the injected spam
