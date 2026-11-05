"""Known-answer tests for the bullwhip measures. Each test names the bug it exists to catch."""
import numpy as np
import pandas as pd
import pytest

from src.bullwhip import measure as m


def _months(n, start="2000-01-01"):
    return pd.date_range(start, periods=n, freq="MS")


def _order_up_to(n=240, seed=1):
    """Simulate a retailer: inventory follows I_t = base + noise, it orders exactly what it sold
    plus the inventory change. Returns sales, inventory and the true orders."""
    rng = np.random.default_rng(seed)
    idx = _months(n)
    sales = pd.Series(100 + 10 * np.sin(np.arange(n) / 2) + rng.normal(0, 3, n), idx)
    inv = pd.Series(300 + rng.normal(0, 8, n).cumsum() * 0.1 + rng.normal(0, 5, n), idx)
    orders = sales + inv.diff()
    return sales, inv, orders.dropna()


def test_production_recovers_simulated_orders():
    # catches: using I_t - I_{t+1}, or I_t alone, instead of I_t - I_{t-1}
    sales, inv, orders = _order_up_to()
    pd.testing.assert_series_equal(m.production(sales, inv), orders, check_names=False)


def test_margin_scales_sales_to_cost():
    # catches: margin applied to inventory, or (margin) instead of (1 - margin)
    idx = _months(3)
    s, i = pd.Series([100.0, 100, 100], idx), pd.Series([50.0, 60, 55], idx)
    assert m.production(s, i, margin=0.25).tolist() == [85.0, 70.0]


def test_ratio_is_one_when_production_equals_demand():
    sales, _, _ = _order_up_to()
    p, d = m.paired(sales, sales, "logdiff", False, None, None)
    assert m.amp_ratio(p, d) == pytest.approx(1.0)


def test_ratio_known_scaling():
    # production = demand amplified 2x in log-diff space -> ratio exactly 4
    rng = np.random.default_rng(3)
    d = pd.Series(rng.normal(0, 0.02, 200), _months(200))
    assert m.amp_ratio(2 * d, d) == pytest.approx(4.0)


def test_deseasonalize_removes_pure_seasonal():
    # catches: dummy means computed on the wrong key (e.g. year instead of month)
    idx = _months(120)
    x = pd.Series(np.tile(np.arange(12, dtype=float), 10), idx)
    assert np.allclose(m.deseasonalize(x), 0.0)
    assert m.seasonality_ratio(x + np.random.default_rng(0).normal(0, 1e-6, 120)) > 0.999


def test_logdiff_rejects_non_positive():
    with pytest.raises(ValueError):
        m.transform(pd.Series([1.0, 0.0, 2.0], _months(3), name="x"))


def test_bootstrap_ci_covers_true_ratio_and_reports_direction():
    rng = np.random.default_rng(11)
    d = pd.Series(rng.normal(0, 1, 300), _months(300))
    p = pd.Series(1.5 * d.values + rng.normal(0, 0.2, 300), _months(300))
    true = m.amp_ratio(p, d)
    ci = m.block_bootstrap(p, d, reps=500)
    assert ci["lo"] < true < ci["hi"]
    assert ci["p_gt1"] > 0.99


def test_bootstrap_blocks_widen_ci_on_persistent_series():
    # catches: block length silently ignored (iid resampling understates uncertainty on AR data)
    rng = np.random.default_rng(5)
    n = 400
    e1, e2 = rng.normal(size=n), rng.normal(size=n)
    a, b = np.zeros(n), np.zeros(n)
    for t in range(1, n):
        a[t] = 0.9 * a[t - 1] + e1[t]
        b[t] = 0.9 * b[t - 1] + e2[t]
    p, d = pd.Series(a, _months(n)), pd.Series(b, _months(n))
    w1 = m.block_bootstrap(p, d, block=1, reps=400)
    w24 = m.block_bootstrap(p, d, block=24, reps=400)
    assert (w24["hi"] - w24["lo"]) > 1.3 * (w1["hi"] - w1["lo"])
