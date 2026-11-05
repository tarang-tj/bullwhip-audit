"""Turn registry series into per-industry (production, demand) pairs under one measurement spec."""
from __future__ import annotations

from dataclasses import dataclass, replace

import pandas as pd

from src.bullwhip import measure as m
from src.bullwhip.fetch import fetch
from src.bullwhip.registry import Industry

# Deflators (A6): CPI for retail, PPI all commodities for wholesale and manufacturing. NSA both.
DEFLATOR = {"retail": "CPIAUCNS", "wholesale": "PPIACO", "manufacturing": "PPIACO"}

WINDOWS = {"crs": ("1993-01", "2004-12"), "post": ("2005-01", "2025-12"),
           "full": ("1993-01", "2025-12")}


@dataclass(frozen=True)
class Spec:
    """One cell of the robustness grid. Defaults reproduce the CRS 2007 headline spec,
    except margin and deflation, which CRS applied and we vary (see docs/method.md)."""
    window: str = "full"
    transform: str = "logdiff"
    sa: bool = False
    demand: str = "sales"  # or "orders" where Census publishes new orders
    margin: float = 0.0
    deflate: bool = False
    freq: str = "M"  # or "Q"

    def but(self, **kw) -> Spec:
        return replace(self, **kw)


def _deflate(x: pd.Series, tier: str) -> pd.Series:
    p = fetch(DEFLATOR[tier])
    x, p = x.align(p, join="inner")
    return x / p


def flows(ind: Industry, spec: Spec) -> tuple[pd.Series, pd.Series]:
    """Level series of production and demand for one industry under spec (before transform)."""
    sales, inv = fetch(ind.sales), fetch(ind.inventory)
    if spec.deflate:
        sales, inv = _deflate(sales, ind.tier), _deflate(inv, ind.tier)
    prod = m.production(sales, inv, margin=spec.margin)
    if spec.demand == "orders":
        if ind.orders is None:
            raise ValueError(f"{ind.code}: no new-orders series")
        demand = fetch(ind.orders)
        if spec.deflate:
            demand = _deflate(demand, ind.tier)
    else:
        demand = (1.0 - spec.margin) * sales  # same cost units as production
    prod, demand = prod.align(demand, join="inner")
    if spec.freq == "Q":
        prod, demand = _quarterly(prod), _quarterly(demand)
    return prod, demand


def _quarterly(x: pd.Series) -> pd.Series:
    """Sum monthly flows to calendar quarters, keeping only complete quarters."""
    g = x.groupby(x.index.to_period("Q"))
    q = g.sum()[g.count() == 3]
    q.index = q.index.to_timestamp()
    return q


def evaluate(ind: Industry, spec: Spec) -> dict:
    """Amplification ratio and diagnostics for one industry and one spec."""
    if spec.freq == "Q" and spec.transform == "yoy":
        raise ValueError("yoy is defined for monthly data only")
    prod, demand = flows(ind, spec)
    start, end = WINDOWS[spec.window]
    base = {"tier": ind.tier, "code": ind.code}
    # cut levels at the window end before transforming; earlier months stay for the lags
    prod, demand = prod.loc[:end], demand.loc[:end]
    # e.g. clothing stores, April 2020: the inventory drawdown exceeded cost-adjusted sales
    if spec.transform in ("logdiff", "yoy") and (pd.concat([prod, demand]) <= 0).any():
        return {**base, "n": 0, "ratio": float("nan"), "bf_p": float("nan"),
                "seasonality": float("nan"), "undefined": "nonpositive production"}
    p, d = m.paired(prod, demand, spec.transform, False, start, end)
    # predictable seasonality is a property of the unadjusted demand (CRS eq. 2)
    seas = m.seasonality_ratio(d) if spec.freq == "M" else float("nan")
    if spec.sa and spec.transform != "yoy":  # 12-month differences already remove seasonality
        p, d = m.deseasonalize(p), m.deseasonalize(d)
    return {**base, "n": len(p), "ratio": m.amp_ratio(p, d),
            "bf_p": m.brown_forsythe_p(p, d), "seasonality": seas, "undefined": ""}
