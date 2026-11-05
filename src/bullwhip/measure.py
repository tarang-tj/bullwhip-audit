"""Bullwhip measurement, following Cachon, Randall and Schmidt (2007), MSOM 9(4).

production_t = (1 - margin) * sales_t + inventory_t - inventory_{t-1}   (CRS p.6)
amplification ratio = Var[transformed production] / Var[transformed demand]   (CRS eq. 1)
CRS transform: log, then first difference, no seasonal adjustment (CRS p.7-8).
Seasonal adjustment, when asked for, = residuals from month dummies (CRS p.13).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

TRANSFORMS = ("logdiff", "yoy", "diff")


def production(sales: pd.Series, inventory: pd.Series, margin: float = 0.0) -> pd.Series:
    """Imputed production (material inflow). Sales are scaled to cost by (1 - margin)."""
    if not 0.0 <= margin < 1.0:
        raise ValueError("margin must be in [0, 1)")
    s, i = sales.align(inventory, join="inner")
    prod = (1.0 - margin) * s + i - i.shift(1)
    return prod.dropna().rename("production")


def transform(x: pd.Series, how: str = "logdiff") -> pd.Series:
    """Detrend a level series. logdiff = CRS default; yoy = 12-month log diff; diff = level diff."""
    if how not in TRANSFORMS:
        raise ValueError(f"unknown transform {how}")
    if how in ("logdiff", "yoy") and (x <= 0).any():
        raise ValueError(f"{x.name}: non-positive values cannot be logged")
    if how == "logdiff":
        return np.log(x).diff().dropna()
    if how == "yoy":
        return np.log(x).diff(12).dropna()
    return x.diff().dropna()


def deseasonalize(x: pd.Series) -> pd.Series:
    """Residuals of x on 12 month dummies (same as OLS with intercept + 11 dummies)."""
    return x - x.groupby(x.index.month).transform("mean")


def window(x: pd.Series, start: str | None, end: str | None) -> pd.Series:
    return x.loc[start:end]


def paired(prod: pd.Series, demand: pd.Series, how: str, sa: bool,
           start: str | None, end: str | None) -> tuple[pd.Series, pd.Series]:
    """Transform both series, align, window, and optionally deseasonalize within the window."""
    p, d = transform(prod, how), transform(demand, how)
    p, d = p.align(d, join="inner")
    p, d = window(p, start, end), window(d, start, end)
    if sa:
        p, d = deseasonalize(p), deseasonalize(d)
    return p, d


def amp_ratio(p: pd.Series, d: pd.Series) -> float:
    """Var[p] / Var[d] on already-transformed, aligned series (sample variance, ddof=1 both)."""
    if len(p) != len(d) or len(p) < 24:
        raise ValueError("need aligned series with at least 24 observations")
    return float(np.var(p, ddof=1) / np.var(d, ddof=1))


def seasonality_ratio(d: pd.Series) -> float:
    """CRS eq. 2: (V[d] - V[deseasonalized d]) / V[d], on a transformed demand series."""
    v = np.var(d, ddof=1)
    return float((v - np.var(deseasonalize(d), ddof=1)) / v)


def brown_forsythe_p(p: pd.Series, d: pd.Series) -> float:
    """CRS use Brown-Forsythe for equal variances: Levene's test centered on the median."""
    return float(stats.levene(p.values, d.values, center="median").pvalue)


def block_bootstrap(p: pd.Series, d: pd.Series, block: int = 12, reps: int = 2000,
                    seed: int = 7) -> dict:
    """Moving-block bootstrap of the ratio, resampling (p, d) pairs in blocks to keep the
    serial dependence and the cross-correlation. Returns 95% percentile CI and P(ratio > 1)."""
    pv, dv = np.asarray(p, float), np.asarray(d, float)
    n = len(pv)
    if n < 2 * block:
        raise ValueError("series too short for the block length")
    rng = np.random.default_rng(seed)
    starts = np.arange(n - block + 1)
    k = int(np.ceil(n / block))
    draws = np.empty(reps)
    for r in range(reps):
        idx = (rng.choice(starts, size=k)[:, None] + np.arange(block)).ravel()[:n]
        draws[r] = np.var(pv[idx], ddof=1) / np.var(dv[idx], ddof=1)
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return {"lo": float(lo), "hi": float(hi), "p_gt1": float((draws > 1).mean())}
