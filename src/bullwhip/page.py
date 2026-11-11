"""Build docs/index.html: the rendered memo plus four interactive charts, one self-contained
file (no CDN, no external requests). Chart data come only from outputs/ and the registry."""
from __future__ import annotations

import csv
import html
import json
import re

import markdown
import pandas as pd

from src.bullwhip.fetch import ROOT
from src.bullwhip.hero import HERO_CSS, HERO_JS, build_hero
from src.bullwhip.registry import load

WEB = ROOT / "web"
OUT = ROOT / "docs" / "index.html"
TIERS = ("retail", "wholesale", "manufacturing")

FIGS = {
    "split": (("Share of grid cells where an industry amplifies, by whether the seasonal pattern "
               "is kept (filled circle) or removed (open square). Dashed line: half."),
              [("seasonality kept", 0, "kept"), ("seasonality removed", 0, "sq removed")]),
    "industries": (("Every industry's amplification ratio, 1993 to 2025, unadjusted, log scale. "
                    "Above the dashed line the industry passes on more volatility than it gets."),
                   None),
    "season": (("Across: share of demand variance explained by the calendar month. Up: "
                "amplification ratio, log scale. More seasonal demand, lower ratio. Each dot is "
                "one industry."), None),
    "rolling": (("Aggregate amplification ratio over trailing 60-month windows. Dashed, after the "
                 "study window: the current Census vintage, refreshed monthly."), None),
}


def short_name(title: str) -> str:
    """'Retail Sales: Food and Beverage Stores' -> 'Food and Beverage Stores'."""
    name = title.split(":")[-1].strip()
    return re.sub(r"\s+Sales$", "", name)


def data() -> dict:
    nums = {r["key"]: float(r["value"]) for r in csv.DictReader(
        (ROOT / "outputs" / "numbers.csv").open())}
    names = {(r["tier"], r["code"]): short_name(r["title"]) for r in load()
             if r["measure"] == "sales"}
    g = pd.read_csv(ROOT / "outputs" / "grid.csv")
    b = g[(g["level"] == "industry") & (g["window"] == "full") & (g["transform"] == "logdiff")
          & (g["freq"] == "M") & (g["demand"] == "sales") & (g["margin"] == 0)
          & (~g["deflate"]) & (~g["sa"])].dropna(subset=["ratio"])
    inds = [{"tier": r.tier, "code": r.code, "name": names[(r.tier, r.code)],
             "ratio": round(r.ratio, 4), "seasonality": round(r.seasonality, 4)}
            for r in b.sort_values(["tier", "ratio"]).itertuples()]
    roll = pd.read_csv(ROOT / "outputs" / "rolling.csv").dropna()
    roll = [{"date": r["observation_date"], **{t: round(r[t], 4) for t in TIERS}}
            for _, r in roll.iterrows()]
    live = []
    lp = ROOT / "outputs" / "live.csv"
    if lp.exists():  # months after the study window, current vintage (src/bullwhip/live.py)
        lv = pd.read_csv(lp)
        lv = lv[lv["observation_date"] > roll[-1]["date"]]  # the study's months are already drawn
        live = [{"date": r["observation_date"],
                 **{t: (None if pd.isna(r[t]) else round(r[t], 4)) for t in TIERS}}
                for _, r in lv.iterrows()]
    split = {t: {"kept": nums[f"robust_kept_{t}"], "removed": nums[f"robust_removed_{t}"]}
             for t in TIERS}
    return {"industries": inds, "rolling": roll, "live": live, "split": split}


def figure(key: str) -> str:
    caption, legend = FIGS[key]
    items = legend or [(t, i + 1, "") for i, t in enumerate(TIERS)]
    leg = "".join(f'<span><i class="{c}"'
                  + (f' style="background:var(--series-{n})"' if n else "")
                  + f"></i>{html.escape(t)}</span>" for t, n, c in items)
    return (f'<figure><div class="legend">{leg}</div>'
            f'<div id="chart-{key}" data-label="{html.escape(caption)}"></div>'
            f"<figcaption>{html.escape(caption)}</figcaption></figure>")


def build() -> str:
    memo = (ROOT / "docs" / "findings.md").read_text()
    body = markdown.markdown(memo, extensions=["tables"])
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace(
        "</table>", "</table></div>")
    for key in FIGS:
        marker = f"<!-- fig:{key} -->"
        if marker not in body:
            raise KeyError(f"figure marker {marker} missing from memo")
        body = body.replace(marker, figure(key))
    body = body.replace("<h1>", '<h2 class="memo-title">', 1).replace("</h1>", "</h2>", 1)
    page = (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>Where the bullwhip shows up</title>"
        "<meta name=\"description\" content=\"A replication of Cachon, Randall and Schmidt (2007)"
        " on US Census supply chain data through 2025.\">"
        f"<style>{(WEB / 'style.css').read_text()}{HERO_CSS}</style></head><body><main>"
        f"{build_hero()}{body}</main><div id=\"tip\" hidden></div>"
        f"<script>window.DATA={json.dumps(data(), separators=(',', ':'))};</script>"
        f"<script>{(WEB / 'charts.js').read_text()}{HERO_JS}</script></body></html>\n")
    OUT.write_text(page)
    return page


if __name__ == "__main__":
    print(f"{len(build()) // 1024} KB -> {OUT.relative_to(ROOT)}")
