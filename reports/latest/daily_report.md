# BTC Quant Desk — report giornaliero

- Protocollo: **V5.6**
- Stato: **COMPLETE_NOT_PROMOTED**
- Avvio UTC: 2026-11-19T18:42:39.924912+00:00
- Fine UTC: 2026-11-19T18:47:56.083993+00:00
- Commit: `9c79c41e885dacd8bf8928ec8363609d80944f96`
- Workflow run: 44590617265

> I valori di mercato sono distinti tra osservazioni live, snapshot e candele chiuse. USD e USDT non sono convertiti né uniti.

## 1. Acquisizione e qualità dati

| Feed | Stato | Evidenza / dettaglio |
|---|---|---|
| binance_acquisition_and_qa | PASS | righe=3381, gap=0, duplicati=0, ultima candela=2026-11-18T00:00:00+00:00 |
| bitstamp_acquisition_and_qa | PASS | righe=3650, gap=0, duplicati=0, ultima candela=2026-11-18T00:00:00+00:00 |
| coinbase_recent_cross_check | PASS | righe=300, gap=0, duplicati=0, ultima candela=2026-11-18T00:00:00+00:00 |
| kraken_recent_cross_check | PASS | righe=720, gap=0, duplicati=0, ultima candela=2026-11-18T00:00:00+00:00 |
| supplemental_market_context | PASS | PASS |
| walk_forward | SCORED_NOT_PROMOTED | SCORED_NOT_PROMOTED |

## 2. Prezzi spot — ultime candele giornaliere chiuse

| Venue | Strumento | Candela UTC | Close | 1D | 7D | 30D | Range intraday | Vol 1D BTC | Vol 7D BTC | Vol 30D BTC |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Binance | BTCUSDT (USDT) | 2026-11-18T00:00:00+00:00 | 63,068.22 | -2.893% | -14.790% | -23.030% | 4.525% | 18,699.70 | 175,728.60 | 512,397.96 |
| Bitstamp | BTC/USD (USD) | 2026-11-18T00:00:00+00:00 | 62,976.18 | -2.930% | -14.799% | -23.050% | 4.534% | 1,216.28 | 10,877.00 | 49,736.17 |

### Quotazioni spot — ultimo scambio osservato

| Venue | Stato | Prezzo | Variazione 24h | Volume base 24h | Timestamp ultimo scambio UTC | Età sec |
|---|---|---:|---:|---:|---|---:|
| Bitstamp_BTCUSD_USD | PASS | 63,009.72 | 0.051% | 1,131.51 BTC | 2026-11-19T18:43:37+00:00 | 1.8 |

### Livelli tecnici descrittivi — non segnali

| Venue | SMA20 | SMA50 | SMA200 | Massimo 20D | Minimo 20D | ATR14 |
|---|---:|---:|---:|---:|---:|---:|
| Binance | 72,804.14 | 78,669.02 | 72,776.64 | 81,196.01 | 62,006.00 | 2,641.55 |
| Bitstamp | 72,704.64 | 78,580.06 | 72,719.98 | 81,105.28 | 61,946.62 | 2,632.38 |

## 3. Copertura dei dati supplementari

| Categoria | Stato | Nota / limite |
|---|---|---|
| spot_ohlcv | PASS | Primary Binance/Bitstamp acquisition is reported separately. |
| spot_live_quotes | PARTIAL |  |
| per_exchange_derivatives | PARTIAL |  |
| options | PARTIAL |  |
| us_spot_etf_flows | PASS |  |
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
- Snapshot acquisito UTC: 2026-11-19T18:43:52.003506+00:00.
- Ultimo prezzo: 63,029.80 USDT (ticker 2026-11-19T18:43:49.673000+00:00).
- Volume 24h: 130,324.33 BTC (13,032,432.78 contratti).
- Open interest snapshot: 32,383.64 BTC (2,041,513,260 USD; snapshot 2026-11-19T18:43:51.030000+00:00).
- OI storico giornaliero UTC: 1D -1.72%; 7D -12.61%; 30D 10.26% (ultimo punto 2026-11-19T00:00:00+00:00).
- Funding previsto per il prossimo settlement (2026-11-20T00:00:00+00:00): 0.00006594 (frazione per intervallo).
- Ultimo funding effettivamente settled: -0.00001786 al 2026-11-19T16:00:00+00:00 (stato settled).
- Settlement successivo dopo il periodo corrente: 2026-11-20T08:00:00+00:00.
- Storico funding: 100 settlement acquisiti.
- Delta taker futures BTC (buy − sell, barre UTC chiuse): 1D -2,458.12 BTC; 7D -22,330.83 BTC; 30D n/d BTC.
- Copertura delta taker: 29 barre UTC complete su 30 scaricate.
- Nota CVD: OKX BTC-USDT perpetual contract taker volume in BTC; buy minus sell. Completed UTC daily bars only; exchange-specific derivatives delta proxy, not spot CVD or total-market CVD.
- Liquidazioni: NOT_ACQUIRED; nessuna stima ricavata da endpoint non pertinenti.
- Copertura per venue: Binance FAIL; Bybit FAIL; OKX PASS.

### CVD orario Binance — delta taker aggregato

- Stato: PARTIAL. Hourly Binance kline taker-buy base volume minus inferred taker-sell base volume for rolling 24h/7d/30d windows; not tick-level order-book delta.
| Mercato | Finestra | Delta BTC | Delta / volume % | Volume BTC | Buy BTC | Sell BTC |
|---|---:|---:|---:|---:|---:|---:|
| Spot BTCUSDT | 24h | -109.63 | -0.62% | 17,551.77 | 8,721.07 | 8,830.70 |
| Spot BTCUSDT | 7d | -2,782.69 | -1.58% | 176,186.73 | 86,702.02 | 89,484.71 |
| Spot BTCUSDT | 30d | 4,309.95 | 0.84% | 513,808.20 | 259,059.07 | 254,749.13 |
| Futures BTCUSDT | 24h | n/d | n/d% | n/d | n/d | n/d |
| Futures BTCUSDT | 7d | n/d | n/d% | n/d | n/d | n/d |
| Futures BTCUSDT | 30d | n/d | n/d% | n/d | n/d | n/d |

### Opzioni Deribit

- Stato: PARTIAL; open interest con ritardo provider di 8 ore.
- OI call/put: 227,739.4000 / 179,692.4000 BTC.
- Put/call OI: 0.7890.
- Put/call volume USD 24h: 3.1525.

| Scadenza | DTE | ATM IV % | OI call BTC | OI put BTC |
|---|---:|---:|---:|---:|
| 2026-11-20 | 1 | 49.68 | 21,661.60 | 13,360.30 |
| 2026-11-21 | 2 | 48.61 | 774.10 | 1,090.90 |
| 2026-11-22 | 3 | 42.12 | 250.30 | 126.00 |
| 2026-11-23 | 4 | 40.66 | 11.50 | 9.90 |
| 2026-11-27 | 8 | 43.70 | 53,407.20 | 51,895.50 |
| 2026-12-04 | 15 | 44.02 | 5,289.20 | 9,717.50 |
| 2026-12-11 | 22 | 44.51 | 8.70 | 557.50 |
| 2026-12-25 | 36 | 43.06 | 89,523.60 | 61,195.00 |
| 2027-01-29 | 71 | 42.23 | 8,016.10 | 7,868.70 |
| 2027-03-26 | 127 | 42.46 | 29,277.30 | 19,365.10 |
| 2027-06-25 | 218 | 42.31 | 12,010.40 | 10,035.20 |
| 2027-09-24 | 309 | 42.15 | 7,509.40 | 4,470.80 |

| Scadenza | 25Δ put IV % | 25Δ call IV % | Put-call skew vol points |
|---|---:|---:|---:|
| 2026-11-20 | n/d | n/d | n/d |
| 2026-11-21 | n/d | n/d | n/d |
| 2026-11-22 | n/d | n/d | n/d |
| 2026-11-23 | 49.90 | n/d | n/d |
- Gamma/dealer positioning: NOT_IDENTIFIABLE; Public open interest and option Greeks do not reveal whether dealers are net long or short; no dealer-side sign is inferred.

### ETF spot Bitcoin USA

- Stato: PASS; dati aggiornati al 2026-11-18 (circa 1 sessioni USA di ritardo).
- Flusso ultima sessione: -306,421,294.34 USD.
- AUM totale ultima sessione: 77,706,592,903.47 USD.
- Flusso cumulativo dalla partenza: 54,147,391,129.98 USD.
- Flusso ultime 21 sessioni: -3,333,162,157.92 USD.
- Flusso ultime 30 sessioni: -3,234,981,309.27 USD.
- Fonte/licenza: The Commoner Bitcoin ETF Tracker by TFTC, tftc.io/bitcoin-etf-flows / https://creativecommons.org/licenses/by/4.0/.

## 4. Macro e mercati USA

| Serie | Periodo osservato | Freschezza fino | Valore | Unità | Stato | Recuperato UTC | Fonte / metodo |
|---|---|---|---:|---|---|---|---|
| DGS2 — US Treasury 2Y yield | 2026-11-18 | 2026-11-18 | 4.8000 | percent | PASS | 2026-11-19T18:44:55.316414+00:00 | official Treasury daily par yield curve; independent of FRED transport |
| DGS10 — US Treasury 10Y yield | 2026-11-18 | 2026-11-18 | 5.0700 | percent | PASS | 2026-11-19T18:44:55.296867+00:00 | official Treasury daily par yield curve; independent of FRED transport |
| VIXCLS — CBOE VIX | 2026-11-18 | 2026-11-18 | 24.5600 | index points | PASS | 2026-11-19T18:47:55.750210+00:00 | Cboe official historical daily VIX close; independent of FRED transport |

Feed macro non acquisiti: {'DFII10': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=DFII10&cosd=2025-11-19&coed=2026-11-19 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'FEDFUNDS': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=FEDFUNDS&cosd=2021-11-20&coed=2026-11-19 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'CPIAUCSL': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=CPIAUCSL&cosd=2021-11-20&coed=2026-11-19 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'PCEPILFE': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=PCEPILFE&cosd=2021-11-20&coed=2026-11-19 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'UNRATE': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=UNRATE&cosd=2021-11-20&coed=2026-11-19 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'PAYEMS': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=PAYEMS&cosd=2021-11-20&coed=2026-11-19 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'DTWEXBGS': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=DTWEXBGS&cosd=2025-11-19&coed=2026-11-19 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'WALCL': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=WALCL&cosd=2025-11-19&coed=2026-11-19 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'RRPONTSYD': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=RRPONTSYD&cosd=2025-11-19&coed=2026-11-19 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'NFCI': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=NFCI&cosd=2025-11-19&coed=2026-11-19 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'SP500': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=SP500&cosd=2025-11-19&coed=2026-11-19 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'NASDAQCOM': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=NASDAQCOM&cosd=2025-11-19&coed=2026-11-19 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'M2SL': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=M2SL&cosd=2021-11-20&coed=2026-11-19 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))'}

## 5. Ciclo Bitcoin — confronto post-halving

- Stato: PASS; fonte: Bitstamp BTC/USD daily OHLCV; same venue and quote currency.
- Orizzonte corrente: 942 sessioni dal 20 aprile 2024.
- Limite: Descriptive comparison at the same elapsed days after halving; sample is small, cycles are structurally different, and this is not a timing forecast.
| Ciclo | Stato | Giorni/sessioni | Rendimento stesso orizzonte | Massimo rendimento | Giorni al picco | Drawdown massimo da picco |
|---|---|---:|---:|---:|---:|---:|
| 2012 cycle | INSUFFICIENT_HISTORY | n/d | n/d% | n/d% | n/d | n/d% |
| 2016 cycle | INSUFFICIENT_HISTORY | n/d | n/d% | n/d% | n/d | n/d% |
| 2020 cycle | PASS | 942 | 99.81% | 688.14% | 546 | -76.66% |
| 2024 cycle (current) | PASS | 942 | -3.10% | 91.92% | 534 | -53.08% |

## 6. Eventi, regolamentazione e geopolitica — feed descrittivi

- Stato: PARTIAL. Headlines and keyword tags are descriptive only; no sentiment, event-impact score or trading signal is inferred.
| Fonte | Stato | Acquisiti | Rilevanti nel report |
|---|---|---:|---:|
| Federal Reserve | PASS | 20 | 11 |
| SEC | PASS | 25 | 15 |
| White House | PASS | 30 | 1 |
| ECB | PASS | 15 | 5 |
| CFTC | NOT_CONFIGURED | n/d | 0 |
| GDELT | FAIL | n/d | 0 |
- 2026-11-19T16:00:00+00:00 — Federal Reserve — Federal Reserve Board issues enforcement action with former employee of First Security Bancorp [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/enforcement20261119a.htm
- 2026-11-19T14:39:02+00:00 — SEC — SEC: Eight Entities Used Fake Crypto Asset Trading Platforms to Steal More Than $37 Million From U.S. Investors [regulatory, crypto] — https://www.sec.gov/newsroom/press-releases/2026-115-sec-eight-entities-used-fake-crypto-asset-trading-platforms-steal-more-37-million-us-investors
- 2026-11-19T13:53:04+00:00 — White House — U.S.-Russia-China Heads of State Declaration toward Peace [geopolitical] — https://www.whitehouse.gov/briefings-statements/2026/11/u-s-russia-china-heads-of-state-declaration-toward-peace/
- 2026-11-17T18:30:00+00:00 — ECB — Philip R. Lane: The practice and science of monetary policy communication: the ECB experience [macro_monetary] — https://www.ecb.europa.eu//press/key/date/2026/html/ecb.sp261117~7f5d3b1a0e.en.pdf
- 2026-11-13T16:57:00+00:00 — SEC — SEC Proposes Executive and Director Compensation Disclosure Reforms [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-114-sec-proposes-executive-director-compensation-disclosure-reforms
- 2026-11-12T18:30:00+00:00 — Federal Reserve — Federal Reserve Board announces pricing, effective January 1, 2027, for payment services the Federal Reserve Banks provide to banks and credit unions, and changes to streamline and adjust their check services [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/other20261112a.htm
- 2026-11-12T17:45:00+00:00 — Federal Reserve — Federal Reserve announces revised tentative schedule of Federal Open Market Committee meetings in 2027 [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/monetary20261112a.htm
- 2026-11-12T16:00:00+00:00 — Federal Reserve — Federal Reserve Board issues enforcement action with former employee of United Community Bank [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/enforcement20261112a.htm
- 2026-11-10T16:45:00+00:00 — ECB — Philip R. Lane: The science and practice of monetary policy communication: the ECB experience [macro_monetary] — https://www.ecb.europa.eu//press/key/date/2026/html/ecb.sp261110_1~9725b7aa07.en.html
- 2026-11-10T16:15:35+00:00 — SEC — SEC Announces Enforcement Annual Results for Fiscal Year 2026 [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-113-sec-announces-enforcement-annual-results-fiscal-year-2026
- 2026-11-09T21:00:00+00:00 — Federal Reserve — Federal Reserve Board announces approval of two applications by Mutual Federal Bancorp, MHC, and MFB Bancorp, Inc. [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/orders20261109a.htm
- 2026-11-06T09:00:00+00:00 — ECB — ECB publishes consolidated banking data for end-June 2026 [macro_monetary] — https://www.ecb.europa.eu//press/pr/date/2026/html/ecb.pr261106~356f2fc73a.en.html

## 7. Fatti, interpretazioni, ipotesi e previsioni

### FATTI
- binance_acquisition_and_qa: PASS.
- bitstamp_acquisition_and_qa: PASS.
- coinbase_recent_cross_check: PASS.
- kraken_recent_cross_check: PASS.
- supplemental_market_context: PASS.
- walk_forward: SCORED_NOT_PROMOTED.
- Le metriche storiche sono diagnostiche di continuità, non prove prospettiche.
- Il ledger prospettico conteggia esclusivamente eventi SCORE maturati.
- Supplemental feed spot_ohlcv: PASS.
- Supplemental feed spot_live_quotes: PARTIAL.
- Supplemental feed per_exchange_derivatives: PARTIAL.
- Supplemental feed options: PARTIAL.
- Supplemental feed us_spot_etf_flows: PASS.
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
- Point forecast emessi in questo run: 0.
- Forecast maturati/scorati in questo run: 0.
- Probabilità calibrate pubblicate: False.
- Eventuali valori nel ledger sono point forecast sperimentali; non sono probabilità calibrate né segnali operativi.

## 8. Validazione quantitativa

Le metriche seguenti sono diagnostiche sul periodo storico già ispezionato; non sono prova prospettica né PnL eseguibile.

| Orizzonte | N | Zero MAE | Drift MAE | Momentum MAE | Ridge MAE |
|---:|---:|---:|---:|---:|---:|
| 1 sessioni | 362 | 0.015751 | 0.015809 | 0.027318 | 0.015808 |
| 3 sessioni | 360 | 0.028263 | 0.028453 | 0.049059 | 0.028547 |
| 7 sessioni | 356 | 0.043092 | 0.043897 | 0.077250 | 0.043841 |
| 30 sessioni | 333 | 0.102905 | 0.103960 | 0.184991 | 0.105137 |

## 9. Ledger e rischio

- Stato ledger: VERIFIED_IN_WORKSPACE_PENDING_WORKFLOW_COMMIT; eventi prima/dopo: 25 / 25.
- Nuove previsioni: 0; duplicate soppresse: 4; score maturati: 0.
- Campione prospettico: INSUFFICIENT_PROSPECTIVE_EVIDENCE.
- Rischio: paper_only; live trading: False; esposizione teorica: 0.00%.
- Champion congelato: zero-return. Ridge è challenger non promosso.
- Nessun PnL economico o probabilità calibrata è dichiarato.

## 10. Revisione critica e conclusione

- Gate pre-report: PASS; cicli completati: 7; fallimenti bloccanti: [].
- Fattore osservato: Variazione close-to-close = -2.8933 % (Binance spot BTCUSDT, 2026-11-18T00:00:00+00:00).
- Fattore osservato: Ampiezza intraday high-low/open = 4.5252 % (Binance spot BTCUSDT, 2026-11-18T00:00:00+00:00).
- Fattore osservato: Volume rispetto alla mediana precedente = 1.2042 multiplo (Binance spot BTCUSDT, 2026-11-18T00:00:00+00:00).
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
