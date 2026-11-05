"""Playwright boot probe for docs/index.html at desktop and phone widths.

Fails on: console errors, page errors, any network request (the page must be self-contained),
horizontal scroll, a chart that drew no marks, or a tooltip that does not appear on hover.
Optional argv[1]: a directory to save screenshots into.
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.bullwhip.fetch import ROOT

PAGE = ROOT / "docs" / "index.html"
CHARTS = {"chart-split": 6, "chart-industries": 44, "chart-season": 44, "chart-rolling": 3}


def run(shots: Path | None = None) -> list[str]:
    fails: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for width, scheme in ((1440, "light"), (375, "dark")):
            page = browser.new_page(viewport={"width": width, "height": 900},
                                    color_scheme=scheme)
            page.on("console", lambda m, w=width: m.type == "error" and fails.append(
                f"{w}px console error: {m.text}"))
            page.on("pageerror", lambda e, w=width: fails.append(f"{w}px page error: {e}"))
            page.on("request", lambda r, w=width: not r.url.startswith("file:") and fails.append(
                f"{w}px external request: {r.url}"))
            page.goto(PAGE.as_uri())
            page.wait_for_timeout(300)
            if page.evaluate("document.documentElement.scrollWidth > window.innerWidth"):
                fails.append(f"{width}px: horizontal scroll")
            for cid, want in CHARTS.items():
                marks = page.locator(f"#{cid} circle, #{cid} rect.mark, #{cid} path.line").count()
                if marks < want:
                    fails.append(f"{width}px {cid}: {marks} marks, expected >= {want}")
            dot = page.locator("#chart-industries circle").first
            dot.scroll_into_view_if_needed()
            dot.hover()
            if page.locator("#tip").is_hidden():
                fails.append(f"{width}px: tooltip did not show on hover")
            if shots:
                shots.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(shots / f"page-{width}.png"), full_page=True)
            page.close()
        browser.close()
    return fails


if __name__ == "__main__":
    out = run(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
    for f in out:
        print("PROBE FAIL", f)
    print(f"probe: 2 viewports, {len(CHARTS)} charts, {len(out)} failures")
    sys.exit(1 if out else 0)
