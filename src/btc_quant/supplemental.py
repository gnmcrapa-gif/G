"""Optional, timestamped BTC market-context feeds; no context feed trains the model yet."""
from __future__ import annotations

import hashlib
import io
import math
import re
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

import pandas as pd
import requests

USER_AGENT = "btc-quant-desk/0.3 research"
BINANCE_FUTURES = "https://fapi.binance.com"
BYBIT_API = "https://api.bybit.com"
DERIBIT_API = "https://www.deribit.com/api/v2"
TFTC_BASE = "https://www.tftc.io/bitcoin-etf-flows"
FRED_GRAPH = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _save_object(directory: Path, filename: str, payload: bytes, *, source: str,
                 url: str, venue: str, symbol: str, quote: str,
                 source_grade: str = "B") -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_bytes(payload)
    return {
        "source": source,
        "url": url,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "file": str(path),
        "size_bytes": len(payload),
        "sha256": _sha256(payload),
        "venue": venue,
        "symbol": symbol,
        "quote_currency": quote,
        "schema_version": "1.0",
        "source_grade": source_grade,
        "license_terms_note": "Public endpoint; provider terms apply; legal review not performed.",
    }


def _request_json(session: requests.Session, method: str, url: str, directory: Path,
                  filename: str, *, params: dict | None = None,
                  body: dict | None = None, source: str, venue: str,
                  symbol: str, quote: str) -> tuple[dict | list, dict]:
    response = session.request(method, url, params=params, json=body, timeout=30)
    response.raise_for_status()
    payload = response.content
    parsed = response.json()
    obj = _save_object(
        directory, filename, payload, source=source, url=response.url,
        venue=venue, symbol=symbol, quote=quote,
    )
    return parsed, obj


def _pct_change(first: float | None, last: float | None) -> float | None:
    if first is None or last is None or first == 0:
        return None
    return (last / first - 1.0) * 100.0


def _timestamp_ms(value) -> str | None:
    try:
        return pd.to_datetime(int(value), unit="ms", utc=True).isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def _spot_live_snapshot(directory: Path) -> tuple[dict, list[dict]]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    objects, summary, errors = [], {}, {}
    sources = (
        ("Binance", "https://api.binance.com/api/v3/ticker/24hr",
         {"symbol": "BTCUSDT"}, "binance_btcusdt_ticker_24h.json"),
        ("Bitstamp", "https://www.bitstamp.net/api/v2/ticker/btcusd/",
         None, "bitstamp_btcusd_ticker_24h.json"),
    )
    for venue, url, params, filename in sources:
        try:
            payload, obj = _request_json(
                session, "GET", url, directory, filename, params=params,
                source=f"{venue} public spot ticker", venue=venue,
                symbol="BTCUSDT" if venue == "Binance" else "BTC/USD",
                quote="USDT" if venue == "Binance" else "USD",
            )
            objects.append(obj)
            if venue == "Binance":
                summary["Binance_BTCUSDT_USDT"] = {
                    "last_trade_price": _float_or_none(payload.get("lastPrice")),
                    "price_change_24h_pct": _float_or_none(payload.get("priceChangePercent")),
                    "base_volume_24h_btc": _float_or_none(payload.get("volume")),
                    "quote_volume_24h_usdt": _float_or_none(payload.get("quoteVolume")),
                    "last_trade_timestamp_utc": _timestamp_ms(payload.get("closeTime")),
                    "snapshot_type": "24h ticker last-trade snapshot",
                }
            else:
                summary["Bitstamp_BTCUSD_USD"] = {
                    "last_trade_price": _float_or_none(payload.get("last")),
                    "price_change_24h_pct": _pct_change(
                        _float_or_none(payload.get("open")), _float_or_none(payload.get("last"))
                    ),
                    "base_volume_24h_btc": _float_or_none(payload.get("volume")),
                    "last_trade_timestamp_utc": (
                        pd.to_datetime(int(payload["timestamp"]), unit="s", utc=True).isoformat()
                        if payload.get("timestamp") else None
                    ),
                    "snapshot_type": "24h ticker last-trade snapshot",
                }
        except Exception as exc:  # noqa: BLE001
            errors[venue] = f"{type(exc).__name__}: {exc}"
    now = datetime.now(UTC)
    for item in summary.values():
        stamp = item.get("last_trade_timestamp_utc")
        try:
            age_seconds = (now - pd.Timestamp(stamp).to_pydatetime()).total_seconds()
        except (TypeError, ValueError):
            age_seconds = None
        item["last_trade_age_seconds"] = age_seconds
        item["status"] = "PASS" if age_seconds is not None and 0 <= age_seconds <= 300 else "STALE"
    fresh_count = sum(item.get("status") == "PASS" for item in summary.values())
    status = (
        "PASS" if len(summary) == 2 and fresh_count == 2
        else "STALE" if len(summary) == 2 and fresh_count == 0
        else "PARTIAL" if summary else "FAIL"
    )
    manifest = {
        "source": "Binance and Bitstamp public spot ticker endpoints",
        "venue": "Binance;Bitstamp", "symbol": "BTCUSDT;BTC/USD",
        "quote_currency": "USDT;USD", "interval": "24h rolling ticker snapshot",
        "timezone": "UTC", "schema_version": "1.0", "source_grade": "A",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "parser": "BTC Quant Desk spot ticker parser", "parser_version": "0.3",
        "schema": ["venue-specific ticker JSON"],
        "objects": objects, "status": status, "errors": errors,
    }
    return {"status": status, "retrieved_at_utc": now.isoformat(),
            "venues": summary, "errors": errors}, [manifest]


def _summarize_hourly_taker_delta(rows: list) -> dict:
    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    closed = sorted(
        [row for row in rows if int(row[6]) < now_ms],
        key=lambda row: int(row[0]),
    )
    result = {"status": "PASS" if len(closed) >= 720 else "PARTIAL", "closed_hourly_bars": len(closed)}
    for label, hours in (("24h", 24), ("7d", 168), ("30d", 720)):
        window = closed[-hours:]
        if len(window) < hours:
            result[label] = {"status": "INSUFFICIENT_BARS", "required_hours": hours, "actual_hours": len(window)}
            continue
        total_volume = sum(float(row[5]) for row in window)
        buy_volume = sum(float(row[9]) for row in window)
        if buy_volume > total_volume + 1e-8:
            raise ValueError("taker-buy base volume exceeds total base volume")
        sell_volume = total_volume - buy_volume
        delta = buy_volume - sell_volume
        result[label] = {
            "status": "PASS",
            "hours": hours,
            "start_candle_open_utc": _timestamp_ms(window[0][0]),
            "end_candle_close_utc": _timestamp_ms(window[-1][6]),
            "total_volume_btc": total_volume,
            "taker_buy_volume_btc": buy_volume,
            "taker_sell_volume_btc": sell_volume,
            "cumulative_delta_btc": delta,
            "delta_pct_of_total_volume": delta / total_volume * 100.0 if total_volume else None,
            "method": "sum(hourly taker-buy base volume minus taker-sell base volume)",
        }
    return result


def _binance_cvd(directory: Path) -> tuple[dict, list[dict]]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    objects, manifests, summaries, errors = [], [], {}, {}
    sources = (
        ("spot", "https://api.binance.com/api/v3/klines", "Binance Spot", "BTCUSDT", "USDT"),
        ("futures", BINANCE_FUTURES + "/fapi/v1/klines", "Binance USD-M Futures", "BTCUSDT", "USDT"),
    )
    for market, url, venue, symbol, quote in sources:
        try:
            rows, obj = _request_json(
                session, "GET", url, directory, f"{market}_btc_cvd_1h_30d.json",
                params={"symbol": symbol, "interval": "1h", "limit": 745},
                source=f"{venue} hourly taker-volume candles",
                venue=venue, symbol=symbol, quote=quote,
            )
            objects.append(obj)
            summaries[market] = _summarize_hourly_taker_delta(rows)
            manifests.append({
                "source": f"{venue} hourly taker-volume candles",
                "venue": venue, "symbol": symbol, "quote_currency": quote,
                "interval": "1h; 24h/7d/30d rolling windows", "timezone": "UTC",
                "schema_version": "1.0", "source_grade": "A",
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "parser": "Binance kline taker-buy/sell volume delta parser",
                "parser_version": "0.3",
                "schema": ["open_time", "open", "high", "low", "close", "base_volume",
                           "close_time", "quote_volume", "trade_count", "taker_buy_base_volume",
                           "taker_buy_quote_volume", "ignore"],
                "objects": [obj], "status": summaries[market]["status"],
            })
        except (requests.RequestException, ValueError, TypeError, IndexError) as exc:
            errors[market] = f"{type(exc).__name__}: {exc}"
            summaries[market] = {"status": "FAIL", "error": errors[market]}
            manifests.append({
                "source": f"{venue} hourly taker-volume candles",
                "venue": venue, "symbol": symbol, "quote_currency": quote,
                "interval": "1h; 24h/7d/30d rolling windows", "timezone": "UTC",
                "schema_version": "1.0", "source_grade": "A",
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "parser": "Binance kline taker-buy/sell volume delta parser",
                "parser_version": "0.3", "schema": [], "objects": [],
                "status": "FAIL", "error": errors[market],
            })
    statuses = [item.get("status") for item in summaries.values()]
    overall = "PASS" if len(statuses) == 2 and all(s == "PASS" for s in statuses) else (
        "PARTIAL" if any(s in {"PASS", "PARTIAL"} for s in statuses) else "FAIL"
    )
    return {
        "status": overall,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "markets": summaries,
        "errors": errors,
        "measurement_note": "Hourly Binance kline taker-buy base volume minus inferred taker-sell base volume for rolling 24h/7d/30d windows; not tick-level order-book delta.",
    }, manifests


def _binance_derivatives(directory: Path) -> tuple[dict, dict]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    objects, errors, raw = [], {}, {}
    specs = {
        "premium_index": ("/fapi/v1/premiumIndex", {"symbol": "BTCUSDT"}),
        "open_interest": ("/fapi/v1/openInterest", {"symbol": "BTCUSDT"}),
        "open_interest_daily_30d": (
            "/futures/data/openInterestHist",
            {"symbol": "BTCUSDT", "period": "1d", "limit": 30},
        ),
        "taker_buy_sell_daily_30d": (
            "/futures/data/takerlongshortRatio",
            {"symbol": "BTCUSDT", "period": "1d", "limit": 30},
        ),
        "global_long_short_account_ratio_daily_30d": (
            "/futures/data/globalLongShortAccountRatio",
            {"symbol": "BTCUSDT", "period": "1d", "limit": 30},
        ),
        "funding_history": ("/fapi/v1/fundingRate", {"symbol": "BTCUSDT", "limit": 1000}),
        "daily_futures_klines": ("/fapi/v1/klines", {"symbol": "BTCUSDT", "interval": "1d", "limit": 31}),
    }
    for key, (path, params) in specs.items():
        try:
            parsed, obj = _request_json(
                session, "GET", BINANCE_FUTURES + path, directory, f"{key}.json",
                params=params, source="Binance USD-M Futures public market data",
                venue="Binance Futures", symbol="BTCUSDT perpetual", quote="USDT",
            )
            raw[key] = parsed
            objects.append(obj)
        except Exception as exc:  # noqa: BLE001 - keep independent feeds visible
            errors[key] = f"{type(exc).__name__}: {exc}"

    summary = {
        "venue": "Binance USD-M Futures",
        "historical_limits": {
            "open_interest_statistics_max_lookback_days": 30,
            "taker_buy_sell_ratio_max_lookback_days": 30,
            "global_account_ratio_max_lookback_days": 30,
            "funding_history_limit_records": 1000,
        },
        "symbol": "BTCUSDT perpetual",
        "quote_currency": "USDT",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "status": (
            "PASS" if all(key in raw for key in (
                "premium_index", "open_interest", "open_interest_daily_30d",
                "taker_buy_sell_daily_30d", "global_long_short_account_ratio_daily_30d",
                "funding_history",
            ))
            else "PARTIAL" if raw else "FAIL"
        ),
        "errors": errors,
    }
    premium = raw.get("premium_index")
    if isinstance(premium, dict):
        summary["mark_price_usdt"] = _float_or_none(premium.get("markPrice"))
        summary["index_price_usdt"] = _float_or_none(premium.get("indexPrice"))
        summary["current_funding_rate"] = _float_or_none(premium.get("lastFundingRate"))
        summary["next_funding_time_utc"] = _timestamp_ms(premium.get("nextFundingTime"))
        summary["funding_rate_unit"] = "fraction per provider funding interval"
    oi = raw.get("open_interest")
    if isinstance(oi, dict):
        summary["open_interest_btc"] = _float_or_none(oi.get("openInterest"))
        summary["open_interest_timestamp_utc"] = _timestamp_ms(oi.get("time"))
    oi_hist = raw.get("open_interest_daily_30d", [])
    if isinstance(oi_hist, list) and oi_hist:
        points = sorted(oi_hist, key=lambda row: int(row.get("timestamp", 0)))
        latest = _float_or_none(points[-1].get("sumOpenInterestValue"))
        summary["open_interest_value_usdt_latest"] = latest
        summary["open_interest_history_latest_timestamp_utc"] = _timestamp_ms(points[-1].get("timestamp"))
        for days in (1, 7, 30):
            target = int(points[-1].get("timestamp", 0)) - days * 86400_000
            prior = min(points, key=lambda row: abs(int(row.get("timestamp", 0)) - target))
            summary[f"open_interest_value_change_{days}d_pct"] = _pct_change(
                _float_or_none(prior.get("sumOpenInterestValue")), latest
            )
    taker = raw.get("taker_buy_sell_daily_30d", [])
    if isinstance(taker, list) and taker:
        latest = max(taker, key=lambda row: int(row.get("timestamp", 0)))
        summary["taker_buy_sell_ratio_latest"] = _float_or_none(latest.get("buySellRatio"))
        summary["taker_buy_volume_btc_latest"] = _float_or_none(latest.get("buyVol"))
        summary["taker_sell_volume_btc_latest"] = _float_or_none(latest.get("sellVol"))
        summary["taker_volume_timestamp_utc"] = _timestamp_ms(latest.get("timestamp"))
        summary["order_flow_measurement"] = (
            "Daily taker buy/sell volume ratio proxy; not a reconstructed cumulative volume delta."
        )
    account_ratio = raw.get("global_long_short_account_ratio_daily_30d", [])
    if isinstance(account_ratio, list) and account_ratio:
        latest = max(account_ratio, key=lambda row: int(row.get("timestamp", 0)))
        summary["global_long_short_account_ratio"] = _float_or_none(latest.get("longShortRatio"))
        summary["global_long_account_share_pct"] = (
            (_float_or_none(latest.get("longAccount")) or 0.0) * 100.0
        )
        summary["global_short_account_share_pct"] = (
            (_float_or_none(latest.get("shortAccount")) or 0.0) * 100.0
        )
        summary["global_long_short_ratio_timestamp_utc"] = _timestamp_ms(latest.get("timestamp"))
    funding = raw.get("funding_history", [])
    if isinstance(funding, list) and funding:
        points = sorted(funding, key=lambda row: int(row.get("fundingTime", 0)))
        summary["last_funding_settlements"] = [
            {
                "timestamp_utc": _timestamp_ms(row.get("fundingTime")),
                "funding_rate": _float_or_none(row.get("fundingRate")),
                "mark_price_usdt": _float_or_none(row.get("markPrice")),
            }
            for row in points[-6:]
        ]
    klines = raw.get("daily_futures_klines", [])
    if isinstance(klines, list) and len(klines) >= 2:
        # The last row is normally the still-forming UTC session; exclude it.
        last_closed = klines[-2]
        summary["last_closed_daily_futures_volume_btc"] = _float_or_none(last_closed[5])
        summary["last_closed_daily_futures_candle_open_utc"] = _timestamp_ms(last_closed[0])
    summary["liquidations"] = {
        "status": "UNAVAILABLE_AUTH_REQUIRED",
        "reason": "Binance forceOrders is a signed USER_DATA endpoint; no private API credentials are configured.",
    }
    manifest = {
        "source": "Binance USD-M Futures public market data",
        "venue": "Binance Futures", "symbol": "BTCUSDT perpetual",
        "quote_currency": "USDT", "interval": "snapshot plus daily history",
        "timezone": "UTC", "schema_version": "1.0", "source_grade": "A",
        "retrieved_at_utc": summary["retrieved_at_utc"],
        "parser": "BTC Quant Desk JSON market-data parser", "parser_version": "0.3",
        "schema": ["provider JSON; endpoint-specific fields preserved in raw objects"],
        "objects": objects, "status": summary["status"], "errors": errors,
    }
    return summary, manifest


def _bybit_derivatives(directory: Path) -> tuple[dict, dict]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    objects, errors, raw = [], {}, {}
    specs = {
        "ticker": ("/v5/market/tickers", {"category": "linear", "symbol": "BTCUSDT"}),
        "open_interest_daily_200d": (
            "/v5/market/open-interest",
            {"category": "linear", "symbol": "BTCUSDT", "intervalTime": "1d", "limit": 200},
        ),
        "global_account_ratio_daily_30d": (
            "/v5/market/account-ratio",
            {"category": "linear", "symbol": "BTCUSDT", "period": "1d", "limit": 30},
        ),
        "funding_history": (
            "/v5/market/funding/history",
            {"category": "linear", "symbol": "BTCUSDT", "limit": 200},
        ),
    }
    for key, (path, params) in specs.items():
        try:
            parsed, obj = _request_json(
                session, "GET", BYBIT_API + path, directory, f"{key}.json",
                params=params, source="Bybit V5 public market data",
                venue="Bybit Linear", symbol="BTCUSDT perpetual", quote="USDT",
            )
            if parsed.get("retCode") != 0:
                raise RuntimeError(f"Bybit retCode={parsed.get('retCode')} retMsg={parsed.get('retMsg')}")
            raw[key] = parsed.get("result", {})
            objects.append(obj)
        except Exception as exc:  # noqa: BLE001
            errors[key] = f"{type(exc).__name__}: {exc}"
    summary = {
        "venue": "Bybit Linear",
        "symbol": "BTCUSDT perpetual",
        "quote_currency": "USDT",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "status": (
            "PASS" if all(key in raw for key in (
                "ticker", "open_interest_daily_200d", "global_account_ratio_daily_30d",
                "funding_history",
            ))
            else "PARTIAL" if raw else "FAIL"
        ),
        "errors": errors,
    }
    ticker_rows = raw.get("ticker", {}).get("list", [])
    if ticker_rows:
        ticker = ticker_rows[0]
        summary.update({
            "last_price_usdt": _float_or_none(ticker.get("lastPrice")),
            "mark_price_usdt": _float_or_none(ticker.get("markPrice")),
            "index_price_usdt": _float_or_none(ticker.get("indexPrice")),
            "open_interest_btc": _float_or_none(ticker.get("openInterest")),
            "open_interest_value_usdt": _float_or_none(ticker.get("openInterestValue")),
            "funding_rate_current": _float_or_none(ticker.get("fundingRate")),
            "funding_rate_unit": "fraction per provider funding interval",
            "volume_24h_btc": _float_or_none(ticker.get("volume24h")),
            "turnover_24h_usdt": _float_or_none(ticker.get("turnover24h")),
        })
    oi_rows = raw.get("open_interest_daily_200d", {}).get("list", [])
    if oi_rows:
        points = sorted(oi_rows, key=lambda row: int(row.get("timestamp", 0)))
        latest = _float_or_none(points[-1].get("openInterest"))
        summary["open_interest_history_latest_timestamp_utc"] = _timestamp_ms(points[-1].get("timestamp"))
        summary["open_interest_history_latest_btc"] = latest
        for days in (1, 7, 30, 90, 180):
            target = int(points[-1].get("timestamp", 0)) - days * 86400_000
            prior = min(points, key=lambda row: abs(int(row.get("timestamp", 0)) - target))
            actual_days = (
                int(points[-1].get("timestamp", 0)) - int(prior.get("timestamp", 0))
            ) / 86400_000
            summary[f"open_interest_history_change_{days}d_pct"] = (
                _pct_change(_float_or_none(prior.get("openInterest")), latest)
                if actual_days >= max(1, days - 2) else None
            )
        summary["open_interest_history_max_days"] = (
            int(points[-1].get("timestamp", 0)) - int(points[0].get("timestamp", 0))
        ) / 86400_000
    account_rows = raw.get("global_account_ratio_daily_30d", {}).get("list", [])
    if account_rows:
        latest = max(account_rows, key=lambda row: int(row.get("timestamp", 0)))
        summary["global_long_short_account_ratio"] = _float_or_none(latest.get("buyRatio")) / (
            _float_or_none(latest.get("sellRatio")) or 1.0
        )
        summary["global_long_account_share_pct"] = (
            (_float_or_none(latest.get("buyRatio")) or 0.0) * 100.0
        )
        summary["global_short_account_share_pct"] = (
            (_float_or_none(latest.get("sellRatio")) or 0.0) * 100.0
        )
        summary["global_long_short_ratio_timestamp_utc"] = _timestamp_ms(latest.get("timestamp"))
    funding_rows = raw.get("funding_history", {}).get("list", [])
    if funding_rows:
        points = sorted(funding_rows, key=lambda row: int(row.get("fundingRateTimestamp", 0)))
        summary["last_funding_settlements"] = [
            {
                "timestamp_utc": _timestamp_ms(row.get("fundingRateTimestamp")),
                "funding_rate": _float_or_none(row.get("fundingRate")),
            }
            for row in points[-6:]
        ]
    manifest = {
        "source": "Bybit V5 public market data",
        "venue": "Bybit Linear", "symbol": "BTCUSDT perpetual",
        "quote_currency": "USDT", "interval": "snapshot plus daily history",
        "timezone": "UTC", "schema_version": "1.0", "source_grade": "A",
        "retrieved_at_utc": summary["retrieved_at_utc"],
        "parser": "BTC Quant Desk Bybit V5 parser", "parser_version": "0.3",
        "schema": ["provider JSON; endpoint-specific fields preserved in raw objects"],
        "objects": objects, "status": summary["status"], "errors": errors,
    }
    return summary, manifest


def _float_or_none(value) -> float | None:
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _parse_deribit_instrument(name: str) -> tuple[str, float, str] | None:
    parts = name.split("-")
    if len(parts) != 4:
        return None
    try:
        expiry = datetime.strptime(parts[1].upper(), "%d%b%y").date().isoformat()
        strike = float(parts[2])
    except ValueError:
        return None
    option_type = parts[3].upper()
    if option_type not in {"C", "P"}:
        return None
    return expiry, strike, option_type


def _deribit_options(directory: Path) -> tuple[dict, dict]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    objects = []
    url = DERIBIT_API + "/public/get_book_summary_by_currency"
    payload, obj = _request_json(
        session, "POST", url, directory, "btc_options_book_summary.json",
        body={"jsonrpc": "2.0", "id": 1, "method": "public/get_book_summary_by_currency",
              "params": {"currency": "BTC", "kind": "option"}},
        source="Deribit public options market data", venue="Deribit Options",
        symbol="BTC options", quote="BTC/USD",
    )
    if payload.get("error"):
        raise RuntimeError(f"Deribit API error: {payload['error']}")
    objects.append(obj)
    rows = payload.get("result", [])
    parsed_rows = []
    for row in rows:
        parsed = _parse_deribit_instrument(str(row.get("instrument_name", "")))
        if not parsed:
            continue
        expiry, strike, option_type = parsed
        parsed_rows.append({**row, "expiry_date": expiry, "strike": strike, "option_type": option_type})
    if not parsed_rows:
        raise RuntimeError("Deribit returned no parseable active BTC option instruments")

    by_expiry: dict[str, dict] = {}
    by_strike: dict[tuple[str, float], dict] = {}
    for row in parsed_rows:
        expiry, strike, side = row["expiry_date"], row["strike"], row["option_type"]
        oi = _float_or_none(row.get("open_interest")) or 0.0
        volume_usd = _float_or_none(row.get("volume_usd")) or 0.0
        block = by_expiry.setdefault(expiry, {
            "expiry_date": expiry, "call_open_interest_btc": 0.0,
            "put_open_interest_btc": 0.0, "call_volume_usd_24h": 0.0,
            "put_volume_usd_24h": 0.0, "options": [],
        })
        block["call_open_interest_btc" if side == "C" else "put_open_interest_btc"] += oi
        block["call_volume_usd_24h" if side == "C" else "put_volume_usd_24h"] += volume_usd
        block["options"].append(row)
        strike_block = by_strike.setdefault((expiry, strike), {
            "expiry_date": expiry, "strike_usd": strike,
            "call_open_interest_btc": 0.0, "put_open_interest_btc": 0.0,
        })
        strike_block["call_open_interest_btc" if side == "C" else "put_open_interest_btc"] += oi

    expiry_rows = []
    now_date = datetime.now(UTC).date()
    for expiry, block in sorted(by_expiry.items()):
        opts = block.pop("options")
        underlying = next((_float_or_none(row.get("underlying_price")) for row in opts
                           if _float_or_none(row.get("underlying_price"))), None)
        atm_candidates = [row for row in opts if underlying and row["strike"] > 0]
        atm = min(atm_candidates, key=lambda row: abs(math.log(row["strike"] / underlying))) if atm_candidates else None
        dte = (date.fromisoformat(expiry) - now_date).days
        expiry_rows.append({
            **block,
            "days_to_expiry": dte,
            "underlying_price_usd": underlying,
            "nearest_atm_instrument": atm.get("instrument_name") if atm else None,
            "nearest_atm_mark_iv_pct": _float_or_none(atm.get("mark_iv")) if atm else None,
        })

    total_call_oi = sum(row["call_open_interest_btc"] for row in expiry_rows)
    total_put_oi = sum(row["put_open_interest_btc"] for row in expiry_rows)
    total_call_volume = sum(row["call_volume_usd_24h"] for row in expiry_rows)
    total_put_volume = sum(row["put_volume_usd_24h"] for row in expiry_rows)
    top_strikes = sorted(
        (dict(row) for row in by_strike.values()),
        key=lambda row: row["call_open_interest_btc"] + row["put_open_interest_btc"],
        reverse=True,
    )[:40]

    # Query Greeks only for a bounded set of near-ATM contracts in the nearest four expiries.
    ticker_rows = []
    ticker_errors = []
    selected_expiries = [row["expiry_date"] for row in expiry_rows if row["days_to_expiry"] >= 0][:4]
    for expiry in selected_expiries:
        options = [row for row in parsed_rows if row["expiry_date"] == expiry]
        underlying = next((_float_or_none(row.get("underlying_price")) for row in options
                           if _float_or_none(row.get("underlying_price"))), None)
        if not underlying:
            continue
        selected = []
        for side, targets in (("P", (0.85, 0.90, 0.95)), ("C", (1.05, 1.10, 1.15))):
            candidates = [row for row in options if row["option_type"] == side]
            for target in targets:
                if candidates:
                    selected.append(min(candidates, key=lambda row: abs(row["strike"] / underlying - target)))
        unique = {row["instrument_name"]: row for row in selected}
        for instrument in unique:
            try:
                ticker_payload, ticker_obj = _request_json(
                    session, "POST", DERIBIT_API + "/public/ticker", directory,
                    f"ticker_{instrument.replace('-', '_')}.json",
                    body={"jsonrpc": "2.0", "id": 2, "method": "public/ticker",
                          "params": {"instrument_name": instrument}},
                    source="Deribit public options ticker/Greeks",
                    venue="Deribit Options", symbol=instrument, quote="BTC/USD",
                )
                objects.append(ticker_obj)
                ticker = ticker_payload.get("result", {})
                greeks = ticker.get("greeks") or {}
                ticker_rows.append({
                    "instrument_name": instrument, "expiry_date": expiry,
                    "option_type": "call" if instrument.endswith("-C") else "put",
                    "delta": _float_or_none(greeks.get("delta")),
                    "gamma": _float_or_none(greeks.get("gamma")),
                    "mark_iv_pct": _float_or_none(ticker.get("mark_iv")),
                    "ticker_timestamp_utc": _timestamp_ms(ticker.get("timestamp")),
                })
            except (requests.RequestException, ValueError, RuntimeError, KeyError, TypeError) as exc:
                ticker_errors.append({
                    "instrument_name": instrument,
                    "error": f"{type(exc).__name__}: {exc}",
                })
                continue

    skew_by_expiry = []
    for expiry in selected_expiries:
        candidates = [row for row in ticker_rows if row["expiry_date"] == expiry and row["delta"] is not None]
        calls = [row for row in candidates if row["option_type"] == "call" and 0.15 <= row["delta"] <= 0.35]
        puts = [row for row in candidates if row["option_type"] == "put" and -0.35 <= row["delta"] <= -0.15]
        call = min(calls, key=lambda row: abs(row["delta"] - 0.25)) if calls else None
        put = min(puts, key=lambda row: abs(row["delta"] + 0.25)) if puts else None
        skew_by_expiry.append({
            "expiry_date": expiry,
            "call_25d_instrument": call["instrument_name"] if call else None,
            "put_25d_instrument": put["instrument_name"] if put else None,
            "call_25d_mark_iv_pct": call["mark_iv_pct"] if call else None,
            "put_25d_mark_iv_pct": put["mark_iv_pct"] if put else None,
            "put_minus_call_25d_skew_vol_points": (
                put["mark_iv_pct"] - call["mark_iv_pct"]
                if call and put and call["mark_iv_pct"] is not None and put["mark_iv_pct"] is not None
                else None
            ),
            "greeks_samples": [row for row in candidates],
        })

    skew_available = any(
        row.get("put_minus_call_25d_skew_vol_points") is not None
        for row in skew_by_expiry
    )
    summary = {
        "status": "PASS" if skew_available else "PARTIAL",
        "venue": "Deribit",
        "instrument_scope": "active BTC options",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "open_interest_unit": "BTC underlying base currency; provider reports an 8-hour delay",
        "implied_volatility_unit": "percent",
        "total_call_open_interest_btc": total_call_oi,
        "total_put_open_interest_btc": total_put_oi,
        "put_call_open_interest_ratio": total_put_oi / total_call_oi if total_call_oi else None,
        "total_call_volume_usd_24h": total_call_volume,
        "total_put_volume_usd_24h": total_put_volume,
        "put_call_volume_ratio": total_put_volume / total_call_volume if total_call_volume else None,
        "expiry_term_structure": expiry_rows,
        "top_strikes_by_open_interest": top_strikes,
        "sampled_25d_skew": skew_by_expiry,
        "dealer_gamma_positioning": {
            "status": "NOT_IDENTIFIABLE",
            "reason": "Public open interest and option Greeks do not reveal whether dealers are net long or short; no dealer-side sign is inferred.",
        },
        "ticker_greeks_sample_count": len(ticker_rows),
        "ticker_greeks_errors": ticker_errors,
        "greeks_status": "PASS" if ticker_rows else "UNAVAILABLE",
        "raw_option_instruments": len(parsed_rows),
        "open_interest_delay_hours": 8,
    }
    manifest = {
        "source": "Deribit public BTC options API", "venue": "Deribit Options",
        "symbol": "BTC options chain", "quote_currency": "BTC/USD",
        "interval": "live chain snapshot; open interest delayed 8h",
        "timezone": "UTC", "schema_version": "1.0", "source_grade": "A",
        "retrieved_at_utc": summary["retrieved_at_utc"],
        "parser": "Deribit JSON-RPC chain and ticker parser", "parser_version": "0.3",
        "schema": ["instrument_name", "expiry", "strike", "option_type", "open_interest", "mark_iv", "ticker greeks"],
        "objects": objects,
    }
    return summary, manifest


def _find_etf_sessions(payload) -> list[dict]:
    candidates = []

    def walk(value):
        if isinstance(value, list):
            rows = [row for row in value if isinstance(row, dict)]
            if rows and sum("date" in row and "netFlowUsd" in row for row in rows) >= max(1, int(len(rows) * 0.8)):
                candidates.append(rows)
            for row in value:
                walk(row)
        elif isinstance(value, dict):
            for child in value.values():
                walk(child)

    walk(payload)
    return max(candidates, key=len) if candidates else []


def _etf_flows(directory: Path) -> tuple[dict, dict]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    objects = []
    latest_url = TFTC_BASE + "/latest.json"
    latest_response = session.get(latest_url, timeout=30)
    latest_response.raise_for_status()
    latest_raw = latest_response.content
    latest = latest_response.json()
    objects.append(_save_object(
        directory, "us_spot_btc_etf_latest.json", latest_raw,
        source="The Commoner Bitcoin ETF Tracker by TFTC",
        url=latest_response.url, venue="US spot Bitcoin ETFs", symbol="aggregate",
        quote="USD", source_grade="B",
    ))
    data_url = TFTC_BASE + "/data.json"
    full_history_error = None
    data_payload = {}
    try:
        data_response = session.get(data_url, timeout=30)
        data_response.raise_for_status()
        data_raw = data_response.content
        data_payload = data_response.json()
        objects.append(_save_object(
            directory, "us_spot_btc_etf_full_history.json", data_raw,
            source="The Commoner Bitcoin ETF Tracker by TFTC",
            url=data_response.url, venue="US spot Bitcoin ETFs", symbol="daily history",
            quote="USD", source_grade="B",
        ))
    except (requests.RequestException, ValueError) as exc:
        full_history_error = f"{type(exc).__name__}: {exc}"
    latest_session = latest.get("latestSession") or {}
    updated_through = latest.get("updatedThrough") or latest_session.get("date")
    sessions = _find_etf_sessions(data_payload)
    if not sessions:
        sessions = latest.get("recentSessions") or []
    sessions = sorted(sessions, key=lambda row: row.get("date", ""))
    latest_date = date.fromisoformat(str(updated_through)[:10]) if updated_through else None
    today = datetime.now(UTC).date()
    business_days_old = 0
    if latest_date:
        cursor = latest_date + timedelta(days=1)
        while cursor <= today:
            if cursor.weekday() < 5:
                business_days_old += 1
            cursor += timedelta(days=1)
    recent_21 = sessions[-21:]
    recent_30 = sessions[-30:]
    full_history_available = len(sessions) >= 30
    summary = {
        "source": latest.get("attribution", "The Commoner Bitcoin ETF Tracker by TFTC"),
        "source_url": latest_url,
        "license": latest.get("license"),
        "status": (
            "STALE" if business_days_old > 1
            else "PASS" if full_history_available
            else "PARTIAL"
        ),
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "updated_through": updated_through,
        "business_sessions_behind_approx": business_days_old,
        "latest_session": latest_session,
        "cumulative_net_flow_usd": _float_or_none(latest.get("cumulativeNetFlowUsd")),
        "last_21_sessions_net_flow_usd": (
            sum(_float_or_none(row.get("netFlowUsd")) or 0.0 for row in recent_21)
            if len(recent_21) >= 21 else None
        ),
        "last_30_sessions_net_flow_usd": (
            sum(_float_or_none(row.get("netFlowUsd")) or 0.0 for row in recent_30)
            if len(recent_30) >= 30 else None
        ),
        "history_rows_available": len(sessions),
        "history_coverage_start": sessions[0].get("date") if sessions else None,
        "full_history_error": full_history_error,
        "global_etp_flows": {
            "status": "UNAVAILABLE",
            "reason": "This dataset covers US spot ETFs only; global ETPs require a separate source.",
        },
    }
    manifest = {
        "source": "The Commoner Bitcoin ETF Tracker by TFTC",
        "venue": "US spot Bitcoin ETFs", "symbol": "US spot BTC ETFs aggregate",
        "quote_currency": "USD", "interval": "US trading sessions",
        "timezone": "US session date; update timestamp in UTC",
        "schema_version": "1.0", "source_grade": "B",
        "license": latest.get("license"),
        "attribution": latest.get("attribution"),
        "retrieved_at_utc": summary["retrieved_at_utc"],
        "parser": "TFTC open JSON recursive session parser", "parser_version": "0.3",
        "schema": ["date", "netFlowUsd", "vendorNetFlowUsd", "totalNetAssetsUsd", "perEtfUsd"],
        "objects": objects,
        "updated_through": updated_through,
        "status": summary["status"],
    }
    return summary, manifest


FRED_SERIES = {
    "DGS2": {"label": "US Treasury 2Y yield", "unit": "percent", "max_age_days": 5, "lookback_days": 365},
    "DGS10": {"label": "US Treasury 10Y yield", "unit": "percent", "max_age_days": 5, "lookback_days": 365},
    "DFII10": {"label": "US 10Y real yield", "unit": "percent", "max_age_days": 5, "lookback_days": 365},
    "FEDFUNDS": {"label": "Federal funds effective rate", "unit": "percent", "max_age_days": 45, "lookback_days": 1825},
    "CPIAUCSL": {"label": "US CPI index", "unit": "index 1982-84=100", "max_age_days": 45, "lookback_days": 1825},
    "PCEPILFE": {"label": "US core PCE price index", "unit": "index 2017=100", "max_age_days": 45, "lookback_days": 1825},
    "UNRATE": {"label": "US unemployment rate", "unit": "percent", "max_age_days": 45, "lookback_days": 1825},
    "PAYEMS": {"label": "US nonfarm payrolls", "unit": "thousands of persons", "max_age_days": 45, "lookback_days": 1825},
    "DTWEXBGS": {"label": "US broad trade-weighted dollar index (not ICE DXY)", "unit": "index", "max_age_days": 10, "lookback_days": 365},
    "WALCL": {"label": "Federal Reserve total assets", "unit": "millions of USD", "max_age_days": 14, "lookback_days": 365},
    "RRPONTSYD": {"label": "Overnight reverse repo take-up", "unit": "billions of USD", "max_age_days": 10, "lookback_days": 365},
    "NFCI": {"label": "Chicago Fed National Financial Conditions Index", "unit": "index", "max_age_days": 14, "lookback_days": 365},
    "SP500": {"label": "S&P 500 index", "unit": "index points", "max_age_days": 5, "lookback_days": 365},
    "NASDAQCOM": {"label": "NASDAQ Composite index", "unit": "index points", "max_age_days": 5, "lookback_days": 365},
    "VIXCLS": {"label": "CBOE VIX", "unit": "index points", "max_age_days": 5, "lookback_days": 365},
    "M2SL": {"label": "US M2 money stock", "unit": "billions of USD", "max_age_days": 45, "lookback_days": 1825},
}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse_rss_articles(payload: bytes, source: str) -> list[dict]:
    root = ET.fromstring(payload)
    articles = []
    for element in root.iter():
        if _local_name(element.tag) not in {"item", "entry"}:
            continue
        values = {_local_name(child.tag): (child.text or "").strip() for child in element}
        links = [
            child.attrib.get("href")
            for child in element
            if _local_name(child.tag) == "link" and child.attrib.get("href")
        ]
        link = values.get("link") or (links[0] if links else None)
        title = values.get("title")
        date_text = values.get("pubDate") or values.get("published") or values.get("updated")
        published = None
        if date_text:
            try:
                parsed = parsedate_to_datetime(date_text)
                published = parsed.astimezone(UTC).isoformat()
            except (TypeError, ValueError, OverflowError):
                try:
                    published = pd.to_datetime(date_text, utc=True).isoformat()
                except (TypeError, ValueError):
                    published = None
        description = values.get("description") or values.get("summary") or ""
        description = unescape(re.sub(r"<[^>]+>", " ", description))
        description = " ".join(description.split())[:500]
        if title and link:
            articles.append({
                "title": unescape(title),
                "url": link,
                "published_at_utc": published,
                "source": source,
                "snippet": description,
                "date_semantics": "publisher RSS publication/update date",
            })
    return articles


def _news_keyword_tags(title: str, snippet: str = "") -> list[str]:
    text = f"{title} {snippet}".lower()
    groups = {
        "regulatory": ("sec", "cftc", "regulation", "regulatory", "legislation", "court", "mica", "law"),
        "macro_monetary": ("federal reserve", "fomc", "inflation", "cpi", "treasury", "yield", "interest rate", "payroll"),
        "geopolitical": ("war", "sanctions", "election", "tariff", "conflict", "ceasefire", "ukraine", "iran", "israel", "russia"),
        "crypto": ("bitcoin", "crypto", "digital asset", "etf", "exchange"),
    }
    return [tag for tag, words in groups.items() if any(word in text for word in words)]


def _news_context(directory: Path) -> tuple[dict, list[dict]]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    directory.mkdir(parents=True, exist_ok=True)
    objects, manifests, errors, articles, source_status = [], [], {}, [], {}
    feeds = {
        "Federal Reserve": "https://www.federalreserve.gov/feeds/press_all.xml",
        "SEC": "https://www.sec.gov/news/pressreleases.rss",
        "White House": "https://www.whitehouse.gov/news/feed/",
        "ECB": "https://www.ecb.europa.eu/rss/press.html",
    }
    for name, url in feeds.items():
        obj = None
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            raw = response.content
            obj = _save_object(
                directory, f"rss_{name.lower().replace(' ', '_')}.xml", raw,
                source=f"{name} official RSS feed", url=response.url,
                venue=name, symbol="official releases", quote="not_applicable",
                source_grade="A",
            )
            objects.append(obj)
            feed_articles = _parse_rss_articles(raw, name)
            articles.extend(feed_articles[:15])
            source_status[name] = {"status": "PASS", "article_count": len(feed_articles)}
            manifests.append({
                "source": f"{name} official RSS feed", "venue": name,
                "symbol": "official releases", "quote_currency": "not_applicable",
                "interval": "latest publisher RSS items", "timezone": "publisher date normalized to UTC",
                "schema_version": "1.0", "source_grade": "A",
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "parser": "ElementTree RSS/Atom parser", "parser_version": "0.3",
                "schema": ["title", "link", "pubDate/published/updated", "description/summary"],
                "objects": [obj], "status": "PASS",
            })
        except (requests.RequestException, ET.ParseError, ValueError) as exc:
            errors[name] = f"{type(exc).__name__}: {exc}"
            source_status[name] = {"status": "FAIL", "error": errors[name]}
            manifests.append({
                "source": f"{name} official RSS feed", "venue": name,
                "symbol": "official releases", "quote_currency": "not_applicable",
                "interval": "latest publisher RSS items", "timezone": "publisher date normalized to UTC",
                "schema_version": "1.0", "source_grade": "A",
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "parser": "ElementTree RSS/Atom parser", "parser_version": "0.3",
                "schema": ["raw XML retained; parsing failed"] if obj else [],
                "objects": [obj] if obj else [], "status": "FAIL",
                "error": errors[name],
            })
    source_status["CFTC"] = {
        "status": "UNAVAILABLE",
        "reason": "CFTC reports its RSS feeds temporarily disabled as of October 2026.",
    }

    gdelt_url = "https://api.gdeltproject.org/api/v2/doc/doc"
    gdelt_obj = None
    try:
        response = session.get(
            gdelt_url,
            params={
                "query": '(Bitcoin OR cryptocurrency OR "digital assets" OR ETF OR SEC OR CFTC OR '
                         'Federal Reserve OR FOMC OR sanctions OR election OR tariff OR war OR conflict)',
                "mode": "ArtList", "format": "json", "maxrecords": 50,
                "timespan": "7d", "sort": "DateDesc",
            },
            timeout=45,
        )
        response.raise_for_status()
        raw = response.content
        gdelt_obj = _save_object(
            directory, "gdelt_doc_articles_7d.json", raw,
            source="GDELT DOC 2.0 article search", url=response.url,
            venue="Global news aggregator", symbol="BTC/macro/regulation/geopolitics",
            quote="not_applicable", source_grade="C",
        )
        objects.append(gdelt_obj)
        payload = response.json()
        gdelt_rows = payload.get("articles", [])
        for row in gdelt_rows:
            try:
                seen_at = (
                    pd.to_datetime(row.get("seendate"), format="%Y%m%dT%H%M%SZ", utc=True).isoformat()
                    if row.get("seendate") else None
                )
            except (TypeError, ValueError):
                seen_at = None
            articles.append({
                "title": row.get("title"),
                "url": row.get("url"),
                "seen_at_utc": seen_at,
                "source": row.get("domain", "GDELT"),
                "source_country": row.get("sourcecountry"),
                "language": row.get("language"),
                "date_semantics": "GDELT first-seen timestamp, not publisher publication time",
            })
        source_status["GDELT"] = {"status": "PASS", "article_count": len(gdelt_rows)}
        manifests.append({
            "source": "GDELT DOC 2.0 article search", "venue": "Global news aggregator",
            "symbol": "BTC/macro/regulation/geopolitics", "quote_currency": "not_applicable",
            "interval": "rolling 7d", "timezone": "GDELT seendate UTC",
            "schema_version": "1.0", "source_grade": "C",
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
            "parser": "GDELT DOC JSON parser", "parser_version": "0.3",
            "schema": ["title", "url", "seendate", "domain", "sourcecountry", "language"],
            "objects": [gdelt_obj], "status": "PASS",
        })
    except (requests.RequestException, ValueError, TypeError) as exc:
        errors["GDELT"] = f"{type(exc).__name__}: {exc}"
        source_status["GDELT"] = {"status": "FAIL", "error": errors["GDELT"]}
        manifests.append({
            "source": "GDELT DOC 2.0 article search", "venue": "Global news aggregator",
            "symbol": "BTC/macro/regulation/geopolitics", "quote_currency": "not_applicable",
            "interval": "rolling 7d", "timezone": "GDELT seendate UTC",
            "schema_version": "1.0", "source_grade": "C",
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
            "parser": "GDELT DOC JSON parser", "parser_version": "0.3",
            "schema": ["raw JSON retained; parsing failed"] if gdelt_obj else [],
            "objects": [gdelt_obj] if gdelt_obj else [], "status": "FAIL",
            "error": errors["GDELT"],
        })

    deduped = {}
    for article in articles:
        key = article.get("url") or article.get("title")
        if key and article.get("title"):
            article["keyword_tags"] = _news_keyword_tags(article["title"], article.get("snippet", ""))
            deduped[key] = article
    final_articles = sorted(
        deduped.values(),
        key=lambda row: row.get("published_at_utc") or row.get("seen_at_utc") or "",
        reverse=True,
    )[:30]
    official_passes = sum(
        source_status.get(name, {}).get("status") == "PASS"
        for name in feeds
    )
    gdelt_pass = source_status.get("GDELT", {}).get("status") == "PASS"
    status = "PASS" if gdelt_pass and official_passes >= 1 else (
        "PARTIAL" if gdelt_pass or official_passes else "FAIL"
    )
    summary = {
        "status": status,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "window": "7d for GDELT; latest items for official RSS",
        "articles": final_articles,
        "source_status": source_status,
        "errors": errors,
        "interpretation_limit": "Headlines and keyword tags are descriptive only; no sentiment, event-impact score or trading signal is inferred.",
    }
    return summary, manifests


def _flow_millions(value_text: str, direction: str) -> float:
    value = float(re.sub(r"[,\s]", "", value_text))
    return -abs(value) if direction.lower() == "outflows" else abs(value)


def _parse_bitwise_weekly_flows(
    html_payload: bytes, report_year: int, report_week: int
) -> dict:
    html_text = html_payload.decode("utf-8", errors="replace")
    clean = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", html_text, flags=re.I | re.S)
    text_content = unescape(re.sub(r"<[^>]+>", " ", clean))
    text_content = re.sub(r"\s+", " ", text_content)

    global_crypto = re.search(
        r"Global crypto ETPs experienced around\s*([+-]?\s*[\d,.]+)\s*mn USD in net\s*(inflows|outflows)",
        text_content, re.I,
    )
    global_btc = re.search(
        r"Global Bitcoin ETPs experienced net\s*(inflows|outflows)\s*of\s*([+-]?\s*[\d,.]+)\s*mn USD",
        text_content, re.I,
    )
    us_spot_btc = re.search(
        r"of which\s*([+-]?\s*[\d,.]+)\s*mn USD in net\s*(inflows|outflows)\s*were related to US spot Bitcoin ETFs",
        text_content, re.I,
    )
    if not global_crypto and not global_btc:
        raise ValueError("Bitwise weekly page did not expose parseable global ETP flow statements")

    published = re.search(
        r'<meta[^>]+(?:property|name)=["\'](?:article:published_time|datePublished)["\'][^>]+content=["\']([^"\']+)',
        html_text, re.I,
    )
    published_at = None
    if published:
        try:
            published_at = pd.to_datetime(published.group(1), utc=True).isoformat()
        except (TypeError, ValueError):
            published_at = None
    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_text, re.I | re.S)
    title = unescape(re.sub(r"<[^>]+>", " ", title_match.group(1))).strip() if title_match else None

    global_crypto_value = (
        _flow_millions(global_crypto.group(1), global_crypto.group(2))
        if global_crypto else None
    )
    global_btc_value = (
        _flow_millions(global_btc.group(2), global_btc.group(1))
        if global_btc else None
    )
    us_spot_value = (
        _flow_millions(us_spot_btc.group(1), us_spot_btc.group(2))
        if us_spot_btc else None
    )
    return {
        "report_week": f"{report_year}-W{report_week:02d}",
        "report_year": report_year,
        "report_week_number": report_week,
        "published_at_utc": published_at,
        "title": title,
        "global_crypto_etp_weekly_flow_usd_mn": global_crypto_value,
        "global_bitcoin_etp_weekly_flow_usd_mn": global_btc_value,
        "us_spot_bitcoin_etf_component_usd_mn": us_spot_value,
        "non_us_bitcoin_etp_residual_usd_mn": (
            global_btc_value - us_spot_value
            if global_btc_value is not None and us_spot_value is not None else None
        ),
        "flow_period_label": "last week, as stated by publisher; exact session dates not independently reconstructed",
        "status": "PASS" if global_crypto_value is not None and global_btc_value is not None else "PARTIAL",
    }


def _global_etp_weekly(directory: Path) -> tuple[dict, list[dict]]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    objects, manifests, errors, history = [], [], {}, []
    today = datetime.now(UTC).date()
    attempted = []
    for offset in range(6):
        week_date = today - timedelta(weeks=offset)
        iso = week_date.isocalendar()
        year, week = iso.year, iso.week
        if (year, week) in attempted:
            continue
        attempted.append((year, week))
        url = (
            "https://bitwiseinvestments.eu/blog/regular-updates/"
            f"Bitwise_Crypto_Market_Compass_{year}_{week:02d}/"
        )
        try:
            response = session.get(url, timeout=30)
            if response.status_code == 404:
                errors[f"{year}-W{week:02d}"] = "HTTP 404: weekly report not published at expected URL"
                continue
            response.raise_for_status()
            raw = response.content
            obj = _save_object(
                directory, f"bitwise_crypto_market_compass_{year}_w{week:02d}.html", raw,
                source="Bitwise Europe Weekly Crypto Market Compass",
                url=response.url, venue="Global crypto ETPs", symbol=f"{year}-W{week:02d}",
                quote="USD millions", source_grade="B",
            )
            objects.append(obj)
            parsed = _parse_bitwise_weekly_flows(raw, year, week)
            parsed["source_url"] = response.url
            parsed["retrieved_at_utc"] = obj["retrieved_at_utc"]
            history.append(parsed)
            manifests.append({
                "source": "Bitwise Europe Weekly Crypto Market Compass",
                "venue": "Global crypto ETPs", "symbol": f"{year}-W{week:02d}",
                "quote_currency": "USD millions", "interval": "weekly",
                "timezone": "publisher report date", "schema_version": "1.0",
                "source_grade": "B", "retrieved_at_utc": obj["retrieved_at_utc"],
                "parser": "Bitwise weekly ETP flow statement parser", "parser_version": "0.3",
                "schema": [
                    "global_crypto_etp_weekly_flow_usd_mn",
                    "global_bitcoin_etp_weekly_flow_usd_mn",
                    "us_spot_bitcoin_etf_component_usd_mn",
                    "non_us_bitcoin_etp_residual_usd_mn",
                    "published_at_utc",
                ],
                "objects": [obj], "status": parsed["status"],
            })
            if len(history) >= 4:
                break
        except (requests.RequestException, ValueError) as exc:
            errors[f"{year}-W{week:02d}"] = f"{type(exc).__name__}: {exc}"
            if "obj" in locals() and obj:
                manifests.append({
                    "source": "Bitwise Europe Weekly Crypto Market Compass",
                    "venue": "Global crypto ETPs", "symbol": f"{year}-W{week:02d}",
                    "quote_currency": "USD millions", "interval": "weekly",
                    "timezone": "publisher report date", "schema_version": "1.0",
                    "source_grade": "B", "retrieved_at_utc": obj["retrieved_at_utc"],
                    "parser": "Bitwise weekly ETP flow statement parser", "parser_version": "0.3",
                    "schema": ["raw HTML retained; flow parsing failed"], "objects": [obj],
                    "status": "FAIL", "error": errors[f"{year}-W{week:02d}"],
                })
    history.sort(key=lambda row: row["report_week"], reverse=True)
    four_weeks = history[:4]
    complete_four = len(four_weeks) == 4 and all(
        row.get("global_bitcoin_etp_weekly_flow_usd_mn") is not None for row in four_weeks
    )
    summary = {
        "status": "PASS" if history and all(row["status"] == "PASS" for row in history) else (
            "PARTIAL" if history else "FAIL"
        ),
        "source": "Bitwise Europe Weekly Crypto Market Compass; data subject to publisher revision",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "weekly_history": history,
        "last_four_weeks_global_crypto_etp_flow_usd_mn": (
            sum(row["global_crypto_etp_weekly_flow_usd_mn"] for row in four_weeks)
            if complete_four and all(row.get("global_crypto_etp_weekly_flow_usd_mn") is not None for row in four_weeks)
            else None
        ),
        "last_four_weeks_global_bitcoin_etp_flow_usd_mn": (
            sum(row["global_bitcoin_etp_weekly_flow_usd_mn"] for row in four_weeks)
            if complete_four else None
        ),
        "daily_flows": {"status": "UNAVAILABLE", "reason": "Source publishes weekly totals, not daily flow series."},
        "aum_and_turnover": {"status": "UNAVAILABLE", "reason": "The parsed weekly flow statements do not expose global ETP AUM or turnover."},
        "coverage_note": "Global ETP weekly aggregate; the US spot ETF component is a subset, not the full global market.",
        "errors": errors,
    }
    return summary, manifests


def _fred_macro(directory: Path) -> tuple[dict, list[dict]]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    observations, manifests, errors = {}, [], {}
    today = datetime.now(UTC).date()
    for series_id, meta in FRED_SERIES.items():
        start = today - timedelta(days=meta["lookback_days"])
        url = FRED_GRAPH
        obj = None
        try:
            response = session.get(
                url, params={"id": series_id, "cosd": start.isoformat(), "coed": today.isoformat()},
                timeout=30,
            )
            response.raise_for_status()
            raw = response.content
            obj = _save_object(
                directory, f"fred_{series_id.lower()}.csv", raw,
                source="FRED / original statistical release provider",
                url=response.url, venue="United States macro", symbol=series_id,
                quote=meta["unit"], source_grade="A",
            )
            frame = pd.read_csv(io.BytesIO(raw))
            if frame.empty or len(frame.columns) < 2:
                raise ValueError(f"FRED CSV has unexpected schema for {series_id}")
            date_col, value_col = frame.columns[0], frame.columns[1]
            frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")
            valid = frame.dropna(subset=[value_col])
            if valid.empty:
                raise ValueError(f"FRED series {series_id} has no numeric observations")
            last = valid.iloc[-1]
            last_date = date.fromisoformat(str(last[date_col])[:10])
            age_days = (today - last_date).days
            observations[series_id] = {
                "label": meta["label"], "value": float(last[value_col]),
                "unit": meta["unit"], "observation_date": last_date.isoformat(),
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "age_calendar_days": age_days,
                "status": "PASS" if age_days <= meta["max_age_days"] else "STALE",
                "previous_value": float(valid.iloc[-2][value_col]) if len(valid) > 1 else None,
                "source_url": f"https://fred.stlouisfed.org/series/{series_id}",
            }
            manifests.append({
                "source": "FRED / original statistical release provider",
                "venue": "United States macro", "symbol": series_id,
                "quote_currency": meta["unit"], "interval": "provider native frequency",
                "timezone": "observation date; release timing may lag",
                "schema_version": "1.0", "source_grade": "A",
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "parser": "pandas CSV parser", "parser_version": "0.3",
                "schema": list(frame.columns), "objects": [obj],
                "status": observations[series_id]["status"],
            })
        except Exception as exc:  # noqa: BLE001
            errors[series_id] = f"{type(exc).__name__}: {exc}"
            manifests.append({
                "source": "FRED / original statistical release provider",
                "venue": "United States macro", "symbol": series_id,
                "quote_currency": meta["unit"], "interval": "provider native frequency",
                "timezone": "observation date", "schema_version": "1.0",
                "source_grade": "A", "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "parser": "pandas CSV parser", "parser_version": "0.3",
                "schema": ["raw CSV retained; parsing failed"] if obj else [],
                "objects": [obj] if obj else [], "status": "FAIL",
                "error": errors[series_id],
            })
    passed = sum(item["status"] == "PASS" for item in observations.values())
    summary = {
        "status": "PASS" if passed == len(FRED_SERIES) else "PARTIAL" if passed else "FAIL",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "series": observations,
        "errors": errors,
        "source_note": "FRED observation dates are not release timestamps; monthly/weekly series naturally lag the run date.",
    }
    return summary, manifests


def empty_supplemental_coverage() -> dict:
    """Return explicit not-run states so even blocked reports disclose missing domains."""
    return {
        "spot_ohlcv": {"status": "NOT_RUN", "note": "Primary Binance/Bitstamp acquisition is reported separately."},
        "spot_live_quotes": {"status": "NOT_RUN"},
        "per_exchange_derivatives": {"status": "NOT_RUN"},
        "options": {"status": "NOT_RUN"},
        "us_spot_etf_flows": {"status": "NOT_RUN"},
        "global_etp_flows": {"status": "NOT_RUN"},
        "exchange_flows_and_reserves": {
            "status": "UNAVAILABLE",
            "reason": "No verifiable exchange-wallet-label dataset is configured; raw blockchain transfers are not exchange netflows.",
        },
        "liquidations": {
            "status": "UNAVAILABLE",
            "reason": "No public, complete cross-exchange liquidation history source is configured.",
        },
        "macro_and_indices": {"status": "NOT_RUN"},
        "spot_futures_cvd": {
            "status": "NOT_RUN",
            "reason": "Hourly taker-volume delta has not yet been acquired.",
        },
        "geopolitical_regulatory_news": {
            "status": "NOT_IMPLEMENTED",
            "reason": "No verified event feed is yet wired into this run.",
        },
    }


def acquire_supplemental(output_dir: Path) -> tuple[dict, list[dict]]:
    """Acquire public context feeds independently; failures never fabricate values or block price QA."""
    output_dir.mkdir(parents=True, exist_ok=True)
    manifests = []
    summary = {
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "coverage": empty_supplemental_coverage(),
    }
    summary["coverage"]["spot_ohlcv"]["status"] = "PASS"
    try:
        live_spot, live_spot_manifests = _spot_live_snapshot(output_dir / "spot_live")
        summary["spot_live"] = live_spot
        manifests.extend(live_spot_manifests)
        summary["coverage"]["spot_live_quotes"]["status"] = live_spot["status"]
    except Exception as exc:  # noqa: BLE001
        summary["spot_live"] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
        summary["coverage"]["spot_live_quotes"]["status"] = "FAIL"
    try:
        cvd_data, cvd_manifests = _binance_cvd(output_dir / "binance_cvd")
        summary["cvd"] = cvd_data
        manifests.extend(cvd_manifests)
        summary["coverage"]["spot_futures_cvd"] = {
            "status": cvd_data.get("status", "FAIL"),
            "reason": cvd_data.get("measurement_note"),
        }
    except Exception as exc:  # noqa: BLE001
        summary["cvd"] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
        summary["coverage"]["spot_futures_cvd"] = {
            "status": "FAIL", "reason": summary["cvd"]["error"],
        }
    try:
        news_data, news_manifests = _news_context(output_dir / "news")
        summary["news"] = news_data
        manifests.extend(news_manifests)
        summary["coverage"]["geopolitical_regulatory_news"] = {
            "status": news_data.get("status", "FAIL"),
            "reason": news_data.get("interpretation_limit"),
        }
    except Exception as exc:  # noqa: BLE001
        summary["news"] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
        summary["coverage"]["geopolitical_regulatory_news"] = {
            "status": "FAIL", "reason": summary["news"]["error"],
        }
    derivative_statuses = {}
    for name, function, directory in (
        ("binance_futures", _binance_derivatives, output_dir / "binance_futures"),
        ("bybit_futures", _bybit_derivatives, output_dir / "bybit_futures"),
        ("deribit_options", _deribit_options, output_dir / "deribit_options"),
        ("us_spot_etf_flows", _etf_flows, output_dir / "etf_flows"),
    ):
        try:
            result, manifest = function(directory)
            summary[name] = result
            manifests.append(manifest)
            if name.endswith("futures"):
                derivative_statuses[name] = result.get("status", "FAIL")
            elif name == "deribit_options":
                summary["coverage"]["options"]["status"] = result.get("status", "PARTIAL")
            elif name == "us_spot_etf_flows":
                summary["coverage"]["us_spot_etf_flows"]["status"] = result.get("status", "PARTIAL")
                summary["coverage"]["global_etp_flows"] = result.get("global_etp_flows", {
                    "status": "UNAVAILABLE",
                })
        except Exception as exc:  # noqa: BLE001
            if name.endswith("futures"):
                derivative_statuses[name] = "FAIL"
            elif name == "deribit_options":
                summary["coverage"]["options"]["status"] = "FAIL"
            elif name == "us_spot_etf_flows":
                summary["coverage"]["us_spot_etf_flows"]["status"] = "FAIL"
                summary["coverage"]["global_etp_flows"] = {
                    "status": "UNAVAILABLE",
                    "reason": "US spot ETF feed failed; global ETP feed is not configured.",
                }
            summary[name] = {
                "status": "FAIL",
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "error": f"{type(exc).__name__}: {exc}",
            }
            manifests.append({
                "source": name, "venue": name, "symbol": "BTC",
                "quote_currency": "not_applicable", "interval": "snapshot",
                "timezone": "UTC", "schema_version": "1.0", "source_grade": "C",
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "parser": "BTC Quant Desk optional source wrapper", "parser_version": "0.3",
                "schema": [], "objects": [], "status": "FAIL",
                "error": summary[name]["error"],
            })
    derivative_passes = sum(status == "PASS" for status in derivative_statuses.values())
    summary["coverage"]["per_exchange_derivatives"] = {
        "status": (
            "PASS" if len(derivative_statuses) == 2 and derivative_passes == 2
            else "PARTIAL" if derivative_passes else "FAIL"
        ),
        "by_exchange": derivative_statuses,
    }
    try:
        macro, macro_manifests = _fred_macro(output_dir / "fred")
        summary["macro"] = macro
        manifests.extend(macro_manifests)
        summary["coverage"]["macro_and_indices"]["status"] = macro["status"]
    except Exception as exc:  # noqa: BLE001
        summary["macro"] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
        summary["coverage"]["macro_and_indices"]["status"] = "FAIL"
    return summary, manifests
