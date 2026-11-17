"""Structured report construction and same-source longitudinal comparison."""
from __future__ import annotations

import pandas as pd


def _market_snapshot(frame, venue: str, symbol: str, quote: str, retrieved_at: str) -> dict:
    """Describe the latest closed daily candle; never label it a live spot quote."""
    latest = frame.iloc[-1]
    previous = frame.iloc[-2] if len(frame) > 1 else None
    prior_volumes = frame.iloc[-31:-1]["volume"].astype(float)
    prior_30d_median_volume = float(prior_volumes.median()) if not prior_volumes.empty else None
    stamp = pd.Timestamp(latest["timestamp"]).tz_convert("UTC")
    closes = frame["close"].astype(float)
    highs = frame["high"].astype(float)
    lows = frame["low"].astype(float)
    def change_over_sessions(sessions: int) -> float | None:
        if len(frame) <= sessions:
            return None
        prior = float(closes.iloc[-(sessions + 1)])
        return (float(latest["close"]) / prior - 1.0) * 100.0 if prior else None
    previous_close = closes.shift(1)
    true_range = pd.concat([
        highs - lows, (highs - previous_close).abs(), (lows - previous_close).abs()
    ], axis=1).max(axis=1)
    return {
        "venue": venue, "symbol": symbol, "quote_currency": quote,
        "snapshot_type": "latest_closed_daily_candle_not_realtime_spot",
        "candle_open_timestamp_utc": stamp.isoformat(),
        "candle_close_timestamp_utc": (stamp + pd.Timedelta(days=1)).isoformat(),
        "retrieved_at_utc": retrieved_at,
        "open_quote_per_btc": float(latest["open"]),
        "high_quote_per_btc": float(latest["high"]),
        "low_quote_per_btc": float(latest["low"]),
        "close_quote_per_btc": float(latest["close"]),
        "volume_btc": float(latest["volume"]),
        "prior_30d_median_volume_btc": prior_30d_median_volume,
        "volume_vs_prior_30d_median": (
            float(latest["volume"]) / prior_30d_median_volume
            if prior_30d_median_volume and prior_30d_median_volume > 0 else None
        ),
        "intraday_range_pct": (
            (float(latest["high"]) - float(latest["low"])) / float(latest["open"]) * 100.0
        ),
        "prior_close_quote_per_btc": float(previous["close"]) if previous is not None else None,
        "close_change_1d_pct": (
            (float(latest["close"]) / float(previous["close"]) - 1.0) * 100.0
            if previous is not None else None
        ),
        "close_change_7d_pct": change_over_sessions(7),
        "close_change_30d_pct": change_over_sessions(30),
        "volume_7d_btc": float(frame["volume"].astype(float).tail(7).sum()) if len(frame) >= 7 else None,
        "volume_30d_btc": float(frame["volume"].astype(float).tail(30).sum()) if len(frame) >= 30 else None,
        "sma_20_quote_per_btc": float(closes.tail(20).mean()) if len(closes) >= 20 else None,
        "sma_50_quote_per_btc": float(closes.tail(50).mean()) if len(closes) >= 50 else None,
        "sma_200_quote_per_btc": float(closes.tail(200).mean()) if len(closes) >= 200 else None,
        "high_20d_quote_per_btc": float(highs.tail(20).max()) if len(highs) >= 20 else None,
        "low_20d_quote_per_btc": float(lows.tail(20).min()) if len(lows) >= 20 else None,
        "high_50d_quote_per_btc": float(highs.tail(50).max()) if len(highs) >= 50 else None,
        "low_50d_quote_per_btc": float(lows.tail(50).min()) if len(lows) >= 50 else None,
        "atr_14_quote_per_btc": (
            float(true_range.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean().iloc[-1])
            if len(true_range) >= 14 else None
        ),
        "atr_14_pct_of_close": (
            float(true_range.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean().iloc[-1])
            / float(latest["close"]) * 100.0
            if len(true_range) >= 14 and float(latest["close"]) > 0 else None
        ),
    }


def _build_halving_cycle_comparison(frame) -> dict:
    """Compare completed halving cycles at the same elapsed-session horizon; descriptive only."""
    data = frame.reset_index(drop=True).copy()
    stamps = pd.to_datetime(data["timestamp"], utc=True)
    session_dates = stamps.dt.normalize()
    latest_session = session_dates.iloc[-1]
    current_halving = pd.Timestamp("2024-04-20", tz="UTC")
    elapsed_days = int((latest_session - current_halving).days)
    cycles = []
    halving_dates = (
        ("2012 cycle", "2012-11-28"),
        ("2016 cycle", "2016-07-09"),
        ("2020 cycle", "2020-05-11"),
        ("2024 cycle (current)", "2024-04-20"),
    )
    for label, date_text in halving_dates:
        halving = pd.Timestamp(date_text, tz="UTC")
        starts = data.index[session_dates == halving]
        if len(starts) == 0:
            cycles.append({
                "cycle": label,
                "halving_date": date_text,
                "status": "INSUFFICIENT_HISTORY",
                "first_available_session_utc": stamps.iloc[0].isoformat(),
            })
            continue
        start_idx = int(starts[0])
        target = halving + pd.Timedelta(days=elapsed_days)
        ends = data.index[(session_dates <= target) & (data.index >= start_idx)]
        if len(ends) == 0:
            cycles.append({
                "cycle": label, "halving_date": date_text,
                "status": "INSUFFICIENT_FORWARD_HISTORY",
            })
            continue
        end_idx = int(ends[-1])
        segment = data.iloc[start_idx:end_idx + 1]
        closes = segment["close"].astype(float)
        start_close = float(closes.iloc[0])
        end_close = float(closes.iloc[-1])
        peak_idx = int(closes.to_numpy().argmax())
        peak_close = float(closes.iloc[peak_idx])
        drawdown = closes / closes.cummax() - 1.0
        cycles.append({
            "cycle": label,
            "halving_date": date_text,
            "status": "PASS",
            "elapsed_sessions": len(segment) - 1,
            "comparison_target_session_utc": stamps.iloc[end_idx].isoformat(),
            "start_close_usd": start_close,
            "close_at_same_elapsed_horizon_usd": end_close,
            "return_at_same_elapsed_horizon_pct": (end_close / start_close - 1.0) * 100.0,
            "maximum_close_return_pct": (peak_close / start_close - 1.0) * 100.0,
            "days_to_maximum_close": peak_idx,
            "maximum_close_drawdown_from_peak_pct": float(drawdown.min()) * 100.0,
        })
    current = next((item for item in cycles if item["cycle"].startswith("2024")), {})
    historical_cycles = [
        item for item in cycles
        if not item["cycle"].startswith("2024") and item.get("status") == "PASS"
    ]
    return {
        "status": "PASS" if current.get("status") == "PASS" and historical_cycles else "PARTIAL",
        "source": "Bitstamp BTC/USD daily OHLCV; same venue and quote currency",
        "latest_closed_session_utc": stamps.iloc[-1].isoformat(),
        "current_cycle_elapsed_sessions": elapsed_days,
        "comparison_horizon_days": elapsed_days,
        "cycles": cycles,
        "interpretation_limit": (
            "Descriptive comparison at the same elapsed days after halving; sample is small, "
            "cycles are structurally different, and this is not a timing forecast."
        ),
    }


def _build_report_sections(run: dict, scores: dict) -> tuple[dict, dict, dict]:
    metrics = scores.get("holdout_metrics", {})
    horizons = sorted(metrics, key=lambda value: int(value))
    zero_wins = [
        horizon for horizon in horizons
        if metrics[horizon].get("zero", {}).get("mae") is not None
        and all(metrics[horizon]["zero"]["mae"] <= block.get("mae", float("inf"))
                for model, block in metrics[horizon].items() if model != "zero")
    ]
    prospective = run.get("prospective_ledger_validation", {})
    by_horizon = prospective.get("by_horizon", {})
    matured = {str(h): int(by_horizon.get(str(h), {}).get("n", 0)) for h in (1, 3, 7, 30)}
    new_forecasts = int(run.get("ledger", {}).get("forecast_events_created", 0))
    scored_now = int(run.get("ledger", {}).get("score_events_created", 0))
    snapshots = run.get("market_snapshot", {}).get("venues", [])
    primary = next((item for item in snapshots if item.get("venue") == "Binance"), None)
    drivers = []
    if primary:
        source = "Binance spot BTCUSDT"
        stamp = primary.get("candle_open_timestamp_utc")
        for name, value, unit, window in (
            ("Variazione close-to-close", primary.get("close_change_1d_pct"), "%",
             "1 sessione giornaliera"),
            ("Ampiezza intraday high-low/open", primary.get("intraday_range_pct"), "%",
             "candela giornaliera"),
            ("Volume rispetto alla mediana precedente", primary.get("volume_vs_prior_30d_median"),
             "multiplo", "volume giornaliero / mediana 30 sessioni precedenti"),
        ):
            if value is not None:
                drivers.append({
                    "name": name, "value": value, "unit": unit, "window": window,
                    "timestamp_utc": stamp, "source": source, "qa_status": "PASS",
                    "interpretation": "Osservazione descrittiva; non attribuzione causale.",
                })
    supplemental = run.get("supplemental_data", {})
    coverage = supplemental.get("coverage", {})
    supplemental_facts = [
        {
            "statement": f"Supplemental feed {name}: {details.get('status', 'UNSPECIFIED')}.",
            "evidence": details,
        }
        for name, details in coverage.items()
    ]
    taxonomy = {
        "FACT": [
            {
                "statement": f"{step.get('step')}: {step.get('status')}.",
                "evidence": step.get("qa", step.get("error", "stato registrato nel run report")),
            }
            for step in run.get("steps", [])
        ] + [
            {
                "statement": "Le metriche storiche sono diagnostiche di continuità, non prove prospettiche.",
                "evidence": {
                    "holdout_role": scores.get("holdout_role"),
                    "holdout_globally_unseen": scores.get("holdout_globally_unseen"),
                    "historical_rows_by_horizon": run.get("historical_continuity_rows_by_horizon", {}),
                },
            },
            {
                "statement": "Il ledger prospettico conteggia esclusivamente eventi SCORE maturati.",
                "evidence": {"matured_by_horizon": matured, "new_score_events": scored_now},
            },
        ] + supplemental_facts + [
            {
                "statement": "Il confronto dei cicli post-halving è descrittivo e usa la stessa venue/quote e lo stesso orizzonte temporale.",
                "evidence": run.get("cycle_comparison", {}),
            },
        ],
        "INTERPRETATION": [
            {
                "statement": "Zero-return ha la MAE più bassa in tutti gli orizzonti storici confrontati."
                if len(zero_wins) == len(horizons) and horizons else
                "Il confronto storico non dimostra un vantaggio uniforme del challenger.",
                "horizons_where_zero_has_lowest_mae": zero_wins,
                "scope": "holdout storico già ispezionato; sola diagnostica di continuità",
            },
            {
                "statement": "Ridge resta challenger non promosso; nessuna conclusione economica è autorizzata.",
            },
        ],
        "HYPOTHESIS": [
            {
                "experiment_id": "V5.5-OHLCV-001",
                "statement": "Volume normalizzato e geometria delle candele potrebbero aggiungere informazione oltre le feature price-only.",
                "status": "PROPOSED_NOT_RUN",
                "evaluation_scope": "solo ledger prospettico; holdout storico escluso",
            },
        ],
        "FORECAST": {
            "new_point_forecasts_issued_this_run": new_forecasts,
            "new_forecasts_scored_this_run": scored_now,
            "matured_prospective_counts_by_horizon": matured,
            "calibrated_probabilities_published": False,
            "directional_alerts_published": False,
            "qualification": "Eventuali valori nel ledger sono point forecast sperimentali; non sono probabilità calibrate né segnali operativi.",
        },
    }
    economic = {
        "status": "BLOCKED_INSUFFICIENT_PROSPECTIVE_EVIDENCE",
        "matured_prospective_forecasts_by_horizon": matured,
        "minimum_required_per_horizon": 200,
        "historical_holdout_used_for_economic_promotion": False,
        "cost_adjusted_strategy_backtest_executed": False,
        "reason": (
            "Nessun campione prospettico maturo sufficiente; il periodo storico è già stato ispezionato. "
            "Non sono disponibili nel run una regola operativa approvata e serie storiche documentate "
            "di fee effettive, spread, slippage e funding per simulare PnL eseguibile."
        ),
        "required_inputs": [
            "almeno 200 forecast prospettici maturati per orizzonte",
            "regola di ingresso/uscita e sizing fissata ex ante",
            "fee schedule applicabile all'account/venue e relativo timestamp",
            "spread e slippage osservati o una sensibilità esplicitamente ipotetica",
            "funding solo per strumenti derivati, con serie e timestamp",
            "stress 1x/2x/3x costi, turnover, drawdown e confronto benchmark",
        ],
    }
    closing = {
        "observed_drivers": drivers,
        "principal_limit": (
            "Assenza di evidenza prospettica maturata e di validazione economica eseguibile; "
            "il holdout storico è solo diagnostico."
        ),
        "evidence_that_would_change_assessment": (
            "Un campione prospettico indipendente, almeno 200 osservazioni maturate per orizzonte, "
            "lift stabile contro zero-return/drift dopo HAC-Holm, calibrazione verificata e valore netto "
            "positivo dopo costi documentati e stress 1x/2x/3x."
        ),
        "single_next_priority_experiment": (
            "V5.5-OHLCV-001: challenger volume-surprise/candle-geometry, registrato prima del test "
            "e valutato esclusivamente sul ledger prospettico."
        ),
    }
    return taxonomy, economic, closing



def _walk_forward_scores(report: dict | None) -> dict:
    if not report:
        return {}
    step = next((item for item in report.get("steps", [])
                 if item.get("step") == "walk_forward"), {})
    return step.get("scores", {})


def _build_longitudinal_comparison(previous: dict | None, current: dict,
                                   current_scores: dict) -> dict:
    if not previous:
        return {
            "status": "NO_PRIOR_REPORT",
            "comparison_performed": False,
            "reason": "No prior persisted run_report.json was available at run start.",
        }
    previous_snapshots = {
        (item.get("venue"), item.get("symbol"), item.get("quote_currency")): item
        for item in previous.get("market_snapshot", {}).get("venues", [])
    }
    venue_comparison = []
    for item in current.get("market_snapshot", {}).get("venues", []):
        key = (item.get("venue"), item.get("symbol"), item.get("quote_currency"))
        old = previous_snapshots.get(key)
        if old and old.get("close_quote_per_btc") and item.get("close_quote_per_btc"):
            change = (
                float(item["close_quote_per_btc"]) / float(old["close_quote_per_btc"]) - 1.0
            ) * 100.0
            venue_comparison.append({
                "venue": item["venue"], "symbol": item["symbol"],
                "quote_currency": item["quote_currency"],
                "previous_candle_open_timestamp_utc": old.get("candle_open_timestamp_utc"),
                "current_candle_open_timestamp_utc": item.get("candle_open_timestamp_utc"),
                "close_change_since_previous_report_pct": change,
                "unit": "%", "comparison_type": "same_venue_same_quote_only",
            })
        else:
            venue_comparison.append({
                "venue": item.get("venue"), "symbol": item.get("symbol"),
                "status": "NOT_COMPARABLE_NO_MATCHING_PRIOR_SNAPSHOT",
            })
    previous_scores = _walk_forward_scores(previous)
    previous_window = (
        previous_scores.get("holdout_start_utc"), previous_scores.get("holdout_end_utc")
    )
    current_window = (
        current_scores.get("holdout_start_utc"), current_scores.get("holdout_end_utc")
    )
    metric_comparison = {"status": "NOT_COMPARABLE_DIFFERENT_OR_MISSING_HOLDOUT_WINDOW"}
    if previous_window == current_window and all(current_window):
        prior_metrics = previous_scores.get("holdout_metrics", {})
        current_metrics = current_scores.get("holdout_metrics", {})
        rows = {}
        for horizon in ("1", "3", "7", "30"):
            old = prior_metrics.get(horizon, {}).get("zero", {}).get("mae")
            new = current_metrics.get(horizon, {}).get("zero", {}).get("mae")
            rows[horizon] = {
                "previous_zero_mae_log_return_units": old,
                "current_zero_mae_log_return_units": new,
                "difference_log_return_units": (
                    float(new) - float(old) if old is not None and new is not None else None
                ),
            }
        metric_comparison = {
            "status": "COMPARABLE_SAME_HISTORICAL_CONTINUITY_WINDOW",
            "holdout_start_utc": current_window[0],
            "holdout_end_utc": current_window[1],
            "zero_return_mae": rows,
            "warning": "Same previously inspected historical window; not independent prospective evidence.",
        }
    previous_ledger = previous.get("prospective_ledger_validation", {}).get("by_horizon", {})
    current_ledger = current.get("prospective_ledger_validation", {}).get("by_horizon", {})
    matured_counts = {
        str(h): {
            "previous_matured": int(previous_ledger.get(str(h), {}).get("n", 0)),
            "current_matured": int(current_ledger.get(str(h), {}).get("n", 0)),
        }
        for h in (1, 3, 7, 30)
    }
    return {
        "status": "COMPARISON_AVAILABLE",
        "comparison_performed": True,
        "previous_run_started_at_utc": previous.get("started_at_utc"),
        "previous_run_finished_at_utc": previous.get("finished_at_utc"),
        "previous_run_status": previous.get("status"),
        "current_run_status": current.get("status"),
        "same_venue_price_snapshots": venue_comparison,
        "historical_benchmark_comparison": metric_comparison,
        "prospective_matured_counts": matured_counts,
        "interpretation_policy": (
            "Compare price snapshots only within identical venue/symbol/quote. Compare MAE only on identical "
            "holdout windows; all such historical results remain continuity diagnostics."
        ),
    }


def _display(value, digits: int = 4) -> str:
    if value is None:
        return "n/d"
    if isinstance(value, float):
        return f"{value:,.{digits}f}"
    return str(value)


def render_markdown_report(run: dict, scores: dict) -> str:
    """Render a human-readable report from the exact run payload; no extra data lookups."""
    lines = [
        "# BTC Quant Desk — report giornaliero",
        "",
        f"- Protocollo: **{run.get('protocol', 'n/d')}**",
        f"- Stato: **{run.get('status', 'BLOCKED')}**",
        f"- Avvio UTC: {run.get('started_at_utc', 'n/d')}",
        f"- Fine UTC: {run.get('finished_at_utc', 'n/d')}",
        f"- Commit: `{run.get('code_provenance', {}).get('commit_sha', 'n/d')}`",
        f"- Workflow run: {run.get('code_provenance', {}).get('workflow_run_id', 'n/d')}",
        "",
        "> I valori di mercato sono distinti tra osservazioni live, snapshot e candele chiuse. USD e USDT non sono convertiti né uniti.",
        "",
        "## 1. Acquisizione e qualità dati",
        "",
        "| Feed | Stato | Evidenza / dettaglio |",
        "|---|---|---|",
    ]
    for step in run.get("steps", []):
        qa = step.get("qa", {})
        detail = (
            f"righe={qa.get('rows')}, gap={qa.get('gap_count')}, duplicati={qa.get('duplicates')}, "
            f"ultima candela={qa.get('last_timestamp_utc')}"
            if qa else step.get("error", step.get("status", "n/d"))
        )
        lines.append(f"| {step.get('step')} | {step.get('status')} | {detail} |")
    lines += ["", "## 2. Prezzi spot — ultime candele giornaliere chiuse", "",
              "| Venue | Strumento | Candela UTC | Close | 1D | 7D | 30D | Range intraday | Vol 1D BTC | Vol 7D BTC | Vol 30D BTC |",
              "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for item in run.get("market_snapshot", {}).get("venues", []):
        lines.append(
            f"| {item.get('venue')} | {item.get('symbol')} ({item.get('quote_currency')}) | "
            f"{item.get('candle_open_timestamp_utc')} | {_display(item.get('close_quote_per_btc'), 2)} | "
            f"{_display(item.get('close_change_1d_pct'), 3)}% | "
            f"{_display(item.get('close_change_7d_pct'), 3)}% | "
            f"{_display(item.get('close_change_30d_pct'), 3)}% | "
            f"{_display(item.get('intraday_range_pct'), 3)}% | {_display(item.get('volume_btc'), 2)} | "
            f"{_display(item.get('volume_7d_btc'), 2)} | {_display(item.get('volume_30d_btc'), 2)} |"
        )
    lines += ["", "### Quotazioni spot — ultimo scambio osservato", "",
              "| Venue | Stato | Prezzo | Variazione 24h | Volume base 24h | Timestamp ultimo scambio UTC | Età sec |",
              "|---|---|---:|---:|---:|---|---:|"]
    live_spot = run.get("supplemental_data", {}).get("spot_live", {})
    for venue, item in live_spot.get("venues", {}).items():
        lines.append(
            f"| {venue} | {item.get('status')} | {_display(item.get('last_trade_price'), 2)} | "
            f"{_display(item.get('price_change_24h_pct'), 3)}% | "
            f"{_display(item.get('base_volume_24h_btc'), 2)} BTC | "
            f"{item.get('last_trade_timestamp_utc')} | {_display(item.get('last_trade_age_seconds'), 1)} |"
        )
    lines += ["", "### Livelli tecnici descrittivi — non segnali", "",
              "| Venue | SMA20 | SMA50 | SMA200 | Massimo 20D | Minimo 20D | ATR14 |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for item in run.get("market_snapshot", {}).get("venues", []):
        lines.append(
            f"| {item.get('venue')} | {_display(item.get('sma_20_quote_per_btc'), 2)} | "
            f"{_display(item.get('sma_50_quote_per_btc'), 2)} | "
            f"{_display(item.get('sma_200_quote_per_btc'), 2)} | "
            f"{_display(item.get('high_20d_quote_per_btc'), 2)} | "
            f"{_display(item.get('low_20d_quote_per_btc'), 2)} | "
            f"{_display(item.get('atr_14_quote_per_btc'), 2)} |"
        )
    lines += ["", "## 3. Copertura dei dati supplementari", "",
              "| Categoria | Stato | Nota / limite |", "|---|---|---|"]
    supplemental = run.get("supplemental_data", {})
    coverage = supplemental.get("coverage", {})
    for name, item in coverage.items():
        note = item.get("reason", item.get("note", ""))
        lines.append(f"| {name} | {item.get('status', 'n/d')} | {note} |")

    for name, label in (("binance_futures", "Binance Futures"), ("bybit_futures", "Bybit Linear")):
        item = supplemental.get(name, {})
        if item:
            lines += ["", f"### {label}", "",
                      f"- Stato: {item.get('status', 'n/d')}",
                      f"- Funding corrente/ultimo: {_display(item.get('current_funding_rate', item.get('funding_rate_current')))} ({item.get('funding_rate_unit', 'fraction per funding interval')})",
                      f"- Open interest: {_display(item.get('open_interest_btc'))} BTC",
                      f"- Variazione OI 1D: {_display(item.get('open_interest_value_change_1d_pct', item.get('open_interest_history_change_1d_pct')))}%",
                      f"- Variazione OI 7D: {_display(item.get('open_interest_value_change_7d_pct', item.get('open_interest_history_change_7d_pct')))}%",
                      f"- Variazione OI 30D: {_display(item.get('open_interest_value_change_30d_pct', item.get('open_interest_history_change_30d_pct')))}%",
                      f"- Long/short account ratio: {_display(item.get('global_long_short_account_ratio'))} (long {_display(item.get('global_long_account_share_pct'), 2)}% / short {_display(item.get('global_short_account_share_pct'), 2)}%)",
                      f"- Taker buy/sell ratio (Binance proxy): {_display(item.get('taker_buy_sell_ratio_latest'))}",
                      f"- Volume futures ultima candela chiusa 1D (Binance): {_display(item.get('last_closed_daily_futures_volume_btc'))} BTC",
                      f"- Volume futures 24h (Bybit): {_display(item.get('volume_24h_btc'))} BTC"]
            if item.get("errors"):
                lines.append(f"- Errori feed: {item['errors']}")

    okx = supplemental.get("okx_swap", {})
    if okx:
        oi_history = okx.get("open_interest_history", {})
        taker_summary = okx.get("daily_taker_volume_summary", {})
        taker_windows = taker_summary.get("cumulative_delta_btc", {})
        venue_coverage = coverage.get("per_exchange_derivatives", {}).get("by_exchange", {})
        lines += [
            "", "### OKX BTC-USDT Perpetual", "",
            f"- Stato: {okx.get('status', 'n/d')}; strumento {okx.get('instrument', 'n/d')}.",
            f"- Ultimo prezzo: {_display(okx.get('last_price_usdt'), 2)} USDT.",
            (f"- Volume 24h: {_display(okx.get('volume_24h_base_currency'), 2)} BTC "
             f"({_display(okx.get('volume_24h_contracts'), 2)} contratti)."),
            (f"- Open interest snapshot: {_display(okx.get('open_interest_btc'), 2)} BTC "
             f"({_display(okx.get('open_interest_usd'), 0)} USD)."),
            (f"- OI storico giornaliero UTC: 1D {_display(oi_history.get('change_1d_pct'), 2)}%; "
             f"7D {_display(oi_history.get('change_7d_pct'), 2)}%; "
             f"30D {_display(oi_history.get('change_30d_pct'), 2)}% "
             f"(ultimo punto {oi_history.get('timestamp_utc', 'n/d')})."),
            (f"- Funding previsto per il settlement corrente: {_display(okx.get('funding_rate_predicted_current'), 8)}; "
             f"ultimo settlement: {_display(okx.get('settled_funding_rate'), 8)} "
             f"(stato {okx.get('funding_settlement_state', 'n/d')}; "
             f"unità frazione per intervallo)."),
            (f"- Settlement timestamp: {okx.get('funding_timestamp_utc', 'n/d')}; "
             f"prossimo funding: {okx.get('next_funding_time_utc', 'n/d')}."),
            f"- Storico funding: {okx.get('funding_history_rows', 0)} settlement acquisiti.",
            (f"- Delta taker futures BTC (buy − sell, barre UTC chiuse): "
             f"1D {_display(taker_windows.get('1d'), 2)} BTC; "
             f"7D {_display(taker_windows.get('7d'), 2)} BTC; "
             f"30D {_display(taker_windows.get('30d'), 2)} BTC."),
            f"- Nota CVD: {taker_summary.get('measurement_note', 'n/d')}",
            "- Liquidazioni: NOT_ACQUIRED; nessuna stima ricavata da endpoint non pertinenti.",
            (f"- Copertura per venue: Binance {venue_coverage.get('binance_futures', 'n/d')}; "
             f"Bybit {venue_coverage.get('bybit_futures', 'n/d')}; "
             f"OKX {venue_coverage.get('okx_swap', okx.get('status', 'n/d'))}."),
        ]
        if okx.get("errors"):
            lines.append(f"- Errori feed OKX: {okx['errors']}")

    cvd = supplemental.get("cvd", {})
    if cvd:
        lines += ["", "### CVD orario Binance — delta taker aggregato", "",
                  f"- Stato: {cvd.get('status')}. {cvd.get('measurement_note', '')}",
                  "| Mercato | Finestra | Delta BTC | Delta / volume % | Volume BTC | Buy BTC | Sell BTC |",
                  "|---|---:|---:|---:|---:|---:|---:|"]
        for market, label in (("spot", "Spot BTCUSDT"), ("futures", "Futures BTCUSDT")):
            market_data = cvd.get("markets", {}).get(market, {})
            for horizon in ("24h", "7d", "30d"):
                item = market_data.get(horizon, {})
                lines.append(
                    f"| {label} | {horizon} | {_display(item.get('cumulative_delta_btc'), 2)} | "
                    f"{_display(item.get('delta_pct_of_total_volume'), 2)}% | "
                    f"{_display(item.get('total_volume_btc'), 2)} | "
                    f"{_display(item.get('taker_buy_volume_btc'), 2)} | "
                    f"{_display(item.get('taker_sell_volume_btc'), 2)} |"
                )
    options = supplemental.get("deribit_options", {})
    if options:
        lines += ["", "### Opzioni Deribit", "",
                  f"- Stato: {options.get('status', 'n/d')}; open interest con ritardo provider di {options.get('open_interest_delay_hours', 'n/d')} ore.",
                  f"- OI call/put: {_display(options.get('total_call_open_interest_btc'))} / {_display(options.get('total_put_open_interest_btc'))} BTC.",
                  f"- Put/call OI: {_display(options.get('put_call_open_interest_ratio'))}.",
                  f"- Put/call volume USD 24h: {_display(options.get('put_call_volume_ratio'))}."]
        lines += ["", "| Scadenza | DTE | ATM IV % | OI call BTC | OI put BTC |",
                  "|---|---:|---:|---:|---:|"]
        for expiry in options.get("expiry_term_structure", [])[:12]:
            lines.append(
                f"| {expiry.get('expiry_date')} | {expiry.get('days_to_expiry')} | "
                f"{_display(expiry.get('nearest_atm_mark_iv_pct'), 2)} | "
                f"{_display(expiry.get('call_open_interest_btc'), 2)} | "
                f"{_display(expiry.get('put_open_interest_btc'), 2)} |"
            )
        lines += ["", "| Scadenza | 25Δ put IV % | 25Δ call IV % | Put-call skew vol points |",
                  "|---|---:|---:|---:|"]
        for skew in options.get("sampled_25d_skew", []):
            lines.append(
                f"| {skew.get('expiry_date')} | {_display(skew.get('put_25d_mark_iv_pct'), 2)} | "
                f"{_display(skew.get('call_25d_mark_iv_pct'), 2)} | "
                f"{_display(skew.get('put_minus_call_25d_skew_vol_points'), 2)} |"
            )
        lines.append(
            f"- Gamma/dealer positioning: {options.get('dealer_gamma_positioning', {}).get('status')}; "
            f"{options.get('dealer_gamma_positioning', {}).get('reason', '')}"
        )

    etf = supplemental.get("us_spot_etf_flows", {})
    if etf:
        latest = etf.get("latest_session", {})
        lines += ["", "### ETF spot Bitcoin USA", "",
                  f"- Stato: {etf.get('status')}; dati aggiornati al {etf.get('updated_through')} (circa {etf.get('business_sessions_behind_approx')} sessioni USA di ritardo).",
                  f"- Flusso ultima sessione: {_display(latest.get('netFlowUsd'), 2)} USD.",
                  f"- AUM totale ultima sessione: {_display(latest.get('totalNetAssetsUsd'), 2)} USD.",
                  f"- Flusso cumulativo dalla partenza: {_display(etf.get('cumulative_net_flow_usd'), 2)} USD.",
                  f"- Flusso ultime 21 sessioni: {_display(etf.get('last_21_sessions_net_flow_usd'), 2)} USD.",
                  f"- Flusso ultime 30 sessioni: {_display(etf.get('last_30_sessions_net_flow_usd'), 2)} USD.",
                  f"- Fonte/licenza: {etf.get('source')} / {etf.get('license')}."]
    macro = supplemental.get("macro", {})
    if macro:
        lines += ["", "## 4. Macro e mercati USA", "",
                  "| Serie | Periodo osservato | Freschezza fino | Valore | Unità | Stato | Recuperato UTC | Fonte / metodo |",
                  "|---|---|---|---:|---|---|---|---|"]
        for series_id, item in macro.get("series", {}).items():
            lines.append(
                f"| {series_id} — {item.get('label')} | {item.get('observation_date')} | "
                f"{item.get('freshness_reference_date', item.get('observation_date'))} | "
                f"{_display(item.get('value'), 4)} | {item.get('unit')} | {item.get('status')} | "
                f"{item.get('retrieved_at_utc', macro.get('retrieved_at_utc', 'n/d'))} | "
                f"{item.get('source_method', item.get('source_url', 'FRED'))} |"
            )
        if macro.get("errors"):
            lines.append("")
            lines.append(f"Feed macro non acquisiti: {macro['errors']}")

    cycle = run.get("cycle_comparison", {})
    if cycle:
        lines += ["", "## 5. Ciclo Bitcoin — confronto post-halving", "",
                  f"- Stato: {cycle.get('status')}; fonte: {cycle.get('source')}.",
                  f"- Orizzonte corrente: {cycle.get('current_cycle_elapsed_sessions')} sessioni dal 20 aprile 2024.",
                  f"- Limite: {cycle.get('interpretation_limit', '')}",
                  "| Ciclo | Stato | Giorni/sessioni | Rendimento stesso orizzonte | Massimo rendimento | Giorni al picco | Drawdown massimo da picco |",
                  "|---|---|---:|---:|---:|---:|---:|"]
        for item in cycle.get("cycles", []):
            lines.append(
                f"| {item.get('cycle')} | {item.get('status')} | "
                f"{item.get('elapsed_sessions', 'n/d')} | "
                f"{_display(item.get('return_at_same_elapsed_horizon_pct'), 2)}% | "
                f"{_display(item.get('maximum_close_return_pct'), 2)}% | "
                f"{item.get('days_to_maximum_close', 'n/d')} | "
                f"{_display(item.get('maximum_close_drawdown_from_peak_pct'), 2)}% |"
            )

    news = supplemental.get("news", {})
    if news:
        lines += ["", "## 6. Eventi, regolamentazione e geopolitica — feed descrittivi", "",
                  f"- Stato: {news.get('status')}. {news.get('interpretation_limit', '')}",
                  "| Fonte | Stato | Acquisiti | Rilevanti nel report |",
                  "|---|---|---:|---:|"]
        for source_name, source_item in news.get("source_status", {}).items():
            lines.append(
                f"| {source_name} | {source_item.get('status')} | "
                f"{source_item.get('article_count', 'n/d')} | "
                f"{source_item.get('relevant_article_count', 'n/d')} |"
            )
        for article in news.get("articles", [])[:12]:
            title = str(article.get("title", "")).replace("|", "\\|").replace("\\n", " ")
            date_label = article.get("published_at_utc") or article.get("seen_at_utc") or "data non disponibile"
            tags = ", ".join(article.get("keyword_tags", [])) or "nessun tag"
            lines.append(
                f"- {date_label} — {article.get('source')} — {title} "
                f"[{tags}] — {article.get('url')}"
            )

    taxonomy = run.get("report_taxonomy", {})
    lines += ["", "## 7. Fatti, interpretazioni, ipotesi e previsioni", "",
              "### FATTI"]
    for item in taxonomy.get("FACT", []):
        lines.append(f"- {item.get('statement')}")
    lines.append("### INTERPRETAZIONI")
    for item in taxonomy.get("INTERPRETATION", []):
        lines.append(f"- {item.get('statement')}")
    lines.append("### IPOTESI")
    for item in taxonomy.get("HYPOTHESIS", []):
        lines.append(
            f"- {item.get('statement')} — stato: {item.get('status', 'n/d')}; "
            f"esperimento: {item.get('experiment_id', 'n/d')}."
        )
    forecast_taxonomy = taxonomy.get("FORECAST", {})
    lines += ["### FORECAST",
              f"- Point forecast emessi in questo run: {forecast_taxonomy.get('new_point_forecasts_issued_this_run', 0)}.",
              f"- Forecast maturati/scorati in questo run: {forecast_taxonomy.get('new_forecasts_scored_this_run', 0)}.",
              f"- Probabilità calibrate pubblicate: {forecast_taxonomy.get('calibrated_probabilities_published', False)}.",
              f"- {forecast_taxonomy.get('qualification', 'Nessuna previsione qualificata disponibile.')}"]

    lines += ["", "## 8. Validazione quantitativa", "",
              "Le metriche seguenti sono diagnostiche sul periodo storico già ispezionato; non sono prova prospettica né PnL eseguibile.",
              "", "| Orizzonte | N | Zero MAE | Drift MAE | Momentum MAE | Ridge MAE |",
              "|---:|---:|---:|---:|---:|---:|"]
    for horizon, block in scores.get("holdout_metrics", {}).items():
        lines.append(
            f"| {horizon} sessioni | {block.get('zero', {}).get('n', 0)} | "
            f"{_display(block.get('zero', {}).get('mae'), 6)} | "
            f"{_display(block.get('drift', {}).get('mae'), 6)} | "
            f"{_display(block.get('momentum', {}).get('mae'), 6)} | "
            f"{_display(block.get('ridge', {}).get('mae'), 6)} |"
        )
    ledger = run.get("ledger", {})
    lines += ["", "## 9. Ledger e rischio", "",
              f"- Stato ledger: {ledger.get('persistence_status', 'n/d')}; eventi prima/dopo: {ledger.get('existing_events_before_run', 'n/d')} / {ledger.get('total_events_after_run', 'n/d')}.",
              f"- Nuove previsioni: {ledger.get('forecast_events_created', 0)}; duplicate soppresse: {ledger.get('duplicate_forecasts_suppressed', 0)}; score maturati: {ledger.get('score_events_created', 0)}.",
              f"- Campione prospettico: {run.get('prospective_ledger_validation', {}).get('decision', 'n/d')}.",
              f"- Rischio: {run.get('risk', {}).get('mode', 'n/d')}; live trading: {run.get('risk', {}).get('live_trading_enabled', False)}; esposizione teorica: {_display(run.get('risk', {}).get('theoretical_exposure_pct'), 2)}%.",
              "- Champion congelato: zero-return. Ridge è challenger non promosso.",
              "- Nessun PnL economico o probabilità calibrata è dichiarato.",
              "", "## 10. Revisione critica e conclusione", ""]
    audit = run.get("pre_report_review", {})
    lines.append(
        f"- Gate pre-report: {audit.get('status', 'n/d')}; cicli completati: "
        f"{len(audit.get('review_cycles', []))}; fallimenti bloccanti: "
        f"{audit.get('blocking_failures', [])}."
    )
    closing = run.get("closing_assessment", {})
    for driver in closing.get("observed_drivers", []):
        lines.append(
            f"- Fattore osservato: {driver.get('name')} = {_display(driver.get('value'), 4)} "
            f"{driver.get('unit')} ({driver.get('source')}, {driver.get('timestamp_utc')})."
        )
    lines.append(f"- Limite principale: {closing.get('principal_limit', 'n/d')}")
    lines.append(f"- Evidenza che cambierebbe la valutazione: {closing.get('evidence_that_would_change_assessment', 'n/d')}")
    lines.append(f"- Prossimo esperimento: {closing.get('single_next_priority_experiment', 'n/d')}")
    lines += ["", "## 11. Limiti dichiarati", ""]
    for limitation in run.get("limitations", []):
        lines.append(f"- {limitation}")
    return "\n".join(lines) + "\n"
