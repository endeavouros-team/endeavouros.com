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
from urllib.parse import urlparse

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

    if not cur.get("magnet", "").startswith("magnet:?xt=urn:btih:"):
        fail("release.toml", "magnet is not a btih magnet URI")
    if not cur.get("torrent", "").startswith("https://"):
        fail("release.toml", "torrent must be an https URL")

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

    if problems:
        print(f"\n  {len(problems)} problem(s) in data/\n", file=sys.stderr)
        for p in problems:
            print(f"    {p}", file=sys.stderr)
        print(file=sys.stderr)
        return 1

    n = len(mirrors.get("mirrors", []))
    print(f"  data ok — {n} mirrors, {n * 3} composed URLs, checksum and fingerprint well-formed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
