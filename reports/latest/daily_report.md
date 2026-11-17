# BTC Quant Desk — report giornaliero

- Protocollo: **V5.6**
- Stato: **COMPLETE_NOT_PROMOTED**
- Avvio UTC: 2026-11-17T22:34:34.433842+00:00
- Fine UTC: 2026-11-17T22:36:08.243031+00:00
- Commit: `fbbf957cdc5446023b228d6fc2e74a1a4b2223d1`
- Workflow run: 44191321836

> I valori di mercato sono distinti tra osservazioni live, snapshot e candele chiuse. USD e USDT non sono convertiti né uniti.

## 1. Acquisizione e qualità dati

| Feed | Stato | Evidenza / dettaglio |
|---|---|---|
| binance_acquisition_and_qa | PASS | righe=3379, gap=0, duplicati=0, ultima candela=2026-11-16T00:00:00+00:00 |
| bitstamp_acquisition_and_qa | PASS | righe=3650, gap=0, duplicati=0, ultima candela=2026-11-16T00:00:00+00:00 |
| coinbase_recent_cross_check | PASS | righe=300, gap=0, duplicati=0, ultima candela=2026-11-16T00:00:00+00:00 |
| kraken_recent_cross_check | PASS | righe=720, gap=0, duplicati=0, ultima candela=2026-11-16T00:00:00+00:00 |
| supplemental_market_context | PARTIAL | PARTIAL |
| walk_forward | SCORED_NOT_PROMOTED | SCORED_NOT_PROMOTED |

## 2. Prezzi spot — ultime candele giornaliere chiuse

| Venue | Strumento | Candela UTC | Close | 1D | 7D | 30D | Range intraday | Vol 1D BTC | Vol 7D BTC | Vol 30D BTC |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Binance | BTCUSDT (USDT) | 2026-11-16T00:00:00+00:00 | 64,882.87 | -0.716% | -13.912% | -20.380% | 2.741% | 21,929.24 | 161,324.20 | 488,271.97 |
| Bitstamp | BTC/USD (USD) | 2026-11-16T00:00:00+00:00 | 64,821.90 | -0.751% | -13.877% | -20.351% | 2.747% | 990.62 | 12,646.17 | 49,270.36 |

### Quotazioni spot — ultimo scambio osservato

| Venue | Stato | Prezzo | Variazione 24h | Volume base 24h | Timestamp ultimo scambio UTC | Età sec |
|---|---|---:|---:|---:|---|---:|
| Bitstamp_BTCUSD_USD | PASS | 64,621.12 | -0.330% | 1,073.76 BTC | 2026-11-17T22:35:26+00:00 | 1.3 |

### Livelli tecnici descrittivi — non segnali

| Venue | SMA20 | SMA50 | SMA200 | Massimo 20D | Minimo 20D | ATR14 |
|---|---:|---:|---:|---:|---:|---:|
| Binance | 74,370.13 | 79,451.99 | 72,921.15 | 81,971.00 | 62,006.00 | 2,657.72 |
| Bitstamp | 74,264.11 | 79,364.81 | 72,865.33 | 81,888.33 | 61,946.62 | 2,647.07 |

## 3. Copertura dei dati supplementari

| Categoria | Stato | Nota / limite |
|---|---|---|
| spot_ohlcv | PASS | Primary Binance/Bitstamp acquisition is reported separately. |
| spot_live_quotes | PARTIAL |  |
| per_exchange_derivatives | FAIL |  |
| options | PARTIAL |  |
| us_spot_etf_flows | STALE |  |
| global_etp_flows | UNAVAILABLE | This dataset covers US spot ETFs only; global ETPs require a separate source. |
| exchange_flows_and_reserves | UNAVAILABLE | No verifiable exchange-wallet-label dataset is configured; raw blockchain transfers are not exchange netflows. |
| liquidations | UNAVAILABLE | No public, complete cross-exchange liquidation history source is configured. |
| macro_and_indices | FAIL |  |
| spot_futures_cvd | PARTIAL | Hourly Binance kline taker-buy base volume minus inferred taker-sell base volume for rolling 24h/7d/30d windows; not tick-level order-book delta. |
| geopolitical_regulatory_news | PARTIAL | Headlines and keyword tags are descriptive only; no sentiment, event-impact score or trading signal is inferred. |

### Binance Futures

- Stato: FAIL
- Funding corrente/ultimo: n/d (fraction per funding interval)
- Open interest: n/d BTC
- Variazione OI 1D: n/d%
- Variazione OI 7D: n/d%
- Variazione OI 30D: n/d%
- Long/short account ratio: n/d (long n/d% / short n/d%)
- Taker buy/sell ratio (Binance proxy): n/d
- Volume futures ultima candela chiusa 1D (Binance): n/d BTC
- Volume futures 24h (Bybit): n/d BTC
- Errori feed: {'premium_index': 'HTTPError: 451 Client Error:  for url: https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT', 'open_interest': 'HTTPError: 451 Client Error:  for url: https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT', 'open_interest_daily_30d': 'HTTPError: 451 Client Error:  for url: https://fapi.binance.com/futures/data/openInterestHist?symbol=BTCUSDT&period=1d&limit=30', 'taker_buy_sell_daily_30d': 'HTTPError: 451 Client Error:  for url: https://fapi.binance.com/futures/data/takerlongshortRatio?symbol=BTCUSDT&period=1d&limit=30', 'global_long_short_account_ratio_daily_30d': 'HTTPError: 451 Client Error:  for url: https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=BTCUSDT&period=1d&limit=30', 'funding_history': 'HTTPError: 451 Client Error:  for url: https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1000', 'daily_futures_klines': 'HTTPError: 451 Client Error:  for url: https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1d&limit=31'}

### Bybit Linear

- Stato: FAIL
- Funding corrente/ultimo: n/d (fraction per funding interval)
- Open interest: n/d BTC
- Variazione OI 1D: n/d%
- Variazione OI 7D: n/d%
- Variazione OI 30D: n/d%
- Long/short account ratio: n/d (long n/d% / short n/d%)
- Taker buy/sell ratio (Binance proxy): n/d
- Volume futures ultima candela chiusa 1D (Binance): n/d BTC
- Volume futures 24h (Bybit): n/d BTC
- Errori feed: {'ticker': 'HTTPError: 403 Client Error: Forbidden for url: https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT', 'open_interest_daily_200d': 'HTTPError: 403 Client Error: Forbidden for url: https://api.bybit.com/v5/market/open-interest?category=linear&symbol=BTCUSDT&intervalTime=1d&limit=200', 'global_account_ratio_daily_30d': 'HTTPError: 403 Client Error: Forbidden for url: https://api.bybit.com/v5/market/account-ratio?category=linear&symbol=BTCUSDT&period=1d&limit=30', 'funding_history': 'HTTPError: 403 Client Error: Forbidden for url: https://api.bybit.com/v5/market/funding/history?category=linear&symbol=BTCUSDT&limit=200'}

### CVD orario Binance — delta taker aggregato

- Stato: PARTIAL. Hourly Binance kline taker-buy base volume minus inferred taker-sell base volume for rolling 24h/7d/30d windows; not tick-level order-book delta.
| Mercato | Finestra | Delta BTC | Delta / volume % | Volume BTC | Buy BTC | Sell BTC |
|---|---:|---:|---:|---:|---:|---:|
| Spot BTCUSDT | 24h | 2,355.56 | 8.22% | 28,650.93 | 15,503.24 | 13,147.69 |
| Spot BTCUSDT | 7d | -2,989.13 | -1.73% | 172,593.68 | 84,802.28 | 87,791.40 |
| Spot BTCUSDT | 30d | 6,405.31 | 1.26% | 506,585.77 | 256,495.54 | 250,090.23 |
| Futures BTCUSDT | 24h | n/d | n/d% | n/d | n/d | n/d |
| Futures BTCUSDT | 7d | n/d | n/d% | n/d | n/d | n/d |
| Futures BTCUSDT | 30d | n/d | n/d% | n/d | n/d | n/d |

### Opzioni Deribit

- Stato: PARTIAL; open interest con ritardo provider di 8 ore.
- OI call/put: 219,769.4000 / 169,614.0000 BTC.
- Put/call OI: 0.7718.
- Put/call volume USD 24h: 1.5796.

| Scadenza | DTE | ATM IV % | OI call BTC | OI put BTC |
|---|---:|---:|---:|---:|
| 2026-11-18 | 1 | 41.38 | 1,242.60 | 1,664.30 |
| 2026-11-19 | 2 | 49.37 | 594.60 | 627.30 |
| 2026-11-20 | 3 | 50.03 | 20,458.30 | 13,117.80 |
| 2026-11-21 | 4 | 48.97 | 39.20 | 28.90 |
| 2026-11-27 | 10 | 44.17 | 51,181.40 | 50,880.60 |
| 2026-12-04 | 17 | 42.70 | 4,567.90 | 3,312.40 |
| 2026-12-25 | 38 | 41.40 | 88,450.90 | 60,035.80 |
| 2027-01-29 | 73 | 41.17 | 6,246.50 | 6,806.10 |
| 2027-03-26 | 129 | 41.05 | 28,732.40 | 18,660.10 |
| 2027-06-25 | 220 | 41.24 | 11,483.50 | 10,075.60 |
| 2027-09-24 | 311 | 41.17 | 6,772.10 | 4,405.10 |

| Scadenza | 25Δ put IV % | 25Δ call IV % | Put-call skew vol points |
|---|---:|---:|---:|
| 2026-11-18 | n/d | n/d | n/d |
| 2026-11-19 | n/d | n/d | n/d |
| 2026-11-20 | n/d | n/d | n/d |
| 2026-11-21 | 55.57 | n/d | n/d |
- Gamma/dealer positioning: NOT_IDENTIFIABLE; Public open interest and option Greeks do not reveal whether dealers are net long or short; no dealer-side sign is inferred.

### ETF spot Bitcoin USA

- Stato: STALE; dati aggiornati al 2026-11-13 (circa 2 sessioni USA di ritardo).
- Flusso ultima sessione: -185,450,233.40 USD.
- AUM totale ultima sessione: 86,199,738,908.25 USD.
- Flusso cumulativo dalla partenza: 54,685,771,071.43 USD.
- Flusso ultime 21 sessioni: -2,327,413,101.03 USD.
- Flusso ultime 30 sessioni: -3,154,704,110.43 USD.
- Fonte/licenza: The Commoner Bitcoin ETF Tracker by TFTC, tftc.io/bitcoin-etf-flows / https://creativecommons.org/licenses/by/4.0/.

## 4. Macro e mercati USA

| Serie | Osservazione | Valore | Unità | Stato |
|---|---|---:|---|---|

Feed macro non acquisiti: {'DGS2': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)", 'DGS10': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)", 'DFII10': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)", 'FEDFUNDS': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)", 'CPIAUCSL': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)", 'PCEPILFE': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)", 'UNRATE': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)", 'PAYEMS': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)", 'DTWEXBGS': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)", 'WALCL': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)", 'RRPONTSYD': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)", 'NFCI': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)", 'SP500': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)", 'NASDAQCOM': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)", 'VIXCLS': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)", 'M2SL': "ReadTimeout: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=12)"}

## 5. Ciclo Bitcoin — confronto post-halving

- Stato: PASS; fonte: Bitstamp BTC/USD daily OHLCV; same venue and quote currency.
- Orizzonte corrente: 940 sessioni dal 20 aprile 2024.
- Limite: Descriptive comparison at the same elapsed days after halving; sample is small, cycles are structurally different, and this is not a timing forecast.
| Ciclo | Stato | Giorni/sessioni | Rendimento stesso orizzonte | Massimo rendimento | Giorni al picco | Drawdown massimo da picco |
|---|---|---:|---:|---:|---:|---:|
| 2012 cycle | INSUFFICIENT_HISTORY | n/d | n/d% | n/d% | n/d | n/d% |
| 2016 cycle | INSUFFICIENT_HISTORY | n/d | n/d% | n/d% | n/d | n/d% |
| 2020 cycle | PASS | 940 | 96.41% | 688.14% | 546 | -76.66% |
| 2024 cycle (current) | PASS | 940 | -0.26% | 91.92% | 534 | -53.08% |

## 6. Eventi, regolamentazione e geopolitica — feed descrittivi

- Stato: PARTIAL. Headlines and keyword tags are descriptive only; no sentiment, event-impact score or trading signal is inferred.
| Fonte | Stato | Acquisiti | Rilevanti nel report |
|---|---|---:|---:|
| Federal Reserve | PASS | 20 | 12 |
| SEC | PASS | 25 | 15 |
| White House | PASS | 30 | 0 |
| ECB | PASS | 15 | 7 |
| CFTC | NOT_CONFIGURED | n/d | 0 |
| GDELT | FAIL | n/d | 0 |
- 2026-11-17T18:30:00+00:00 — ECB — Philip R. Lane: The practice and science of monetary policy communication: the ECB experience [macro_monetary] — https://www.ecb.europa.eu//press/key/date/2026/html/ecb.sp261117~7f5d3b1a0e.en.pdf
- 2026-11-13T16:57:00+00:00 — SEC — SEC Proposes Executive and Director Compensation Disclosure Reforms [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-114-sec-proposes-executive-director-compensation-disclosure-reforms
- 2026-11-12T18:30:00+00:00 — Federal Reserve — Federal Reserve Board announces pricing, effective January 1, 2027, for payment services the Federal Reserve Banks provide to banks and credit unions, and changes to streamline and adjust their check services [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/other20261112a.htm
- 2026-11-12T17:45:00+00:00 — Federal Reserve — Federal Reserve announces revised tentative schedule of Federal Open Market Committee meetings in 2027 [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/monetary20261112a.htm
- 2026-11-12T16:00:00+00:00 — Federal Reserve — Federal Reserve Board issues enforcement action with former employee of United Community Bank [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/enforcement20261112a.htm
- 2026-11-10T16:45:00+00:00 — ECB — Philip R. Lane: The science and practice of monetary policy communication: the ECB experience [macro_monetary] — https://www.ecb.europa.eu//press/key/date/2026/html/ecb.sp261110_1~9725b7aa07.en.html
- 2026-11-10T16:15:35+00:00 — SEC — SEC Announces Enforcement Annual Results for Fiscal Year 2026 [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-113-sec-announces-enforcement-annual-results-fiscal-year-2026
- 2026-11-09T21:00:00+00:00 — Federal Reserve — Federal Reserve Board announces approval of two applications by Mutual Federal Bancorp, MHC, and MFB Bancorp, Inc. [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/orders20261109a.htm
- 2026-11-06T09:00:00+00:00 — ECB — ECB publishes consolidated banking data for end-June 2026 [macro_monetary] — https://www.ecb.europa.eu//press/pr/date/2026/html/ecb.pr261106~356f2fc73a.en.html
- 2026-11-05T16:00:00+00:00 — Federal Reserve — Federal Reserve Board announces termination of enforcement action with Allegiant United Holdings, LLC, Nano Financial Holdings, Inc., and Nano Banc [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/enforcement20261105a.htm
- 2026-11-05T08:00:00+00:00 — ECB — Isabel Schnabel: Navigating stormy waters: reflections on monetary policy [macro_monetary] — https://www.ecb.europa.eu//press/key/date/2026/html/ecb.sp261105_1~5e97d9d5a0.en.html
- 2026-11-04T16:28:00+00:00 — SEC — SEC Adopts Amendments to Update Definitions of Small Entity for Investment Companies and Investment Advisers [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-112-sec-adopts-amendments-update-definitions-small-entity-investment-companies-investment-advisers

## 7. Fatti, interpretazioni, ipotesi e previsioni

### FATTI
- binance_acquisition_and_qa: PASS.
- bitstamp_acquisition_and_qa: PASS.
- coinbase_recent_cross_check: PASS.
- kraken_recent_cross_check: PASS.
- supplemental_market_context: PARTIAL.
- walk_forward: SCORED_NOT_PROMOTED.
- Le metriche storiche sono diagnostiche di continuità, non prove prospettiche.
- Il ledger prospettico conteggia esclusivamente eventi SCORE maturati.
- Supplemental feed spot_ohlcv: PASS.
- Supplemental feed spot_live_quotes: PARTIAL.
- Supplemental feed per_exchange_derivatives: FAIL.
- Supplemental feed options: PARTIAL.
- Supplemental feed us_spot_etf_flows: STALE.
- Supplemental feed global_etp_flows: UNAVAILABLE.
- Supplemental feed exchange_flows_and_reserves: UNAVAILABLE.
- Supplemental feed liquidations: UNAVAILABLE.
- Supplemental feed macro_and_indices: FAIL.
- Supplemental feed spot_futures_cvd: PARTIAL.
- Supplemental feed geopolitical_regulatory_news: PARTIAL.
- Il confronto dei cicli post-halving è descrittivo e usa la stessa venue/quote e lo stesso orizzonte temporale.
### INTERPRETAZIONI
- Zero-return ha la MAE più bassa in tutti gli orizzonti storici confrontati.
- Ridge resta challenger non promosso; nessuna conclusione economica è autorizzata.
### IPOTESI
- Volume normalizzato e geometria delle candele potrebbero aggiungere informazione oltre le feature price-only. — stato: PROPOSED_NOT_RUN; esperimento: V5.5-OHLCV-001.
### FORECAST
- Point forecast emessi in questo run: 0.
- Forecast maturati/scorati in questo run: 0.
- Probabilità calibrate pubblicate: False.
- Eventuali valori nel ledger sono point forecast sperimentali; non sono probabilità calibrate né segnali operativi.

## 8. Validazione quantitativa

Le metriche seguenti sono diagnostiche sul periodo storico già ispezionato; non sono prova prospettica né PnL eseguibile.

| Orizzonte | N | Zero MAE | Drift MAE | Momentum MAE | Ridge MAE |
|---:|---:|---:|---:|---:|---:|
| 1 sessioni | 362 | 0.015923 | 0.015988 | 0.027317 | 0.015989 |
| 3 sessioni | 360 | 0.028545 | 0.028754 | 0.049103 | 0.028831 |
| 7 sessioni | 356 | 0.042520 | 0.043340 | 0.076994 | 0.043273 |
| 30 sessioni | 333 | 0.101881 | 0.102956 | 0.185131 | 0.103926 |

## 9. Ledger e rischio

- Stato ledger: VERIFIED_IN_WORKSPACE_PENDING_WORKFLOW_COMMIT; eventi prima/dopo: 16 / 16.
- Nuove previsioni: 0; duplicate soppresse: 4; score maturati: 0.
- Campione prospettico: INSUFFICIENT_PROSPECTIVE_EVIDENCE.
- Rischio: paper_only; live trading: False; esposizione teorica: 0.00%.
- Champion congelato: zero-return. Ridge è challenger non promosso.
- Nessun PnL economico o probabilità calibrata è dichiarato.

## 10. Revisione critica e conclusione

- Gate pre-report: PASS; cicli completati: 7; fallimenti bloccanti: [].
- Fattore osservato: Variazione close-to-close = -0.7164 % (Binance spot BTCUSDT, 2026-11-16T00:00:00+00:00).
- Fattore osservato: Ampiezza intraday high-low/open = 2.7408 % (Binance spot BTCUSDT, 2026-11-16T00:00:00+00:00).
- Fattore osservato: Volume rispetto alla mediana precedente = 1.5029 multiplo (Binance spot BTCUSDT, 2026-11-16T00:00:00+00:00).
- Limite principale: Assenza di evidenza prospettica maturata e di validazione economica eseguibile; il holdout storico è solo diagnostico.
- Evidenza che cambierebbe la valutazione: Un campione prospettico indipendente, almeno 200 osservazioni maturate per orizzonte, lift stabile contro zero-return/drift dopo HAC-Holm, calibrazione verificata e valore netto positivo dopo costi documentati e stress 1x/2x/3x.
- Prossimo esperimento: V5.5-OHLCV-001: challenger volume-surprise/candle-geometry, registrato prima del test e valutato esclusivamente sul ledger prospettico.

## 11. Limiti dichiarati

- Ridge is challenger only; no automatic promotion.
- Calibration and >=200 matured OOS forecasts per horizon are required before probabilities.
- Regime slices are descriptive; no regime-specific inferential claim is made.
- The reused historical holdout is continuity diagnostics only, not independent prospective evidence.
- No cost-adjusted strategy PnL, funding, slippage or execution backtest is claimed.
- No calibrated probability or live trading claim is permitted.
