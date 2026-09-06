#!/usr/bin/env python3
"""Detect an SEO-poisoning hijack of the live site from outside.

The site was hijacked twice — 2026-08-10, and again on 2026-08-20 — by a
referrer-triggered cloak: a direct visit served EndeavourOS, while a click from
Google served a Turkish gambling site. Both times it was users who noticed. This
script is the thing that notices next time, in minutes rather than days.

It needs no access to the production host, which is the point: nobody on the
website rebuild has any. It fetches public URLs the way an attacker's cloak
expects to be fetched, and compares what comes back.

Two independent signals, because either alone can be evaded:

  cloaking  the same URL fetched as a plain browser, as Googlebot, and as a
            click arriving from Google should return the same page. A cloak's
            whole mechanism is that it does not.
  keywords  gambling vocabulary appearing anywhere in a response.

A cloak that avoids our keyword list still trips the diff; a lazy injection that
serves everyone the same spam still trips the keywords.

Caveat worth stating, because it bounds what a clean run proves: Google verifies
Googlebot by IP, not by user-agent string. A cloak keyed to real Googlebot
address ranges will not fire for this script, and no external prober can make it.
Only Search Console's URL Inspection ("View Crawled Page") shows what Google
actually received.
"""

import argparse
import concurrent.futures
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SITE = "https://endeavouros.com"
PATHS = ("/", "/news/", "/download/")

BROWSER = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
MOBILE = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1"
FROM_GOOGLE = "https://www.google.com/search?q=endeavouros"

# The cloak fired on the Google referrer specifically — the forum reports Bing,
# DuckDuckGo, Ecosia and Brave were all unaffected — so every persona but the
# baseline carries either Googlebot's identity or a Google referrer.
PERSONAS = (
    ("direct", BROWSER, None),
    ("googlebot", GOOGLEBOT, None),
    ("from-google", BROWSER, FROM_GOOGLE),
    ("googlebot+ref", GOOGLEBOT, FROM_GOOGLE),
    ("mobile+ref", MOBILE, FROM_GOOGLE),
)

# Word-boundary matching is not fussiness, it is the difference between a canary
# and noise. A bare "bet" substring scan flags the real post slugs
# "the-new-beta-is-available" and "a-dynamic-force-between-individuals"; a
# checker that cries wolf gets muted, and a muted checker is worse than none.
# Every term here is one that cannot plausibly occur on a Linux distribution
# site, which is why "slot" and "bet" are absent: "PCI slot" and "beta" are
# ordinary words here.
# Two language families, because the operators are not the same people. The
# Turkish set is from the August 2026 hijacks; the Indonesian set was added on
# 2026-09-05, when the site came back cloaked to a "situs toto / slot gacor"
# page and this check reported "no gambling vocabulary" while the cloaking
# check was flagging every path. The list is the signal that goes stale, which
# is exactly why there are two independent signals.
#
# Single words that plausibly occur in legitimate Linux copy are deliberately
# absent: "slot" alone matches a PCIe or memory slot, so the Indonesian entries
# are phrases. "gacor", "togel" and "maxwin" have no such collision.
TERMS = (
    # Turkish — the 2026-08-10 and 2026-08-20 hijacks
    "pusulabet", "bahis", "iddaa", "kumarhane", "kumar", "bettilt",
    "casino", "casino sitesi", "deneme bonusu", "bonus veren",
    "güvenilir bahis", "slot oyunları", "canlı bahis", "betting site",
    # Indonesian — the 2026-09-05 hijack
    "gacor", "togel", "maxwin", "judi", "judi online",
    "situs toto", "situs slot", "slot gacor", "slot online",
    "bandar togel", "jackpot",
)
TERM_RE = re.compile(r"\b(" + "|".join(re.escape(t) for t in TERMS) + r")\b", re.I)

# The five headers the build expects and production does not send. Tracked here
# so this doubles as the regression test when the production config lands.
HEADERS = (
    "content-security-policy",
    "strict-transport-security",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
)

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
HOST_RE = re.compile(r"https?://([a-zA-Z0-9.-]+)")


def fetch(url: str, ua: str, referer: str | None, timeout: int) -> dict:
    """GET a URL as one persona, following redirects, returning what came back."""
    headers = {"User-Agent": ua, "Accept": "text/html,application/xhtml+xml"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(2_000_000).decode("utf-8", "replace")
            return {"ok": True, "status": r.status, "final": r.geturl(),
                    "headers": {k.lower(): v for k, v in r.headers.items()}, "body": body}
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "final": url, "headers": {}, "body": ""}
    except Exception as e:
        return {"ok": False, "status": type(e).__name__, "final": url, "headers": {}, "body": ""}


def fingerprint(res: dict) -> dict:
    """Reduce a response to what a cloak necessarily changes.

    Deliberately not a byte comparison: WordPress varies nonces and inline
    timestamps between requests, so identical pages differ byte-for-byte and a
    strict diff would report a hijack every run. A cloak, by contrast, swaps the
    destination host, the title, or the set of sites the page links to — none of
    which drift on their own.
    """
    body = res["body"]
    title = TITLE_RE.search(body)
    return {
        "host": urllib.parse.urlsplit(res["final"]).netloc,
        "title": (title.group(1).strip()[:80] if title else ""),
        "hosts": frozenset(HOST_RE.findall(body)),
        # Bucketed, so ordinary page-to-page variance does not register but a
        # wholesale content swap does.
        "size": len(body) // 4096,
    }


def compare(base: dict, other: dict) -> list[str]:
    """Name the components that differ, or return empty if the pages agree."""
    out = []
    if base["host"] != other["host"]:
        out.append(f"redirected off-site to {other['host']!r}")
    if base["title"] != other["title"]:
        out.append(f"title {other['title']!r} != {base['title']!r}")
    new_hosts = other["hosts"] - base["hosts"]
    if new_hosts:
        out.append("extra hosts: " + ", ".join(sorted(new_hosts)[:5]))
    if base["size"] != other["size"]:
        out.append(f"size bucket {other['size']} != {base['size']}")
    return out


def count_sitemap(url: str, ua: str, timeout: int) -> tuple[int, str]:
    """Total the URLs a sitemap advertises, descending one level into an index.

    /sitemap.xml is a <sitemapindex>, so counting its <loc> elements directly
    returns the number of child sitemaps — 2 — rather than the number of pages.
    A URL count is only useful as a tripwire if it is the real one: a sudden
    jump is how a bulk injection of spam pages announces itself.
    """
    top = fetch(url, ua, None, timeout)
    if not top["ok"]:
        return 0, f" ({top['status']})"
    locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", top["body"])
    if "<sitemapindex" not in top["body"]:
        return len(locs), ""
    total = 0
    for child in locs:
        c = fetch(child, ua, None, timeout)
        total += len(re.findall(r"<loc>", c["body"])) if c["ok"] else 0
    return total, f" across {len(locs)} child sitemaps"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=SITE, help=f"origin to probe (default {SITE})")
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if the site looks hijacked (cloaking or gambling terms)")
    ap.add_argument("--strict-all", action="store_true",
                    help="also exit non-zero on the hygiene and header findings")
    args = ap.parse_args()
    site = args.site.rstrip("/")

    jobs = [(p, name, ua, ref) for p in PATHS for name, ua, ref in PERSONAS]
    print(f"  probing {site} — {len(PATHS)} paths x {len(PERSONAS)} personas\n")

    res = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch, site + p, ua, ref, args.timeout): (p, name)
                for p, name, ua, ref in jobs}
        for fut in concurrent.futures.as_completed(futs):
            res[futs[fut]] = fut.result()

    hijack = 0  # signals that mean "we are compromised again"
    hygiene = 0  # signals that mean "this was never finished"

    print("  cloaking")
    for p in PATHS:
        base = res[(p, "direct")]
        if not base["ok"]:
            print(f"    warn  {p:<12} baseline unreachable ({base['status']})")
            hygiene += 1
            continue
        base_fp = fingerprint(base)
        bad = []
        for name, _, _ in PERSONAS[1:]:
            other = res[(p, name)]
            if not other["ok"]:
                bad.append(f"{name}: unreachable ({other['status']})")
                continue
            diff = compare(base_fp, fingerprint(other))
            if diff:
                bad.append(f"{name}: " + "; ".join(diff))
        if bad:
            hijack += len(bad)
            print(f"    warn  {p:<12} {len(bad)} persona(s) diverge from a direct visit")
            for b in bad:
                print(f"            {b}")
        else:
            print(f"    ok    {p:<12} {len(PERSONAS)}/{len(PERSONAS)} personas identical")

    print("\n  keywords")
    hits = {}
    for (p, name), r in res.items():
        for m in TERM_RE.findall(r["body"]):
            hits.setdefault(m.lower(), set()).add(f"{p} [{name}]")
    if hits:
        hijack += len(hits)
        for term, where in sorted(hits.items()):
            print(f"    warn  {term!r} in {len(where)} response(s): {sorted(where)[0]} ...")
    else:
        print(f"    ok    no gambling vocabulary in {len(res)} responses")

    print("\n  hygiene")
    robots = fetch(site + "/robots.txt", BROWSER, None, args.timeout)
    if robots["ok"] and "sitemap:" in robots["body"].lower():
        print("    ok    robots.txt   present, declares a sitemap")
    elif robots["ok"]:
        hygiene += 1
        print("    warn  robots.txt   present but declares no sitemap")
    else:
        hygiene += 1
        print(f"    warn  robots.txt   {robots['status']} — should exist and declare the sitemap")

    n, detail = count_sitemap(site + "/sitemap.xml", BROWSER, args.timeout)
    if n:
        print(f"    ok    sitemap      {n} URLs{detail}")
    else:
        hygiene += 1
        print(f"    warn  sitemap      no URLs found{detail}")

    print("\n  headers")
    live = res[("/", "direct")]["headers"]
    for h in HEADERS:
        if h in live:
            print(f"    ok    {h}")
        else:
            hygiene += 1
            print(f"    warn  {h:<28} absent")

    print()
    if hijack:
        print(f"  HIJACK SIGNALS: {hijack} — the site may be compromised again.")
        print("  Escalate to whoever administers the host.")
    else:
        print("  no hijack signals — cloaking and keyword checks both clean")
        print("  (a cloak keyed to verified Googlebot IPs cannot be seen from here;")
        print("   confirm with Search Console URL Inspection → View Crawled Page)")
    if hygiene:
        print(f"  {hygiene} hygiene finding(s) — outstanding deployment work, see status.md issue 1")

    # --strict alarms only on hijack signals. The hygiene findings are known and
    # will stay outstanding until someone with server access acts on issue 1;
    # tripping the alarm on them every run is how a scheduled check gets ignored.
    if args.strict_all and (hijack or hygiene):
        return 1
    return 1 if (args.strict and hijack) else 0


if __name__ == "__main__":
    sys.exit(main())
