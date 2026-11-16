"""Venue-separated public spot OHLCV acquisition with raw-object provenance."""
from __future__ import annotations

import hashlib
import io
import json
import time
import zipfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

BINANCE_BASE = "https://data.binance.vision/data/spot"
USER_AGENT = "btc-quant-desk/0.2 research"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _save_raw(output_dir: Path, name: str, payload: bytes, url: str, source: str,
              venue: str, symbol: str, quote: str) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / name
    path.write_bytes(payload)
    return {
        "source": source, "url": url, "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "file": str(path), "size_bytes": len(payload), "sha256": _sha256_bytes(payload),
        "venue": venue, "symbol": symbol, "quote_currency": quote,
    }


def _month_range(start: date, end: date):
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        yield year, month
        month += 1
        if month == 13:
            year, month = year + 1, 1


def _parse_binance_zip(payload: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if not names:
            raise ValueError("ZIP contains no CSV")
        frame = pd.read_csv(archive.open(names[0]), header=None)
    if frame.empty:
        raise ValueError("empty CSV")
    if str(frame.iloc[0, 0]).lower() in {"open_time", "open time"}:
        frame = frame.iloc[1:].copy()
    if frame.shape[1] < 6:
        raise ValueError(f"expected at least 6 columns, got {frame.shape[1]}")
    frame = frame.iloc[:, :6].copy()
    frame.columns = ["timestamp", "open", "high", "low", "close", "volume"]
    # Binance changed spot kline archive timestamps from milliseconds to microseconds
    # for newer data. Detect the epoch unit per archive; never parse microseconds as ms.
    epoch = pd.to_numeric(frame["timestamp"], errors="raise").astype("int64")
    median_epoch = int(epoch.median())
    if median_epoch >= 100_000_000_000_000:
        epoch_unit = "us"
    elif median_epoch >= 100_000_000_000:
        epoch_unit = "ms"
    else:
        raise ValueError(f"unsupported Binance epoch timestamp magnitude: {median_epoch}")
    frame["timestamp"] = pd.to_datetime(epoch, unit=epoch_unit, utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame


def download_binance_daily(output_dir: Path, start: date = date(2017, 8, 1)) -> tuple[pd.DataFrame, dict]:
    """Acquire monthly archives plus completed daily files through yesterday UTC."""
    output_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(UTC).date()
    current_month = date(today.year, today.month, 1)
    frames, objects, failures = [], [], []
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    for year, month in _month_range(start, current_month - timedelta(days=1)):
        month_start = date(year, month, 1)
        if month_start >= current_month:
            break
        name = f"BTCUSDT-1d-{year}-{month:02d}.zip"
        url = f"{BINANCE_BASE}/monthly/klines/BTCUSDT/1d/{name}"
        try:
            response = session.get(url, timeout=45)
            if response.status_code == 404:
                failures.append({"url": url, "status": 404, "reason": "archive_not_found"})
                continue
            response.raise_for_status()
            frame = _parse_binance_zip(response.content)
            frames.append(frame)
            objects.append(_save_raw(output_dir, name, response.content, url,
                                     "Binance Vision spot monthly klines", "Binance",
                                     "BTCUSDT", "USDT"))
            objects[-1]["rows"] = len(frame)
        except Exception as exc:  # noqa: BLE001 - source failures belong in manifest
            failures.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
    day = current_month
    yesterday = today - timedelta(days=1)
    while day <= yesterday:
        name = f"BTCUSDT-1d-{day.isoformat()}.zip"
        url = f"{BINANCE_BASE}/daily/klines/BTCUSDT/1d/{name}"
        try:
            response = session.get(url, timeout=45)
            if response.status_code == 404:
                failures.append({"url": url, "status": 404, "reason": "daily_archive_not_yet_available"})
            else:
                response.raise_for_status()
                frame = _parse_binance_zip(response.content)
                frames.append(frame)
                objects.append(_save_raw(output_dir, name, response.content, url,
                                         "Binance Vision spot daily klines", "Binance",
                                         "BTCUSDT", "USDT"))
                objects[-1]["rows"] = len(frame)
        except Exception as exc:  # noqa: BLE001
            failures.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
        day += timedelta(days=1)
    if not frames:
        raise RuntimeError(f"No Binance data acquired; failures={json.dumps(failures[:10])}")
    data = pd.concat(frames, ignore_index=True).sort_values("timestamp")
    duplicates = int(data["timestamp"].duplicated().sum())
    if duplicates:
        data = data.drop_duplicates("timestamp", keep="last")
    data = data[data["timestamp"].dt.date < today].reset_index(drop=True)
    manifest = {
        "source": "Binance Vision", "venue": "Binance", "symbol": "BTCUSDT",
        "quote_currency": "USDT", "interval": "1d", "timezone": "UTC",
        "retrieved_at_utc": datetime.now(UTC).isoformat(), "parser": "pandas CSV + zipfile",
        "parser_version": "btc-quant-acquisition-0.2", "schema": ["timestamp_utc", "open", "high", "low", "close", "volume"], "objects": objects,
        "failures": failures, "duplicates_removed": duplicates,
        "first_timestamp": data.timestamp.min().isoformat(),
        "last_timestamp": data.timestamp.max().isoformat(), "rows": len(data),
    }
    return data, manifest


def download_bitstamp_recent(output_dir: Path, days: int = 3650) -> tuple[pd.DataFrame, dict]:
    """Acquire Bitstamp daily OHLCV and preserve each original JSON response."""
    output_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    end_ts = int(now.timestamp())
    cursor = end_ts - days * 86400
    rows, objects, failures = [], [], []
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    request_number = 0
    while cursor < end_ts:
        window_end = min(cursor + 999 * 86400, end_ts)
        url = "https://www.bitstamp.net/api/v2/ohlc/btcusd/"
        params = {"step": 86400, "limit": 1000, "start": cursor, "end": window_end}
        response = session.get(url, params=params, timeout=45)
        response.raise_for_status()
        payload = response.content
        body = response.json()
        candles = body.get("data", {}).get("ohlc", [])
        raw = _save_raw(output_dir / "raw", f"bitstamp_ohlc_{request_number:03d}.json",
                        payload, response.url, "Bitstamp public OHLC API", "Bitstamp",
                        "BTC/USD", "USD")
        raw["rows"] = len(candles)
        objects.append(raw)
        if not candles:
            break
        rows.extend(candles)
        newest = max(int(c["timestamp"]) for c in candles)
        # The API may return its latest 1,000 candles when the requested window
        # reaches the present. Once yesterday's UTC candle is present, the
        # remaining response would repeat the same capped page.
        latest_closed_start = int(datetime.combine(
            now.date() - timedelta(days=1), datetime.min.time(), tzinfo=UTC
        ).timestamp())
        if newest >= latest_closed_start:
            break
        if newest <= cursor:
            raise RuntimeError(
                f"Bitstamp pagination did not advance before latest closed candle; "
                f"cursor={cursor}, newest={newest}, url={response.url}"
            )
        cursor = newest + 1
        request_number += 1
        time.sleep(0.15)
    if not rows:
        raise RuntimeError(f"No Bitstamp candles returned; failures={failures}")
    frame = pd.DataFrame(rows)
    frame["timestamp"] = pd.to_datetime(pd.to_numeric(frame["timestamp"]), unit="s", utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame[["timestamp", "open", "high", "low", "close", "volume"]]
    frame = frame[frame["timestamp"].dt.date < now.date()]
    frame = frame.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
    manifest = {
        "source": "Bitstamp public OHLC API", "venue": "Bitstamp", "symbol": "BTC/USD",
        "quote_currency": "USD", "interval": "1d", "timezone": "UTC",
        "retrieved_at_utc": datetime.now(UTC).isoformat(), "parser": "requests JSON + pandas",
        "parser_version": "btc-quant-acquisition-0.2", "schema": ["timestamp_utc", "open", "high", "low", "close", "volume"], "objects": objects,
        "failures": failures, "rows": len(frame),
        "first_timestamp": frame.timestamp.min().isoformat(),
        "last_timestamp": frame.timestamp.max().isoformat(),
    }
    return frame, manifest


def download_coinbase_recent(output_dir: Path, limit_days: int = 300) -> tuple[pd.DataFrame, dict]:
    """Recent Coinbase BTC-USD candles (API cap 300); preserve source JSON."""
    url = "https://api.exchange.coinbase.com/products/BTC-USD/candles"
    end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=limit_days)
    response = requests.get(url, params={"granularity": 86400, "start": start.isoformat(),
                                         "end": end.isoformat()},
                            headers={"User-Agent": USER_AGENT}, timeout=45)
    response.raise_for_status()
    raw = response.content
    payload = response.json()
    frame = pd.DataFrame(payload, columns=["timestamp", "low", "high", "open", "close", "volume"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="s", utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame[["timestamp", "open", "high", "low", "close", "volume"]]
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    obj = _save_raw(output_dir, "coinbase_btcusd_1d_recent.json", raw, response.url,
                    "Coinbase Exchange candles API", "Coinbase", "BTC-USD", "USD")
    return frame, {"source": obj["source"], "venue": "Coinbase", "symbol": "BTC-USD",
                   "quote_currency": "USD", "interval": "1d", "timezone": "UTC",
                   "retrieved_at_utc": datetime.now(UTC).isoformat(),
                   "parser": "Coinbase candle array parser", "parser_version": "0.2",
                   "objects": [obj], "rows": len(frame),
                   "first_timestamp": frame.timestamp.min().isoformat(),
                   "last_timestamp": frame.timestamp.max().isoformat()}


def download_kraken_recent(output_dir: Path) -> tuple[pd.DataFrame, dict]:
    """Recent Kraken XBT/USD OHLC (public endpoint maximum 720 rows)."""
    url = "https://api.kraken.com/0/public/OHLC"
    response = requests.get(url, params={"pair": "XBTUSD", "interval": 1440},
                            headers={"User-Agent": USER_AGENT}, timeout=45)
    response.raise_for_status()
    raw = response.content
    payload = response.json()
    if payload.get("error"):
        raise RuntimeError(f"Kraken API error: {payload['error']}")
    result = payload["result"]
    key = next(key for key in result if key != "last")
    frame = pd.DataFrame(result[key], columns=[
        "timestamp", "open", "high", "low", "close", "vwap", "volume", "count"
    ])
    frame["timestamp"] = pd.to_datetime(pd.to_numeric(frame["timestamp"]), unit="s", utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame[["timestamp", "open", "high", "low", "close", "volume"]]
    frame = frame[frame.timestamp < pd.Timestamp(datetime.now(UTC).date(), tz="UTC")]
    obj = _save_raw(output_dir, "kraken_btcusd_1d_recent.json", raw, response.url,
                    "Kraken public OHLC API", "Kraken", "XBT/USD", "USD")
    return frame.sort_values("timestamp").reset_index(drop=True), {
        "source": obj["source"], "venue": "Kraken", "symbol": "XBT/USD",
        "quote_currency": "USD", "interval": "1d", "timezone": "UTC",
        "retrieved_at_utc": datetime.now(UTC).isoformat(), "parser": "Kraken OHLC parser",
        "parser_version": "0.2", "objects": [obj], "rows": len(frame),
        "first_timestamp": frame.timestamp.min().isoformat(),
        "last_timestamp": frame.timestamp.max().isoformat()}


def write_manifest(manifests: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"generated_at_utc": datetime.now(UTC).isoformat(),
                                "sources": manifests}, indent=2), encoding="utf-8")
