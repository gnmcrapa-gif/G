import calendar
import hashlib
from datetime import UTC, datetime

import pandas as pd
import pytest

from btc_quant.audit import (
    AUDIT_LENSES,
    _check_ledger,
    _check_ohlcv_challenger,
    audit_outlier_date,
    build_observed_drivers,
    build_longitudinal_comparison,
    select_audit_lens,
    verify_binance_archive_coverage,
    verify_bitstamp_page_reconciliation,
    verify_raw_objects,
)


def _binance_manifest():
    now = datetime(2026, 11, 17, 16, tzinfo=UTC)
    objects = []
    year, month = 2017, 8
    while (year, month) <= (2026, 10):
        days = calendar.monthrange(year, month)[1]
        rows = days - 16 if (year, month) == (2017, 8) else days
        key = f"{year:04d}-{month:02d}"
        objects.append({"file": f"data/raw/binance/BTCUSDT-1d-{key}.zip", "rows": rows})
        month += 1
        if month == 13:
            year, month = year + 1, 1
    for day in range(1, 17):
        key = f"2026-11-{day:02d}"
        objects.append({"file": f"data/raw/binance/BTCUSDT-1d-{key}.zip", "rows": 1})
    return {
        "venue": "Binance", "first_timestamp": "2017-08-17T00:00:00+00:00",
        "last_timestamp": "2026-11-16T00:00:00+00:00",
        "rows": 3379, "duplicates_removed": 0, "failures": [], "objects": objects,
    }, now


def test_binance_archive_coverage_checks_every_expected_month_and_day():
    manifest, now = _binance_manifest()
    result = verify_binance_archive_coverage(manifest, now)
    assert result["status"] == "PASS"
    assert result["expected_monthly_archives"] == 111
    assert result["expected_current_month_daily_archives"] == 16
    assert result["observed_rows"] == result["expected_rows"] == 3379


def test_binance_archive_coverage_blocks_a_missing_month():
    manifest, now = _binance_manifest()
    manifest["objects"] = [
        obj for obj in manifest["objects"]
        if "BTCUSDT-1d-2020-03.zip" not in obj["file"]
    ]
    result = verify_binance_archive_coverage(manifest, now)
    assert result["status"] == "BLOCKED"
    assert result["missing_months"] == ["2020-03"]


def test_bitstamp_raw_pages_reconcile_overlap_and_one_unclosed_row():
    result = verify_bitstamp_page_reconciliation({
        "objects": [{"rows": 1000}] * 4,
        "duplicates_removed_at_page_boundaries": 349,
        "rows": 3650,
    })
    assert result["status"] == "PASS"
    assert result["filtered_unclosed_rows"] == 1


def test_raw_manifest_objects_are_checked_by_size_and_sha256(tmp_path):
    payload = b"raw-evidence"
    (tmp_path / "sample.bin").write_bytes(payload)
    result = verify_raw_objects([{"objects": [{
        "file": "sample.bin", "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }]}], tmp_path)
    assert result["status"] == "PASS"
    assert result["objects_checked"] == 1


def test_outlier_review_separates_price_corroboration_from_volume_claims():
    b = pd.DataFrame([{
        "timestamp": pd.Timestamp("2022-11-08T00:00:00Z"),
        "open": 20590.67, "high": 20700.88, "low": 17166.83,
        "close": 18547.23, "volume": 760705.362783,
    }])
    s = pd.DataFrame([{
        "timestamp": pd.Timestamp("2022-11-08T00:00:00Z"),
        "open": 20591.00, "high": 20669.00, "low": 17114.00,
        "close": 18550.00, "volume": 12035.90178845,
    }])
    result = audit_outlier_date(b, s)
    assert result["status"] == "WARN_VOLUME_NOT_INDEPENDENTLY_VERIFIED"
    assert result["base_volume_ratio_binance_to_bitstamp"] > 60
    assert abs(result["binance_vs_bitstamp_ohlc_pct"]["close"]) < 0.02
    assert "not interchangeable" in result["interpretation"]


def test_rotating_audit_contains_distinct_lenses():
    assert len(AUDIT_LENSES) == 6
    assert len(set(AUDIT_LENSES)) == 6



def test_ledger_audit_accepts_documented_legacy_late_entry_invalidation():
    now = datetime(2026, 11, 17, 20, tzinfo=UTC)
    forecast = {
        "event_id": "f", "event_type": "FORECAST", "forecast_id": "f",
        "issued_at_utc": "2026-11-17T19:18:40+00:00",
        "entry_timestamp_utc": "2026-11-16T00:00:00+00:00",
        "expiry_timestamp_utc": "2026-11-17T00:00:00+00:00",
        "forecast": "[-0.01]",
    }
    invalidation = {"event_id": "i", "event_type": "INVALIDATION", "forecast_id": "f"}
    result = _check_ledger([forecast, invalidation], now)
    assert result["status"] == "PASS"
    assert result["legacy_singleton_vector_forecasts_accepted"] == 1


def test_ledger_audit_blocks_duplicate_event_ids():
    now = datetime(2026, 11, 17, 20, tzinfo=UTC)
    event = {"event_id": "same", "event_type": "UNKNOWN", "forecast_id": "f"}
    result = _check_ledger([event, event], now)
    assert result["status"] == "BLOCKED"
    assert result["duplicate_event_ids"] == 1



def test_bitstamp_page_reconciliation_blocks_unexplained_row_loss():
    result = verify_bitstamp_page_reconciliation({
        "objects": [{"rows": 1000}] * 4,
        "duplicates_removed_at_page_boundaries": 349,
        "rows": 3640,
    })
    assert result["status"] == "BLOCKED"


def test_ledger_audit_blocks_matured_pending_forecast_without_score():
    now = datetime(2026, 11, 20, 20, tzinfo=UTC)
    forecast = {
        "event_id": "f", "event_type": "FORECAST", "forecast_id": "f",
        "issued_at_utc": "2026-11-17T16:00:00+00:00",
        "signal_timestamp_utc": "2026-11-16T00:00:00+00:00",
        "feature_cutoff_utc": "2026-11-17T00:00:00+00:00",
        "target": "log(Open[t+h+2]/Open[t+2])", "horizon": 1,
        "entry_timestamp_utc": "2026-11-18T00:00:00+00:00",
        "expiry_timestamp_utc": "2026-11-19T00:00:00+00:00",
        "forecast": 0.01,
    }
    result = _check_ledger(
        [forecast], now, latest_data_timestamp="2026-11-19T00:00:00+00:00"
    )
    assert result["status"] == "BLOCKED"
    assert "matured pending forecast has no SCORE event" in result["issues"][0]["reason"]



def test_report_observed_drivers_are_fixed_1_7_30_session_facts():
    close = [100.0 + index for index in range(31)]
    frame = pd.DataFrame({
        "timestamp": pd.date_range("2026-10-17", periods=31, freq="D", tz="UTC"),
        "open": close, "high": [value * 1.01 for value in close],
        "low": [value * 0.99 for value in close], "close": close,
        "volume": [100.0] * 30 + [150.0],
    })
    result = build_observed_drivers(frame)
    assert result["status"] == "PASS"
    assert [row["window_sessions"] for row in result["three_observed_price_drivers"]] == [1, 7, 30]
    assert result["latest_volume_vs_previous_30_session_median"] == 1.5
    assert all(row["source"] == "Binance BTCUSDT spot daily OHLCV" for row in result["three_observed_price_drivers"])



def test_audit_rotation_can_change_between_same_day_reruns():
    now = datetime(2026, 11, 17, 16, tzinfo=UTC)
    first = select_audit_lens({"started_at_utc": "2026-11-17T16:00:00+00:00"}, now)
    second = select_audit_lens({"started_at_utc": "2026-11-17T16:00:01+00:00"}, now)
    assert first[0] != second[0]
    assert first[1] in AUDIT_LENSES
    assert second[1] in AUDIT_LENSES



def test_ohlcv_challenger_audit_requires_training_cutoff_before_holdout():
    event = {
        "event_type": "FORECAST", "forecast_id": "o1",
        "model_version": "ohlcv-challenger-0.1-fixed-alpha-100",
        "forecast": 0.01,
        "notes": (
            "V5.5-OHLCV-001; fixed alpha=100; "
            "training_cutoff_utc=2025-10-15T00:00:00+00:00; "
            "holdout_start_utc=2025-11-17T00:00:00+00:00; "
            "historical holdout excluded from training and tuning"
        ),
    }
    result = _check_ohlcv_challenger([event], {"ohlcv_challenger": {"status": "PROSPECTIVE_ONLY_ACTIVE"}})
    assert result["status"] == "PASS"
    event["notes"] = event["notes"].replace("2025-10-15", "2025-12-15")
    result = _check_ohlcv_challenger([event], {"ohlcv_challenger": {"status": "PROSPECTIVE_ONLY_ACTIVE"}})
    assert result["status"] == "BLOCKED"



def test_longitudinal_comparison_separates_continuity_from_prospective_evidence():
    previous = {
        "started_at_utc": "2026-11-16T19:00:00+00:00",
        "steps": [{"step": "walk_forward", "scores": {
            "holdout_start_utc": "2025-11-17T00:00:00+00:00",
            "holdout_metrics": {"1": {"zero": {"mae": 0.02, "n": 300}, "ridge": {"mae": 0.021, "n": 300}}},
        }}],
        "prospective_ledger_validation": {"by_horizon": {"1": {"n": 0}}},
    }
    current = {
        "started_at_utc": "2026-11-17T19:00:00+00:00",
        "steps": [{"step": "walk_forward", "scores": {
            "holdout_start_utc": "2025-11-17T00:00:00+00:00",
            "holdout_metrics": {"1": {"zero": {"mae": 0.019, "n": 301}, "ridge": {"mae": 0.020, "n": 301}}},
        }}],
        "prospective_ledger_validation": {"by_horizon": {"1": {"n": 1}}},
    }
    manifests = [{"venue": "Binance", "rows": 3379, "last_timestamp": "2026-11-16T00:00:00Z"}]
    previous_manifest = {"sources": [{"venue": "Binance", "rows": 3378, "last_timestamp": "2026-11-15T00:00:00Z"}]}
    result = build_longitudinal_comparison(current, previous, manifests, previous_manifest)
    assert result["status"] == "PASS"
    assert result["holdout_cutoff_unchanged"] is True
    assert result["historical_metric_changes"]["1"]["ridge"]["delta_mae_log_return"] == pytest.approx(-0.001)
    assert result["holdout_comparison_role"] == "CONTINUITY_ONLY_NOT_INDEPENDENT_OOS"
    assert result["price_only_matured_forecasts_by_horizon"]["current"]["1"]["n"] == 1



def test_ledger_audit_blocks_valid_forecast_with_misaligned_target():
    now = datetime(2026, 11, 17, 20, tzinfo=UTC)
    event = {
        "event_id": "f", "event_type": "FORECAST", "forecast_id": "f",
        "issued_at_utc": "2026-11-17T16:00:00+00:00",
        "signal_timestamp_utc": "2026-11-16T00:00:00+00:00",
        "feature_cutoff_utc": "2026-11-17T00:00:00+00:00",
        "target": "log(Open[t+h+1]/Open[t+1])", "horizon": 1,
        "entry_timestamp_utc": "2026-11-18T00:00:00+00:00",
        "expiry_timestamp_utc": "2026-11-19T00:00:00+00:00",
        "forecast": 0.01,
    }
    result = _check_ledger([event], now)
    assert result["status"] == "BLOCKED"
    assert "executable h+2 protocol" in result["issues"][0]["reason"]
