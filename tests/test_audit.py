import hashlib
from datetime import UTC, datetime

import numpy as np
import pandas as pd

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
        "absolute_close_return_max_timestamp_utc": timestamps[-10].isoformat(),
        "intraday_range_pct_max_timestamp_utc": timestamps[-5].isoformat(),
    }
    run = {
        "started_at_utc": "2025-06-23T12:00:00+00:00",
        "steps": [
            {"step": "binance_acquisition_and_qa", "status": "PASS", "qa": qa},
            {"step": "bitstamp_acquisition_and_qa", "status": "PASS", "qa": qa},
        ],
        "cross_checks": [{"venue": "Coinbase", "status": "PASS"}],
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
    }
    metrics = {
        str(h): {model: {"n": 250} for model in ("zero", "drift", "momentum", "ridge")}
        for h in (1, 3, 7, 30)
    }
    scores = {
        "target": "log(Open[t+h+2]/Open[t+2])",
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
    assert result["status"] == "PASS"
    assert result["publication_gate"] == "OPEN"
    assert result["executed_before_report_serialization"] is True
    assert len(result["review_cycles"]) == 6
    assert all(cycle["status"] == "PASS" for cycle in result["review_cycles"])
    assert result["rotating_adversarial_lens"] in {
        "outlier_volume", "outlier_close_return", "outlier_intraday_range", "ledger_replay",
    }


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
