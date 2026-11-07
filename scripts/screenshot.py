"""Capture the README image of the live page's first findings chart, so it can be
re-shot whenever the page changes. Run: python scripts/screenshot.py [url]"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://tarang-tj.github.io/bullwhip-audit/"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("docs/img/chart-split.png")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 900}, device_scale_factor=2)
    page.goto(URL, wait_until="load")
    chart = page.locator("#chart-split")
    chart.locator("svg, canvas").first.wait_for(timeout=30000)
    page.wait_for_timeout(800)
    # The chart plus its legend: the chart's parent holds both.
    box = chart.locator("xpath=..").bounding_box()
    pad = 20
    page.screenshot(path=str(OUT), full_page=True, clip={"x": box["x"] - pad, "y": box["y"] - pad,
                                                      "width": box["width"] + 2 * pad, "height": box["height"] + 2 * pad})
    browser.close()
print(f"wrote {OUT} from {URL}")
