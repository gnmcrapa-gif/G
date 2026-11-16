# Data contract and QA gates

## Canonical bar schema

| Field | Type | Meaning |
|---|---|---|
| timestamp | UTC datetime | Candle open time, unique and increasing |
| open | float64 | Positive price |
| high | float64 | Candle high |
| low | float64 | Candle low |
| close | float64 | Positive close |
| volume | float64 | Base-volume units as documented |
| venue | string | Exchange/source identifier |
| symbol | string | Exact market symbol |
| quote_currency | string | Exact quote asset |
| interval | string | Expected bar interval |
| is_closed | boolean | Whether candle is complete |

Do not combine venues, symbols, or quote currencies in one price series without an explicit, tested transformation.

## Manifest

Each raw object needs: source URL, retrieval timestamp UTC, license/terms, venue, symbol, quote currency, interval, file size, SHA-256, first/last timestamp, row count, parser version, schema version, and source grade.

## QA gates

- timestamps parse and normalize to UTC;
- timestamps are unique and strictly increasing;
- expected interval and gaps are quantified;
- OHLC values are finite and positive;
- high >= max(open, close, low), low <= min(open, close, high);
- volume is finite and non-negative, with zero distinct from missing;
- duplicates, gaps, outliers, scale anomalies and missing values are reported;
- incomplete candles are excluded from historical training;
- feature availability is no later than the forecast cutoff;
- all transformations preserve source lineage.

No silent row dropping, forward-fill, or imputation of market bars. Any exclusion must be counted and explained. A failed critical invariant blocks downstream training and validation.

## Source grades

- A: primary, reproducible, documented raw data and clean QA.
- B: credible source with limited, quantified caveats.
- C: partial/secondary/snapshot data; exploratory only.
- D: unverifiable, malformed, or unsuitable; excluded.

## Forecast-time contract

Every feature row carries an as-of timestamp and a source-availability timestamp. Require availability <= forecast cutoff. Target rows are constructed separately from features. For the scheduled daily run, the executable target is `log(Open[t+h+2]/Open[t+2])`: one full daily bar is reserved for operational latency. The ledger rejects entries that are not strictly future to the actual issue timestamp. Split boundaries are chronological and embargoed by the target horizon plus this latency buffer.