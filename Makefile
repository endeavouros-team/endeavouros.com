# Zola's load_data() is sandboxed to the site root and cannot read ../data,
# so the shared data directory is mirrored into zola/ before every build.
# zola/data/ is gitignored: data/ stays the only committed copy.

.PHONY: sync check lint mirrors verify dev-zola build-zola dev-astro build-astro build serve clean

sync:
	@rm -rf zola/data && cp -r data zola/data
	@cp brand/favicon.svg zola/static/favicon.svg
	@cp brand/favicon.svg astro/public/favicon.svg
	@python3 scripts/gen-logo-partial.py

check:
	@python3 scripts/validate-data.py

# _tokens.scss is the only file allowed to name a colour. Everything else reads
# the semantic custom properties. Without this the stylesheet drifts into the
# unmaintainable fork the previous Zola site ended up with.
lint:
	@! grep -rnE "#[0-9a-fA-F]{3,8}\\b|rgba?\\(" zola/sass --include="*.scss" \
	   | grep -v "^zola/sass/_tokens.scss:" \
	   || (echo "  raw colour outside _tokens.scss (see above)"; exit 1)
	@echo "  css lint ok - no colour literals outside _tokens.scss"

mirrors:
	@python3 scripts/check-mirrors.py

dev-zola: sync
	@cd zola && zola serve --interface 0.0.0.0 --port 1111

build-zola: check lint sync
	@cd zola && zola build

dev-astro:
	@cd astro && npm run dev

build-astro: check
	@cd astro && npm run build

build: build-zola build-astro

# Assert neither build output contains a script we did not write or an outbound
# origin that is not in data/. The Astro track additionally cross-checks its CSP
# hashes in npm run build.
verify: build
	@python3 scripts/check-output.py zola/public
	@cd astro && node scripts/check-build.mjs

# Preview both builds on the LAN/tailnet for team review.
serve:
	@echo "  zola  -> http://$$(hostname):8811"
	@echo "  astro -> http://$$(hostname):8812"
	@(cd zola/public && python3 -m http.server 8811 --bind 0.0.0.0 >/dev/null 2>&1 &) ; \
	 (cd astro/dist  && python3 -m http.server 8812 --bind 0.0.0.0 >/dev/null 2>&1 &) ; \
	 echo "  serving; stop with: pkill -f 'http.server 881'"

clean:
	@rm -rf zola/public zola/data astro/dist astro/.astro
