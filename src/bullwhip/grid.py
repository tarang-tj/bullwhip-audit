"""Robustness grid: every industry under every measurement spec -> outputs/grid.csv."""
from __future__ import annotations

import itertools

import pandas as pd

from src.bullwhip.fetch import ROOT
from src.bullwhip.panel import Spec, evaluate
from src.bullwhip.registry import AGGREGATES, industries

OUT = ROOT / "outputs" / "grid.csv"
MARGINS = (0.0, 0.15, 0.30, 0.45)


def specs() -> list[Spec]:
    """All grid cells. yoy is monthly-only and already seasonally neutral, so it has one SA state."""
    out = []
    for window, margin, deflate in itertools.product(("crs", "post", "full"), MARGINS,
                                                     (False, True)):
        for transform, freq, sa in itertools.product(("logdiff", "diff", "yoy"), ("M", "Q"),
                                                     (False, True)):
            if transform == "yoy" and (freq == "Q" or sa):
                continue
            out.append(Spec(window, transform, sa, "sales", margin, deflate, freq))
    return out


def run() -> pd.DataFrame:
    rows = []
    units = [(i, "aggregate") for i in AGGREGATES] + [(i, "industry") for i in industries()]
    for spec in specs():
        for ind, level in units:
            demands = ("sales", "orders") if ind.orders else ("sales",)
            for dem in demands:
                s = spec.but(demand=dem)
                rows.append({**vars(s), "level": level, **evaluate(ind, s)})
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, float_format="%.10g")
    return df


if __name__ == "__main__":
    d = run()
    print(f"{len(d)} rows, {d['code'].nunique()} units, {len(specs())} specs -> {OUT.name}")
