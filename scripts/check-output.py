#!/usr/bin/env python3
"""Build-output integrity gate for a generated site directory.

The compromise showed up as injected markup in served pages, so assert that the
output contains no script we did not write and no outbound origin we did not put
there. Run against either track's output; the allowlist comes from data/, so
adding a mirror permits its origin automatically and cannot drift.

    scripts/check-output.py zola/public
    scripts/check-output.py astro/dist
"""

import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def load(name: str) -> dict:
    return tomllib.loads((DATA / name).read_text())


def allowed_origins() -> set[str]:
    mirrors, site = load("mirrors.toml"), load("site.toml")
    release, packages = load("release.toml")["current"], load("packages.toml")
    origins = {urlparse(m["base"]).scheme + "://" + urlparse(m["base"]).netloc for m in mirrors["mirrors"]}
    # Imported news bodies link out to hosts that are in no other data file.
    # This list is hand-maintained on purpose; see data/site.toml.
    origins.update(site.get("contentOrigins", []))
    for url in (
        [release["torrent"], site["url"]]
        + [n["url"] for n in site["nav"] if n.get("external")]
        + [l["url"] for c in site["footer"] for l in c["links"]]
        + [p["url"] for p in packages["packages"] if p.get("url")]
    ):
        u = urlparse(url)
        origins.add(f"{u.scheme}://{u.netloc}")
    return origins


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    out = Path(sys.argv[1])
    if not out.is_dir():
        print(f"  {out} does not exist — build first", file=sys.stderr)
        return 2

    allowed = allowed_origins()
    problems: list[str] = []
    scripts = inline = 0

    for f in sorted(out.rglob("*.html")):
        rel = f.relative_to(out)
        html = f.read_text(errors="replace")

        for attrs, body in re.findall(r"<script([^>]*)>(.*?)</script>", html, re.S | re.I):
            scripts += 1
            src = re.search(r'src=["\']?([^"\'\s>]+)', attrs, re.I)
            if src:
                if re.match(r"https?:", src.group(1), re.I):
                    problems.append(f"{rel}: external <script src={src.group(1)}>")
                # An external script must carry an SRI hash.
                elif "integrity=" not in attrs:
                    problems.append(f"{rel}: <script src={src.group(1)}> has no integrity attribute")
            elif "ld+json" not in attrs.lower():
                inline += 1
                problems.append(f"{rel}: unexpected inline <script> ({len(body.strip())} bytes)")

        for url in re.findall(r'(?:src|href|action|poster)=["\']?(https?://[^"\'\s>]+)', html, re.I):
            u = urlparse(url)
            origin = f"{u.scheme}://{u.netloc}"
            if origin not in allowed:
                problems.append(f"{rel}: unexpected external origin {origin}")

        for bad in ("eval(", "document.write(", "atob("):
            if bad in html:
                problems.append(f"{rel}: dynamic-code construct {bad}")

    if problems:
        print(f"\n  {len(problems)} problem(s) in {out}\n", file=sys.stderr)
        for p in dict.fromkeys(problems):
            print(f"    {p}", file=sys.stderr)
        print(file=sys.stderr)
        return 1

    print(f"  {out} ok — {scripts} script tags, {inline} inline, every external origin allowlisted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
