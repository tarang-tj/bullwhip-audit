"""Pipeline tests on the cached real data. Each one exists because the bug it names happened
once during the build or is easy to make."""
import pandas as pd
import pytest

from src.bullwhip import fetch, panel
from src.bullwhip.findings import Numbers
from src.bullwhip.registry import industries

LOOKUP = {(i.tier, i.code): i for i in industries()}


def test_seasonality_measured_before_adjustment():
    # bug seen in the build: seasonality computed on already-deseasonalized demand (~0)
    ind = LOOKUP[("retail", "452")]
    nsa = panel.evaluate(ind, panel.Spec(sa=False))
    sa = panel.evaluate(ind, panel.Spec(sa=True))
    assert nsa["seasonality"] == pytest.approx(sa["seasonality"])
    assert nsa["seasonality"] > 0.5


def test_window_end_cuts_levels_before_transform():
    # bug seen in the build: April 2020 clothing-store production broke the 1993-2004 window
    ind = LOOKUP[("retail", "448")]
    early = panel.evaluate(ind, panel.Spec(window="crs", margin=0.30))
    late = panel.evaluate(ind, panel.Spec(window="full", margin=0.30))
    assert early["undefined"] == "" and early["n"] == 144
    assert late["undefined"] == "nonpositive production"


def test_quarterly_keeps_only_complete_quarters():
    idx = pd.date_range("2000-01-01", periods=7, freq="MS")
    q = panel._quarterly(pd.Series(1.0, idx))
    assert q.tolist() == [3.0, 3.0]


def test_orders_demand_requires_orders_series():
    with pytest.raises(ValueError):
        panel.flows(LOOKUP[("retail", "441")], panel.Spec(demand="orders"))


def test_robustness_split_counts_kept_specs():
    # bug seen in the build: df.transform is a pandas method, so attribute access compared
    # a method to "yoy" and leaked 12-month-difference cells into "seasonality kept"
    nums = pd.read_csv(fetch.ROOT / "outputs" / "numbers.csv").set_index("key")["value"]
    assert nums["n_spec_kept"] == 3 * 4 * 2 * 2 * 2  # window, margin, deflate, transform, freq


def test_numbers_reject_duplicate_keys():
    n = Numbers()
    n.add("a", 1, "int", "x")
    with pytest.raises(KeyError):
        n.add("a", 2, "int", "y")


def test_parse_drops_missing_marker():
    body = b"observation_date,X\n2000-01-01,1.5\n2000-02-01,.\n2000-03-01,2\n"
    assert fetch.parse(body, "X").tolist() == [1.5, 2.0]


def test_cache_matches_manifest():
    assert fetch.verify_cache() == []
