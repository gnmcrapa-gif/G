import hashlib
from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest

from btc_quant.audit import run_pre_report_review


def _review_inputs(tmp_path):
    raw = tmp_path / "raw.json"
    raw.write_bytes(b"raw-market-data")
    sha = hashlib.sha256(raw.read_bytes()).hexdigest()
    timestamps = pd.date_range("2020-01-01", periods=2000, freq="D", tz="UTC")
    close = 10000.0 * np.exp(np.arange(2000) * 0.0001)
    frame = pd.DataFrame({
        "timestamp": timestamps,
        "open": close * 0.999,
        "high": close * 1.01,
        "low": close * 0.99,
        "close": close,
        "volume": np.full(2000, 100.0),
    })
    binance_objects = []
    for period in pd.period_range("2020-01", "2025-05", freq="M"):
        binance_objects.append({
            "file": str(raw), "sha256": sha, "size_bytes": raw.stat().st_size,
            "url": f"https://example.test/monthly/BTCUSDT-1d-{period.strftime('%Y-%m')}.zip",
            "retrieved_at_utc": "2025-06-23T12:00:00+00:00",
        })
    for day in pd.date_range("2025-06-01", "2025-06-22", freq="D"):
        binance_objects.append({
            "file": str(raw), "sha256": sha, "size_bytes": raw.stat().st_size,
            "url": f"https://example.test/daily/BTCUSDT-1d-{day.strftime('%Y-%m-%d')}.zip",
            "retrieved_at_utc": "2025-06-23T12:00:00+00:00",
        })
    manifests = [
        {
            "venue": "Binance", "symbol": "BTCUSDT", "quote_currency": "USDT",
            "rows": 2000, "parser_version": "test-1",
            "schema": ["timestamp", "open", "high", "low", "close", "volume"],
            "objects": binance_objects,
        },
        {
            "venue": "Bitstamp", "symbol": "BTC/USD", "quote_currency": "USD",
            "parser_version": "test-1", "schema": ["timestamp", "open", "high", "low", "close", "volume"],
            "rows": 2000, "duplicates_removed_at_page_boundaries": 0,
            "objects": [{
                "file": str(raw), "sha256": sha, "size_bytes": raw.stat().st_size,
                "rows": 2000, "url": "https://example.test/bitstamp",
                "retrieved_at_utc": "2025-06-23T12:00:00+00:00",
            }],
        },
    ]
    qa = {
        "volume_robust_z_max_timestamp_utc": timestamps[-20].isoformat(),
        "volume_max_timestamp_utc": timestamps[-30].isoformat(),
        "absolute_close_return_max_timestamp_utc": timestamps[-10].isoformat(),
        "intraday_range_pct_max_timestamp_utc": timestamps[-5].isoformat(),
        "volume_robust_z_window_sessions": 90,
        "volume_robust_z_min_history_sessions": 60,
    }
    run = {
        "supplemental_data": {
            "coverage": {
                "spot_ohlcv": {"status": "PASS"},
                "spot_live_quotes": {"status": "PASS"},
                "per_exchange_derivatives": {"status": "PASS"},
                "options": {"status": "PASS"},
                "us_spot_etf_flows": {"status": "STALE"},
                "global_etp_flows": {"status": "UNAVAILABLE"},
                "exchange_flows_and_reserves": {"status": "UNAVAILABLE"},
                "liquidations": {"status": "UNAVAILABLE"},
                "macro_and_indices": {"status": "PARTIAL"},
                "spot_futures_cvd": {"status": "PROXY_ONLY"},
                "geopolitical_regulatory_news": {"status": "NOT_IMPLEMENTED"},
            },
        },
        "started_at_utc": "2025-06-23T12:00:00+00:00",
        "performance": {"acquisition_and_qa_seconds": 10.0, "walk_forward_seconds": 2.0},
        "steps": [
            {"step": "binance_acquisition_and_qa", "status": "PASS", "qa": qa},
            {"step": "bitstamp_acquisition_and_qa", "status": "PASS", "qa": qa},
        ],
        "cross_checks": [{
            "venue": "Coinbase", "status": "PASS",
            "metric_metadata": {
                "overlap_start_utc": "2025-01-01T00:00:00+00:00",
                "overlap_end_utc": "2025-06-22T00:00:00+00:00",
                "return_correlation_unit": "dimensionless",
            },
        }],
        "numeric_conventions": {
            "price": "quote currency per BTC", "volume": "BTC",
            "percentage": "%", "log_return": "natural-log return units",
            "horizon": "daily sessions", "timestamp": "UTC candle-open",
        },
        "probabilistic_claims_allowed": False,
        "prospective_ledger_validation": {"probability_calibration_claim_allowed": False},
        "risk": {"mode": "paper_only", "live_trading_enabled": False, "theoretical_exposure_pct": 0.0},
        "report_taxonomy": {
            "FACT": [], "INTERPRETATION": [], "HYPOTHESIS": [], "FORECAST": {},
        },
        "economic_validation": {
            "cost_adjusted_strategy_backtest_executed": False,
            "historical_holdout_used_for_economic_promotion": False,
        },
        "closing_assessment": {
            "principal_limit": "insufficient prospective evidence",
            "evidence_that_would_change_assessment": "prospective lift and calibration",
            "single_next_priority_experiment": "prospective challenger",
        },
        "longitudinal_comparison": {
            "status": "NO_PRIOR_REPORT", "comparison_performed": False,
        },
        "code_provenance": {"commit_sha": "test-sha", "workflow_run_id": "test-run"},
    }
    metrics = {
        str(h): {model: {"n": 250} for model in ("zero", "drift", "momentum", "ridge")}
        for h in (1, 3, 7, 30)
    }
    scores = {
        "target": "log(Open[t+h+2]/Open[t+2]); signal after close t",
        "metric_metadata": {
            "source": "Binance spot BTCUSDT", "quote_currency": "USDT",
            "target_unit": "natural-log return units", "horizon_unit": "daily sessions",
            "historical_window_start_utc": "2024-01-01T00:00:00+00:00",
            "historical_window_end_utc": "2025-06-22T00:00:00+00:00",
            "sample_role": "historical_continuity_diagnostic_only",
            "data_qa_status": "PASS",
        },
        "requested_next_open_target_executable_at_scheduled_run": False,
        "training_uses_holdout": False,
        "holdout_globally_unseen": False,
        "holdout_role": "historical_continuity_diagnostic_only",
        "holdout_training_and_tuning_excluded_in_this_run": True,
        "holdout_metrics": metrics,
    }
    return run, manifests, frame, frame.copy(), [], scores


def test_pre_report_review_passes_and_records_rotating_review_cycles(tmp_path):
    run, manifests, binance, bitstamp, events, scores = _review_inputs(tmp_path)
    result = run_pre_report_review(
        run, manifests, binance, bitstamp, events, scores,
        now=datetime(2025, 6, 23, 12, tzinfo=UTC), run_id="workflow-100",
    )
    assert result["status"] == "PASS", result["blocking_failures"]
    assert result["publication_gate"] == "OPEN"
    assert result["executed_before_report_serialization"] is True
    assert len(result["review_cycles"]) == 7
    assert all(cycle["status"] == "PASS" for cycle in result["review_cycles"])
    assert result["rotating_adversarial_lens"] in {
        "outlier_volume", "outlier_close_return", "outlier_intraday_range", "ledger_replay",
    }
    event = run["anomaly_event_cross_venue_checks"]["outlier_volume"]
    assert event["binance_usdt_to_bitstamp_usd_close_price_ratio"] == pytest.approx(1.0)
    assert event["implied_usd_per_usdt_if_btc_prices_were_at_parity"] == pytest.approx(1.0)
    assert "not an observed USDT/USD exchange rate" in event["quote_basis_caveat"]


def test_pre_report_review_blocks_risk_and_raw_hash_tampering(tmp_path):
    run, manifests, binance, bitstamp, events, scores = _review_inputs(tmp_path)
    manifests[0]["objects"][0]["sha256"] = "0" * 64
    run["risk"]["theoretical_exposure_pct"] = 1.0
    result = run_pre_report_review(
        run, manifests, binance, bitstamp, events, scores,
        now=datetime(2025, 6, 23, 12, tzinfo=UTC), run_id="workflow-101",
    )
    assert result["status"] == "FAIL"
    assert result["publication_gate"] == "BLOCKED"
    assert "raw_object_integrity" in result["blocking_failures"]
    assert "risk_fail_closed" in result["blocking_failures"]


def test_rotating_red_team_lens_changes_across_run_ids(tmp_path):
    run, manifests, binance, bitstamp, events, scores = _review_inputs(tmp_path)
    lenses = {
        run_pre_report_review(
            run, manifests, binance, bitstamp, events, scores,
            now=datetime(2025, 6, 23, 12, tzinfo=UTC), run_id=f"run-{index}",
        )["rotating_adversarial_lens"]
        for index in range(20)
    }
    assert len(lenses) == 4


def test_invalidated_backdated_forecasts_remain_auditable_not_blocking(tmp_path):
    run, manifests, binance, bitstamp, _, scores = _review_inputs(tmp_path)
    forecast = {
        "event_id": "f-event", "event_type": "FORECAST", "forecast_id": "f1",
        "issued_at_utc": "2025-06-23T12:00:00+00:00",
        "entry_timestamp_utc": "2025-06-23T00:00:00+00:00",
    }
    invalidation = {
        "event_id": "i-event", "event_type": "INVALIDATION", "forecast_id": "f1",
    }
    result = run_pre_report_review(
        run, manifests, binance, bitstamp, [forecast, invalidation], scores,
        now=datetime(2025, 6, 23, 12, tzinfo=UTC), run_id="workflow-invalidated",
    )
    ledger_check = next(item for item in result["checks"]
                        if item["check_id"] == "append_only_ledger_consistency")
    assert ledger_check["status"] == "PASS"
