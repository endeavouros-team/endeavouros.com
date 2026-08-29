# EndeavourOS website

A statically generated replacement for endeavouros.com.

The current site runs WordPress and was affected by a compromise originating upstream in the
WordPress plugin ecosystem, not on our own infrastructure. A static site has no interpreter,
no admin panel and no writable webroot, so that entire class of attack disappears.

## Status

**Astro, for both the main site and the wiki.** The slice was built twice — once in Zola,
once in Astro — so the choice rested on real output rather than preference. `docs/bake-off.md`
records what that measured and why the decision went the way it did.

- `astro/` — the main site. Homepage and download section.
- `wiki/` — Discovery, on Starlight. A demo with three converted articles, not a migration.
- `zola/` — the Zola track, frozen at decision time. Kept until the team has read the
  comparison; it found two real bugs in the Astro track by disagreeing with it.

`docs/status.md` is the current picture: what is done, what is open, and what is next.
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
    make build-wiki  # -> wiki/dist/

    make verify      # build everything, then run both integrity gates
    make deploy-preview

Zola is in the Arch `extra` repository: `sudo pacman -S zola`.

## Documentation

- `docs/status.md` — where the work stands, what is open, what is next
- `docs/bake-off.md` — the Zola vs Astro comparison, written from measured output
- `docs/preview-hosting.md` — how the three previews are served, and what breaks them

Planned, and listed in `docs/status.md`:

- `docs/release-bump.md` — how to publish a new ISO release
- `docs/seo-recovery.md` — reclaiming the search index from the injected spam
