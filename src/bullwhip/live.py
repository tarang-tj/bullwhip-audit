"""Monthly live panel: the trailing 60-month ratio per tier through the latest Census month.

Usage: python -m src.bullwhip.live [--offline] [--out report.md]

The study itself is frozen: every finding uses the 2026-11-05 vintage in data/raw and ends in
2025-12. This module downloads the CURRENT vintage of the six aggregate series into data/live
(its own sha256 manifest), and writes outputs/live.csv: the 60-month ratio for 2025-12 onward,
so the page can extend the rolling chart past the study window. It also recomputes each
aggregate's 1993-2025 ratio on the new vintage; if Census revised history enough to move it,
the report says so, and the frozen findings are NOT touched (a person decides on a re-run).

Exit 0: nothing changed. Exit 3: new bytes (a new month or a revision); the workflow rebuilds
the page, runs the gate and commits. Any API error raises, so a broken refresh is red.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import UTC, datetime

import pandas as pd

from src.bullwhip import fetch as f
from src.bullwhip import measure as m
from src.bullwhip.registry import AGGREGATES
from src.bullwhip.shocks import rolling_ratio

LIVE = f.ROOT / "data" / "live"
MANIFEST = LIVE / "manifest.json"
OUT = f.ROOT / "outputs" / "live.csv"
NUMS = f.ROOT / "outputs" / "numbers.csv"
STUDY_END = "2025-12"
REVISION_TOL = 0.005  # a 1993-2025 aggregate ratio moving more than this counts as a revision


def series_ids() -> list[str]:
    return [sid for ind in AGGREGATES for sid in (ind.sales, ind.inventory)]


def download_all() -> dict:
    """Fetch the current vintage of each series into data/live; return the new manifest."""
    url = os.environ.get("BULLWHIP_LIVE_URL") or f.URL  # the workflow's failure drill sets a bad one
    LIVE.mkdir(parents=True, exist_ok=True)
    man, bodies = {}, {}
    for sid in series_ids():  # download and parse all six before writing any (no half-written set)
        body = f._download(sid) if url == f.URL else _get(url.format(sid=sid))
        s = f.parse(body, sid)
        bodies[sid] = body
        man[sid] = {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body),
                    "last": s.index.max().strftime("%Y-%m"), "url": url.format(sid=sid)}
    for sid, body in bodies.items():
        (LIVE / f"{sid}.csv").write_bytes(body)
    return man


def _get(url: str) -> bytes:
    import urllib.request
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": f.UA}),
                                timeout=30) as r:
        return r.read()


def load(sid: str) -> pd.Series:
    return f.parse((LIVE / f"{sid}.csv").read_bytes(), sid)


def compute() -> tuple[pd.DataFrame, dict]:
    """Rolling ratios from STUDY_END on, and the 1993-2025 aggregate ratio, on the live vintage."""
    cols, agg, last = {}, {}, {}
    for ind in AGGREGATES:
        sales, inv = load(ind.sales), load(ind.inventory)
        prod = m.production(sales, inv)
        prod, dem = prod.align(sales, join="inner")
        cols[ind.tier] = rolling_ratio(prod, dem).loc[STUDY_END:]
        p, d = m.paired(prod, dem, "logdiff", False, "1993-01", STUDY_END)
        agg[ind.tier] = m.amp_ratio(p, d)
        last[ind.tier] = prod.index.max().strftime("%Y-%m")
    return pd.DataFrame(cols), {"agg": agg, "last": last}


def study_aggregates() -> dict:
    rows = csv.DictReader(NUMS.read_text().splitlines())
    return {r["key"][4:]: float(r["value"]) for r in rows
            if r["key"] in {f"agg_{i.tier}" for i in AGGREGATES}}


def report(roll: pd.DataFrame, info: dict, changed: bool) -> str:
    frozen = study_aggregates()
    end = roll.dropna().index.max()
    lines = [f"# Bullwhip live refresh, {datetime.now(UTC):%Y-%m-%d}", "",
             f"Latest month every tier has: {end:%Y-%m}. Files changed: {'yes' if changed else 'no'}.",
             "", "| tier | latest month | 60-month ratio | 1993-2025 ratio, study | same, live vintage |",
             "|---|---|---|---|---|"]
    revised = []
    for t in roll.columns:
        s = roll[t].dropna()
        lines.append(f"| {t} | {info['last'][t]} | {s.iloc[-1]:.3f} | {frozen[t]:.4f} | "
                     f"{info['agg'][t]:.4f} |")
        new = info["agg"][t]  # also flag a move that changes the 2-decimal figure the memo prints
        if abs(new - frozen[t]) > REVISION_TOL or round(new, 2) != round(frozen[t], 2):
            revised.append(t)
    lines += ["", "REVISION: Census revised history enough to move the study's ratio for "
              + ", ".join(revised) + ". The findings still use the frozen vintage; decide on a re-run."
              if revised else "No revision moved a 1993-2025 aggregate ratio past "
              f"{REVISION_TOL}."]
    return "\n".join(lines)


def write(roll: pd.DataFrame) -> None:
    roll.index.name = "observation_date"
    roll.to_csv(OUT, float_format="%.6g", date_format="%Y-%m-%d")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="recompute from data/live, no download")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    before = MANIFEST.read_text() if MANIFEST.exists() else ""
    if not a.offline:
        man = download_all()
        MANIFEST.write_text(json.dumps(man, indent=2, sort_keys=True) + "\n")
    changed = MANIFEST.read_text() != before
    roll, info = compute()
    write(roll)
    text = report(roll, info, changed)
    print(text)
    if a.out:
        with open(a.out, "w") as fh:
            fh.write(text + "\n")
    return 3 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
