"""Download public spot OHLCV with source-level provenance; never merge venues."""

from __future__ import annotations

import hashlib
import io
import json
import time
import zipfile
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import requests

BINANCE_BASE = "https://data.binance.vision/data/spot"
BINANCE_COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "trade_count", "taker_buy_base", "taker_buy_quote", "ignore",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _month_range(start: date, end: date):
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        yield year, month
        month += 1
        if month == 13:
            year, month = year + 1, 1


def download_binance_daily(output_dir: Path, start: date = date(2017, 8, 1)) -> tuple[pd.DataFrame, dict]:
    """Download monthly daily-klines archives through the last completed UTC month."""
    output_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(UTC).date()
    last_month = date(today.year, today.month, 1)
    frames, objects, failures = [], [], []
    session = requests.Session()
    session.headers.update({"User-Agent": "btc-quant-desk/0.1 research"})
    for year, month in _month_range(start, last_month):
        month_start = date(year, month, 1)
        if month_start >= last_month:
            break
        name = f"BTCUSDT-1d-{year}-{month:02d}.zip"
        url = f"{BINANCE_BASE}/monthly/klines/BTCUSDT/1d/{name}"
        try:
            response = session.get(url, timeout=45)
            if response.status_code == 404:
                failures.append({"url": url, "status": 404, "reason": "archive_not_found"})
                continue
            response.raise_for_status()
            archive = zipfile.ZipFile(io.BytesIO(response.content))
            csv_names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                raise ValueError("ZIP contains no CSV")
            frame = pd.read_csv(archive.open(csv_names[0]), header=None)
            if frame.empty:
                raise ValueError("empty CSV")
            if str(frame.iloc[0, 0]).lower() in {"open_time", "open time"}:
                frame = frame.iloc[1:].copy()
            if frame.shape[1] < 6:
                raise ValueError(f"expected at least 6 columns, got {frame.shape[1]}")
            frame = frame.iloc[:, :6].copy()
            frame.columns = ["timestamp", "open", "high", "low", "close", "volume"]
            frame["timestamp"] = pd.to_datetime(pd.to_numeric(frame["timestamp"]), unit="ms", utc=True)
            for col in ["open", "high", "low", "close", "volume"]:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
            frames.append(frame)
            raw_path = output_dir / name
            raw_path.write_bytes(response.content)
            objects.append({
                "source": "Binance Vision spot monthly klines",
                "url": url,
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "file": str(raw_path),
                "size_bytes": raw_path.stat().st_size,
                "sha256": _sha256(raw_path),
                "rows": len(frame),
                "venue": "Binance",
                "symbol": "BTCUSDT",
                "quote_currency": "USDT",
            })
            time.sleep(0.05)
        except Exception as exc:  # noqa: BLE001 - preserve exact source failure in manifest  # noqa: BLE001 - preserve exact source failure in manifest
            failures.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
    # Fetch current-month daily archives through yesterday; the current UTC day is incomplete.
    from datetime import timedelta
    day = last_month
    yesterday = today - timedelta(days=1)
    while day <= yesterday:
        name = f"BTCUSDT-1d-{day.isoformat()}.zip"
        url = f"{BINANCE_BASE}/daily/klines/BTCUSDT/1d/{name}"
        try:
            response = session.get(url, timeout=45)
            if response.status_code == 404:
                failures.append({"url": url, "status": 404, "reason": "daily_archive_not_yet_available"})
                day += timedelta(days=1)
                continue
            response.raise_for_status()
            archive = zipfile.ZipFile(io.BytesIO(response.content))
            csv_names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                raise ValueError("ZIP contains no CSV")
            frame = pd.read_csv(archive.open(csv_names[0]), header=None)
            if frame.empty:
                raise ValueError("empty CSV")
            if str(frame.iloc[0, 0]).lower() in {"open_time", "open time"}:
                frame = frame.iloc[1:].copy()
            if frame.shape[1] < 6:
                raise ValueError(f"expected at least 6 columns, got {frame.shape[1]}")
            frame = frame.iloc[:, :6].copy()
            frame.columns = ["timestamp", "open", "high", "low", "close", "volume"]
            frame["timestamp"] = pd.to_datetime(pd.to_numeric(frame["timestamp"]), unit="ms", utc=True)
            for col in ["open", "high", "low", "close", "volume"]:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
            frames.append(frame)
            raw_path = output_dir / name
            raw_path.write_bytes(response.content)
            objects.append({
                "source": "Binance Vision spot daily klines",
                "url": url,
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "file": str(raw_path),
                "size_bytes": raw_path.stat().st_size,
                "sha256": _sha256(raw_path),
                "rows": len(frame),
                "venue": "Binance",
                "symbol": "BTCUSDT",
                "quote_currency": "USDT",
            })
        except Exception as exc:
            failures.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
        day += timedelta(days=1)
    if not frames:
        raise RuntimeError(f"No Binance monthly/daily data acquired; failures={json.dumps(failures[:5])}")
    data = pd.concat(frames, ignore_index=True).sort_values("timestamp")
    data = data.drop_duplicates(subset=["timestamp"], keep="last").reset_index(drop=True)
    manifest = {
        "source": "Binance Vision",
        "venue": "Binance",
        "symbol": "BTCUSDT",
        "quote_currency": "USDT",
        "interval": "1d",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "objects": objects,
        "failures": failures,
        "first_timestamp": data.timestamp.min().isoformat(),
        "last_timestamp": data.timestamp.max().isoformat(),
        "rows": len(data),
    }
    return data, manifest


def download_bitstamp_recent(output_dir: Path, days: int = 900) -> tuple[pd.DataFrame, dict]:
    """Download Bitstamp BTC/USD daily candles in <=1000-bar windows."""
    output_dir.mkdir(parents=True, exist_ok=True)
    end_ts = int(datetime.now(UTC).timestamp())
    start_ts = end_ts - days * 86400
    cursor = start_ts
    rows, requests_log = [], []
    session = requests.Session()
    while cursor < end_ts:
        window_end = min(cursor + 999 * 86400, end_ts)
        url = "https://www.bitstamp.net/api/v2/ohlc/btcusd/"
        params = {"step": 86400, "limit": 1000, "start": cursor, "end": window_end}
        response = session.get(url, params=params, timeout=45)
        response.raise_for_status()
        payload = response.json()
        candles = payload.get("data", {}).get("ohlc", [])
        requests_log.append({"url": response.url, "status": response.status_code, "rows": len(candles)})
        if not candles:
            break
        rows.extend(candles)
        newest = max(int(c["timestamp"]) for c in candles)
        if newest <= cursor:
            raise RuntimeError("Bitstamp pagination did not advance")
        cursor = newest + 1
        time.sleep(0.15)
    if not rows:
        raise RuntimeError(f"No Bitstamp candles returned; requests={requests_log}")
    frame = pd.DataFrame(rows)
    frame["timestamp"] = pd.to_datetime(pd.to_numeric(frame["timestamp"]), unit="s", utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame[["timestamp", "open", "high", "low", "close", "volume"]]
    frame = frame.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
    csv_path = output_dir / "bitstamp_btcusd_1d_recent.csv"
    frame.to_csv(csv_path, index=False)
    manifest = {
        "source": "Bitstamp public OHLC API",
        "venue": "Bitstamp",
        "symbol": "BTC/USD",
        "quote_currency": "USD",
        "interval": "1d",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "requests": requests_log,
        "file": str(csv_path),
        "size_bytes": csv_path.stat().st_size,
        "sha256": _sha256(csv_path),
        "rows": len(frame),
        "first_timestamp": frame.timestamp.min().isoformat(),
        "last_timestamp": frame.timestamp.max().isoformat(),
    }
    return frame, manifest


def write_manifest(manifests: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"generated_at_utc": datetime.now(UTC).isoformat(),
                                "sources": manifests}, indent=2), encoding="utf-8")
