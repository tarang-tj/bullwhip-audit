/* Four SVG charts drawn from window.DATA. No libraries. Tier colors are the validated
   reference palette's first three slots (all-pairs safe); every chart has a hover tooltip
   and a legend, and the memo tables carry the same numbers for non-visual readers. */
(function () {
  "use strict";
  const D = window.DATA;
  const TIERS = ["retail", "wholesale", "manufacturing"];
  const NS = "http://www.w3.org/2000/svg";
  const tip = document.getElementById("tip");

  function el(name, attrs, parent) {
    const n = document.createElementNS(NS, name);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function frame(id, h) {
    const host = document.getElementById(id);
    const w = Math.max(300, Math.min(host.clientWidth || 720, 760));
    const svg = el("svg", { viewBox: `0 0 ${w} ${h}`, width: "100%", role: "img",
      "aria-label": host.dataset.label || "" }, host);
    return { svg, w, h, m: { t: 16, r: 16, b: 36, l: 48 } };
  }
  function hover(node, html) {
    node.addEventListener("pointerenter", () => { tip.innerHTML = html; tip.hidden = false; });
    node.addEventListener("pointermove", (e) => {
      const x = Math.min(e.clientX + 14, window.innerWidth - tip.offsetWidth - 8);
      tip.style.left = x + "px"; tip.style.top = (e.clientY + 14) + "px";
    });
    node.addEventListener("pointerleave", () => { tip.hidden = true; });
  }
  const color = (t) => `var(--series-${TIERS.indexOf(t) + 1})`;
  const pct = (v) => Math.round(v * 100) + "%";
  function yAxis(f, scale, ticks, fmt) {
    ticks.forEach((v) => {
      const y = scale(v);
      el("line", { x1: f.m.l, x2: f.w - f.m.r, y1: y, y2: y, class: "grid" }, f.svg);
      el("text", { x: f.m.l - 6, y: y + 4, class: "axis", "text-anchor": "end" }, f.svg)
        .textContent = fmt(v);
    });
  }

  // 1. dumbbell: share of cells amplifying, seasonality kept vs removed
  (function () {
    const f = frame("chart-split", 190);
    const x = (v) => f.m.l + 70 + v * (f.w - f.m.l - 70 - f.m.r);
    [0, 0.5, 1].forEach((v) => {
      el("line", { x1: x(v), x2: x(v), y1: 8, y2: 160, class: v === 0.5 ? "ref" : "grid" }, f.svg);
      el("text", { x: x(v), y: 178, class: "axis", "text-anchor": "middle" }, f.svg).textContent = pct(v);
    });
    TIERS.forEach((t, i) => {
      const y = 34 + i * 50, a = D.split[t].kept, b = D.split[t].removed;
      el("text", { x: 4, y: y + 4, class: "label" }, f.svg).textContent = t;
      el("line", { x1: x(a), x2: x(b), y1: y, y2: y, class: "stem" }, f.svg);
      // neutral ink, not tier colors: blue and orange mean retail and wholesale elsewhere
      const k = el("circle", { cx: x(a), cy: y, r: 7, fill: "var(--ink)", class: "dot" }, f.svg);
      const r = el("rect", { x: x(b) - 6, y: y - 6, width: 12, height: 12, rx: 2,
        fill: "var(--surface)", stroke: "var(--ink-2)", "stroke-width": 2, class: "mark" }, f.svg);
      hover(k, `<b>${t}</b><br>seasonality kept: ${pct(a)} of cells amplify`);
      hover(r, `<b>${t}</b><br>seasonality removed: ${pct(b)} of cells amplify`);
    });
  })();

  // 2. every industry's ratio, log scale, by tier
  (function () {
    const f = frame("chart-industries", 260);
    const lo = Math.log(0.25), hi = Math.log(4);
    const y = (v) => f.m.t + (hi - Math.log(v)) / (hi - lo) * (f.h - f.m.t - f.m.b);
    yAxis(f, y, [0.25, 0.5, 1, 2, 4], (v) => v + "x");
    el("line", { x1: f.m.l, x2: f.w - f.m.r, y1: y(1), y2: y(1), class: "ref" }, f.svg);
    const band = (f.w - f.m.l - f.m.r) / 3;
    TIERS.forEach((t, i) => {
      const rows = D.industries.filter((r) => r.tier === t);
      el("text", { x: f.m.l + band * (i + 0.5), y: f.h - 10, class: "label",
        "text-anchor": "middle" }, f.svg).textContent = t;
      rows.forEach((r, j) => {
        const cx = f.m.l + band * i + band * (0.15 + 0.7 * (j + 0.5) / rows.length);
        const c = el("circle", { cx, cy: y(Math.min(4, Math.max(0.25, r.ratio))), r: 5,
          fill: color(t), class: "dot" }, f.svg);
        hover(c, `<b>${r.name}</b><br>ratio ${r.ratio.toFixed(2)} (1993-2025, unadjusted)`);
      });
    });
  })();

  // 3. seasonality vs ratio
  (function () {
    const f = frame("chart-season", 280);
    const x = (v) => f.m.l + v * (f.w - f.m.l - f.m.r);
    const lo = Math.log(0.25), hi = Math.log(4);
    const y = (v) => f.m.t + (hi - Math.log(v)) / (hi - lo) * (f.h - f.m.t - f.m.b);
    yAxis(f, y, [0.25, 0.5, 1, 2, 4], (v) => v + "x");
    el("line", { x1: f.m.l, x2: f.w - f.m.r, y1: y(1), y2: y(1), class: "ref" }, f.svg);
    [0, 0.5, 1].forEach((v) => {
      el("text", { x: x(v), y: f.h - 14, class: "axis", "text-anchor": "middle" }, f.svg)
        .textContent = pct(v);
    });
    D.industries.forEach((r) => {
      const c = el("circle", { cx: x(r.seasonality), r: 5, fill: color(r.tier), class: "dot",
        cy: y(Math.min(4, Math.max(0.25, r.ratio))) }, f.svg);
      hover(c, `<b>${r.name}</b><br>${r.tier}<br>seasonality ${pct(r.seasonality)}, ratio ${r.ratio.toFixed(2)}`);
    });
  })();

  // 4. rolling 60-month ratio, aggregate tiers
  (function () {
    const f = frame("chart-rolling", 260);
    const live = D.live || [], pts = D.rolling.concat(live), n = pts.length, s0 = D.rolling.length - 1;
    const x = (i) => f.m.l + i / (n - 1) * (f.w - f.m.l - f.m.r);
    const y = (v) => f.m.t + (1.3 - v) / (1.3 - 0.3) * (f.h - f.m.t - f.m.b);
    yAxis(f, y, [0.4, 0.6, 0.8, 1, 1.2], (v) => v.toFixed(1));
    el("line", { x1: f.m.l, x2: f.w - f.m.r, y1: y(1), y2: y(1), class: "ref" }, f.svg);
    pts.forEach((p, i) => {
      if (p.date.endsWith("-01-01") && +p.date.slice(0, 4) % 5 === 0)
        el("text", { x: x(i), y: f.h - 14, class: "axis", "text-anchor": "middle" }, f.svg)
          .textContent = p.date.slice(0, 4);
    });
    const path = (t, a, b) => {  // a null lifts the pen, so gaps stay gaps
      let up = true;
      return pts.slice(a, b + 1).map((p, k) => {
        if (p[t] == null) { up = true; return ""; }
        const c = up ? "M" : "L"; up = false;
        return `${c}${x(a + k).toFixed(1)},${y(p[t]).toFixed(1)}`;
      }).join("");
    };
    TIERS.forEach((t) => {
      el("path", { d: path(t, 0, s0), stroke: color(t), class: "line" }, f.svg);
      if (live.length) el("path", { d: path(t, s0, n - 1), stroke: color(t), class: "line live" }, f.svg);
    });
    if (live.length) {  // months after the study window, current Census vintage
      el("line", { x1: x(s0), x2: x(s0), y1: f.m.t, y2: f.h - f.m.b, class: "ref" }, f.svg);
      el("text", { x: x(s0) - 4, y: f.m.t + 10, class: "axis", "text-anchor": "end" }, f.svg)
        .textContent = "study ends";
    }
    const cross = el("line", { y1: f.m.t, y2: f.h - f.m.b, class: "cross", visibility: "hidden" }, f.svg);
    const hit = el("rect", { x: f.m.l, y: f.m.t, width: f.w - f.m.l - f.m.r,
      height: f.h - f.m.t - f.m.b, fill: "transparent" }, f.svg);
    hit.addEventListener("pointermove", (e) => {
      const b = f.svg.getBoundingClientRect(), sx = (e.clientX - b.left) * f.w / b.width;
      const i = Math.max(0, Math.min(n - 1, Math.round((sx - f.m.l) / (f.w - f.m.l - f.m.r) * (n - 1))));
      cross.setAttribute("x1", x(i)); cross.setAttribute("x2", x(i));
      cross.setAttribute("visibility", "visible");
      const p = pts[i];
      tip.innerHTML = `<b>60 months to ${p.date.slice(0, 7)}</b><br>` +
        TIERS.map((t) => `${t}: ${p[t] == null ? "not yet published" : p[t].toFixed(2)}`).join("<br>") +
        (i > s0 ? "<br><i>after the study window, current vintage</i>" : "");
      tip.hidden = false;
      tip.style.left = Math.min(e.clientX + 14, window.innerWidth - tip.offsetWidth - 8) + "px";
      tip.style.top = (e.clientY + 14) + "px";
    });
    hit.addEventListener("pointerleave", () => { tip.hidden = true; cross.setAttribute("visibility", "hidden"); });
  })();
})();
