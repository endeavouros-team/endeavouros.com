#!/usr/bin/env python3
"""Screenshot the site for visual review.

Structural checks cannot see layout. This captures every combination of page,
viewport and theme so they can be compared side by side.

playwright is the one dependency outside the standard library:

    pip install playwright && playwright install chromium

It shoots the preview `make serve` publishes on :8812, so build first:

    make build
    make serve
    python3 scripts/shoot.py

Set SHOOT_CHANNEL to a Playwright channel name (msedge, chrome) to drive an
installed system browser instead, which is what a machine with no bundled
Chromium needs. `--headed` wants a display.

launch() rather than launch_persistent_context(): no profile means no Singleton
lock to collide with. Note that page.evaluate() ignores the default timeouts, so
the theme flip is done with a short explicit wait rather than a polling loop.
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "shots"
BASE = "http://127.0.0.1:8812"
PAGES = {
    "home": "/",
    "download": "/download/",
    "news": "/news/",
    "post": "/news/titan-nova-is-available/",
    "arm": "/endeavouros-arm/",
    "info": "/info/",
    "about": "/about-us/",
    "donate": "/donate/",
    "contact": "/contact/",
    "privacy": "/privacy-policy/",
    "media": "/media-images/",
}
WIDTHS = (390, 768, 1440)
THEMES = ("dark", "light")


SETTLE = """async () => {
  const step = window.innerHeight / 2;
  for (let y = 0; y < document.body.scrollHeight; y += step) {
    window.scrollTo(0, y);
    await new Promise((r) => setTimeout(r, 40));
  }
  window.scrollTo(0, 0);
  await Promise.all([...document.images].filter((i) => !i.complete)
    .map((i) => new Promise((r) => { i.onload = i.onerror = r; })));
}"""


def settle(page) -> None:
    """Scroll the whole page so lazy images load, then wait for them to decode.

    A full-page screenshot does not itself trigger loading="lazy", so without
    this every image below the first viewport captures as an empty box -- which
    reads as a broken site in review when nothing is actually wrong.
    """
    page.evaluate(SETTLE)
    page.wait_for_timeout(250)


def main() -> int:
    OUT.mkdir(exist_ok=True)
    headless = "--headed" not in sys.argv
    shots = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            channel=os.environ.get("SHOOT_CHANNEL") or None, headless=headless
        )
        try:
            for page_name, path in PAGES.items():
                for width in WIDTHS:
                    ctx = browser.new_context(
                        viewport={"width": width, "height": 900},
                        device_scale_factor=2,
                    )
                    ctx.set_default_timeout(20_000)
                    ctx.set_default_navigation_timeout(60_000)
                    page = ctx.new_page()
                    page.goto(BASE + path, wait_until="networkidle", timeout=30_000)
                    for theme in THEMES:
                        page.evaluate(
                            "t => document.documentElement.setAttribute('data-theme', t)",
                            theme,
                        )
                        page.wait_for_timeout(120)
                        settle(page)
                        name = f"{page_name}-{width}-{theme}.png"
                        page.screenshot(path=str(OUT / name), full_page=True)
                        shots += 1

                        # The mobile nav panel is the one surface a default
                        # capture never shows: every shot above is of a closed
                        # menu.
                        if width == 390 and page.locator("#nav-toggle").is_visible():
                            page.click("#nav-toggle")
                            page.wait_for_timeout(200)
                            name = f"{page_name}-{width}-{theme}-menu.png"
                            page.screenshot(path=str(OUT / name))
                            shots += 1
                            page.keyboard.press("Escape")
                            page.wait_for_timeout(120)
                    ctx.close()
        finally:
            browser.close()

    print(f"  {shots} screenshots -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
