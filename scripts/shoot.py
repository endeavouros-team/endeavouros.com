#!/usr/bin/env python3
"""Screenshot both tracks for visual review.

Structural checks cannot see layout. This captures every combination of track,
page, viewport and theme so they can be compared side by side.

Needs a Playwright install and the system Edge; there is no bundled Chromium on
this machine, so channel="msedge" is the only path that works:

    make serve
    DISPLAY=:6 /home/sradjoker/Documents/ai/health-research/.venv/bin/python scripts/shoot.py

launch() rather than launch_persistent_context(): no profile means no Singleton
lock to collide with. Note that page.evaluate() ignores the default timeouts, so
the theme flip is done with a short explicit wait rather than a polling loop.
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "shots"
TRACKS = {"zola": "http://127.0.0.1:8811", "astro": "http://127.0.0.1:8812"}
PAGES = {"home": "/", "download": "/download/"}
WIDTHS = (390, 768, 1440)
THEMES = ("dark", "light")


def main() -> int:
    OUT.mkdir(exist_ok=True)
    headless = "--headed" not in sys.argv
    shots = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=headless)
        try:
            for track, base in TRACKS.items():
                for page_name, path in PAGES.items():
                    for width in WIDTHS:
                        ctx = browser.new_context(
                            viewport={"width": width, "height": 900},
                            device_scale_factor=2,
                        )
                        ctx.set_default_timeout(20_000)
                        ctx.set_default_navigation_timeout(60_000)
                        page = ctx.new_page()
                        page.goto(base + path, wait_until="networkidle", timeout=30_000)
                        for theme in THEMES:
                            page.evaluate(
                                "t => document.documentElement.setAttribute('data-theme', t)",
                                theme,
                            )
                            page.wait_for_timeout(120)
                            name = f"{track}-{page_name}-{width}-{theme}.png"
                            page.screenshot(path=str(OUT / name), full_page=True)
                            shots += 1

                            # The mobile nav panel is the one surface a default
                            # capture never shows: every shot above is of a
                            # closed menu. Only the Astro track has one.
                            if track == "astro" and width == 390:
                                if page.locator("#nav-toggle").is_visible():
                                    page.click("#nav-toggle")
                                    page.wait_for_timeout(200)
                                    name = f"{track}-{page_name}-{width}-{theme}-menu.png"
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
