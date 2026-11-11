"""The first screen and the live panel claim real numbers: check them against the files."""
import hashlib
import json
import re

import pandas as pd
import pytest

from src.bullwhip import live
from src.bullwhip.fetch import ROOT
from src.bullwhip.hero import build_hero, dots, x

PAGE = ROOT / "docs" / "index.html"
has_live = pytest.mark.skipif(not live.MANIFEST.exists(), reason="no live vintage yet")


def test_hero_counts_are_the_dots_it_draws():
    d = dots()
    assert len(d) == 44  # every industry in the panel, none undefined under the headline spec
    kept, removed = int((d["kept"] > 1).sum()), int((d["removed"] > 1).sum())
    html = build_hero()
    assert f"{kept} of 44 industries amplify demand" in html and f"out and {removed} do" in html
    assert html.count('class="dot ') == 44
    for r in d.itertuples():
        assert 0 <= x(r.kept) <= 100 and 0 <= x(r.removed) <= 100


def test_dot_positions_put_amplifiers_right_of_the_line():
    html = build_hero()
    one = float(re.search(r'class="one" style="--p:([\d.]+)"', html).group(1)) * 100
    right = sum(float(a) > one for a in re.findall(r"--a:([\d.]+)%", html))
    assert right == int((dots()["kept"] > 1).sum())


@has_live
def test_live_files_match_their_manifest():
    man = json.loads(live.MANIFEST.read_text())
    assert sorted(man) == sorted(live.series_ids())
    for sid, meta in man.items():
        body = (live.LIVE / f"{sid}.csv").read_bytes()
        assert hashlib.sha256(body).hexdigest() == meta["sha256"]


@has_live
def test_live_csv_recomputes_and_the_page_shows_its_last_month():
    roll, _ = live.compute()
    saved = pd.read_csv(live.OUT, parse_dates=["observation_date"]).set_index("observation_date")
    pd.testing.assert_frame_equal(roll, saved, check_names=False, check_freq=False,
                                  atol=1e-5, rtol=0)  # live.csv is written to 6 digits
    common = min(saved[t].dropna().index.max() for t in saved.columns)
    assert f"Census data through {common:%b %Y}" in PAGE.read_text()


def test_a_broken_source_fails_loud(monkeypatch, tmp_path):
    monkeypatch.setenv("BULLWHIP_LIVE_URL", "http://127.0.0.1:9/{sid}")
    monkeypatch.setattr(live, "LIVE", tmp_path)
    with pytest.raises(OSError):
        live.download_all()
