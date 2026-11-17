"""Optional, timestamped BTC market-context feeds; no context feed trains the model yet."""
from __future__ import annotations

import hashlib
import io
import json
import math
from datetime import UTC, date, datetime, timedelta
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
    status = "PASS" if len(summary) == 2 else "PARTIAL" if summary else "FAIL"
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
    return {"status": status, "retrieved_at_utc": datetime.now(UTC).isoformat(),
            "venues": summary, "errors": errors}, [manifest]


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
        "symbol": "BTCUSDT perpetual",
        "quote_currency": "USDT",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "status": "PASS" if "premium_index" in raw and "open_interest" in raw else "PARTIAL",
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
        "open_interest_daily_30d": (
            "/v5/market/open-interest",
            {"category": "linear", "symbol": "BTCUSDT", "intervalTime": "1d", "limit": 30},
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
        "status": "PASS" if "ticker" in raw and "open_interest_daily_30d" in raw else "PARTIAL",
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
            "volume_24h_btc": _float_or_none(ticker.get("volume24h")),
            "turnover_24h_usdt": _float_or_none(ticker.get("turnover24h")),
        })
    oi_rows = raw.get("open_interest_daily_30d", {}).get("list", [])
    if oi_rows:
        points = sorted(oi_rows, key=lambda row: int(row.get("timestamp", 0)))
        latest = _float_or_none(points[-1].get("openInterest"))
        summary["open_interest_history_latest_timestamp_utc"] = _timestamp_ms(points[-1].get("timestamp"))
        summary["open_interest_history_latest_btc"] = latest
        for days in (1, 7, 30):
            target = int(points[-1].get("timestamp", 0)) - days * 86400_000
            prior = min(points, key=lambda row: abs(int(row.get("timestamp", 0)) - target))
            summary[f"open_interest_history_change_{days}d_pct"] = _pct_change(
                _float_or_none(prior.get("openInterest")), latest
            )
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
            except Exception:
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

    summary = {
        "status": "PASS",
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
    latest_session = latest.get("latestSession") or {}
    updated_through = latest.get("updatedThrough") or latest_session.get("date")
    sessions = _find_etf_sessions(data_payload)
    if not sessions:
        sessions = latest.get("recentSessions") or []
    sessions = sorted(sessions, key=lambda row: row.get("date", ""))
    newest = sessions[-1] if sessions else latest_session
    latest_date = date.fromisoformat(updated_through) if updated_through else None
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
    summary = {
        "source": latest.get("attribution", "The Commoner Bitcoin ETF Tracker by TFTC"),
        "source_url": latest_url,
        "license": latest.get("license"),
        "status": "PASS" if business_days_old <= 1 else "STALE",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "updated_through": updated_through,
        "business_sessions_behind_approx": business_days_old,
        "latest_session": latest_session,
        "cumulative_net_flow_usd": _float_or_none(latest.get("cumulativeNetFlowUsd")),
        "last_21_sessions_net_flow_usd": sum(_float_or_none(row.get("netFlowUsd")) or 0.0 for row in recent_21),
        "last_30_sessions_net_flow_usd": sum(_float_or_none(row.get("netFlowUsd")) or 0.0 for row in recent_30),
        "history_rows_available": len(sessions),
        "history_coverage_start": sessions[0].get("date") if sessions else None,
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


def _fred_macro(directory: Path) -> tuple[dict, list[dict]]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    observations, manifests, errors = {}, [], {}
    today = datetime.now(UTC).date()
    for series_id, meta in FRED_SERIES.items():
        start = today - timedelta(days=meta["lookback_days"])
        url = FRED_GRAPH
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
                "schema": [], "objects": [], "status": "FAIL",
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


def acquire_supplemental(output_dir: Path) -> tuple[dict, list[dict]]:
    """Acquire public context feeds independently; failures never fabricate values or block price QA."""
    output_dir.mkdir(parents=True, exist_ok=True)
    manifests = []
    summary = {
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "coverage": {
            "spot_ohlcv": {"status": "PASS", "note": "Primary Binance/Bitstamp acquisition is reported separately."},
            "spot_live_quotes": {"status": "UNAVAILABLE"},
            "per_exchange_derivatives": {"status": "UNAVAILABLE"},
            "options": {"status": "UNAVAILABLE"},
            "us_spot_etf_flows": {"status": "UNAVAILABLE"},
            "global_etp_flows": {"status": "UNAVAILABLE"},
            "exchange_flows_and_reserves": {
                "status": "UNAVAILABLE",
                "reason": "No verifiable exchange-wallet-label dataset is configured; raw blockchain transfers are not exchange netflows.",
            },
            "liquidations": {
                "status": "UNAVAILABLE",
                "reason": "No public, complete cross-exchange liquidation history source is configured.",
            },
            "macro_and_indices": {"status": "UNAVAILABLE"},
            "spot_futures_cvd": {
                "status": "PROXY_ONLY",
                "reason": "Taker buy/sell volume ratio is not a complete cumulative volume delta.",
            },
            "geopolitical_regulatory_news": {
                "status": "NOT_IMPLEMENTED",
                "reason": "No verified event feed is yet wired into this run.",
            },
        },
    }
    try:
        live_spot, live_spot_manifests = _spot_live_snapshot(output_dir / "spot_live")
        summary["spot_live"] = live_spot
        manifests.extend(live_spot_manifests)
        summary["coverage"]["spot_live_quotes"]["status"] = live_spot["status"]
    except Exception as exc:  # noqa: BLE001
        summary["spot_live"] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
        summary["coverage"]["spot_live_quotes"]["status"] = "FAIL"
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
                summary["coverage"]["per_exchange_derivatives"]["status"] = (
                    "PASS" if result.get("status") == "PASS" else "PARTIAL"
                )
            elif name == "deribit_options":
                summary["coverage"]["options"]["status"] = result.get("status", "PARTIAL")
            elif name == "us_spot_etf_flows":
                summary["coverage"]["us_spot_etf_flows"]["status"] = result.get("status", "PARTIAL")
                summary["coverage"]["global_etp_flows"] = result.get("global_etp_flows", {
                    "status": "UNAVAILABLE",
                })
        except Exception as exc:  # noqa: BLE001
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
    try:
        macro, macro_manifests = _fred_macro(output_dir / "fred")
        summary["macro"] = macro
        manifests.extend(macro_manifests)
        summary["coverage"]["macro_and_indices"]["status"] = macro["status"]
    except Exception as exc:  # noqa: BLE001
        summary["macro"] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
        summary["coverage"]["macro_and_indices"]["status"] = "FAIL"
    return summary, manifests
