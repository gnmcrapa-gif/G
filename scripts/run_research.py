from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from btc_quant.acquisition import download_binance_daily, download_bitstamp_recent, write_manifest
from btc_quant.research import cross_check_venues, walk_forward
from btc_quant.validation import validate_ohlcv


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/raw")
    parser.add_argument("--output-dir", default="reports/latest")
    parser.add_argument("--min-train-rows", type=int, default=730)
    args = parser.parse_args()
    data_dir, output_dir = Path(args.data_dir), Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    run = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "status": "BLOCKED",
           "protocol": "V5.3", "steps": [], "limitations": []}
    manifests = []
    try:
        binance, manifest = download_binance_daily(data_dir / "binance")
        manifests.append(manifest)
        qa = validate_ohlcv(binance)
        run["steps"].append({"step": "binance_acquisition_and_qa", "status": "PASS",
                             "qa": qa, "first": binance.timestamp.min().isoformat(),
                             "last": binance.timestamp.max().isoformat()})
        bitstamp, bs_manifest = download_bitstamp_recent(data_dir / "bitstamp")
        manifests.append(bs_manifest)
        bs_qa = validate_ohlcv(bitstamp)
        run["steps"].append({"step": "bitstamp_acquisition_and_qa", "status": "PASS", "qa": bs_qa})
        venue_check = cross_check_venues(binance, bitstamp)
        run["steps"].append({"step": "venue_cross_check", **venue_check})
        write_manifest(manifests, output_dir / "data_manifest.json")
        # Keep venue/quote series separate. Binance alone is the modelling series.
        predictions, scores = walk_forward(binance, min_train_rows=args.min_train_rows)
        if len(predictions):
            counts = predictions.groupby("horizon").size().to_dict()
            run["matured_oos_counts_by_horizon"] = {str(k): int(v) for k, v in counts.items()}
            run["probabilistic_claims_allowed"] = all(v >= 200 for v in counts.values())
        else:
            run["probabilistic_claims_allowed"] = False
        predictions.to_csv(output_dir / "oos_predictions.csv", index=False)
        (output_dir / "scores.json").write_text(json.dumps(scores, indent=2), encoding="utf-8")
        run["steps"].append({"step": "walk_forward", "status": scores["status"],
                             "oos_rows": len(predictions), "scores": scores})
        run["status"] = "COMPLETE_NOT_PROMOTED" if scores["status"] == "SCORED_NOT_PROMOTED" else "BLOCKED"
        run["limitations"].append("This runner scores statistical forecasts only; it does not validate an executable trading strategy or Risk Overlay.")
    except Exception as exc:
        run["status"] = "BLOCKED"
        run["error"] = f"{type(exc).__name__}: {exc}"
        run["limitations"].append("No model claim or positive exposure is permitted when acquisition, QA, or evaluation is blocked.")
    run["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    (output_dir / "run_report.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
    print(json.dumps(run, indent=2))
    return 0 if run["status"].startswith("COMPLETE") else 2


if __name__ == "__main__":
    raise SystemExit(main())
