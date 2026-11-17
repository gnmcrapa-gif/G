import pandas as pd
import pytest

from btc_quant.reporting import (
    _build_halving_cycle_comparison,
    _build_longitudinal_comparison,
    _build_report_sections,
    _market_snapshot,
    render_markdown_report,
)


def _scores(start="2025-11-17", end="2026-11-16", mae=0.01):
    return {
        "holdout_start_utc": start,
        "holdout_end_utc": end,
        "holdout_metrics": {
            str(h): {"zero": {"mae": mae}, "ridge": {"mae": mae + 0.001}}
            for h in (1, 3, 7, 30)
        },
    }


def test_longitudinal_comparison_only_compares_same_venue_quote_and_window():
    previous = {
        "started_at_utc": "2026-11-16T19:00:00+00:00",
        "finished_at_utc": "2026-11-16T19:01:00+00:00",
        "status": "COMPLETE_NOT_PROMOTED",
        "market_snapshot": {"venues": [{
            "venue": "Binance", "symbol": "BTCUSDT", "quote_currency": "USDT",
            "close_quote_per_btc": 65000.0,
        }]},
        "steps": [{"step": "walk_forward", "scores": _scores()}],
        "prospective_ledger_validation": {"by_horizon": {"1": {"n": 0}}},
    }
    current = {
        "status": "COMPLETE_NOT_PROMOTED",
        "market_snapshot": {"venues": [
            {
                "venue": "Binance", "symbol": "BTCUSDT", "quote_currency": "USDT",
                "close_quote_per_btc": 66000.0, "candle_open_timestamp_utc": "2026-11-16T00:00:00+00:00",
            },
            {
                "venue": "Bitstamp", "symbol": "BTC/USD", "quote_currency": "USD",
                "close_quote_per_btc": 65500.0,
            },
        ]},
        "prospective_ledger_validation": {"by_horizon": {"1": {"n": 2}}},
    }
    result = _build_longitudinal_comparison(previous, current, _scores())
    assert result["status"] == "COMPARISON_AVAILABLE"
    assert result["historical_benchmark_comparison"]["status"] == "COMPARABLE_SAME_HISTORICAL_CONTINUITY_WINDOW"
    assert result["historical_benchmark_comparison"]["zero_return_mae"]["1"]["difference_log_return_units"] == pytest.approx(0.0)
    assert result["same_venue_price_snapshots"][0]["close_change_since_previous_report_pct"] == pytest.approx(1000.0 / 65000.0 * 100.0)
    assert result["same_venue_price_snapshots"][1]["status"] == "NOT_COMPARABLE_NO_MATCHING_PRIOR_SNAPSHOT"
    assert result["prospective_matured_counts"]["1"] == {"previous_matured": 0, "current_matured": 2}


def test_longitudinal_comparison_refuses_different_holdout_windows():
    previous = {"steps": [{"step": "walk_forward", "scores": _scores()}]}
    result = _build_longitudinal_comparison(previous, {}, _scores(start="2025-12-01"))
    assert result["historical_benchmark_comparison"]["status"] == "NOT_COMPARABLE_DIFFERENT_OR_MISSING_HOLDOUT_WINDOW"


def test_report_sections_keep_cost_backtest_blocked_without_prospective_sample():
    run = {
        "steps": [],
        "prospective_ledger_validation": {"by_horizon": {}},
        "ledger": {"forecast_events_created": 0, "score_events_created": 0},
        "market_snapshot": {"venues": [{
            "venue": "Binance", "close_change_1d_pct": 1.0, "intraday_range_pct": 2.0,
            "volume_vs_prior_30d_median": 1.5, "candle_open_timestamp_utc": "2026-11-16T00:00:00+00:00",
        }]},
    }
    taxonomy, economic, closing = _build_report_sections(run, _scores())
    assert set(taxonomy) == {"FACT", "INTERPRETATION", "HYPOTHESIS", "FORECAST"}
    assert economic["status"] == "BLOCKED_INSUFFICIENT_PROSPECTIVE_EVIDENCE"
    assert economic["cost_adjusted_strategy_backtest_executed"] is False
    assert len(closing["observed_drivers"]) == 3
    assert closing["single_next_priority_experiment"]



def test_market_snapshot_adds_7d_30d_and_technical_reference_levels():
    timestamps = pd.date_range("2026-01-01", periods=250, freq="D", tz="UTC")
    close = [100.0 + index for index in range(250)]
    frame = pd.DataFrame({
        "timestamp": timestamps,
        "open": close,
        "high": [value + 2.0 for value in close],
        "low": [value - 2.0 for value in close],
        "close": close,
        "volume": [1000.0] * 250,
    })
    snapshot = _market_snapshot(frame, "Binance", "BTCUSDT", "USDT", "2026-09-07T00:00:00+00:00")
    assert snapshot["close_change_7d_pct"] == pytest.approx((349.0 / 342.0 - 1.0) * 100.0)
    assert snapshot["close_change_30d_pct"] == pytest.approx((349.0 / 319.0 - 1.0) * 100.0)
    assert snapshot["sma_200_quote_per_btc"] is not None
    assert snapshot["high_20d_quote_per_btc"] == 351.0
    assert snapshot["low_20d_quote_per_btc"] == 328.0
    assert snapshot["atr_14_quote_per_btc"] == 4.0
    assert snapshot["volume_7d_btc"] == 7000.0
    assert snapshot["volume_30d_btc"] == 30000.0


def test_markdown_report_discloses_stale_and_unavailable_context_sources():
    report = render_markdown_report({
        "protocol": "V5.6",
        "status": "COMPLETE_NOT_PROMOTED",
        "started_at_utc": "2026-11-17T00:00:00+00:00",
        "supplemental_data": {
            "coverage": {
                "us_spot_etf_flows": {"status": "STALE", "reason": "two sessions behind"},
                "exchange_flows_and_reserves": {"status": "UNAVAILABLE", "reason": "no wallet labels"},
            },
            "spot_live": {"venues": {}},
        },
        "steps": [],
        "market_snapshot": {"venues": []},
        "ledger": {},
        "risk": {"mode": "paper_only", "live_trading_enabled": False, "theoretical_exposure_pct": 0},
        "pre_report_review": {"status": "PASS", "review_cycles": [], "blocking_failures": []},
        "closing_assessment": {},
        "report_taxonomy": {
            "FACT": [], "INTERPRETATION": [], "HYPOTHESIS": [],
            "FORECAST": {
                "new_point_forecasts_issued_this_run": 4,
                "new_forecasts_scored_this_run": 0,
                "calibrated_probabilities_published": False,
                "qualification": "Point forecast only; not calibrated.",
            },
        },
    }, {})
    assert "Point forecast emessi in questo run: 4." in report
    assert "us_spot_etf_flows" in report
    assert "STALE" in report
    assert "exchange_flows_and_reserves" in report
    assert "UNAVAILABLE" in report



def test_macro_report_discloses_observation_freshness_retrieval_and_source():
    report = render_markdown_report({
        "protocol": "V5.6",
        "status": "COMPLETE_NOT_PROMOTED",
        "started_at_utc": "2026-11-18T00:00:00+00:00",
        "supplemental_data": {
            "coverage": {},
            "macro": {
                "status": "PARTIAL",
                "retrieved_at_utc": "2026-11-18T00:05:00+00:00",
                "series": {
                    "CPIAUCSL": {
                        "label": "US CPI index",
                        "observation_date": "2026-10-01",
                        "freshness_reference_date": "2026-10-31",
                        "value": 326.5,
                        "unit": "index 1982-84=100",
                        "status": "PASS",
                        "retrieved_at_utc": "2026-11-18T00:04:00+00:00",
                        "source_method": "official BLS monthly series API v1",
                    },
                },
                "errors": {},
            },
            "spot_live": {"venues": {}},
        },
        "steps": [],
        "market_snapshot": {"venues": []},
        "ledger": {},
        "risk": {"mode": "paper_only", "live_trading_enabled": False, "theoretical_exposure_pct": 0},
        "pre_report_review": {"status": "PASS", "review_cycles": [], "blocking_failures": []},
        "closing_assessment": {},
        "report_taxonomy": {
            "FACT": [], "INTERPRETATION": [], "HYPOTHESIS": [],
            "FORECAST": {
                "new_point_forecasts_issued_this_run": 0,
                "new_forecasts_scored_this_run": 0,
                "calibrated_probabilities_published": False,
                "qualification": "No calibrated forecast.",
            },
        },
    }, {})
    assert "2026-10-31" in report
    assert "2026-11-18T00:04:00+00:00" in report
    assert "official BLS monthly series API v1" in report


def test_markdown_report_includes_okx_perpetual_context_and_cvd_limits():
    report = render_markdown_report({
        "protocol": "V5.6",
        "status": "COMPLETE_NOT_PROMOTED",
        "started_at_utc": "2026-11-17T23:00:00+00:00",
        "supplemental_data": {
            "coverage": {
                "per_exchange_derivatives": {
                    "status": "PARTIAL",
                    "by_exchange": {
                        "binance_futures": "FAIL",
                        "bybit_futures": "FAIL",
                        "okx_swap": "PASS",
                    },
                },
            },
            "okx_swap": {
                "status": "PASS",
                "instrument": "BTC-USDT-SWAP",
                "last_price_usdt": 64881.6,
                "ticker_timestamp_utc": "2026-11-17T23:24:10+00:00",
                "retrieved_at_utc": "2026-11-17T23:24:10+00:00",
                "open_interest_timestamp_utc": "2026-11-17T23:24:10+00:00",
                "volume_24h_base_currency": 116747.6857,
                "volume_24h_contracts": 11674768.57,
                "open_interest_btc": 31166.2211,
                "open_interest_usd": 2021693546.9369,
                "open_interest_history": {
                    "timestamp_utc": "2026-11-17T00:00:00+00:00",
                    "change_1d_pct": 1.9,
                    "change_7d_pct": -13.1,
                    "change_30d_pct": 3.5,
                },
                "funding_rate_predicted_current": -0.0000131486,
                "settled_funding_rate": -0.0000069841,
                "funding_settlement_state": "settled",
                "funding_timestamp_utc": "2026-11-18T00:00:00+00:00",
                "last_settled_funding_time_utc": "2026-11-17T16:00:00+00:00",
                "next_funding_time_utc": "2026-11-18T08:00:00+00:00",
                "daily_taker_volume_history_rows": 30,
                "funding_history_rows": 100,
                "daily_taker_volume_summary": {
                    "closed_daily_rows": 29,
                    "cumulative_delta_btc": {"1d": -313.2, "7d": -22127.8, "30d": None},
                    "measurement_note": "Exchange-specific derivatives delta proxy; not spot CVD.",
                },
                "errors": {},
            },
            "spot_live": {"venues": {}},
        },
        "steps": [],
        "market_snapshot": {"venues": []},
        "ledger": {},
        "risk": {"mode": "paper_only", "live_trading_enabled": False, "theoretical_exposure_pct": 0},
        "pre_report_review": {"status": "PASS", "review_cycles": [], "blocking_failures": []},
        "closing_assessment": {},
        "report_taxonomy": {
            "FACT": [], "INTERPRETATION": [], "HYPOTHESIS": [],
            "FORECAST": {
                "new_point_forecasts_issued_this_run": 0,
                "new_forecasts_scored_this_run": 0,
                "calibrated_probabilities_published": False,
                "qualification": "No calibrated forecast.",
            },
        },
    }, {})
    assert "### OKX BTC-USDT Perpetual" in report
    assert "Snapshot acquisito UTC: 2026-11-17T23:24:10+00:00" in report
    assert "ticker 2026-11-17T23:24:10+00:00" in report
    assert "31,166.22 BTC" in report
    assert "Funding previsto per il prossimo settlement" in report
    assert "Ultimo funding effettivamente settled" in report
    assert "2026-11-17T16:00:00+00:00" in report
    assert "29 barre UTC complete su 30 scaricate" in report
    assert "30D n/d BTC" in report
    assert "not spot CVD" in report
    assert "Binance FAIL; Bybit FAIL; OKX PASS" in report
    assert "Liquidazioni: NOT_ACQUIRED" in report


def test_halving_cycle_comparison_uses_same_elapsed_horizon_and_marks_missing_history():
    timestamps = pd.date_range("2020-05-11", "2026-11-16", freq="D", tz="UTC")
    close = [100.0 + index for index in range(len(timestamps))]
    frame = pd.DataFrame({
        "timestamp": timestamps,
        "open": close,
        "high": [value + 2.0 for value in close],
        "low": [value - 2.0 for value in close],
        "close": close,
        "volume": [1000.0] * len(close),
    })
    result = _build_halving_cycle_comparison(frame)
    cycles = {item["cycle"]: item for item in result["cycles"]}
    assert result["status"] == "PASS"
    assert cycles["2012 cycle"]["status"] == "INSUFFICIENT_HISTORY"
    assert cycles["2016 cycle"]["status"] == "INSUFFICIENT_HISTORY"
    assert cycles["2020 cycle"]["status"] == "PASS"
    assert cycles["2024 cycle (current)"]["status"] == "PASS"
    assert cycles["2020 cycle"]["elapsed_sessions"] == result["current_cycle_elapsed_sessions"]
    assert cycles["2024 cycle (current)"]["elapsed_sessions"] == result["current_cycle_elapsed_sessions"]
    assert "not a timing forecast" in result["interpretation_limit"]
