#!/usr/bin/env python3
"""Validate data/ against the field contract.

Templates are forgiving: a missing key renders an empty string and the build
succeeds, so a typo can ship a download page with href="" on an ISO link, or a
checksum link that points nowhere while the ISO link still works. For a page
whose whole job is distributing verifiable installation media, that is the wrong
failure mode. This turns it into a build failure.

Exits non-zero on the first problem found, printing every problem.
"""

import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import quote, urlparse

DATA = Path(__file__).resolve().parent.parent / "data"
CONTINENTS = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]

problems: list[str] = []


def fail(where: str, msg: str) -> None:
    problems.append(f"{where}: {msg}")


def load(name: str) -> dict:
    try:
        return tomllib.loads((DATA / name).read_text())
    except FileNotFoundError:
        fail(name, "missing")
    except tomllib.TOMLDecodeError as exc:
        fail(name, f"not valid TOML — {exc}")
    return {}


def check_release(doc: dict) -> str:
    cur = doc.get("current")
    if not cur:
        fail("release.toml", "no [current] table")
        return ""

    for key in ("codename", "date", "iso", "sha512", "sizeBytes", "magnet", "torrent"):
        if key not in cur:
            fail("release.toml", f"[current] missing {key!r}")

    iso = cur.get("iso", "")
    if iso and not re.fullmatch(r"EndeavourOS_[A-Za-z][A-Za-z-]*-\d{4}\.\d{2}\.\d{2}\.iso", iso):
        fail("release.toml", f"iso {iso!r} does not match the release naming convention")

    sha = cur.get("sha512", "")
    if not re.fullmatch(r"[0-9a-f]{128}", sha):
        fail("release.toml", f"sha512 must be 128 lowercase hex characters, got {len(sha)}")

    size = cur.get("sizeBytes")
    if not isinstance(size, int) or size <= 0:
        fail("release.toml", "sizeBytes must be a positive integer")

    magnet = cur.get("magnet", "")
    torrent = cur.get("torrent", "")
    if not magnet.startswith("magnet:?xt=urn:btih:"):
        fail("release.toml", "magnet is not a btih magnet URI")
    if not torrent.startswith("https://"):
        fail("release.toml", "torrent must be an https URL")

    # Both embed the ISO filename, and they sit below [current] rather than in
    # it — they are the two values a release bump forgets. A magnet may
    # percent-encode its display name, so accept either spelling.
    if iso and magnet and f"dn={iso}" not in magnet and f"dn={quote(iso)}" not in magnet:
        fail("release.toml", f"magnet does not carry dn={iso} — it still names an older ISO")
    if iso and torrent and not torrent.endswith(f"{iso}.torrent"):
        fail("release.toml", f"torrent does not end in {iso}.torrent — it still names an older ISO")

    for key in ("sha512Suffix", "sigSuffix"):
        if not cur.get(key, "").startswith("."):
            fail("release.toml", f"{key} should start with a dot")

    sign = cur.get("signing", {})
    fpr = sign.get("fingerprint", "")
    # Rendered verbatim for users to check a key against: 10 groups of 4 hex.
    if not re.fullmatch(r"([0-9A-F]{4} ){9}[0-9A-F]{4}", fpr):
        fail("release.toml", "signing.fingerprint must be 40 hex chars in 10 space-separated groups")
    short = sign.get("shortKey", "")
    if short and not fpr.replace(" ", "").endswith(short):
        fail("release.toml", f"signing.shortKey {short!r} is not the tail of the fingerprint")

    req = cur.get("requirements", {})
    for key in ("diskGb", "ramGb"):
        if not isinstance(req.get(key), int) or req[key] <= 0:
            fail("release.toml", f"requirements.{key} must be a positive integer")

    return iso


def check_mirrors(doc: dict) -> None:
    mirrors = doc.get("mirrors")
    if not mirrors:
        fail("mirrors.toml", "no [[mirrors]] entries")
        return

    seen_ids: dict[str, int] = {}
    seen_base: dict[str, str] = {}

    for i, m in enumerate(mirrors):
        where = f"mirrors.toml[{i}] {m.get('name', '?')!r}"

        for key in ("id", "continent", "country", "countryCode", "name", "base"):
            if not m.get(key):
                fail(where, f"missing {key!r}")

        mid = m.get("id", "")
        if mid and not re.fullmatch(r"[a-z0-9-]+", mid):
            fail(where, f"id {mid!r} must be lowercase alphanumeric and hyphens")
        if mid in seen_ids:
            fail(where, f"duplicate id {mid!r}, first seen at index {seen_ids[mid]}")
        seen_ids[mid] = i

        if m.get("continent") not in CONTINENTS:
            fail(where, f"continent {m.get('continent')!r} not one of {CONTINENTS}")

        cc = m.get("countryCode", "")
        if not re.fullmatch(r"[A-Z]{2}", cc):
            fail(where, f"countryCode {cc!r} must be two uppercase letters")

        base = m.get("base", "")
        if base:
            if not base.startswith("https://"):
                fail(where, f"base must be https, got {base!r}")
            if base.endswith("/"):
                fail(where, "base must not end in a slash — URLs are composed")
            if base in seen_base:
                fail(where, f"duplicate base, already used by {seen_base[base]!r}")
            seen_base[base] = m.get("name", "?")


def check_site(doc: dict) -> None:
    for key in ("name", "tagline", "subtitle", "description", "url"):
        if not doc.get(key):
            fail("site.toml", f"missing {key!r}")
    for i, origin in enumerate(doc.get("contentOrigins", [])):
        where = f"site.toml contentOrigins[{i}]"
        if not origin.startswith("https://"):
            fail(where, f"{origin!r} must be an https origin")
        if urlparse(origin).path or origin.rstrip("/") != origin:
            fail(where, f"{origin!r} must be a bare origin, no path or trailing slash")
    nav = doc.get("nav", [])
    if not nav:
        fail("site.toml", "no [[nav]] entries")
    for i, n in enumerate(nav):
        where = f"site.toml nav[{i}] {n.get('name', '?')!r}"
        if not n.get("name") or not n.get("url"):
            fail(where, "needs both name and url")
        url = n.get("url", "")
        if n.get("external") and not url.startswith("https://"):
            fail(where, "external links must be https")
        if not n.get("external") and not url.startswith("/"):
            fail(where, "internal links must be root-relative")

    # The footer is half the outbound links on every page, and check-build.mjs
    # allowlists every origin it names — a malformed column is a broken column
    # sitewide, not on one page.
    footer = doc.get("footer", [])
    if not footer:
        fail("site.toml", "no [[footer]] columns")
    for i, col in enumerate(footer):
        where = f"site.toml footer[{i}] {col.get('heading', '?')!r}"
        if not col.get("heading"):
            fail(where, "missing 'heading'")
        links = col.get("links", [])
        if not links:
            fail(where, "no [[footer.links]] entries")
        for j, link in enumerate(links):
            lwhere = f"{where} links[{j}] {link.get('name', '?')!r}"
            if not link.get("name"):
                fail(lwhere, "missing 'name'")
            url = link.get("url", "")
            if not url:
                fail(lwhere, "missing 'url'")
            elif not url.startswith("https://"):
                # content.config.ts parses these with z.string().url(), which a
                # root-relative path fails outright. https rather than any URL
                # because nothing the site links to is served over plain http.
                fail(lwhere, f"url must be https, got {url!r}")

    # lib/site.ts forumUrl() resolves the discuss-this link on every news post by
    # origin rather than by link text, and throws when it finds nothing. Catch
    # that here, where the message can say which files are involved.
    urls = [n.get("url", "") for n in nav]
    urls += [l.get("url", "") for c in footer for l in c.get("links", [])]
    if not any(u.startswith("https://forum.") for u in urls):
        fail("site.toml", "no https://forum. link in nav or footer — news post footers need one")


def check_arm(doc: dict) -> int:
    """The ARM images, held to the same composition rule as the mirrors.

    Returns the device count for the summary line. Nothing here stores a full
    URL: a missing `tag` or a filename that is not an image composes a download
    link that 404s, and the page still builds.
    """
    base = doc.get("base", "")
    if not base:
        fail("arm-images.toml", "missing 'base'")
    else:
        if not base.startswith("https://"):
            fail("arm-images.toml", f"base must be https, got {base!r}")
        if base.endswith("/"):
            fail("arm-images.toml", "base must not end in a slash — URLs are composed")

    if not doc.get("sha512Suffix", "").startswith("."):
        fail("arm-images.toml", "sha512Suffix should start with a dot")

    devices = doc.get("devices", [])
    if not devices:
        fail("arm-images.toml", "no [[devices]] entries")

    seen_ids: dict[str, int] = {}
    for i, d in enumerate(devices):
        where = f"arm-images.toml[{i}] {d.get('name', '?')!r}"

        for key in ("id", "name", "tag", "image"):
            if not d.get(key):
                fail(where, f"missing {key!r}")

        did = d.get("id", "")
        if did and not re.fullmatch(r"[a-z0-9-]+", did):
            fail(where, f"id {did!r} must be lowercase alphanumeric and hyphens")
        if did in seen_ids:
            fail(where, f"duplicate id {did!r}, first seen at index {seen_ids[did]}")
        seen_ids[did] = i

        image = d.get("image", "")
        if image and not image.endswith(".img.xz"):
            fail(where, f"image {image!r} must be an .img.xz filename")

        if "server" in d and not isinstance(d["server"], bool):
            fail(where, f"server must be true or false, got {d['server']!r}")

    return len(devices)


def check_packages(doc: dict) -> None:
    if len(doc.get("packages", [])) == 0:
        fail("packages.toml", "no [[packages]] entries")
    for i, p in enumerate(doc.get("packages", [])):
        if not p.get("name") or not p.get("desc"):
            fail(f"packages.toml[{i}]", "needs both name and desc")
    if len(doc.get("bootloaders", [])) < 2:
        fail("packages.toml", "expected at least two bootloader options")


def main() -> int:
    release = load("release.toml")
    mirrors = load("mirrors.toml")
    check_release(release)
    check_mirrors(mirrors)
    check_site(load("site.toml"))
    check_packages(load("packages.toml"))
    devices = check_arm(load("arm-images.toml"))

    if problems:
        print(f"\n  {len(problems)} problem(s) in data/\n", file=sys.stderr)
        for p in problems:
            print(f"    {p}", file=sys.stderr)
        print(file=sys.stderr)
        return 1

    n = len(mirrors.get("mirrors", []))
    print(
        f"  data ok — {n} mirrors, {n * 3} composed URLs, {devices} ARM devices, "
        "checksum and fingerprint well-formed"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
