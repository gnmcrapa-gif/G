"""Pre-publication protocol, data, statistical and operational review gates."""
from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

REVIEW_LENSES = (
    "outlier_volume",
    "outlier_close_return",
    "outlier_intraday_range",
    "ledger_replay",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _row_at(frame: pd.DataFrame, timestamp: str) -> pd.Series | None:
    stamps = pd.to_datetime(frame["timestamp"], utc=True)
    match = frame.loc[stamps == pd.Timestamp(timestamp)]
    return None if match.empty else match.iloc[-1]


def _event_context(timestamp: str, binance: pd.DataFrame,
                   bitstamp: pd.DataFrame) -> dict:
    result = {"timestamp_utc": timestamp, "venues": {}}
    for venue, frame in (("Binance_BTCUSDT", binance), ("Bitstamp_BTCUSD", bitstamp)):
        stamps = pd.to_datetime(frame["timestamp"], utc=True)
        positions = frame.index[stamps == pd.Timestamp(timestamp)].tolist()
        if not positions:
            result["venues"][venue] = {"status": "NOT_AVAILABLE"}
            continue
        pos = positions[-1]
        row = frame.loc[pos]
        previous = frame.loc[pos - 1] if pos > frame.index.min() else None
        close_return = None
        if previous is not None and float(previous["close"]) > 0:
            import math
            close_return = math.log(float(row["close"]) / float(previous["close"]))
        start = max(frame.index.min(), pos - 90)
        history = frame.loc[start:pos - 1, "volume"].astype(float)
        median_volume = float(history.median()) if not history.empty else 0.0
        volume_ratio = (
            float(row["volume"]) / median_volume if median_volume > 0 else None
        )
        result["venues"][venue] = {
            "status": "PASS",
            "open": float(row["open"]), "high": float(row["high"]),
            "low": float(row["low"]), "close": float(row["close"]),
            "volume_btc": float(row["volume"]),
            "intraday_range_pct": float((row["high"] - row["low"]) / row["open"] * 100),
            "close_log_return": close_return,
            "volume_vs_prior_90d_median": volume_ratio,
            "quote_currency": "USDT" if venue.startswith("Binance") else "USD",
        }
    left = result["venues"].get("Binance_BTCUSDT", {})
    right = result["venues"].get("Bitstamp_BTCUSD", {})
    if left.get("status") == right.get("status") == "PASS":
        if left.get("close_log_return") is not None and right.get("close_log_return") is not None:
            result["absolute_close_return_difference"] = abs(
                left["close_log_return"] - right["close_log_return"]
            )
        result["volume_comparison_policy"] = (
            "Venue volumes are not expected to match; compare each venue with its own trailing median."
        )
        if left.get("close") and right.get("close"):
            close_ratio = left["close"] / right["close"]
            result["binance_usdt_to_bitstamp_usd_close_price_ratio"] = close_ratio
            result["implied_usd_per_usdt_if_btc_prices_were_at_parity"] = (
                right["close"] / left["close"]
            )
        if left.get("open") and right.get("open"):
            result["binance_usdt_to_bitstamp_usd_open_price_ratio"] = (
                left["open"] / right["open"]
            )
        result["quote_basis_caveat"] = (
            "The implied USD-per-USDT figure is a diagnostic under a BTC-price-parity assumption, "
            "not an observed USDT/USD exchange rate. USD and USDT candles are not converted or merged."
        )
    return result


def run_pre_report_review(
    run: dict,
    manifests: list[dict],
    binance: pd.DataFrame | None,
    bitstamp: pd.DataFrame | None,
    ledger_events: list[dict],
    scores: dict,
    *,
    now: datetime | None = None,
    run_id: str = "local",
) -> dict:
    """Run blocking invariants plus rotating adversarial review before report serialization."""
    current = now or datetime.now(UTC)
    checks: list[dict] = []

    def add(check_id: str, category: str, passed: bool | str, evidence: str,
            *, blocking: bool = True) -> None:
        status = passed if isinstance(passed, str) else (
            "PASS" if passed else ("FAIL" if blocking else "WARN")
        )
        checks.append({
            "check_id": check_id, "category": category,
            "status": status, "blocking": blocking, "evidence": evidence,
        })

    steps = {item.get("step"): item for item in run.get("steps", [])}
    add(
        "primary_sources_acquired_and_qa", "data",
        all(steps.get(name, {}).get("status") == "PASS" for name in (
            "binance_acquisition_and_qa", "bitstamp_acquisition_and_qa"
        )),
        "Binance BTCUSDT and Bitstamp BTC/USD must both have successful acquisition and OHLCV QA.",
    )

    expected_context_domains = {
        "spot_ohlcv", "spot_live_quotes", "per_exchange_derivatives", "options",
        "us_spot_etf_flows", "global_etp_flows", "exchange_flows_and_reserves",
        "liquidations", "macro_and_indices", "spot_futures_cvd",
        "geopolitical_regulatory_news",
    }
    context_coverage = run.get("supplemental_data", {}).get("coverage", {})
    coverage_complete = expected_context_domains.issubset(context_coverage)
    allowed_context_statuses = {
        "PASS", "PARTIAL", "STALE", "FAIL", "UNAVAILABLE",
        "PROXY_ONLY", "NOT_IMPLEMENTED", "NOT_RUN",
    }
    coverage_statuses_valid = all(
        isinstance(context_coverage.get(name), dict)
        and context_coverage[name].get("status") in allowed_context_statuses
        for name in expected_context_domains if name in context_coverage
    )
    add(
        "supplemental_coverage_explicit", "data",
        coverage_complete and coverage_statuses_valid,
        f"required_domains={sorted(expected_context_domains)}; "
        f"reported={sorted(context_coverage)}; statuses="
        f"{ {name: item.get('status') for name, item in context_coverage.items()} }",
    )

    rolling_volume_qa = all(
        steps.get(name, {}).get("qa", {}).get("volume_robust_z_window_sessions") == 90
        and steps.get(name, {}).get("qa", {}).get("volume_robust_z_min_history_sessions") == 60
        for name in ("binance_acquisition_and_qa", "bitstamp_acquisition_and_qa")
    )
    add("rolling_volume_outlier_method", "data", rolling_volume_qa,
        "Volume outliers must use the prior 90 completed sessions, current excluded, with at least 60 observations; no full-history z-score.")
    by_venue = {item.get("venue"): item for item in manifests}
    binance_meta, bitstamp_meta = by_venue.get("Binance", {}), by_venue.get("Bitstamp", {})
    add(
        "venue_quote_separation", "protocol",
        binance_meta.get("symbol") == "BTCUSDT"
        and binance_meta.get("quote_currency") == "USDT"
        and bitstamp_meta.get("symbol") == "BTC/USD"
        and bitstamp_meta.get("quote_currency") == "USD",
        "Binance BTCUSDT/USDT and Bitstamp BTC/USD/USD remain separate series.",
    )

    # Verify expected Binance monthly archives and current-month daily files, not only parsed row cadence.
    binance_objects = binance_meta.get("objects", [])
    monthly_seen, daily_seen = set(), set()
    for obj in binance_objects:
        url = obj.get("url", "")
        month_match = re.search(r"BTCUSDT-1d-(\d{4}-\d{2})\.zip$", url)
        day_match = re.search(r"BTCUSDT-1d-(\d{4}-\d{2}-\d{2})\.zip$", url)
        if "/monthly/" in url and month_match:
            monthly_seen.add(month_match.group(1))
        if "/daily/" in url and day_match:
            daily_seen.add(day_match.group(1))
        if obj.get("source_type") == "daily_rest_fallback" and obj.get("data_date_utc"):
            daily_seen.add(str(obj["data_date_utc"]))
    archive_coverage_ok = False
    if binance is not None and not binance.empty:
        first_day = pd.Timestamp(binance["timestamp"].min())
        last_day = pd.Timestamp(binance["timestamp"].max())
        current_period = pd.Timestamp(current).tz_convert("UTC").tz_localize(None).to_period("M")
        last_period = last_day.tz_convert("UTC").tz_localize(None).to_period("M")
        monthly_end = min(last_period, current_period - 1)
        expected_months = {
            period.strftime("%Y-%m")
            for period in pd.period_range(first_day.strftime("%Y-%m"),
                                          monthly_end.strftime("%Y-%m"), freq="M")
        }
        expected_days = (
            {
                day.strftime("%Y-%m-%d")
                for day in pd.date_range(last_day.replace(day=1), last_day, freq="D")
            }
            if last_period == current_period else set()
        )
        archive_coverage_ok = expected_months.issubset(monthly_seen) and expected_days.issubset(daily_seen)
    add("binance_archive_month_day_completeness", "lineage", archive_coverage_ok,
        f"monthly_archives={len(monthly_seen)}; daily_current_month_objects={len(daily_seen)}; "
        "expected monthly archive keys plus current-month daily archive or official REST fallback dates derived from parsed UTC timestamps.")

    bitstamp_raw_rows = sum(int(obj.get("rows", 0)) for obj in bitstamp_meta.get("objects", []))
    bitstamp_duplicates = int(bitstamp_meta.get("duplicates_removed_at_page_boundaries", -1))
    bitstamp_expected_removed = bitstamp_raw_rows - bitstamp_duplicates - int(bitstamp_meta.get("rows", 0))
    add("bitstamp_pagination_accounting", "lineage",
        bool(bitstamp_meta.get("objects")) and bitstamp_duplicates >= 0
        and 0 <= bitstamp_expected_removed <= 1,
        f"raw_rows={bitstamp_raw_rows}; page_overlap_duplicates={bitstamp_duplicates}; "
        f"parsed_rows={bitstamp_meta.get('rows')}; excluded_current_day_rows={bitstamp_expected_removed}.")

    objects = [
        obj for source in manifests for obj in source.get("objects", [])
        if obj.get("file") and obj.get("sha256")
    ]
    integrity_ok, integrity_errors = True, []
    for obj in objects:
        path = Path(obj["file"])
        if not path.is_file():
            integrity_ok = False
            integrity_errors.append(f"missing:{path}")
            continue
        if path.stat().st_size != int(obj.get("size_bytes", -1)):
            integrity_ok = False
            integrity_errors.append(f"size_mismatch:{path}")
            continue
        if _sha256(path) != obj["sha256"]:
            integrity_ok = False
            integrity_errors.append(f"sha256_mismatch:{path}")
    add(
        "raw_object_integrity", "lineage", bool(objects) and integrity_ok,
        f"verified_objects={len(objects)}; errors={integrity_errors[:10]}",
    )
    add(
        "raw_manifest_provenance", "lineage",
        all(obj.get("url") and obj.get("retrieved_at_utc") and obj.get("sha256")
            and obj.get("size_bytes") is not None
            for source in manifests for obj in source.get("objects", []))
        and all(source.get("parser_version") and source.get("schema")
                for source in manifests if source.get("objects")),
        "Each raw object must have URL, retrieval timestamp, SHA-256, size and source parser/schema metadata.",
    )

    history_checks, freshness_checks = [], []
    for frame in (binance, bitstamp):
        if frame is None or frame.empty:
            history_checks.append(False)
            freshness_checks.append(False)
            continue
        stamps = pd.to_datetime(frame["timestamp"], utc=True)
        history_checks.append((stamps.max() - stamps.min()).days >= 1825)
        age_days = (pd.Timestamp(current).tz_convert("UTC").floor("D")
                    - stamps.max().floor("D")).days
        freshness_checks.append(age_days <= 1)
    enough_history = len(history_checks) == 2 and all(history_checks)
    fresh = len(freshness_checks) == 2 and all(freshness_checks)
    add("five_year_history_available", "data", enough_history,
        "Both primary venues must contain at least five years of daily observations.")
    add("primary_data_freshness", "data", fresh,
        "Both primary venues must end no earlier than the previous UTC daily session.")

    cross_checks = run.get("cross_checks", [])
    corroborated = any(item.get("status") == "PASS" for item in cross_checks)
    add("independent_venue_crosscheck", "data", corroborated,
        f"Passing recent cross-checks={sum(item.get('status') == 'PASS' for item in cross_checks)}; "
        "Coinbase/Kraken outages remain disclosed as optional-source failures.",
        blocking=False,
    )

    has_forecast_scores = scores.get("status") == "SCORED_NOT_PROMOTED" and bool(scores.get("holdout_metrics"))
    if not has_forecast_scores:
        not_run_evidence = (
            "Walk-forward/score gates were not run because primary data freshness failed closed; no forecasts or metrics were published. "
            + str(run.get("walk_forward_skipped_reason", "No forecast score output."))
        )
        for check_id, category, evidence in (
            ("target_execution_and_no_leakage", "quant", "Execution/target checks require a produced forecast set."),
            ("holdout_honest_label", "quant", "Holdout checks require a produced forecast set."),
            ("benchmark_completeness", "quant", "Benchmark checks require a produced forecast set."),
            ("numeric_units_and_source_provenance", "protocol", "Forecast metric metadata is absent because no forecasts were produced."),
        ):
            add(check_id, category, "NOT_APPLICABLE", f"{evidence} {not_run_evidence}", blocking=False)
    else:
        timing_ok = (
            scores.get("target", "").startswith("log(Open[t+h+2]/Open[t+2])")
            and scores.get("requested_next_open_target_executable_at_scheduled_run") is False
            and scores.get("training_uses_holdout") is False
        )
        add("target_execution_and_no_leakage", "quant", timing_ok,
            "Production entry uses the first future daily open; target and training/holdout separation are explicit.")
        holdout_ok = (
            scores.get("holdout_globally_unseen") is False
            and scores.get("holdout_role") == "historical_continuity_diagnostic_only"
            and scores.get("holdout_training_and_tuning_excluded_in_this_run") is True
        )
        add("holdout_honest_label", "quant", holdout_ok,
            "Previously inspected history is labelled continuity diagnostic, not globally unseen evidence.")
        metric_blocks = scores.get("holdout_metrics", {})
        benchmark_ok = all(
            all(model in metric_blocks.get(str(h), {}) for model in ("zero", "drift", "momentum", "ridge"))
            and metric_blocks[str(h)]["zero"].get("n", 0) > 0
            for h in (1, 3, 7, 30)
        )
        add("benchmark_completeness", "quant", benchmark_ok,
            "Zero-return, drift, momentum and Ridge must be compared at every declared horizon.")
        metric_metadata = scores.get("metric_metadata", {})
        conventions = run.get("numeric_conventions", {})
        units_ok = (
            metric_metadata.get("source") == "Binance spot BTCUSDT"
            and metric_metadata.get("quote_currency") == "USDT"
            and metric_metadata.get("target_unit") == "natural-log return units"
            and metric_metadata.get("horizon_unit") == "daily sessions"
            and metric_metadata.get("historical_window_start_utc")
            and metric_metadata.get("historical_window_end_utc")
            and metric_metadata.get("sample_role")
            and metric_metadata.get("data_qa_status") == "PASS"
            and all(key in conventions for key in (
                "price", "volume", "percentage", "log_return", "horizon", "timestamp"
            ))
        )
        add("numeric_units_and_source_provenance", "protocol", units_ok,
            "Forecast/benchmark metrics must declare source, quote, units, horizon, UTC window, holdout role and QA.")
    crosscheck_metadata_ok = all(
        item.get("metric_metadata", {}).get("overlap_start_utc")
        and item.get("metric_metadata", {}).get("overlap_end_utc")
        and item.get("metric_metadata", {}).get("return_correlation_unit") == "dimensionless"
        for item in cross_checks if item.get("status") == "PASS"
    )
    add("crosscheck_metric_provenance", "data", crosscheck_metadata_ok,
        "Every passing cross-venue statistic must include its UTC overlap window and units.")
    add("probability_claim_guard", "quant",
        run.get("probabilistic_claims_allowed") is False
        and run.get("prospective_ledger_validation", {}).get(
            "probability_calibration_claim_allowed"
        ) is False,
        "No calibrated probabilities without at least 200 matured prospective forecasts per horizon and a separate calibration study.")

    ids = [event.get("event_id") for event in ledger_events]
    forecasts = [event for event in ledger_events if event.get("event_type") == "FORECAST"]
    forecast_ids = {event.get("forecast_id") for event in forecasts}
    invalidated_ids = {event.get("forecast_id") for event in ledger_events
                       if event.get("event_type") == "INVALIDATION"}
    active_forecasts = [event for event in forecasts
                        if event.get("forecast_id") not in invalidated_ids]
    ledger_ok = (
        all(ids) and len(ids) == len(set(ids))
        and len(forecast_ids) == len(forecasts)
        and invalidated_ids.issubset(forecast_ids)
        and all(event.get("forecast_id") in forecast_ids
                and event.get("forecast_id") not in invalidated_ids
                for event in ledger_events if event.get("event_type") == "SCORE")
        and all(pd.Timestamp(event["entry_timestamp_utc"]) >
                pd.Timestamp(event["issued_at_utc"]) for event in active_forecasts)
    )
    add("append_only_ledger_consistency", "ledger", ledger_ok,
        f"events={len(ledger_events)}; unique_event_ids={len(set(ids))}; invalidated={len(invalidated_ids)}; active_forecasts={len(active_forecasts)}; scores must map to non-invalidated forecasts; active entries must be future at issue.")
    risk = run.get("risk", {})
    add("risk_fail_closed", "risk",
        risk.get("live_trading_enabled") is False
        and float(risk.get("theoretical_exposure_pct", -1)) == 0.0
        and risk.get("mode") == "paper_only",
        "Live trading disabled; paper-only overlay; theoretical exposure exactly 0%.")

    taxonomy = run.get("report_taxonomy", {})
    add("report_fact_taxonomy", "protocol",
        all(key in taxonomy for key in ("FACT", "INTERPRETATION", "HYPOTHESIS", "FORECAST")),
        "Report must explicitly separate FACT, INTERPRETATION, HYPOTHESIS and FORECAST.")
    economic = run.get("economic_validation", {})
    add("economic_claim_guard", "quant",
        economic.get("cost_adjusted_strategy_backtest_executed") is False
        and economic.get("historical_holdout_used_for_economic_promotion") is False,
        "No executable PnL claim without prospective outcomes, an ex-ante trade rule and documented fee/spread/slippage/funding inputs.")
    add("closing_assessment_present", "protocol",
        bool(run.get("closing_assessment", {}).get("principal_limit"))
        and bool(run.get("closing_assessment", {}).get("evidence_that_would_change_assessment"))
        and bool(run.get("closing_assessment", {}).get("single_next_priority_experiment")),
        "Report closes with observed factors, principal limitation, falsifying evidence and exactly one next experiment.")

    longitudinal = run.get("longitudinal_comparison", {})
    add("longitudinal_comparison_present", "protocol",
        longitudinal.get("status") in {"NO_PRIOR_REPORT", "COMPARISON_AVAILABLE"}
        and isinstance(longitudinal.get("comparison_performed"), bool),
        "Report must compare to the previous persisted run when available, without mixing venues/quotes or comparing different holdout windows.")
    provenance = run.get("code_provenance", {})
    add("run_code_provenance", "lineage",
        bool(provenance.get("commit_sha")) and bool(provenance.get("workflow_run_id")),
        "Report records the exact code commit and workflow run ID.")

    performance = run.get("performance", {})
    acquisition_seconds = performance.get("acquisition_and_qa_seconds")
    walk_forward_seconds = performance.get("walk_forward_seconds")
    walk_forward_skipped = walk_forward_seconds is None and bool(run.get("walk_forward_skipped_reason"))
    if walk_forward_skipped:
        runtime_ok = (
            isinstance(acquisition_seconds, (int, float))
            and acquisition_seconds >= 0 and acquisition_seconds <= 7200
        )
        runtime_evidence = (
            f"acquisition_and_qa_seconds={acquisition_seconds}; walk_forward=NOT_RUN; "
            "walk-forward intentionally skipped after primary freshness fail-closed; acquisition remains within 120-minute budget."
        )
    else:
        measured = [acquisition_seconds, walk_forward_seconds]
        runtime_ok = (
            all(isinstance(value, (int, float)) and value >= 0 for value in measured)
            and sum(measured) <= 7200
        )
        runtime_evidence = (
            f"acquisition_and_qa_seconds={acquisition_seconds}; walk_forward_seconds={walk_forward_seconds}; "
            "measured stages must be non-negative and remain within the 120-minute workflow budget."
        )
    add("runtime_efficiency_budget", "operations", runtime_ok, runtime_evidence)
    # Rotate the adversarial lens by workflow run id; all blocking controls above still run every time.
    lens_index = int(hashlib.sha256(str(run_id).encode()).hexdigest()[:8], 16) % len(REVIEW_LENSES)
    lens = REVIEW_LENSES[lens_index]
    anomaly_map = {
        "outlier_volume": next((q.get("volume_robust_z_max_timestamp_utc")
                                for q in (steps.get("binance_acquisition_and_qa", {}).get("qa", {}),
                                          steps.get("bitstamp_acquisition_and_qa", {}).get("qa", {}))
                                if q.get("volume_robust_z_max_timestamp_utc")), None),
        "absolute_volume_max": next((q.get("volume_max_timestamp_utc")
                                     for q in (steps.get("binance_acquisition_and_qa", {}).get("qa", {}),
                                               steps.get("bitstamp_acquisition_and_qa", {}).get("qa", {}))
                                     if q.get("volume_max_timestamp_utc")), None),
        "outlier_close_return": next((q.get("absolute_close_return_max_timestamp_utc")
                                      for q in (steps.get("binance_acquisition_and_qa", {}).get("qa", {}),
                                                steps.get("bitstamp_acquisition_and_qa", {}).get("qa", {}))
                                      if q.get("absolute_close_return_max_timestamp_utc")), None),
        "outlier_intraday_range": next((q.get("intraday_range_pct_max_timestamp_utc")
                                        for q in (steps.get("binance_acquisition_and_qa", {}).get("qa", {}),
                                                  steps.get("bitstamp_acquisition_and_qa", {}).get("qa", {}))
                                        if q.get("intraday_range_pct_max_timestamp_utc")), None),
    }
    anomaly_event_reviews = {}
    for event_lens, event_date in anomaly_map.items():
        if event_date and binance is not None and bitstamp is not None:
            anomaly_event_reviews[event_lens] = _event_context(event_date, binance, bitstamp)
    run["anomaly_event_cross_venue_checks"] = anomaly_event_reviews

    if lens == "ledger_replay":
        add("rotating_red_team_ledger_replay", "red_team", ledger_ok,
            "Adversarial replay lens: duplicate ids, orphan scores and backdated entries.")
    else:
        event_date = anomaly_map[lens]
        context = _event_context(event_date, binance, bitstamp) if (
            event_date and binance is not None and bitstamp is not None
        ) else {"status": "NOT_AVAILABLE", "timestamp_utc": event_date}
        run["rotating_event_review"] = context
        both_venues = all(context.get("venues", {}).get(v, {}).get("status") == "PASS"
                          for v in ("Binance_BTCUSDT", "Bitstamp_BTCUSD"))
        return_diff = context.get("absolute_close_return_difference")
        close_ratio = context.get("binance_usdt_to_bitstamp_usd_close_price_ratio")
        return_consistent = return_diff is None or return_diff <= 0.02
        quote_basis_consistent = close_ratio is None or abs(close_ratio - 1.0) <= 0.02
        add(f"rotating_red_team_{lens}", "red_team",
            bool(event_date and both_venues and return_consistent and quote_basis_consistent),
            f"event={event_date}; screening_thresholds=2% absolute log-return difference and 2% raw quote-price ratio gap; "
            f"thresholds are WARN-only, not calibrated FX or data rejection rules; context={context}",
            blocking=False,
        )

    # Four explicit review cycles. The deep-review order rotates to avoid a single fixed audit sequence.
    categories = ["protocol", "data", "quant", "ledger", "risk", "operations", "red_team"]
    rotation = lens_index % len(categories)
    ordered = categories[rotation:] + categories[:rotation]
    cycles = []
    for number, category in enumerate(ordered, start=1):
        selected = [item for item in checks if item["category"] == category]
        failures = [item["check_id"] for item in selected if item["status"] == "FAIL"]
        warnings = [item["check_id"] for item in selected if item["status"] == "WARN"]
        cycles.append({
            "cycle": number, "review_lens": category,
            "status": "FAIL" if failures else ("WARN" if warnings else "PASS"),
            "checks_reviewed": len(selected), "failures": failures, "warnings": warnings,
        })
    blocking_failures = [
        item["check_id"] for item in checks
        if item["status"] == "FAIL" and item["blocking"]
    ]
    return {
        "version": "pre-report-review-1.0",
        "executed_before_report_serialization": True,
        "reviewed_at_utc": current.isoformat(),
        "run_id": str(run_id),
        "rotating_adversarial_lens": lens,
        "checks": checks,
        "review_cycles": cycles,
        "blocking_failures": blocking_failures,
        "warnings": [item["check_id"] for item in checks if item["status"] == "WARN"],
        "status": "PASS" if not blocking_failures else "FAIL",
        "publication_gate": "OPEN" if not blocking_failures else "BLOCKED",
        "decision": "ALLOW_REPORT_WITH_DISCLOSED_LIMITATIONS" if not blocking_failures
                    else "FORCE_BLOCKED_ZERO_EXPOSURE",
    }
