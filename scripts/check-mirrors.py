#!/usr/bin/env python3
"""Check that every composed mirror URL is reachable.

Composes the three URLs for each mirror exactly as the templates do, then issues
a HEAD request for each. This is what catches a mirror that has not yet synced a
new release, which is the most common breakage after a version bump.

Non-200 is reported as a WARNING, not an error: some mirrors reject scripted
requests (403/400) while serving browsers fine, and a mirror being briefly down
must not block a site build. Use --strict to exit non-zero on any failure.
"""

import argparse
import concurrent.futures
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
UA = "Mozilla/5.0 (X11; Linux x86_64) endeavouros-website-mirror-check"


def head(url: str, timeout: int) -> tuple[str, str]:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return ("ok", str(r.status))
    except urllib.error.HTTPError as e:
        return ("warn", str(e.code))
    except Exception as e:  # DNS, TLS, timeout, connection reset
        return ("warn", type(e).__name__)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--strict", action="store_true", help="exit non-zero on any unreachable URL")
    ap.add_argument("--iso-only", action="store_true", help="skip checksum and signature URLs")
    args = ap.parse_args()

    rel = tomllib.loads((DATA / "release.toml").read_text())["current"]
    mirrors = tomllib.loads((DATA / "mirrors.toml").read_text())["mirrors"]
    iso, sha_sfx, sig_sfx = rel["iso"], rel["sha512Suffix"], rel["sigSuffix"]

    jobs = []
    for m in mirrors:
        if not m.get("active", True):
            continue
        base = m["base"]
        kinds = [("iso", f"{base}/{iso}")]
        if not args.iso_only:
            kinds += [("sha512", f"{base}/{iso}{sha_sfx}"), ("sig", f"{base}/{iso}{sig_sfx}")]
        for kind, url in kinds:
            jobs.append((m, kind, url))

    print(f"  checking {len(jobs)} URLs for {iso}\n")
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        futures = {ex.submit(head, url, args.timeout): (m, kind, url) for m, kind, url in jobs}
        for fut in concurrent.futures.as_completed(futures):
            m, kind, url = futures[fut]
            results[(m["id"], kind)] = (fut.result(), url)

    bad = 0
    for m in mirrors:
        if not m.get("active", True):
            continue
        row = []
        for kind in ("iso", "sha512", "sig"):
            got = results.get((m["id"], kind))
            if got is None:
                continue
            (status, detail), _ = got
            if status != "ok":
                bad += 1
                row.append(f"{kind}={detail}")
        flag = "warn" if row else "ok  "
        detail = ("  " + " ".join(row)) if row else ""
        print(f"  {flag}  {m['countryCode']}  {m['name']:<26}{m['base'].split('/')[2]}{detail}")

    print(f"\n  {len(jobs) - bad}/{len(jobs)} reachable")
    if bad:
        print("  note: some mirrors reject scripted requests but serve browsers fine — "
              "check any failure by hand before removing a mirror")
    return 1 if (bad and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
