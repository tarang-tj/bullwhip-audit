"""First screen: 44 industries slide across the line at 1 when seasonality is taken out.

Each dot is one industry's 1993-2025 amplification ratio under the headline spec (logdiff,
monthly, sales, no margin, no deflator), read from outputs/grid.csv: first with the seasonal
pattern kept (the CRS method), then removed. Positions are precomputed for both states, so
the browser only moves dots; with no JavaScript the page shows the removed state, and the
headline states both counts. Under it, one line of the live panel (outputs/live.csv).
"""
from __future__ import annotations

import math

import pandas as pd

from src.bullwhip.fetch import ROOT

TIERS = ("retail", "wholesale", "manufacturing")
LO, HI = 0.3, 3.3  # log axis bounds; every headline ratio sits inside (0.31 to 3.08)
TICKS = (0.5, 1, 2, 3)


def x(r: float) -> float:
    """Percent across the strip for ratio r on a log axis."""
    return 100 * (math.log(r) - math.log(LO)) / (math.log(HI) - math.log(LO))


def dots() -> pd.DataFrame:
    g = pd.read_csv(ROOT / "outputs" / "grid.csv")
    b = g[(g["level"] == "industry") & (g["window"] == "full") & (g["transform"] == "logdiff")
          & (g["freq"] == "M") & (g["demand"] == "sales") & (g["margin"] == 0)
          & (~g["deflate"])]
    w = b.pivot_table(index=["tier", "code"], columns="sa", values="ratio").dropna()
    w.columns = ["kept", "removed"]
    return w.reset_index()


def live_line() -> str:
    path = ROOT / "outputs" / "live.csv"
    if not path.exists():
        return ""
    roll = pd.read_csv(path, parse_dates=["observation_date"]).set_index("observation_date")
    last = {t: roll[t].dropna() for t in TIERS}
    common = min(s.index.max() for s in last.values())
    vals = ", ".join(f"{t} {last[t].loc[common]:.2f}" for t in TIERS)
    extra = [f"{t} {s.index.max():%b %Y}" for t, s in last.items() if s.index.max() > common]
    more = f" ({', '.join(extra)})" if extra else ""
    return (f'<p class="live"><b>Live:</b> Census data through {common:%b %Y}{more}. '
            f"Five-year ratio to {common:%b %Y}: {vals}. Refreshed monthly from FRED; the "
            "findings below stay on the 1993 to 2025 study window.</p>")


def build_hero() -> str:
    d = dots()
    kept, removed, n = int((d["kept"] > 1).sum()), int((d["removed"] > 1).sum()), len(d)
    rows = []
    for i, t in enumerate(TIERS):
        sub = d[d["tier"] == t]
        marks = "".join(
            f'<i class="dot t{i + 1}" style="--a:{x(r.kept):.2f}%;--b:{x(r.removed):.2f}%;'
            f'--j:{(k % 3 - 1) * 5}px" data-k="{r.kept:.4f}" data-r="{r.removed:.4f}"></i>'
            for k, r in enumerate(sub.itertuples()))
        rows.append(f'<div class="row"><span class="tier">{t}</span>'
                    f'<div class="track">{marks}</div></div>')
    ticks = "".join(f'<span class="tick" style="left:{x(v):.2f}%">{v:g}</span>' for v in TICKS)
    return (
        f'<section class="hero" id="hero" data-kept="{kept}" data-removed="{removed}">'
        '<div class="kicker">Supply chain research · US Census data, 1993 to 2025</div>'
        f"<h1>Leave the seasons in and {kept} of {n} industries amplify demand. "
        f"Take them out and {removed} do.</h1>"
        '<div class="switch" role="group" aria-label="Seasonal pattern">'
        '<button type="button" data-s="kept" aria-pressed="false">Seasons kept</button>'
        '<button type="button" data-s="removed" aria-pressed="true">Seasons removed</button>'
        f'<output class="count"><b>{removed}</b> of {n} amplify</output></div>'
        '<div class="strip" aria-hidden="true"><div class="one" style="--p:'
        f'{x(1) / 100:.4f}"><span>smooths</span><span>amplifies</span></div>{"".join(rows)}'
        f'<div class="axis">{ticks}</div></div>'
        f'<p class="note">Each dot is one industry: its production variance over its sales '
        "variance, log scale. Right of the line, it passes on more volatility than it receives."
        f"</p>{live_line()}</section>")


HERO_CSS = """
.memo-title { font: 1.6rem/1.2 Georgia, "Iowan Old Style", serif; text-transform: none;
  letter-spacing: -0.01em; color: var(--ink); margin-top: 2em; }
.line.live { stroke-dasharray: 4 3; }
.hero { padding: 8px 0 8px; }
.hero h1 { font-size: clamp(1.6rem, 4.6vw, 2.5rem); margin: 0.3em 0 0.8em; }
.switch { display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
  font: 0.85rem ui-sans-serif, system-ui, sans-serif; margin-bottom: 14px; }
.switch button { display: none; font: inherit; color: var(--ink-2); background: var(--surface-2);
  border: 1px solid var(--rule); border-radius: 999px; padding: 6px 12px; cursor: pointer; }
.hero.js .switch button { display: inline-block; }
.switch button[aria-pressed="true"] { color: var(--surface); background: var(--ink);
  border-color: var(--ink); }
.switch .count { margin-left: auto; color: var(--ink-2); }
.switch .count b { font-size: 1.6rem; color: var(--ink); font-variant-numeric: tabular-nums; }
.strip { position: relative; padding: 18px 0 26px; }
.strip .row { display: grid; grid-template-columns: 104px 1fr; align-items: center; height: 40px;
  border-top: 1px solid var(--rule); }
.strip .tier { font: 0.78rem ui-sans-serif, system-ui, sans-serif; color: var(--ink-2); }
.strip .track { position: relative; height: 100%; }
.dot { position: absolute; top: calc(50% - 6px + var(--j)); left: calc(var(--b) - 6px);
  width: 12px; height: 12px; border-radius: 50%; opacity: 0.8;
  transition: left 1.6s cubic-bezier(.6, 0, .2, 1); }
.dot.t1 { background: var(--series-1); } .dot.t2 { background: var(--series-2); }
.dot.t3 { background: var(--series-3); }
.hero.kept .dot { left: calc(var(--a) - 6px); }
.strip .one { position: absolute; top: 0; bottom: 20px; left: calc(104px + (100% - 104px) * var(--p));
  border-left: 2px dashed var(--ink); width: 0; }
.strip .one span { position: absolute; top: -2px; font: 0.72rem ui-sans-serif, system-ui,
  sans-serif; color: var(--ink-2); white-space: nowrap; }
.strip .one span:first-child { right: 6px; } .strip .one span:last-child { left: 6px; }
.strip .axis { position: relative; margin-left: 104px; height: 16px;
  font: 0.72rem ui-sans-serif, system-ui, sans-serif; color: var(--ink-2); }
.strip .tick { position: absolute; transform: translateX(-50%); }
.hero .note, .hero .live { font: 0.85rem/1.5 ui-sans-serif, system-ui, sans-serif;
  color: var(--ink-2); margin: 0 0 8px; }
.hero .live b { color: var(--ink); }
@media (max-width: 520px) { .strip .row { grid-template-columns: 1fr; height: 52px; }
  .strip .tier { margin-top: 2px; } .strip .axis { margin-left: 0; }
  .strip .one { left: calc(100% * var(--p)); } }
@media (prefers-reduced-motion: reduce) { .dot { transition: none; } }
.hero.still .dot { transition: none; }
"""

HERO_JS = """
(function () {
  const h = document.getElementById("hero"); if (!h) return;
  const out = h.querySelector(".count b"), btns = h.querySelectorAll(".switch button");
  let io = null, tid = 0;
  function set(s) {
    h.classList.toggle("kept", s === "kept");
    out.textContent = h.dataset[s];
    btns.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.s === s)));
  }
  h.classList.add("js");
  btns.forEach((b) => b.addEventListener("click", () => {
    if (io) io.disconnect(); clearTimeout(tid); set(b.dataset.s);  // the reader's choice wins
  }));
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;  // stays on removed
  h.classList.add("still"); set("kept"); void h.offsetWidth; h.classList.remove("still");
  io = new IntersectionObserver((es) => {
    if (es[0].isIntersecting) { io.disconnect(); tid = setTimeout(() => set("removed"), 900); }
  }, { threshold: 0.6 });
  io.observe(h.querySelector(".strip"));
})();
"""
