# Zola's load_data() is sandboxed to the site root and cannot read ../data,
# so the shared data directory is mirrored into zola/ before every build.
# zola/data/ is gitignored: data/ stays the only committed copy.

.PHONY: sync check mirrors dev-zola build-zola dev-astro build-astro clean

sync:
	@rm -rf zola/data && cp -r data zola/data

check:
	@python3 scripts/validate-data.py

mirrors:
	@python3 scripts/check-mirrors.py

dev-zola: sync
	@cd zola && zola serve --interface 0.0.0.0 --port 1111

build-zola: check sync
	@cd zola && zola build

dev-astro:
	@cd astro && npm run dev

build-astro: check
	@cd astro && npm run build

clean:
	@rm -rf zola/public zola/data astro/dist astro/.astro
