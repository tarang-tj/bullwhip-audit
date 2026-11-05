"""Every number the memo and page print, computed from outputs/grid.csv and the shock views.

Writes outputs/numbers.csv (key, value, fmt, description) plus tables used by the charts.
"""
from __future__ import annotations

import csv

import numpy as np
import pandas as pd
from scipy import stats

from src.bullwhip import measure as m
from src.bullwhip import shocks
from src.bullwhip.fetch import ROOT
from src.bullwhip.panel import Spec, flows
from src.bullwhip.registry import AGGREGATES, load

OUT = ROOT / "outputs"
TIERS = ("retail", "wholesale", "manufacturing")
# CRS 2007 p.13, Table 1 discussion: share of industries with ratio > 1 (1993-2004)
CRS_NSA = {"retail": 0.14, "wholesale": 0.84, "manufacturing": 0.38}
CRS_SA = {"retail": 1.00, "wholesale": 0.95, "manufacturing": 0.70}


class Numbers:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, key: str, value: float, fmt: str, desc: str) -> None:
        if any(r["key"] == key for r in self.rows):
            raise KeyError(f"duplicate number key {key}")
        self.rows.append({"key": key, "value": float(value), "fmt": fmt, "description": desc})

    def write(self) -> None:
        with (OUT / "numbers.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["key", "value", "fmt", "description"])
            w.writeheader()
            w.writerows({**r, "value": repr(r["value"])} for r in self.rows)


def share_amp(df: pd.DataFrame) -> pd.Series:
    """Share of defined industry cells with ratio > 1, by tier."""
    d = df.dropna(subset=["ratio"])
    return d.groupby("tier")["ratio"].apply(lambda r: float((r > 1).mean()))


def base(g: pd.DataFrame, **kw) -> pd.DataFrame:
    spec = {"level": "industry", "transform": "logdiff", "freq": "M", "demand": "sales",
            "margin": 0.0, "deflate": False, "sa": False, "window": "full", **kw}
    q = g
    for k, v in spec.items():
        if v is not None:
            q = q[q[k] == v]
    return q


def build() -> Numbers:
    g = pd.read_csv(OUT / "grid.csv")
    n = Numbers()
    reg = load()
    n.add("n_series", len(reg), "int", "FRED series used (registry.csv)")
    counts = base(g).groupby("tier").size()
    for t in TIERS:
        n.add(f"n_ind_{t}", counts[t], "int", f"{t} industries in the panel")
    n.add("n_ind_total", counts.sum(), "int", "industries in the panel")
    n.add("n_cells", len(g[g["level"] == "industry"]), "int", "industry-level grid cells")
    n.add("n_undefined", (g["undefined"].fillna("") != "").sum(), "int",
          "grid cells undefined because production was non-positive")

    # 1. replication, CRS window
    for t in TIERS:
        n.add(f"crs_paper_nsa_{t}", CRS_NSA[t], "pct", f"CRS 2007 share of {t} amplifying, NSA")
        n.add(f"crs_paper_sa_{t}", CRS_SA[t], "pct", f"CRS 2007 share of {t} amplifying, SA")
    rep = share_amp(base(g, window="crs"))
    rep_sa = share_amp(base(g, window="crs", sa=True))
    band = base(g, window="crs", margin=None, deflate=None).groupby(["margin", "deflate"])
    band = band[["tier", "ratio"]].apply(share_amp).reset_index()
    for t in TIERS:
        n.add(f"rep_nsa_{t}", rep[t], "pct", f"our share of {t} amplifying, 1993-2004, NSA")
        n.add(f"rep_sa_{t}", rep_sa[t], "pct", f"our share of {t} amplifying, 1993-2004, SA")
        n.add(f"rep_lo_{t}", band[t].min(), "pct", f"{t} share, min over margin x deflation")
        n.add(f"rep_hi_{t}", band[t].max(), "pct", f"{t} share, max over margin x deflation")

    # 2. robustness. Seasonal adjustment and 12-month differences both remove the seasonal
    # pattern, so cells split into "seasonality kept" (NSA, logdiff/diff) and "removed".
    ind = g[g["level"] == "industry"].copy()
    ind["seasonality_kept"] = (~ind["sa"]) & (ind["transform"] != "yoy")
    kept, removed = ind[ind.seasonality_kept], ind[~ind.seasonality_kept]
    for label, part in (("kept", kept), ("removed", removed)):
        for t, v in share_amp(part).items():
            n.add(f"robust_{label}_{t}", v, "pct",
                  f"{t}: share of seasonality-{label} grid cells with ratio > 1")
    sa_full = share_amp(base(g, sa=True))
    for t in TIERS:
        n.add(f"sa_full_{t}", sa_full[t], "pct", f"{t} share amplifying, 1993-2025, SA")
    keys = ["window", "margin", "deflate", "transform", "freq", "sa"]
    cells = ind.groupby(keys + ["seasonality_kept"])[["tier", "ratio"]].apply(share_amp)
    cells.reset_index().to_csv(OUT / "robustness.csv", index=False, float_format="%.6g")
    kc = cells.xs(True, level="seasonality_kept")
    n.add("n_spec_kept", len(kc), "int", "seasonality-kept spec cells")
    for t in TIERS:
        n.add(f"cellmaj_{t}", float((kc[t] > 0.5).mean()), "pct",
              f"{t}: share of seasonality-kept spec cells where most industries amplify")
        n.add(f"cellmaj_n_{t}", int((kc[t] > 0.5).sum()), "int",
              f"{t}: count of seasonality-kept spec cells where most industries amplify")
    sens = []
    for dim in ("window", "margin", "deflate", "transform", "freq"):
        s = kept.groupby(dim)[["tier", "ratio"]].apply(share_amp)
        sens.append({"dimension": dim, **{t: float(s[t].max() - s[t].min()) for t in TIERS}})
    pd.DataFrame(sens).to_csv(OUT / "sensitivity.csv", index=False, float_format="%.6g")
    sens_df = pd.DataFrame(sens).set_index("dimension")
    n.add("margin_swing_manufacturing", sens_df.loc["margin", "manufacturing"], "pct",
          "manufacturing share range across the four margins, seasonality kept")

    # 3. seasonality predicts smoothing (CRS hypothesis 1)
    b = base(g).dropna(subset=["ratio"])
    rho, p = stats.spearmanr(b["seasonality"], np.log(b["ratio"]))
    n.add("seas_rho", rho, "f2", "Spearman rho, seasonality vs log ratio, 1993-2025 NSA")
    n.add("seas_p", p, "p", "p-value of that correlation")
    n.add("seas_n", len(b), "int", "industries in that correlation")

    # 4. era change
    era = base(g, window=None).pivot_table(index=["tier", "code"], columns="window",
                                           values="ratio")
    for t in TIERS:
        e = era.loc[t]
        n.add(f"med_crs_{t}", e["crs"].median(), "f2", f"median {t} ratio 1993-2004")
        n.add(f"med_post_{t}", e["post"].median(), "f2", f"median {t} ratio 2005-2025")
    _aggregates(n)
    _shocks(n)
    return n


def _aggregates(n: Numbers) -> None:
    for ind in AGGREGATES:
        prod, dem = flows(ind, Spec())
        p, d = m.paired(prod, dem, "logdiff", False, "1993-01", "2025-12")
        ci = m.block_bootstrap(p, d)
        n.add(f"agg_{ind.tier}", m.amp_ratio(p, d), "f2", f"aggregate {ind.tier} ratio 1993-2025")
        n.add(f"agg_{ind.tier}_lo", ci["lo"], "f2", "95% block-bootstrap CI low")
        n.add(f"agg_{ind.tier}_hi", ci["hi"], "f2", "95% block-bootstrap CI high")
    roll = shocks.aggregate_rolling()
    roll.to_csv(OUT / "rolling.csv", float_format="%.6g")
    n.add("roll_retail_2019", roll.loc["2019-12-01", "retail"], "f2",
          "retail 60-month ratio ending 2019-12")
    n.add("roll_retail_peak", roll.loc["2020-01":, "retail"].max(), "f2",
          "retail 60-month ratio peak after 2020")


def _shocks(n: Numbers) -> None:
    st = shocks.shock_table()
    st.to_csv(OUT / "shocks.csv", index=False, float_format="%.6g")
    key = {"retail": "retail", "wholesale": "wholesale", "manufacturing": "manufacturing",
           "computers and electronics mfg": "electronics"}
    tag = {"great recession": "gfc", "covid collapse and rebound": "covid",
           "chip shortage and restock": "chips"}
    for r in st.itertuples():
        n.add(f"swing_{tag[r.shock]}_{key[r.tier]}", r.swing_pct / 100, "pct",
              f"I/S trough-to-peak swing, {r.shock}, {r.tier}")
    chip = st[(st["shock"] == "chip shortage and restock") &
              (st["tier"] == "computers and electronics mfg")].iloc[0]
    n.add("chips_elec_peak", chip.is_peak, "f2", f"electronics mfg I/S peak ({chip.peak_month})")
    ch = shocks.chain_table()
    ch.to_csv(OUT / "chains.csv", index=False, float_format="%.6g")
    pick = {("441", "crs", "sales"): "chain_auto_dealers_crs",
            ("441", "post", "sales"): "chain_auto_dealers_post",
            ("34S", "post", "orders"): "chain_elec_orders_post",
            ("34S", "post", "sales"): "chain_elec_sales_post",
            ("36S", "post", "orders"): "chain_transport_orders_post"}
    for r in ch.itertuples():
        k = pick.get((r.code, r.window, r.demand))
        if k:
            n.add(k, r.ratio, "f2", f"{r.chain} {r.tier} {r.code} {r.window} vs {r.demand}")
            if k == "chain_elec_orders_post":
                n.add("elec_orders_multiple", 1 / r.ratio, "f1",
                      "electronics new-orders variance as a multiple of production variance")


if __name__ == "__main__":
    nums = build()
    nums.write()
    print(f"{len(nums.rows)} numbers -> outputs/numbers.csv")
