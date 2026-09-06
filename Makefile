# The main site is Astro. `data/` holds everything that is not markup and is
# read straight from ../data by the content layer, so there is nothing to copy
# into place before a build.

.PHONY: check links mirrors arm spam-check dev-astro build-astro build verify serve deploy-preview clean

check:
	@python3 scripts/validate-data.py

# A link to a page that does not exist is invisible in review and only shows up
# when someone clicks. Needs a build in astro/dist to check against.
links:
	@python3 scripts/check-links.py

mirrors:
	@python3 scripts/check-mirrors.py

# The ARM images are GitHub release assets tagged `-latest`, so data/arm-images.toml
# stays correct across rebuilds and nothing in the repo notices a device dropped
# or a tag renamed upstream. Only a request does.
arm:
	@python3 scripts/check-arm.py

# Probe the live production site for a recurrence of the referrer-cloak hijack.
# Needs no access to that host, which is why it is ours to run.
spam-check:
	@python3 scripts/check-spam.py

dev-astro:
	@cd astro && npm run dev

build-astro: check
	@cd astro && npm run build

build: build-astro

# Assert the build output contains no script we did not write and no outbound
# origin that is not in data/. npm run build already runs this; calling it again
# here is what makes `make verify` meaningful on its own.
verify: build
	@cd astro && node scripts/check-build.mjs

# Preview the build on the LAN/tailnet for team review.
serve:
	@test -d astro/dist || { echo "  no astro/dist — run make build first"; exit 1; }
	@echo "  astro -> http://$$(hostname):8812"
	@(cd astro/dist && python3 -m http.server 8812 --bind 0.0.0.0 >/dev/null 2>&1 &) ; \
	 echo "  serving; stop with: pkill -f 'http.server 8812'"

# Publish to the always-on preview host.
deploy-preview:
	@scripts/deploy-preview.sh

clean:
	@rm -rf astro/dist astro/.astro
