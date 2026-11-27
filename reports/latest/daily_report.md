# BTC Quant Desk — report giornaliero

- Protocollo: **V5.6**
- Stato: **COMPLETE_NOT_PROMOTED**
- Avvio UTC: 2026-11-27T16:59:14.434082+00:00
- Fine UTC: 2026-11-27T17:04:50.898011+00:00
- Commit: `b7a2fefa805c1d4d44a912a5a39aa0749b7e957a`
- Workflow run: 46038092907

> I valori di mercato sono distinti tra osservazioni live, snapshot e candele chiuse. USD e USDT non sono convertiti né uniti.

## 1. Acquisizione e qualità dati

| Feed | Stato | Evidenza / dettaglio |
|---|---|---|
| binance_acquisition_and_qa | PASS | righe=3389, gap=0, duplicati=0, ultima candela=2026-11-26T00:00:00+00:00 |
| bitstamp_acquisition_and_qa | PASS | righe=3650, gap=0, duplicati=0, ultima candela=2026-11-26T00:00:00+00:00 |
| coinbase_recent_cross_check | PASS | righe=300, gap=0, duplicati=0, ultima candela=2026-11-26T00:00:00+00:00 |
| kraken_recent_cross_check | PASS | righe=720, gap=0, duplicati=0, ultima candela=2026-11-26T00:00:00+00:00 |
| supplemental_market_context | PARTIAL | PARTIAL |
| walk_forward | SCORED_NOT_PROMOTED | SCORED_NOT_PROMOTED |

## 2. Prezzi spot — ultime candele giornaliere chiuse

| Venue | Strumento | Candela UTC | Close | 1D | 7D | 30D | Range intraday | Vol 1D BTC | Vol 7D BTC | Vol 30D BTC |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Binance | BTCUSDT (USDT) | 2026-11-26T00:00:00+00:00 | 60,577.18 | 0.197% | -2.274% | -25.130% | 2.824% | 16,482.41 | 197,503.93 | 620,763.11 |
| Bitstamp | BTC/USD (USD) | 2026-11-26T00:00:00+00:00 | 60,492.37 | 0.183% | -2.296% | -25.143% | 2.757% | 1,037.78 | 11,769.53 | 49,995.54 |

### Quotazioni spot — ultimo scambio osservato

| Venue | Stato | Prezzo | Variazione 24h | Volume base 24h | Timestamp ultimo scambio UTC | Età sec |
|---|---|---:|---:|---:|---|---:|
| Bitstamp_BTCUSD_USD | PASS | 59,885.89 | -0.978% | 1,303.84 BTC | 2026-11-27T17:00:24+00:00 | 1.8 |

### Livelli tecnici descrittivi — non segnali

| Venue | SMA20 | SMA50 | SMA200 | Massimo 20D | Minimo 20D | ATR14 |
|---|---:|---:|---:|---:|---:|---:|
| Binance | 66,031.77 | 74,781.41 | 71,980.11 | 76,249.99 | 55,130.00 | 2,967.85 |
| Bitstamp | 65,943.71 | 74,680.97 | 71,919.78 | 76,143.75 | 55,081.31 | 2,957.36 |

## 3. Copertura dei dati supplementari

| Categoria | Stato | Nota / limite |
|---|---|---|
| spot_ohlcv | PASS | Primary Binance/Bitstamp acquisition is reported separately. |
| spot_live_quotes | PARTIAL |  |
| per_exchange_derivatives | PARTIAL |  |
| options | PARTIAL |  |
| us_spot_etf_flows | STALE |  |
| global_etp_flows | UNAVAILABLE | This dataset covers US spot ETFs only; global ETPs require a separate source. |
| exchange_flows_and_reserves | UNAVAILABLE | No verifiable exchange-wallet-label dataset is configured; raw blockchain transfers are not exchange netflows. |
| liquidations | UNAVAILABLE | No public, complete cross-exchange liquidation history source is configured. |
| macro_and_indices | PARTIAL |  |
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

### OKX BTC-USDT Perpetual

- Stato: PASS; strumento BTC-USDT-SWAP.
- Snapshot acquisito UTC: 2026-11-27T17:00:46.519157+00:00.
- Ultimo prezzo: 59,908.20 USDT (ticker 2026-11-27T17:00:45.271000+00:00).
- Volume 24h: 125,711.85 BTC (12,571,185.13 contratti).
- Open interest snapshot: 31,860.01 BTC (1,908,554,597 USD; snapshot 2026-11-27T17:00:45.725000+00:00).
- OI storico giornaliero UTC: 1D 0.17%; 7D -3.06%; 30D 4.80% (ultimo punto 2026-11-27T00:00:00+00:00).
- Funding previsto per il prossimo settlement (2026-11-28T00:00:00+00:00): -0.00000548 (frazione per intervallo).
- Ultimo funding effettivamente settled: -0.00000057 al 2026-11-27T16:00:00+00:00 (stato settled).
- Settlement successivo dopo il periodo corrente: 2026-11-28T08:00:00+00:00.
- Storico funding: 100 settlement acquisiti.
- Delta taker futures BTC (buy − sell, barre UTC chiuse): 1D 1,064.40 BTC; 7D 1,680.25 BTC; 30D n/d BTC.
- Copertura delta taker: 29 barre UTC complete su 30 scaricate.
- Nota CVD: OKX BTC-USDT perpetual contract taker volume in BTC; buy minus sell. Completed UTC daily bars only; exchange-specific derivatives delta proxy, not spot CVD or total-market CVD.
- Liquidazioni: NOT_ACQUIRED; nessuna stima ricavata da endpoint non pertinenti.
- Copertura per venue: Binance FAIL; Bybit FAIL; OKX PASS.

### CVD orario Binance — delta taker aggregato

- Stato: PARTIAL. Hourly Binance kline taker-buy base volume minus inferred taker-sell base volume for rolling 24h/7d/30d windows; not tick-level order-book delta.
| Mercato | Finestra | Delta BTC | Delta / volume % | Volume BTC | Buy BTC | Sell BTC |
|---|---:|---:|---:|---:|---:|---:|
| Spot BTCUSDT | 24h | 242.33 | 1.18% | 20,584.96 | 10,413.65 | 10,171.32 |
| Spot BTCUSDT | 7d | -3,457.56 | -1.80% | 192,227.77 | 94,385.10 | 97,842.66 |
| Spot BTCUSDT | 30d | -3,980.24 | -0.63% | 630,884.98 | 313,452.37 | 317,432.61 |
| Futures BTCUSDT | 24h | n/d | n/d% | n/d | n/d | n/d |
| Futures BTCUSDT | 7d | n/d | n/d% | n/d | n/d | n/d |
| Futures BTCUSDT | 30d | n/d | n/d% | n/d | n/d | n/d |

### Opzioni Deribit

- Stato: PARTIAL; open interest con ritardo provider di 8 ore.
- OI call/put: 188,410.2000 / 150,712.1000 BTC.
- Put/call OI: 0.7999.
- Put/call volume USD 24h: 1.5846.

| Scadenza | DTE | ATM IV % | OI call BTC | OI put BTC |
|---|---:|---:|---:|---:|
| 2026-11-28 | 1 | 39.17 | 1,865.60 | 1,665.40 |
| 2026-11-29 | 2 | 32.78 | 887.00 | 1,553.40 |
| 2026-11-30 | 3 | 35.88 | 349.50 | 459.90 |
| 2026-12-01 | 4 | 41.61 | 70.80 | 16.70 |
| 2026-12-04 | 7 | 48.67 | 11,702.80 | 16,156.00 |
| 2026-12-11 | 14 | 51.73 | 5,334.50 | 6,983.60 |
| 2026-12-18 | 21 | 49.83 | 166.00 | 420.40 |
| 2026-12-25 | 28 | 47.99 | 98,035.80 | 68,011.30 |
| 2027-01-29 | 63 | 46.57 | 13,829.00 | 14,941.80 |
| 2027-02-26 | 91 | 46.04 | 28.50 | 18.70 |
| 2027-03-26 | 119 | 46.54 | 33,853.60 | 22,737.80 |
| 2027-06-25 | 210 | 45.93 | 13,115.70 | 11,286.60 |

| Scadenza | 25Δ put IV % | 25Δ call IV % | Put-call skew vol points |
|---|---:|---:|---:|
| 2026-11-28 | n/d | n/d | n/d |
| 2026-11-29 | n/d | n/d | n/d |
| 2026-11-30 | n/d | n/d | n/d |
| 2026-12-01 | 50.85 | n/d | n/d |
- Gamma/dealer positioning: NOT_IDENTIFIABLE; Public open interest and option Greeks do not reveal whether dealers are net long or short; no dealer-side sign is inferred.

### ETF spot Bitcoin USA

- Stato: STALE; dati aggiornati al 2026-11-25 (circa 2 sessioni USA di ritardo).
- Flusso ultima sessione: -453,119,620.96 USD.
- AUM totale ultima sessione: 72,026,690,545.29 USD.
- Flusso cumulativo dalla partenza: 51,641,619,662.82 USD.
- Flusso ultime 21 sessioni: -5,880,242,355.01 USD.
- Flusso ultime 30 sessioni: -5,366,509,416.59 USD.
- Fonte/licenza: The Commoner Bitcoin ETF Tracker by TFTC, tftc.io/bitcoin-etf-flows / https://creativecommons.org/licenses/by/4.0/.

## 4. Macro e mercati USA

| Serie | Periodo osservato | Freschezza fino | Valore | Unità | Stato | Recuperato UTC | Fonte / metodo |
|---|---|---|---:|---|---|---|---|
| DGS2 — US Treasury 2Y yield | 2026-11-25 | 2026-11-25 | 4.6100 | percent | PASS | 2026-11-27T17:01:49.990742+00:00 | official Treasury daily par yield curve; independent of FRED transport |
| DGS10 — US Treasury 10Y yield | 2026-11-25 | 2026-11-25 | 4.8500 | percent | PASS | 2026-11-27T17:01:50.121934+00:00 | official Treasury daily par yield curve; independent of FRED transport |
| VIXCLS — CBOE VIX | 2026-11-26 | 2026-11-26 | 26.8000 | index points | PASS | 2026-11-27T17:04:50.559669+00:00 | Cboe official historical daily VIX close; independent of FRED transport |

Feed macro non acquisiti: {'DFII10': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=DFII10&cosd=2025-11-27&coed=2026-11-27 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'FEDFUNDS': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=FEDFUNDS&cosd=2021-11-28&coed=2026-11-27 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'CPIAUCSL': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=CPIAUCSL&cosd=2021-11-28&coed=2026-11-27 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'PCEPILFE': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=PCEPILFE&cosd=2021-11-28&coed=2026-11-27 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'UNRATE': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=UNRATE&cosd=2021-11-28&coed=2026-11-27 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'PAYEMS': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=PAYEMS&cosd=2021-11-28&coed=2026-11-27 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'DTWEXBGS': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=DTWEXBGS&cosd=2025-11-27&coed=2026-11-27 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'WALCL': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=WALCL&cosd=2025-11-27&coed=2026-11-27 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'RRPONTSYD': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=RRPONTSYD&cosd=2025-11-27&coed=2026-11-27 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'NFCI': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=NFCI&cosd=2025-11-27&coed=2026-11-27 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'SP500': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=SP500&cosd=2025-11-27&coed=2026-11-27 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'NASDAQCOM': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=NASDAQCOM&cosd=2025-11-27&coed=2026-11-27 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'M2SL': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=M2SL&cosd=2021-11-28&coed=2026-11-27 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))'}

## 5. Ciclo Bitcoin — confronto post-halving

- Stato: PASS; fonte: Bitstamp BTC/USD daily OHLCV; same venue and quote currency.
- Orizzonte corrente: 950 sessioni dal 20 aprile 2024.
- Limite: Descriptive comparison at the same elapsed days after halving; sample is small, cycles are structurally different, and this is not a timing forecast.
| Ciclo | Stato | Giorni/sessioni | Rendimento stesso orizzonte | Massimo rendimento | Giorni al picco | Drawdown massimo da picco |
|---|---|---:|---:|---:|---:|---:|
| 2012 cycle | INSUFFICIENT_HISTORY | n/d | n/d% | n/d% | n/d | n/d% |
| 2016 cycle | INSUFFICIENT_HISTORY | n/d | n/d% | n/d% | n/d | n/d% |
| 2020 cycle | PASS | 950 | 95.77% | 688.14% | 546 | -76.66% |
| 2024 cycle (current) | PASS | 950 | -6.92% | 91.92% | 534 | -53.08% |

## 6. Eventi, regolamentazione e geopolitica — feed descrittivi

- Stato: PARTIAL. Headlines and keyword tags are descriptive only; no sentiment, event-impact score or trading signal is inferred.
| Fonte | Stato | Acquisiti | Rilevanti nel report |
|---|---|---:|---:|
| Federal Reserve | PASS | 20 | 10 |
| SEC | PASS | 25 | 15 |
| White House | PASS | 30 | 2 |
| ECB | PASS | 15 | 6 |
| CFTC | NOT_CONFIGURED | n/d | 0 |
| GDELT | FAIL | n/d | 0 |
- 2026-11-27T14:00:00+00:00 — ECB — Decisions taken by the Governing Council of the ECB (in addition to decisions setting interest rates) [macro_monetary] — https://www.ecb.europa.eu//press/govcdec/otherdec/2026/html/ecb.gc261127~13ecadc0f2.en.html
- 2026-11-27T09:00:00+00:00 — ECB — ECB Consumer Expectations Survey results – October 2026 [macro_monetary] — https://www.ecb.europa.eu//press/pr/date/2026/html/ecb.pr261127~2e53af695e.en.html
- 2026-11-25T17:30:00+00:00 — ECB — ECB and Sveriges Riksbank conclude agreement for Sweden to join T2 [macro_monetary] — https://www.ecb.europa.eu//press/pr/date/2026/html/ecb.pr261125_1~6333a90f3a.en.html
- 2026-11-25T14:10:24+00:00 — SEC — SEC Investor Advisory Committee to Host Dec. 3 Virtual Meeting [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-118-sec-investor-advisory-committee-host-dec-3-virtual-meeting
- 2026-11-25T12:01:00+00:00 — White House — First Lady Melania Trump Secures Reunification of Nine Additional Children with their Families [geopolitical] — https://www.whitehouse.gov/briefings-statements/2026/11/first-lady-melania-trump-secures-reunification-of-nine-additional-children-with-their-families/
- 2026-11-23T22:33:50+00:00 — White House — President Trump Stands with Victims’ Families as Newsom Grants Mass Clemency to Depraved Killers [geopolitical] — https://www.whitehouse.gov/releases/2026/11/president-trump-stands-with-victims-families-as-newsom-grants-mass-clemency-to-depraved-killers/
- 2026-11-23T14:30:00+00:00 — ECB — Philip R. Lane: Climate change and monetary policy [macro_monetary] — https://www.ecb.europa.eu//press/key/date/2026/html/ecb.sp261123~b5816801a0.en.pdf
- 2026-11-23T10:00:00+00:00 — ECB — ECB expands acceptance of DLT-based assets as eligible Eurosystem collateral [macro_monetary] — https://www.ecb.europa.eu//press/pr/date/2026/html/ecb.pr261123~76b6f57b74.en.html
- 2026-11-20T21:15:00+00:00 — Federal Reserve — Federal Reserve announces College Fed Challenge winners [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/other20261120b.htm
- 2026-11-20T18:03:24+00:00 — SEC — SEC Issues Proposal to Restructure the Consolidated Audit Trail [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-117-sec-issues-proposal-restructure-consolidated-audit-trail
- 2026-11-20T15:00:00+00:00 — Federal Reserve — Federal Reserve Board releases results from survey of senior financial officers at banks about their strategies and practices for managing reserve balances [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/other20261120a.htm
- 2026-11-20T14:28:28+00:00 — SEC — SEC Charges Indianapolis-Based Backward Hat Capital and Its Co-Founders With $560 Million Dollar Offering Fraud and Obtains Emergency Relief [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-116-sec-charges-indianapolis-based-backward-hat-capital-its-co-founders-560-million-dollar-offering

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
- Supplemental feed per_exchange_derivatives: PARTIAL.
- Supplemental feed options: PARTIAL.
- Supplemental feed us_spot_etf_flows: STALE.
- Supplemental feed global_etp_flows: UNAVAILABLE.
- Supplemental feed exchange_flows_and_reserves: UNAVAILABLE.
- Supplemental feed liquidations: UNAVAILABLE.
- Supplemental feed macro_and_indices: PARTIAL.
- Supplemental feed spot_futures_cvd: PARTIAL.
- Supplemental feed geopolitical_regulatory_news: PARTIAL.
- Il confronto dei cicli post-halving è descrittivo e usa la stessa venue/quote e lo stesso orizzonte temporale.
### INTERPRETAZIONI
- Zero-return ha la MAE più bassa in tutti gli orizzonti storici confrontati.
- Ridge resta challenger non promosso; nessuna conclusione economica è autorizzata.
### IPOTESI
- Volume normalizzato e geometria delle candele potrebbero aggiungere informazione oltre le feature price-only. — stato: PROPOSED_NOT_RUN; esperimento: V5.6-OHLCV-001.
### FORECAST
- Point forecast emessi in questo run: 4.
- Forecast maturati/scorati in questo run: 3.
- Probabilità calibrate pubblicate: False.
- Eventuali valori nel ledger sono point forecast sperimentali; non sono probabilità calibrate né segnali operativi.

## 8. Validazione quantitativa

Le metriche seguenti sono diagnostiche sul periodo storico già ispezionato; non sono prova prospettica né PnL eseguibile.

| Orizzonte | N | Zero MAE | Drift MAE | Momentum MAE | Ridge MAE |
|---:|---:|---:|---:|---:|---:|
| 1 sessioni | 362 | 0.015879 | 0.015941 | 0.027156 | 0.015939 |
| 3 sessioni | 360 | 0.028530 | 0.028801 | 0.048298 | 0.028736 |
| 7 sessioni | 356 | 0.044285 | 0.045296 | 0.075832 | 0.044920 |
| 30 sessioni | 333 | 0.109359 | 0.110793 | 0.184544 | 0.112091 |

## 9. Ledger e rischio

- Stato ledger: VERIFIED_IN_WORKSPACE_PENDING_WORKFLOW_COMMIT; eventi prima/dopo: 68 / 75.
- Nuove previsioni: 4; duplicate soppresse: 0; score maturati: 3.
- Campione prospettico: INSUFFICIENT_PROSPECTIVE_EVIDENCE.
- Rischio: paper_only; live trading: False; esposizione teorica: 0.00%.
- Champion congelato: zero-return. Ridge è challenger non promosso.
- Nessun PnL economico o probabilità calibrata è dichiarato.

## 10. Revisione critica e conclusione

- Gate pre-report: PASS; cicli completati: 7; fallimenti bloccanti: [].
- Fattore osservato: Variazione close-to-close = 0.1971 % (Binance spot BTCUSDT, 2026-11-26T00:00:00+00:00).
- Fattore osservato: Ampiezza intraday high-low/open = 2.8241 % (Binance spot BTCUSDT, 2026-11-26T00:00:00+00:00).
- Fattore osservato: Volume rispetto alla mediana precedente = 0.8327 multiplo (Binance spot BTCUSDT, 2026-11-26T00:00:00+00:00).
- Limite principale: Assenza di evidenza prospettica maturata e di validazione economica eseguibile; il holdout storico è solo diagnostico.
- Evidenza che cambierebbe la valutazione: Un campione prospettico indipendente, almeno 200 osservazioni maturate per orizzonte, lift stabile contro zero-return/drift dopo HAC-Holm, calibrazione verificata e valore netto positivo dopo costi documentati e stress 1x/2x/3x.
- Prossimo esperimento: V5.6-OHLCV-001: challenger volume-surprise/candle-geometry, registrato prima del test e valutato esclusivamente sul ledger prospettico.

## 11. Limiti dichiarati

- Ridge is challenger only; no automatic promotion.
- Calibration and >=200 matured OOS forecasts per horizon are required before probabilities.
- Regime slices are descriptive; no regime-specific inferential claim is made.
- The reused historical holdout is continuity diagnostics only, not independent prospective evidence.
- No cost-adjusted strategy PnL, funding, slippage or execution backtest is claimed.
- No calibrated probability or live trading claim is permitted.
