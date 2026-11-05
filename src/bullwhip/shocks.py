"""Regime and shock views: rolling amplification ratios and inventory-to-sales paths."""
from __future__ import annotations

import pandas as pd

from src.bullwhip import measure as m
from src.bullwhip.fetch import fetch
from src.bullwhip.panel import Spec, evaluate, flows
from src.bullwhip.registry import AGGREGATES, SA_LEVELS, industries

SHOCKS = {
    "great recession": ("2008-07", "2009-12"),
    "covid collapse and rebound": ("2020-02", "2021-06"),
    "chip shortage and restock": ("2021-01", "2023-06"),
}
CHAINS = {  # upstream links by NAICS (A5: not closed chains; imports and B2B leak)
    "motor vehicles": [("retail", "441"), ("wholesale", "4231"), ("manufacturing", "36S")],
    "electronics": [("wholesale", "4236"), ("wholesale", "4234"), ("manufacturing", "34S")],
}


def rolling_ratio(prod: pd.Series, demand: pd.Series, months: int = 60) -> pd.Series:
    """Amplification ratio over a trailing window of logdiff NSA months (CRS transform)."""
    p, d = m.paired(prod, demand, "logdiff", False, None, None)
    vp = p.rolling(months).var()
    vd = d.rolling(months).var()
    return (vp / vd).dropna().rename("ratio")


def aggregate_rolling(months: int = 60) -> pd.DataFrame:
    out = {}
    for ind in AGGREGATES:
        prod, dem = flows(ind, Spec())
        out[ind.tier] = rolling_ratio(prod, dem, months)
    return pd.DataFrame(out)


def is_ratio(tier: str) -> pd.Series:
    s_id, i_id = SA_LEVELS[tier]
    s, i = fetch(s_id).align(fetch(i_id), join="inner")
    return (i / s).rename(tier)


def shock_table() -> pd.DataFrame:
    """For each shock and tier: I/S before (12-month mean ending at the start), the peak and
    trough inside the window, and the swing from trough to peak in percent of the baseline."""
    rows = []
    for shock, (start, end) in SHOCKS.items():
        for tier in SA_LEVELS:
            r = is_ratio(tier)
            before = r.loc[:start].iloc[-13:-1].mean()
            inside = r.loc[start:end]
            rows.append({"shock": shock, "tier": tier, "is_before": before,
                         "is_peak": inside.max(), "peak_month": inside.idxmax().strftime("%Y-%m"),
                         "is_trough": inside.min(),
                         "trough_month": inside.idxmin().strftime("%Y-%m"),
                         "swing_pct": 100 * (inside.max() - inside.min()) / before})
    return pd.DataFrame(rows)


def chain_table() -> pd.DataFrame:
    """Amplification ratio per chain link, CRS era vs post-2005, base spec."""
    lookup = {(i.tier, i.code): i for i in industries()}
    rows = []
    for chain, links in CHAINS.items():
        for tier, code in links:
            ind = lookup[(tier, code)]
            for window in ("crs", "post"):
                for dem in (("sales", "orders") if ind.orders else ("sales",)):
                    r = evaluate(ind, Spec(window=window, demand=dem))
                    rows.append({"chain": chain, "tier": tier, "code": code, "window": window,
                                 "demand": dem, "ratio": r["ratio"], "bf_p": r["bf_p"]})
    return pd.DataFrame(rows)
