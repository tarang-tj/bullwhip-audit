"""Render docs/findings.md from its template, and check that every number in it is sourced.

render: {{key}} -> numbers.csv value in that row's format. Unknown keys fail.
check:  after removing rendered values, any digit left in the memo must be on the allowlist
        (years, NAICS codes, citation details, fixed grid parameters). Anything else is an
        unsourced number and fails the gate.
"""
from __future__ import annotations

import csv
import re
import sys

from src.bullwhip.fetch import ROOT

TEMPLATE = ROOT / "docs" / "findings.template.md"
MEMO = ROOT / "docs" / "findings.md"
TOKEN = re.compile(r"\{\{([a-z0-9_]+)\}\}")
ALLOW = re.compile(
    r"\b(19|20)\d\d\b"            # years
    r"|`[^`]*`"                   # code spans (paths, NAICS codes)
    r"|\b(457|479|74)\b|9\(4\)|Table 1\b"                     # citation details
    r"|\bM3\b|\bsha256\b|-(09|21|23)\b"                     # identifiers, year-range suffixes
    r"|95%|\b(2,000|12-month|60-month|0, 15, 30 and 45 percent|3 time windows|4 gross"
    r"|3 detrending|hypothesis 1|above 1|apart from 1|toward 1)\b"  # fixed method parameters
    r"|^\s*\d\.\s|\*\*\d\.\s"     # list and finding numbers
    r"|https?://\S+", re.MULTILINE)


def fmt(value: float, kind: str) -> str:
    if kind == "pct":
        return f"{round(100 * value)}%"
    if kind == "int":
        return f"{round(value):,}"
    if kind == "f1":
        return f"{value:.1f}"
    if kind == "f2":
        return f"{value:.2f}"
    if kind == "p":
        return "< 0.001" if value < 0.001 else f"= {value:.3f}"
    raise ValueError(f"unknown format {kind}")


def numbers() -> dict[str, str]:
    with (ROOT / "outputs" / "numbers.csv").open() as fh:
        return {r["key"]: fmt(float(r["value"]), r["fmt"]) for r in csv.DictReader(fh)}


def render() -> str:
    nums = numbers()
    text = TEMPLATE.read_text()
    missing = sorted(set(TOKEN.findall(text)) - set(nums))
    if missing:
        raise KeyError(f"memo keys not in numbers.csv: {missing}")
    out = TOKEN.sub(lambda mt: nums[mt.group(1)], text)
    MEMO.write_text(out)
    return out


def unsourced(template: str) -> list[str]:
    """Digits in the template that are neither a {{token}} nor allowlisted."""
    stripped = ALLOW.sub(" ", TOKEN.sub(" ", template))
    return [ln.strip() for ln in stripped.splitlines() if re.search(r"\d", ln)]


def check() -> int:
    fails = unsourced(TEMPLATE.read_text())
    if MEMO.read_text() != TOKEN.sub(lambda mt: numbers()[mt.group(1)], TEMPLATE.read_text()):
        fails.append("docs/findings.md is stale: run `make memo`")
    if "—" in MEMO.read_text():
        fails.append("em dash in memo")
    for f in fails:
        print("MEMO FAIL", f)
    print(f"check_memo: {len(TOKEN.findall(TEMPLATE.read_text()))} sourced numbers, "
          f"{len(fails)} failures")
    return 1 if fails else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["check"]:
        sys.exit(check())
    render()
    print(f"rendered {MEMO.relative_to(ROOT)}")
