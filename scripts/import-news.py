#!/usr/bin/env python3
"""Import endeavouros.com news posts into the Astro site.

Scope, set by the project lead: the Mercury release announcement and everything
newer. That is the seven posts in SLUGS below. The other 99 posts and the 19
translated ones stay on WordPress for now; widening the scope means adding
slugs here and re-running.

The WordPress export named in docs/status.md is not needed -- the REST API is
open and gives clean structured JSON, which is what wiki/scripts/convert-wp.py
already consumes for Discovery. The Gutenberg handling is shared with it, in
scripts/wp_common.py.

Media is downloaded rather than hotlinked. Hotlinking would leave the new site
depending on the compromised host, and the build-output gates would reject
i0.wp.com as an origin that is not in data/.

Re-running is safe: output is deterministic, and alt text authored by hand
after import is read back out of the existing Markdown and preserved, since
every alt attribute in the WordPress source is empty.

    scripts/import-news.py --all
    scripts/import-news.py titan-nova-is-available
"""

import html
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wp_common as wp  # noqa: E402

API = "https://endeavouros.com/wp-json/wp/v2"
FIELDS = "slug,title,content,date,author,featured_media,_links"
ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "astro/src/content/news"
ASSETS = ROOT / "astro/src/assets/news"

# Mercury onward, oldest first. Dates are the WordPress publication dates.
SLUGS = [
    "our-new-iso-release-is-here-meet-mercury",                          # 2025-02-10
    "mercury-neo-with-linux-6-13-7-and-arch-mirror-ranking-bug-fix",     # 2025-03-23
    "the-long-wait-is-over-ganymede-has-arrived",                        # 2025-11-29
    "ganymede-neo-is-out-with-core-updates-and-upstream-nvidia-changes",  # 2026-01-15
    "whats-new-in-endeavouros-titan-release",                            # 2026-03-12
    "titan-neo-with-some-fixes-and-upstream-updates-is-available",       # 2026-05-01
    "titan-nova-is-available",                                           # 2026-08-28
]


def unjetpack(url: str) -> str:
    """i0.wp.com/endeavouros.com/wp-content/...?resize=650%2C366&ssl=1 is a CDN
    wrapper around a resized copy. Recover the original so the site ships the
    full-resolution file and lets Astro do the resizing."""
    url = html.unescape(url)
    u = urllib.parse.urlsplit(url)
    if re.fullmatch(r"i\d\.wp\.com", u.netloc):
        # The wrapper's path is /<original-host>/wp-content/uploads/...
        return "https://" + u.path.lstrip("/")
    return urllib.parse.urlunsplit((u.scheme, u.netloc, u.path, "", ""))


def local_asset(url: str) -> tuple[Path, str]:
    """Where a media file lands, and how the Markdown refers to it.

    Uploads are already laid out as /wp-content/uploads/YYYY/MM/name.ext, so the
    year comes from the source path rather than the post date -- an image reused
    by a later post keeps one home and one copy.
    """
    path = urllib.parse.urlsplit(url).path
    name = Path(path).name
    m = re.search(r"/uploads/(\d{4})/", path)
    year = m.group(1) if m else "misc"
    return ASSETS / year / name, f"../../assets/news/{year}/{name}"


def download(url: str) -> str:
    dest, rel = local_asset(url)
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "eos-site-import"})
        with urllib.request.urlopen(req, timeout=120) as r:
            dest.write_bytes(r.read())
        print(f"      fetched {rel}  ({dest.stat().st_size // 1024} KiB)")
    return rel


def existing_alts(path: Path) -> tuple[str, dict[str, str]]:
    """Alt text authored by hand after a previous import. Every alt in the
    WordPress source is empty, so anything non-empty here is the team's work
    and must survive a re-run."""
    if not path.exists():
        return "", {}
    text = path.read_text()
    hero = re.search(r'^heroAlt:\s*"(.*)"\s*$', text, re.M)
    body = {m.group(2): m.group(1) for m in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", text) if m.group(1)}
    return (hero.group(1) if hero else ""), body


def yaml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def rewrite_links(body: str, slugs: set[str]) -> tuple[str, int]:
    """Keep links that mean "somewhere on this site" on this site.

    Three cases, all faithful rather than editorial:
      - a post we now host                -> /news/<slug>/
      - the old homepage                  -> /
      - the old homepage's #Download      -> /download/, which is where that
        section now lives; the anchor no longer exists to link to.

    Everything else stays absolute. Links to sections not rebuilt yet keep
    pointing at the current site, which is allowed: endeavouros.com is already
    an origin in data/site.toml.
    """
    n = 0

    def sub(m):
        nonlocal n
        slug, frag = m.group("slug"), m.group("frag")
        if slug is not None:
            # A news post we do not host stays on the current site.
            if slug not in slugs:
                return m.group(0)
            target = f"/news/{slug}/"
        else:
            target = "/download/" if frag == "#Download" else "/"
        n += 1
        return f"]({target})"

    pattern = (
        r"\]\(https?://endeavouros\.com/"
        r"(?:news/(?P<slug>[a-z0-9-]+)/?"
        r"|(?P<frag>#[A-Za-z]+)?)"
        r"\)"
    )
    return re.sub(pattern, sub, body), n


def import_post(slug: str, slugs: set[str]) -> None:
    post = fetch(slug)
    title = wp.plain_title(post)
    out_path = CONTENT / f"{slug}.md"
    hero_alt, body_alts = existing_alts(out_path)

    def on_image(src, alt, stats):
        src = unjetpack(src)
        stats["img"] += 1
        rel = download(src)
        return f"![{alt or body_alts.get(rel, '')}]({rel})"

    body, st = wp.convert(post["content"]["rendered"], on_image=on_image)
    body = wp.strip_repeated_title(body, title)
    body, relinked = rewrite_links(body, slugs)
    desc = wp.synth_description(body, title)

    author = post.get("_embedded", {}).get("author", [{}])[0].get("name", "")
    if not author:
        raise SystemExit(f"  {slug}: no author returned; refusing to write an empty byline")

    hero_rel = ""
    if post.get("featured_media"):
        media = wp.get_json(f"{API}/media/{post['featured_media']}?_fields=source_url,alt_text")
        hero_rel = download(unjetpack(media["source_url"]))
        hero_alt = hero_alt or media.get("alt_text", "")

    fm = [
        "---",
        f"title: {yaml_str(title)}",
        f"description: {yaml_str(desc)}",
        f"date: {post['date'][:10]}",
        f"author: {yaml_str(author)}",
        f"hero: {yaml_str(hero_rel)}",
        f"heroAlt: {yaml_str(hero_alt)}",
        "---",
    ]
    CONTENT.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(fm) + "\n\n" + body)
    print(
        f"  {slug}.md  {post['date'][:10]}  {author}  "
        f"{st['img']} images, {relinked} links kept on-site"
        + ("" if hero_alt else "   [heroAlt empty - needs authoring]")
    )


def fetch(slug: str) -> dict:
    url = f"{API}/posts?slug={urllib.parse.quote(slug)}&_fields={FIELDS}&_embed=author"
    posts = wp.get_json(url)
    if not posts:
        raise SystemExit(f"  no post found for slug {slug!r}")
    return posts[0]


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    slugs = SLUGS if args == ["--all"] else args
    known = set(SLUGS)
    for slug in slugs:
        import_post(slug, known)
    return 0


if __name__ == "__main__":
    sys.exit(main())
