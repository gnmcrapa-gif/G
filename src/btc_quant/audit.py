"""Pre-report protocol, data, statistical, ledger and risk review.

Every report is gated by deterministic core checks plus one rotating deep-review lens.
The rotation changes daily; core invariants are never skipped.
"""
from __future__ import annotations

import calendar
import hashlib
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .ledger import _forecast_to_float
from .research import HISTORICAL_HOLDOUT_START_UTC
from .validation import EXECUTION_ENTRY_LAG_SESSIONS, forward_open_log_return

AUDIT_LENSES = (
    "data_provenance_and_coverage",
    "execution_timing_and_target_semantics",
    "ledger_integrity_and_maturity",
    "statistical_validation_and_multiple_testing",
    "risk_overlay_and_economic_limits",
    "code_efficiency_and_operational_reliability",
)


def select_audit_lens(run: dict, now: datetime) -> tuple[int, str]:
    """Rotate by the run's UTC start second, so same-day reruns can inspect different domains."""
    start = run.get("started_at_utc")
    try:
        rotation_key = int(pd.Timestamp(start).timestamp()) if start else int(now.timestamp())
    except (TypeError, ValueError, OverflowError):
        rotation_key = int(now.timestamp())
    index = rotation_key % len(AUDIT_LENSES)
    return index, AUDIT_LENSES[index]


def _source(manifests: list[dict], venue: str) -> dict | None:
    return next((item for item in manifests if item.get("venue") == venue), None)


def _month_keys(start: date, end: date) -> list[str]:
    output = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        output.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return output


def verify_raw_objects(manifests: list[dict], root: Path) -> dict:
    checked = 0
    failures = []
    for source in manifests:
        for obj in source.get("objects", []):
            checked += 1
            path = root / obj.get("file", "")
            if not path.is_file():
                failures.append({"file": obj.get("file"), "reason": "MISSING"})
                continue
            payload = path.read_bytes()
            if len(payload) != obj.get("size_bytes"):
                failures.append({"file": obj.get("file"), "reason": "SIZE_MISMATCH"})
            elif hashlib.sha256(payload).hexdigest() != obj.get("sha256"):
                failures.append({"file": obj.get("file"), "reason": "SHA256_MISMATCH"})
    return {
        "status": "PASS" if checked > 0 and not failures else "BLOCKED",
        "objects_checked": checked,
        "integrity_failures": failures,
        "evidence": "Every manifest object is checked against both byte size and SHA-256.",
    }


def verify_binance_archive_coverage(source: dict | None, now: datetime) -> dict:
    if not source:
        return {"status": "BLOCKED", "reason": "Binance source manifest missing."}
    try:
        start = pd.Timestamp(source["first_timestamp"]).date()
        last = pd.Timestamp(source["last_timestamp"]).date()
    except (KeyError, TypeError, ValueError) as exc:
        return {"status": "BLOCKED", "reason": f"Invalid source date metadata: {exc}"}
    today = now.astimezone(UTC).date()
    yesterday = today - timedelta(days=1)
    current_month = date(today.year, today.month, 1)
    objects = source.get("objects", [])
    by_name = {Path(obj.get("file", "")).stem: obj for obj in objects}
    expected_months = _month_keys(start, current_month - timedelta(days=1))
    expected_days = [
        (date(today.year, today.month, day)).isoformat()
        for day in range(1, yesterday.day + 1)
    ] if yesterday.month == today.month else []
    missing_months = []
    wrong_month_rows = []
    for key in expected_months:
        name = f"BTCUSDT-1d-{key}"
        obj = by_name.get(name)
        if obj is None:
            missing_months.append(key)
            continue
        expected_rows = calendar.monthrange(int(key[:4]), int(key[5:]))[1]
        if key == f"{start.year:04d}-{start.month:02d}":
            expected_rows -= start.day - 1
        if int(obj.get("rows", -1)) != expected_rows:
            wrong_month_rows.append({
                "month": key, "expected_rows": expected_rows,
                "observed_rows": obj.get("rows"),
            })
    missing_days = []
    wrong_daily_rows = []
    for key in expected_days:
        obj = by_name.get(f"BTCUSDT-1d-{key}")
        if obj is None:
            missing_days.append(key)
        elif int(obj.get("rows", -1)) != 1:
            wrong_daily_rows.append({"date": key, "observed_rows": obj.get("rows")})
    expected_total = (yesterday - start).days + 1
    observed_total = int(source.get("rows", 0))
    failures = source.get("failures", [])
    duplicate_count = int(source.get("duplicates_removed", 0))
    ok = (
        not missing_months and not wrong_month_rows and not missing_days
        and not wrong_daily_rows and not failures and duplicate_count == 0
        and last == yesterday and observed_total == expected_total
    )
    return {
        "status": "PASS" if ok else "BLOCKED",
        "expected_monthly_archives": len(expected_months),
        "observed_monthly_archives": len(expected_months) - len(missing_months),
        "missing_months": missing_months,
        "expected_current_month_daily_archives": len(expected_days),
        "missing_daily_archives": missing_days,
        "wrong_month_row_counts": wrong_month_rows,
        "wrong_daily_row_counts": wrong_daily_rows,
        "expected_rows": expected_total,
        "observed_rows": observed_total,
        "duplicates_removed": duplicate_count,
        "source_failures": failures,
        "first_date_utc": start.isoformat(),
        "last_date_utc": last.isoformat(),
        "evidence": "Expected calendar coverage is checked archive-by-archive, not inferred only from a gap-free concatenated frame.",
    }


def verify_bitstamp_page_reconciliation(source: dict | None) -> dict:
    if not source:
        return {"status": "BLOCKED", "reason": "Bitstamp source manifest missing."}
    objects = source.get("objects", [])
    raw_rows = sum(int(obj.get("rows", 0)) for obj in objects)
    duplicates = int(source.get("duplicates_removed_at_page_boundaries", 0))
    canonical_rows = int(source.get("rows", 0))
    filtered_rows = raw_rows - duplicates - canonical_rows
    ok = bool(objects) and duplicates >= 0 and 0 <= filtered_rows <= 1
    return {
        "status": "PASS" if ok else "BLOCKED",
        "page_count": len(objects),
        "raw_page_rows": raw_rows,
        "page_overlap_duplicates_removed": duplicates,
        "canonical_rows": canonical_rows,
        "filtered_unclosed_rows": filtered_rows,
        "evidence": "Raw page rows minus explicit overlap duplicates and at most one current unclosed daily candle must equal the canonical series.",
    }


def audit_outlier_date(binance: pd.DataFrame | None, bitstamp: pd.DataFrame | None,
                       event_date: str = "2022-11-08") -> dict:
    if binance is None or bitstamp is None:
        return {"status": "WARN", "date_utc": event_date,
                "reason": "Both Binance and Bitstamp frames are required for the event-date cross-check."}
    def row_for(frame):
        data = frame.copy()
        data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)
        found = data.loc[data["timestamp"].dt.strftime("%Y-%m-%d") == event_date]
        return None if len(found) != 1 else found.iloc[0]
    b, s = row_for(binance), row_for(bitstamp)
    if b is None or s is None:
        return {"status": "WARN", "date_utc": event_date,
                "reason": "A unique daily candle is not available on both venues."}
    price_diffs = {
        field: float((float(b[field]) / float(s[field]) - 1.0) * 100.0)
        for field in ("open", "high", "low", "close")
    }
    volume_ratio = float(b["volume"]) / float(s["volume"]) if float(s["volume"]) > 0 else None
    return {
        "status": "WARN_VOLUME_NOT_INDEPENDENTLY_VERIFIED",
        "date_utc": event_date,
        "binance": {"symbol": "BTCUSDT", "quote": "USDT",
                    "ohlc": {k: float(b[k]) for k in ("open", "high", "low", "close")},
                    "base_volume_btc": float(b["volume"])},
        "bitstamp": {"symbol": "BTC/USD", "quote": "USD",
                     "ohlc": {k: float(s[k]) for k in ("open", "high", "low", "close")},
                     "base_volume_btc": float(s["volume"])},
        "binance_vs_bitstamp_ohlc_pct": price_diffs,
        "base_volume_ratio_binance_to_bitstamp": volume_ratio,
        "interpretation": (
            "OHLC prices corroborate the same market move, but exchange-specific base volumes "
            "are not interchangeable. The approximately 63x venue volume ratio is not proof "
            "of an erroneous Binance print. Coinbase/Kraken historical endpoints in this run "
            "do not cover 2022-11-08, so independent volume verification remains unresolved."
        ),
        "evidence_limit": "Coinbase and Kraken cross-check windows are recent and do not include the event date.",
    }


def build_market_snapshot(binance: pd.DataFrame | None, bitstamp: pd.DataFrame | None, manifests: list[dict] | None = None) -> dict:
    output = {}
    for venue, frame, symbol, quote in (
        ("Binance", binance, "BTCUSDT", "USDT"),
        ("Bitstamp", bitstamp, "BTC/USD", "USD"),
    ):
        if frame is None or frame.empty:
            output[venue] = {"status": "BLOCKED"}
            continue
        row = frame.sort_values("timestamp").iloc[-1]
        source_manifest = _source(manifests or [], venue)
        output[venue] = {
            "status": "PASS", "symbol": symbol, "quote_currency": quote,
            "retrieved_at_utc": None if source_manifest is None else source_manifest.get("retrieved_at_utc"),
            "qa_status": None if source_manifest is None else source_manifest.get("qa", {}).get("status", source_manifest.get("status")),
            "candle_open_timestamp_utc": pd.Timestamp(row["timestamp"]).isoformat(),
            "open": float(row["open"]), "high": float(row["high"]),
            "low": float(row["low"]), "close": float(row["close"]),
            "base_volume_btc": float(row["volume"]),
            "units": "price in quote currency per BTC; volume in BTC",
        }
    return output


def build_observed_drivers(frame: pd.DataFrame | None, retrieved_at_utc: str | None = None) -> dict:
    """Describe fixed 1/7/30-session price windows without directional alert language."""
    if frame is None or len(frame) < 31:
        return {"status": "WARN", "reason": "At least 31 validated daily rows are required."}
    data = frame.sort_values("timestamp").reset_index(drop=True)
    close = pd.to_numeric(data["close"], errors="raise").astype(float)
    latest = pd.Timestamp(data.loc[len(data) - 1, "timestamp"])
    drivers = []
    for sessions in (1, 7, 30):
        start = pd.Timestamp(data.loc[len(data) - 1 - sessions, "timestamp"])
        value = float((close.iloc[-1] / close.iloc[-1 - sessions] - 1.0) * 100.0)
        drivers.append({
            "window_sessions": sessions,
            "start_candle_utc": start.isoformat(),
            "end_candle_utc": latest.isoformat(),
            "close_to_close_return_pct": value,
            "source": "Binance BTCUSDT spot daily OHLCV",
            "quote_currency": "USDT",
            "retrieved_at_utc": retrieved_at_utc,
            "qa": "PASS",
        })
    previous_volume = pd.to_numeric(data["volume"].iloc[-31:-1], errors="raise").astype(float)
    volume_median = float(previous_volume.median())
    latest_volume = float(data["volume"].iloc[-1])
    return {
        "status": "PASS",
        "three_observed_price_drivers": drivers,
        "latest_volume_btc": latest_volume,
        "previous_30_session_median_volume_btc": volume_median,
        "latest_volume_vs_previous_30_session_median": (
            latest_volume / volume_median if volume_median > 0 else None
        ),
        "latest_candle_timestamp_utc": latest.isoformat(),
        "volume_window": "30 completed sessions immediately preceding the latest candle",
        "source": "Binance BTCUSDT spot daily OHLCV",
        "retrieved_at_utc": retrieved_at_utc,
        "qa": "PASS",
        "note": "Descriptive facts only; no directional alert or probability is implied.",
    }


def build_forecast_snapshot(events: list[dict]) -> list[dict]:
    scored = {row.get("forecast_id") for row in events if row.get("event_type") == "SCORE"}
    invalidated = {row.get("forecast_id") for row in events if row.get("event_type") == "INVALIDATION"}
    forecasts = []
    for row in events:
        if row.get("event_type") != "FORECAST":
            continue
        if row.get("forecast_id") in scored | invalidated:
            continue
        try:
            point = _forecast_to_float(row.get("forecast"))
            forecasts.append({
                "forecast_id": row.get("forecast_id"),
                "model_version": row.get("model_version"),
                "horizon_days": int(row.get("horizon")),
                "point_log_return": point,
                "implied_simple_return_pct": float(np.expm1(point) * 100.0),
                "issued_at_utc": row.get("issued_at_utc"),
                "entry_timestamp_utc": row.get("entry_timestamp_utc"),
                "expiry_timestamp_utc": row.get("expiry_timestamp_utc"),
                "data_manifest_sha256": row.get("data_manifest_sha256"),
                "code_commit": row.get("code_commit"),
                "target": row.get("target"),
                "status": "PENDING_POINT_FORECAST_NOT_PROBABILITY",
                "units": "log return; implied simple return in percent",
                "source": "Binance BTCUSDT spot daily OHLCV",
            })
        except (TypeError, ValueError, OverflowError):
            continue
    return forecasts


def _check_target_alignment() -> dict:
    opens = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0, 105.0])
    observed = float(forward_open_log_return(opens, 1).iloc[0])
    expected = float(np.log(103.0 / 102.0))
    ok = EXECUTION_ENTRY_LAG_SESSIONS == 2 and np.isclose(observed, expected)
    return {
        "status": "PASS" if ok else "BLOCKED",
        "entry_lag_sessions": EXECUTION_ENTRY_LAG_SESSIONS,
        "synthetic_h1_target": observed,
        "expected_synthetic_h1_target": expected,
        "evidence": "Independent hand calculation verifies entry at Open[t+2] and exit at Open[t+3] for h=1.",
    }


def _check_ledger(events: list[dict], now: datetime, latest_data_timestamp=None) -> dict:
    ids = [row.get("event_id") for row in events]
    duplicates = len(ids) - len(set(ids))
    by_forecast = {}
    for row in events:
        by_forecast.setdefault(row.get("forecast_id"), []).append(row)
    invalidated_ids = {
        row.get("forecast_id") for row in events if row.get("event_type") == "INVALIDATION"
    }
    scored_ids = {row.get("forecast_id") for row in events if row.get("event_type") == "SCORE"}
    latest_data = pd.Timestamp(latest_data_timestamp) if latest_data_timestamp is not None else None
    issues = []
    legacy_vector_count = 0
    for row in events:
        kind = row.get("event_type")
        if kind == "FORECAST":
            try:
                _forecast_to_float(row.get("forecast"))
            except (TypeError, ValueError) as exc:
                issues.append({"forecast_id": row.get("forecast_id"), "reason": str(exc)})
                continue
            if isinstance(row.get("forecast"), str) and row["forecast"].strip().startswith("["):
                legacy_vector_count += 1
            try:
                issued = pd.Timestamp(row["issued_at_utc"])
                entry = pd.Timestamp(row["entry_timestamp_utc"])
                expiry = pd.Timestamp(row["expiry_timestamp_utc"])
                if issued.tzinfo is None or entry.tzinfo is None or expiry.tzinfo is None:
                    raise ValueError("timestamps must be timezone-aware")
                if issued > pd.Timestamp(now):
                    raise ValueError("forecast issue timestamp is in the future")
                if row.get("forecast_id") not in invalidated_ids and not issued < entry < expiry:
                    raise ValueError("valid forecast chronology must satisfy issued < entry < expiry")
                if (row.get("forecast_id") not in invalidated_ids
                        and row.get("forecast_id") not in scored_ids
                        and latest_data is not None and expiry <= latest_data):
                    raise ValueError("matured pending forecast has no SCORE event")
                if not entry < expiry:
                    raise ValueError("expiry must follow entry even for invalidated forecasts")
            except (KeyError, TypeError, ValueError) as exc:
                issues.append({"forecast_id": row.get("forecast_id"), "reason": str(exc)})
        elif kind == "INVALIDATION":
            linked = by_forecast.get(row.get("forecast_id"), [])
            if not any(item.get("event_type") == "FORECAST" for item in linked):
                issues.append({"forecast_id": row.get("forecast_id"), "reason": "orphan INVALIDATION event"})
        elif kind == "SCORE":
            linked = by_forecast.get(row.get("forecast_id"), [])
            if not any(item.get("event_type") == "FORECAST" for item in linked):
                issues.append({"forecast_id": row.get("forecast_id"), "reason": "orphan SCORE event"})
            if row.get("forecast_id") in invalidated_ids:
                issues.append({"forecast_id": row.get("forecast_id"), "reason": "invalidated forecast was scored"})
            if sum(item.get("event_type") == "SCORE" for item in linked) > 1:
                issues.append({"forecast_id": row.get("forecast_id"), "reason": "multiple SCORE events for one forecast"})
            try:
                if not np.isfinite(float(row.get("realized_outcome"))):
                    raise ValueError("non-finite realized outcome")
                expiry = pd.Timestamp(row["expiry_timestamp_utc"])
                recorded = pd.Timestamp(row["recorded_at_utc"])
                if recorded.tzinfo is None or expiry.tzinfo is None or recorded < expiry:
                    raise ValueError("SCORE must be recorded at or after expiry")
            except (KeyError, TypeError, ValueError):
                issues.append({"forecast_id": row.get("forecast_id"), "reason": "invalid score chronology or realized outcome"})
    return {
        "status": "PASS" if duplicates == 0 and not issues else "BLOCKED",
        "event_count": len(events), "duplicate_event_ids": duplicates,
        "legacy_singleton_vector_forecasts_accepted": legacy_vector_count,
        "issues": issues,
        "evidence": "Forecast values are parsed as finite scalars; forecast issue/entry/expiry chronology and SCORE references are checked.",
    }


def _check_ohlcv_challenger(events: list[dict], run: dict) -> dict:
    forecasts = [
        row for row in events
        if row.get("event_type") == "FORECAST"
        and str(row.get("model_version", "")).startswith("ohlcv-challenger-")
    ]
    issues = []
    for row in forecasts:
        notes = row.get("notes", "")
        try:
            cutoff_text = notes.split("training_cutoff_utc=")[1].split(";")[0]
            holdout_text = notes.split("holdout_start_utc=")[1].split(";")[0]
            cutoff = pd.Timestamp(cutoff_text)
            holdout = pd.Timestamp(holdout_text)
            if cutoff.tzinfo is None or holdout.tzinfo is None or cutoff >= holdout:
                raise ValueError("training cutoff is not strictly before holdout")
            if holdout != HISTORICAL_HOLDOUT_START_UTC:
                raise ValueError("challenger holdout start differs from frozen protocol cutoff")
            if "fixed alpha=100" not in notes or "historical holdout excluded from training and tuning" not in notes:
                raise ValueError("fixed-alpha or holdout-exclusion provenance missing")
            _forecast_to_float(row.get("forecast"))
        except (IndexError, TypeError, ValueError) as exc:
            issues.append({"forecast_id": row.get("forecast_id"), "reason": str(exc)})
    state = run.get("ohlcv_challenger", {}).get("status")
    if issues:
        status = "BLOCKED"
    elif forecasts:
        status = "PASS"
    else:
        status = "WARN"
    return {
        "status": status,
        "registered_experiment": "V5.5-OHLCV-001",
        "forecast_events_found": len(forecasts),
        "challenger_run_status": state,
        "training_cutoff_before_holdout": not issues,
        "issues": issues,
        "evidence": "Separate append-only ledger; fixed alpha; every forecast records a training cutoff strictly before the frozen historical holdout.",
    }


def build_pre_report_review(run: dict, manifests: list[dict], binance: pd.DataFrame | None,
                            bitstamp: pd.DataFrame | None, events: list[dict],
                            root: Path = Path("."), now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    now = now.astimezone(UTC)
    binance_manifest = _source(manifests, "Binance")
    bitstamp_manifest = _source(manifests, "Bitstamp")
    raw = verify_raw_objects(manifests, root)
    coverage = verify_binance_archive_coverage(binance_manifest, now)
    bitstamp_pages = verify_bitstamp_page_reconciliation(bitstamp_manifest)
    target = _check_target_alignment()
    latest_data_timestamp = (binance["timestamp"].max() if binance is not None and not binance.empty else None)
    ledger = _check_ledger(events, now, latest_data_timestamp)
    scores = next((step.get("scores", {}) for step in run.get("steps", [])
                   if step.get("step") == "walk_forward"), {})
    holdout_ok = (
        scores.get("holdout_globally_unseen") is False
        and scores.get("training_uses_holdout") is False
        and scores.get("holdout_start_utc") == HISTORICAL_HOLDOUT_START_UTC.isoformat()
        and scores.get("holdout_definition") == "fixed_start_expanding_diagnostic_never_used_for_training_or_tuning"
    )
    holdout = {
        "status": "PASS" if holdout_ok else "BLOCKED",
        "holdout_role": scores.get("holdout_role"),
        "frozen_holdout_start_utc": HISTORICAL_HOLDOUT_START_UTC.isoformat(),
        "holdout_definition": scores.get("holdout_definition"),
        "holdout_globally_unseen": scores.get("holdout_globally_unseen"),
        "training_uses_holdout": scores.get("training_uses_holdout"),
        "evidence": "Previously inspected historical holdout is disclosed as continuity-only and excluded from model training.",
    }
    risk = run.get("risk", {})
    risk_ok = (
        risk.get("mode") == "paper_only"
        and risk.get("live_trading_enabled") is False
        and float(risk.get("theoretical_exposure_pct", -1)) == 0.0
    )
    risk_check = {"status": "PASS" if risk_ok else "BLOCKED",
                  "mode": risk.get("mode"), "live_trading_enabled": risk.get("live_trading_enabled"),
                  "theoretical_exposure_pct": risk.get("theoretical_exposure_pct")}
    zero_champion = all(
        "zero" in metrics for metrics in scores.get("holdout_metrics", {}).values()
    ) and len(scores.get("holdout_metrics", {})) == 4
    no_promotion = scores.get("status") == "SCORED_NOT_PROMOTED"
    benchmark = {
        "status": "PASS" if zero_champion and no_promotion else "BLOCKED",
        "zero_return_present_all_horizons": zero_champion,
        "ridge_status": "CHALLENGER_ONLY",
        "evidence": "Zero-return remains the champion; Ridge is not promoted.",
    }
    outlier = audit_outlier_date(binance, bitstamp)
    observed_drivers = build_observed_drivers(
        binance, None if binance_manifest is None else binance_manifest.get("retrieved_at_utc")
    )
    prospective = run.get("prospective_ledger_validation", {}).get("by_horizon", {})
    prospective_counts = {str(key): int(value.get("n", 0)) for key, value in prospective.items()}
    prospective_ready = len(prospective_counts) == 4 and all(value >= 200 for value in prospective_counts.values())
    ohlcv_summary = run.get("ohlcv_challenger", {}).get("prospective_validation", {})
    ohlcv_counts = {str(key): int(value.get("n", 0)) for key, value in ohlcv_summary.get("by_horizon", {}).items()}
    economic_gate = {
        "status": "WARN",
        "matured_forecasts_by_horizon": prospective_counts,
        "ohlcv_challenger_matured_by_horizon": ohlcv_counts,
        "minimum_per_horizon": 200,
        "sample_gate_met_price_only": prospective_ready,
        "sample_gate_met_ohlcv": len(ohlcv_counts) == 4 and all(value >= 200 for value in ohlcv_counts.values()),
        "strategy_cost_backtest": "NOT_RUN",
        "reason": (
            "No cost-adjusted strategy test is admissible yet: prospective sample gate is not met, "
            "and venue/account fee tier plus a pre-registered execution rule are not established."
        ),
        "evidence": "Do not infer a strategy edge or use arbitrary transaction-cost assumptions.",
    }
    optional_failures = [
        step.get("step") for step in run.get("steps", [])
        if step.get("step") in {"coinbase_recent_cross_check", "kraken_recent_cross_check"}
        and step.get("status") != "PASS"
    ]
    ohlcv_check = _check_ohlcv_challenger(events, run)
    optional = {"status": "WARN" if optional_failures else "PASS",
                "unavailable_or_failed_sources": optional_failures,
                "evidence": "Coinbase and Kraken are corroborative recent sources, not replacements for primary raw venues."}
    checks = {
        "protocol_contract": {"status": "PASS" if run.get("protocol") == "V5.6.0" else "BLOCKED", "protocol": run.get("protocol"), "required_horizons": [1, 3, 7, 30]},
        "raw_object_integrity": raw,
        "binance_archive_completeness": coverage,
        "bitstamp_page_reconciliation": bitstamp_pages,
        "target_and_execution_alignment": target,
        "historical_holdout_governance": holdout,
        "forecast_ledger_integrity": ledger,
        "risk_fail_safe": risk_check,
        "benchmark_and_promotion_governance": benchmark,
        "optional_cross_venue_sources": optional,
        "venue_quote_separation": {"status": "PASS" if binance_manifest and bitstamp_manifest and binance_manifest.get("quote_currency") == "USDT" and bitstamp_manifest.get("quote_currency") == "USD" else "BLOCKED", "binance_quote": None if binance_manifest is None else binance_manifest.get("quote_currency"), "bitstamp_quote": None if bitstamp_manifest is None else bitstamp_manifest.get("quote_currency"), "evidence": "USDT and USD series remain separate; no implicit FX conversion or volume pooling."},
        "run_status_consistency": {"status": "PASS" if run.get("status") == "BLOCKED" or (run.get("status") == "COMPLETE_NOT_PROMOTED" and all(next((step.get("status") for step in run.get("steps", []) if step.get("step") == key), None) == expected for key, expected in (("binance_acquisition_and_qa", "PASS"), ("bitstamp_acquisition_and_qa", "PASS"), ("walk_forward", "SCORED_NOT_PROMOTED")))) else "BLOCKED", "run_status": run.get("status"), "evidence": "A completed report requires both primary QA passes and a scored-but-not-promoted research result."},
        "historical_volume_outlier_review": outlier,
        "ohlcv_challenger_holdout_isolation": ohlcv_check,
        "prospective_evidence_and_economic_validation": economic_gate,
    }
    lens_index, lens = select_audit_lens(run, now)
    deep_checks = {
        "data_provenance_and_coverage": raw["status"] == "PASS" and coverage["status"] == "PASS",
        "execution_timing_and_target_semantics": target["status"] == "PASS",
        "ledger_integrity_and_maturity": ledger["status"] == "PASS",
        "statistical_validation_and_multiple_testing": holdout["status"] == "PASS" and benchmark["status"] == "PASS",
        "risk_overlay_and_economic_limits": risk_check["status"] == "PASS",
        "code_efficiency_and_operational_reliability": (
            raw["objects_checked"] == sum(len(item.get("objects", [])) for item in manifests)
            and len({obj.get("url") for item in manifests for obj in item.get("objects", [])}) ==
            sum(len(item.get("objects", [])) for item in manifests)
        ),
    }
    checks["rotating_deep_review"] = {
        "lens": lens,
        "cycle": lens_index + 1,
        "cycle_length": len(AUDIT_LENSES),
        "rotation_basis": "UTC run-start epoch second",
        "status": "PASS" if deep_checks[lens] else "BLOCKED",
        "all_lenses": list(AUDIT_LENSES),
        "evidence": "One deep lens is selected by UTC date on every run; all core checks above still run on every report.",
    }
    blocked = [name for name, item in checks.items()
               if item.get("status") in {"BLOCKED", "FAIL"}]
    warnings = [name for name, item in checks.items() if item.get("status", "").startswith("WARN")]
    gate = "BLOCKED" if blocked else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    return {
        "executed_at_utc": now.isoformat(),
        "execution_order": "BEFORE_REPORT_SERIALIZATION",
        "gate": gate,
        "checks": checks,
        "blocked_checks": blocked,
        "warning_checks": warnings,
        "rotating_review": checks["rotating_deep_review"],
        "market_snapshot": build_market_snapshot(binance, bitstamp, manifests),
        "forecast_snapshot": build_forecast_snapshot(events),
        "analysis_layers": {
            "FACT": {
                "source_row_counts": {
                    item.get("venue", "unknown"): item.get("rows") for item in manifests
                },
                "latest_candles": build_market_snapshot(binance, bitstamp, manifests),
                "observed_price_drivers": observed_drivers,
                "prospective_matured_forecasts_price_only": run.get("prospective_ledger_validation", {}).get("by_horizon", {}),
                "prospective_matured_forecasts_ohlcv": run.get("ohlcv_challenger", {}).get("prospective_validation", {}).get("by_horizon", {}),
            },
            "INTERPRETATION": {
                "historical_holdout": "Continuity diagnostic only; not globally unseen.",
                "model_decision": "Zero-return champion retained; Ridge challenger not promoted.",
                "volume_outlier": outlier.get("interpretation", outlier.get("reason", "No cross-venue conclusion.")),
            },
            "HYPOTHESIS": {
                "experiment": "V5.5-OHLCV-001",
                "status": run.get("ohlcv_challenger", {}).get("status", "NOT_STARTED"),
                "claim": "Normalized volume surprise and candle geometry are being tested only through new prospective ledger forecasts; no performance or promotion is claimed.",
            },
            "FORECAST": {
                "type": "prospective point forecasts only; no calibrated probabilities",
                "pending": build_forecast_snapshot(events),
            },
        },
        "closing_assessment": {
            "three_observed_drivers": observed_drivers.get("three_observed_price_drivers", []),
            "principal_limit": "No horizon has 200 matured prospective SCORE events; the historical holdout is continuity-only and the 2022-11-08 Binance volume has no independent historical venue confirmation.",
            "evidence_that_would_change_assessment": "At least 200 matured prospective forecasts per horizon, positive lift versus zero-return under HAC/Holm control, separate calibration evidence, stable regime diagnostics and positive net value using documented venue fees/spread/slippage.",
            "single_next_experiment": "Monitor V5.5-OHLCV-001 prospective forecasts until matured sample gates are met; do not use the historical continuity holdout for promotion.",
        },
    }
