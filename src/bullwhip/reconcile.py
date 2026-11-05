"""Independent recompute of headline ratios from the raw CSV bytes, with csv + numpy only.

Shares no code with fetch/measure/panel, so a bug there cannot hide here. Every check must
match outputs/numbers.csv (or grid.csv) to 1e-9, and the raw bytes must match the manifest.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
TOL = 1e-9


def series(sid: str) -> dict[str, float]:
    with (RAW / f"{sid}.csv").open() as fh:
        rows = list(csv.reader(fh))[1:]
    return {d[:7]: float(v) for d, v in rows if v != "."}


def ratio(s_id: str, i_id: str, start: str, end: str) -> float:
    s, i = series(s_id), series(i_id)
    months = sorted(set(s) & set(i))
    months = [mo for mo in months if mo <= end]
    prod = {months[k]: s[months[k]] + i[months[k]] - i[months[k - 1]]
            for k in range(1, len(months))}
    keys = sorted(prod)
    lp = {keys[k]: np.log(prod[keys[k]]) - np.log(prod[keys[k - 1]]) for k in range(1, len(keys))}
    ls = {keys[k]: np.log(s[keys[k]]) - np.log(s[keys[k - 1]]) for k in range(1, len(keys))}
    sel = [k for k in lp if start <= k <= end]
    a, b = np.array([lp[k] for k in sel]), np.array([ls[k] for k in sel])
    return float(a.var(ddof=1) / b.var(ddof=1))


def numbers() -> dict[str, float]:
    with (ROOT / "outputs" / "numbers.csv").open() as fh:
        return {r["key"]: float(r["value"]) for r in csv.DictReader(fh)}


def grid_cell(tier: str, code: str, window: str) -> float:
    with (ROOT / "outputs" / "grid.csv").open() as fh:
        for r in csv.DictReader(fh):
            if (r["tier"], r["code"], r["window"], r["transform"], r["freq"], r["demand"],
                    r["sa"], r["deflate"], float(r["margin"])) == (
                    tier, code, window, "logdiff", "M", "sales", "False", "False", 0.0):
                return float(r["ratio"])
    raise KeyError((tier, code, window))


def main() -> int:
    fails = []
    manifest = json.loads((ROOT / "data" / "manifest.json").read_text())
    for sid, meta in manifest.items():
        if hashlib.sha256((RAW / f"{sid}.csv").read_bytes()).hexdigest() != meta["sha256"]:
            fails.append(f"hash mismatch {sid}")
    if fails:  # raw bytes changed: nothing downstream can be trusted, stop here
        print("RECONCILE FAIL", *fails, sep="\n  ")
        return 1
    nums = numbers()
    checks = {
        "agg_retail": ratio("RETAILSMNSA", "RETAILIMNSA", "1993-01", "2025-12"),
        "agg_wholesale": ratio("WHLSLRSMNSA", "WHLSLRIMNSA", "1993-01", "2025-12"),
        "agg_manufacturing": ratio("UMTMVS", "UMTMTI", "1993-01", "2025-12"),
        "chain_auto_dealers_crs": ratio("MRTSSM441USN", "MRTSIM441USN", "1993-01", "2004-12"),
        "chain_elec_sales_post": ratio("U34SVS", "U34STI", "2005-01", "2025-12"),
    }
    for key, mine in checks.items():
        if abs(mine - nums[key]) > TOL:
            fails.append(f"{key}: independent {mine:.12f} vs numbers.csv {nums[key]:.12f}")
    for tier, code, sid, iid in (("wholesale", "4234", "S4234SM144NCEN", "I4234IM144NCEN"),
                                 ("manufacturing", "11S", "U11SVS", "U11STI")):
        mine = ratio(sid, iid, "1993-01", "2004-12")
        if abs(mine - grid_cell(tier, code, "crs")) > TOL:
            fails.append(f"grid {tier} {code}: independent {mine:.12f}")
    for f in fails:
        print("RECONCILE FAIL", f)
    print(f"reconcile: {len(manifest)} hashes, {len(checks) + 2} ratios, {len(fails)} failures")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
