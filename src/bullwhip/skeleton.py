"""Walking skeleton: aggregate three-tier ratios on real NSA data, CRS window and full window."""
from __future__ import annotations

from src.bullwhip import measure as m
from src.bullwhip.fetch import fetch

TIERS = {
    "retail": ("RETAILSMNSA", "RETAILIMNSA"),
    "wholesale": ("WHLSLRSMNSA", "WHLSLRIMNSA"),
    "manufacturing": ("UMTMVS", "UMTMTI"),
}


def main() -> None:
    for tier, (s_id, i_id) in TIERS.items():
        s, i = fetch(s_id), fetch(i_id)
        prod = m.production(s, i)
        for label, start, end in (("crs 1993-2004", "1993-01", "2004-12"),
                                  ("full 1993-2025", "1993-01", "2025-12")):
            for sa in (False, True):
                p, d = m.paired(prod, s, "logdiff", sa, start, end)
                ci = m.block_bootstrap(p, d, reps=1000)
                print(f"{tier:13} {label:15} sa={sa!s:5} n={len(p):3} "
                      f"ratio={m.amp_ratio(p, d):.3f} ci=[{ci['lo']:.2f},{ci['hi']:.2f}] "
                      f"BF p={m.brown_forsythe_p(p, d):.3f}")


if __name__ == "__main__":
    main()
