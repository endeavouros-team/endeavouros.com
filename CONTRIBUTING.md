# Contributing

## Editing content

Most changes do not touch markup. `data/` holds the release, the mirrors, the
navigation, the package lists and the ARM images as TOML, and the site is built
from it — so adding a mirror or bumping a release needs no toolchain installed.
`data/README.md` is the field contract.

## Before you commit

- `make check` after any edit under `data/`. It validates the field contract and
  is fast.
- `make verify` before anything that changes build output. It runs the
  build-output gate, which asserts the built site contains no script we did not
  write and no outbound origin absent from `data/`. It fails the build rather
  than warning — that is deliberate, and it is the WordPress compromise
  mechanised.
- `make mirrors` and `make arm` after a release bump, to confirm every composed
  URL still resolves.

## Commit messages

Lowercase `area: summary` subject, imperative mood, wrapped at 76 columns, and a
body that explains *why* rather than restating the diff. `git log -3` is the
reference.

## Two things that fail silently

Both look like success and are expensive to miss.

- **`PUBLIC_INDEXABLE=true` is required for a production build.** Without it
  every page ships `noindex` and `/robots.txt` serves `Disallow: /`. The build
  succeeds and the site is invisible to search.
- **The CSP script hashes are restated in both files in `deploy/`.**
  `astro/scripts/check-build.mjs` cross-checks them against the build, so if the
  inline scripts change, all three move together or the build fails.
