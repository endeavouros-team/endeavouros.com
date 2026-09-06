# Contributing

A change gets in through a pull request against `main`. CI
(`.github/workflows/check.yml`) runs on the pull request, and a maintainer
merges it. Merging publishes nothing: releases are cut by pushing a `v*` tag,
which the README covers.

## Editing content

Most changes do not touch markup. `data/` holds the release, the mirrors, the
navigation, the package lists and the ARM images as TOML, and the site is built
from it — so adding a mirror or bumping a release needs no toolchain installed.
`data/README.md` is the field contract.

## Before you commit

- `make check` after any edit under `data/`. It validates the field contract and
  is fast.
- `make verify` before anything that changes build output. It builds the site,
  then runs the build-output gate over `astro/dist/`. The gate fails on an
  inline script that is not one of ours and on an outbound link to a host that
  is not listed in `contentOrigins` in `data/site.toml`. Failing rather than
  warning is deliberate: it is the check that would have caught the WordPress
  compromise.
- `make links` after `make verify`. It checks that every internal link in the
  build resolves, which is the one error that is invisible in review. CI runs
  it too.
- `make mirrors` and `make arm` after a release bump, to confirm every composed
  URL still resolves.

## What CI does

Every push to `main` and every pull request runs `.github/workflows/check.yml`:
the data validator, the lockfile audit, the build-output gate and the internal
link check. It publishes nothing.

Pushing a `v*` tag runs `.github/workflows/build.yml` instead. It runs the same
steps, then builds with `PUBLIC_INDEXABLE=true`, asserts the result is actually
indexable, and attaches a tarball to a GitHub Release. That tarball is what gets
deployed — see the README. Ordinary commits never produce a release.

## Commit messages

Lowercase `area: summary` subject, imperative mood, wrapped at 76 columns, and a
body that explains *why* rather than restating the diff. `git log -3` is the
reference.

## Two things that fail silently

Both look like success and are expensive to miss.

- **`PUBLIC_INDEXABLE=true` is required for a production build.** Without it
  every page ships `noindex` and `/robots.txt` serves `Disallow: /`. The build
  succeeds and the site is invisible to search.
- **The CSP script hashes are restated in `deploy/nginx-production.conf` and
  `deploy/preview/nginx-preview.conf`.** `astro/scripts/check-build.mjs`
  cross-checks both against the build, so if the inline scripts change, all
  three move together or the build fails. It checks in both directions and
  prints one line per problem, naming the file and the hash: `CSP is missing
  <hash>` means a config does not allow a script the build ships, and `CSP has
  a stale <hash>` means a hash is left over from a script we no longer ship.
  When it fires, run `npm run check:build -- --update` to re-record the
  expected set, then copy the hashes it names into both configs.
