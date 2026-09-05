#!/usr/bin/env python3
"""Check that every composed ARM image URL is reachable.

The ARM equivalent of check-mirrors.py, and it exists for the same reason: the
URLs in data/arm-images.toml are composed from a base plus a tag plus a
filename, never stored, so nothing in the repository can tell you whether they
still describe what upstream publishes. Only a request can.

These point at GitHub release assets tagged `-latest`, which upstream reuses
across image rebuilds. That is what makes the data file stable, and it is also
what makes this check necessary: a device dropped upstream, or a tag renamed,
changes nothing here and would ship as a dead download link.

Non-200 is a WARNING by default, matching check-mirrors.py -- a transient
GitHub error must not block a build. Use --strict to exit non-zero.
"""

import argparse
import concurrent.futures
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
UA = "Mozilla/5.0 (X11; Linux x86_64) endeavouros-website-arm-check"


def head(url: str, timeout: int) -> tuple[str, str, int | None]:
    """HEAD, falling back to a ranged GET.

    GitHub redirects release assets to object storage, and the signature on
    that redirect is issued for the method it was requested with, so a HEAD can
    come back 403 for a file that downloads perfectly.
    """
    result: tuple[str, str, int | None] = ("warn", "unknown", None)
    for method, headers in (("HEAD", {}), ("GET", {"Range": "bytes=0-0"})):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, **headers})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                r.read(1)
                length = r.headers.get("Content-Range") or r.headers.get("Content-Length")
                size = None
                if length and "/" in str(length):
                    size = int(str(length).rsplit("/", 1)[1])
                elif str(length or "").isdigit():
                    size = int(length)
                return ("ok", str(r.status), size)
        except urllib.error.HTTPError as e:
            result = ("warn", str(e.code), None)
        except Exception as e:  # DNS, TLS, timeout, connection reset
            result = ("warn", type(e).__name__, None)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--strict", action="store_true", help="exit non-zero on any failure")
    args = ap.parse_args()

    data = tomllib.loads((DATA / "arm-images.toml").read_text())
    base, suffix = data["base"], data["sha512Suffix"]

    targets = []
    for dev in data["devices"]:
        img = f"{base}/{dev['tag']}/{dev['image']}"
        targets.append((dev["name"], "image", img))
        targets.append((dev["name"], "sha512", img + suffix))

    problems = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(head, url, args.timeout): t for t, url in
                   ((t, t[2]) for t in targets)}
        results = []
        for fut in concurrent.futures.as_completed(futures):
            name, kind, url = futures[fut]
            state, code, size = fut.result()
            results.append((name, kind, state, code, size, url))

    for name, kind, state, code, size, url in sorted(results):
        if state == "ok":
            shown = f"{size / 1024 ** 3:.2f} GiB" if size and kind == "image" else ""
            print(f"  ok    {name:38} {kind:7} {code:4} {shown}")
        else:
            problems += 1
            print(f"  WARN  {name:38} {kind:7} {code}\n        {url}", file=sys.stderr)

    devices = len(data["devices"])
    if problems:
        print(f"\n  {problems} of {len(targets)} ARM URLs did not respond", file=sys.stderr)
        return 1 if args.strict else 0

    print(f"\n  arm ok — {devices} devices, {len(targets)} composed URLs all reachable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
