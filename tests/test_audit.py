import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from btc_quant.audit import (
    AUDIT_LENSES,
    _check_ledger,
    audit_outlier_date,
    verify_binance_archive_coverage,
    verify_bitstamp_page_reconciliation,
    verify_raw_objects,
)


def _binance_manifest():
    now = datetime(2026, 11, 17, 16, tzinfo=UTC)
    objects = []
    start = datetime(2017, 8, 17, tzinfo=UTC).date()
    year, month = 2017, 8
    while (year, month) <= (2026, 10):
        import calendar
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
        "issued_at_utc": "2026-11-16T19:18:40+00:00",
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
