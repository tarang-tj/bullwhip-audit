"""Industry panel definition and a live-verified registry of every FRED series used.

Codes come from a keyless probe of FRED on 2026-11-05 (see docs/method.md). Overlapping
aggregates are excluded, as in CRS 2007, so no NAICS code is counted twice within a tier.
"""
from __future__ import annotations

import csv
import re
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from src.bullwhip.fetch import ROOT, UA, fetch

REGISTRY = ROOT / "data" / "registry.csv"

WHOLESALE = ["4231", "4232", "4233", "4234", "4235", "4236", "4237", "4238", "4239",
             "4241", "4242", "4243", "4244", "4245", "4246", "4247", "4248", "4249"]
RETAIL = ["441", "4423X", "444", "445", "448", "452"]
MFG_DURABLE = ["31S", "32S", "33S", "34S", "35S", "36S", "37S"]  # new orders published
MFG_OTHER = ["39S", "11S", "12S", "13S", "14S", "15S", "16S",
             "21S", "22S", "24S", "25S", "26S", "27S"]


@dataclass(frozen=True)
class Industry:
    tier: str
    code: str
    sales: str
    inventory: str
    orders: str | None = None


def industries() -> list[Industry]:
    out = [Industry("wholesale", c, f"S{c}SM144NCEN", f"I{c}IM144NCEN") for c in WHOLESALE]
    out += [Industry("retail", c, f"MRTSSM{c}USN", f"MRTSIM{c}USN") for c in RETAIL]
    out += [Industry("manufacturing", c, f"U{c}VS", f"U{c}TI", f"U{c}NO") for c in MFG_DURABLE]
    out += [Industry("manufacturing", c, f"U{c}VS", f"U{c}TI") for c in MFG_OTHER]
    return out


AGGREGATES = [
    Industry("retail", "total", "RETAILSMNSA", "RETAILIMNSA"),
    Industry("wholesale", "total", "WHLSLRSMNSA", "WHLSLRIMNSA"),
    Industry("manufacturing", "total", "UMTMVS", "UMTMTI", "UMTMNO"),
]


# Seasonally adjusted levels, used only for inventory-to-sales paths in the shock windows.
SA_LEVELS = {
    "retail": ("RETAILSMSA", "RETAILIMSA"),
    "wholesale": ("WHLSLRSMSA", "WHLSLRIMSA"),
    "manufacturing": ("AMTMVS", "AMTMTI"),
    "computers and electronics mfg": ("A34SVS", "A34STI"),
}
DEFLATORS = ("CPIAUCNS", "PPIACO")


def fred_title(sid: str) -> str:
    """Read the series title from its FRED page; raise if the page has no matching title."""
    req = urllib.request.Request(f"https://fred.stlouisfed.org/series/{sid}",
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        page = resp.read().decode("utf-8", "replace")
    hit = re.search(r"<title>([^<]*?)\s*\(" + re.escape(sid) + r"\)", page)
    if not hit:
        raise ValueError(f"{sid}: no title on FRED page")
    time.sleep(0.5)
    return hit.group(1).strip()


def build(refresh: bool = False) -> list[dict]:
    """Fetch every series (cached), look up its title, write data/registry.csv."""
    rows = []
    for ind in AGGREGATES + industries():
        for measure, sid in (("sales", ind.sales), ("inventory", ind.inventory),
                             ("orders", ind.orders)):
            if sid is None:
                continue
            s = fetch(sid, refresh=refresh)
            rows.append({"id": sid, "tier": ind.tier, "code": ind.code, "measure": measure,
                         "title": fred_title(sid), "rows": len(s),
                         "first": s.index[0].date(), "last": s.index[-1].date()})
    extras = [(t, "sa_sales", s_id) for t, (s_id, _) in SA_LEVELS.items()]
    extras += [(t, "sa_inventory", i_id) for t, (_, i_id) in SA_LEVELS.items()]
    extras += [("all", "deflator", d) for d in DEFLATORS]
    for tier, measure, sid in extras:
        s = fetch(sid, refresh=refresh)
        rows.append({"id": sid, "tier": tier, "code": "total", "measure": measure,
                     "title": fred_title(sid), "rows": len(s),
                     "first": s.index[0].date(), "last": s.index[-1].date()})
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


def load() -> list[dict]:
    with REGISTRY.open() as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    print(f"{len(build())} series registered -> {Path(REGISTRY).relative_to(ROOT)}")
