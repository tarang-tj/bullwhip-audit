"""Fetch FRED series as CSV (keyless fredgraph endpoint) and cache them with a sha256 manifest.

Reruns read the cache; pass refresh=True to download again. Every cached file is recorded in
data/manifest.json so a reader can confirm the exact bytes the numbers came from.
"""
from __future__ import annotations

import hashlib
import io
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "manifest.json"
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
UA = "bullwhip-audit/0.1 (research script)"


def _download(sid: str, retries: int = 3) -> bytes:
    """Download one series, retrying with backoff on network errors."""
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(URL.format(sid=sid), headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
            if not body.startswith(b"observation_date"):
                raise ValueError(f"{sid}: unexpected response body {body[:80]!r}")
            return body
        except Exception as exc:  # network or format error: retry, then raise
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"download failed for {sid}") from last


def _load_manifest() -> dict:
    return json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}


def parse(body: bytes, sid: str) -> pd.Series:
    """Parse FRED CSV bytes into a float Series indexed by month start. '.' means missing."""
    df = pd.read_csv(io.BytesIO(body), na_values=["."])
    if list(df.columns) != ["observation_date", sid]:
        raise ValueError(f"{sid}: unexpected columns {list(df.columns)}")
    s = pd.Series(df[sid].astype(float).values, index=pd.to_datetime(df["observation_date"]),
                  name=sid)
    return s.dropna()


def fetch(sid: str, refresh: bool = False) -> pd.Series:
    """Return a FRED series, from cache unless refresh=True or no cache exists."""
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"{sid}.csv"
    if refresh or not path.exists():
        body = _download(sid)
        path.write_bytes(body)
        manifest = _load_manifest()
        manifest[sid] = {
            "sha256": hashlib.sha256(body).hexdigest(),
            "bytes": len(body),
            "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "url": URL.format(sid=sid),
        }
        MANIFEST.write_text(json.dumps(dict(sorted(manifest.items())), indent=2) + "\n")
        time.sleep(1.0)  # be polite to FRED
    return parse(path.read_bytes(), sid)


def verify_cache() -> list[str]:
    """Return ids whose cached bytes no longer match the manifest hash."""
    bad = []
    for sid, meta in _load_manifest().items():
        path = RAW / f"{sid}.csv"
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != meta["sha256"]:
            bad.append(sid)
    return bad
