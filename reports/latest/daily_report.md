# BTC Quant Desk — report giornaliero

- Protocollo: **V5.6**
- Stato: **COMPLETE_NOT_PROMOTED**
- Avvio UTC: 2026-11-22T16:38:39.631860+00:00
- Fine UTC: 2026-11-22T16:44:03.206870+00:00
- Commit: `d86091a4e669f5a89602d92a129bdce798cc2d7c`
- Workflow run: 45044958920

> I valori di mercato sono distinti tra osservazioni live, snapshot e candele chiuse. USD e USDT non sono convertiti né uniti.

## 1. Acquisizione e qualità dati

| Feed | Stato | Evidenza / dettaglio |
|---|---|---|
| binance_acquisition_and_qa | PASS | righe=3384, gap=0, duplicati=0, ultima candela=2026-11-21T00:00:00+00:00 |
| bitstamp_acquisition_and_qa | PASS | righe=3650, gap=0, duplicati=0, ultima candela=2026-11-21T00:00:00+00:00 |
| coinbase_recent_cross_check | PASS | righe=300, gap=0, duplicati=0, ultima candela=2026-11-21T00:00:00+00:00 |
| kraken_recent_cross_check | PASS | righe=720, gap=0, duplicati=0, ultima candela=2026-11-21T00:00:00+00:00 |
| supplemental_market_context | PASS | PASS |
| walk_forward | SCORED_NOT_PROMOTED | SCORED_NOT_PROMOTED |

## 2. Prezzi spot — ultime candele giornaliere chiuse

| Venue | Strumento | Candela UTC | Close | 1D | 7D | 30D | Range intraday | Vol 1D BTC | Vol 7D BTC | Vol 30D BTC |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Binance | BTCUSDT (USDT) | 2026-11-21T00:00:00+00:00 | 60,215.77 | 2.145% | -6.133% | -26.039% | 9.951% | 48,558.10 | 204,740.52 | 568,986.18 |
| Bitstamp | BTC/USD (USD) | 2026-11-21T00:00:00+00:00 | 60,078.34 | 2.150% | -6.294% | -26.117% | 9.865% | 2,044.49 | 10,203.23 | 49,399.22 |

### Quotazioni spot — ultimo scambio osservato

| Venue | Stato | Prezzo | Variazione 24h | Volume base 24h | Timestamp ultimo scambio UTC | Età sec |
|---|---|---:|---:|---:|---|---:|
| Bitstamp_BTCUSD_USD | PASS | 61,189.54 | 1.850% | 1,469.41 BTC | 2026-11-22T16:39:42+00:00 | 1.1 |

### Livelli tecnici descrittivi — non segnali

| Venue | SMA20 | SMA50 | SMA200 | Massimo 20D | Minimo 20D | ATR14 |
|---|---:|---:|---:|---:|---:|---:|
| Binance | 70,196.60 | 77,231.67 | 72,485.74 | 81,196.01 | 55,130.00 | 3,019.77 |
| Bitstamp | 70,102.43 | 77,137.86 | 72,427.40 | 81,105.28 | 55,081.31 | 3,008.92 |

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
- Snapshot acquisito UTC: 2026-11-22T16:39:58.155006+00:00.
- Ultimo prezzo: 61,249.20 USDT (ticker 2026-11-22T16:39:56.361000+00:00).
- Volume 24h: 100,340.19 BTC (10,034,019.30 contratti).
- Open interest snapshot: 32,097.95 BTC (1,965,973,484 USD; snapshot 2026-11-22T16:39:57.264000+00:00).
- OI storico giornaliero UTC: 1D 2.03%; 7D -1.32%; 30D 3.86% (ultimo punto 2026-11-22T00:00:00+00:00).
- Funding previsto per il prossimo settlement (2026-11-23T00:00:00+00:00): 0.00002153 (frazione per intervallo).
- Ultimo funding effettivamente settled: 0.00002278 al 2026-11-22T16:00:00+00:00 (stato settled).
- Settlement successivo dopo il periodo corrente: 2026-11-23T08:00:00+00:00.
- Storico funding: 100 settlement acquisiti.
- Delta taker futures BTC (buy − sell, barre UTC chiuse): 1D 1,183.80 BTC; 7D -10,838.16 BTC; 30D n/d BTC.
- Copertura delta taker: 29 barre UTC complete su 30 scaricate.
- Nota CVD: OKX BTC-USDT perpetual contract taker volume in BTC; buy minus sell. Completed UTC daily bars only; exchange-specific derivatives delta proxy, not spot CVD or total-market CVD.
- Liquidazioni: NOT_ACQUIRED; nessuna stima ricavata da endpoint non pertinenti.
- Copertura per venue: Binance FAIL; Bybit FAIL; OKX PASS.

### CVD orario Binance — delta taker aggregato

- Stato: PARTIAL. Hourly Binance kline taker-buy base volume minus inferred taker-sell base volume for rolling 24h/7d/30d windows; not tick-level order-book delta.
| Mercato | Finestra | Delta BTC | Delta / volume % | Volume BTC | Buy BTC | Sell BTC |
|---|---:|---:|---:|---:|---:|---:|
| Spot BTCUSDT | 24h | 337.92 | 1.69% | 19,944.20 | 10,141.06 | 9,803.14 |
| Spot BTCUSDT | 7d | -5,725.70 | -2.91% | 196,804.54 | 95,539.42 | 101,265.12 |
| Spot BTCUSDT | 30d | -1,912.68 | -0.33% | 575,352.34 | 286,719.83 | 288,632.51 |
| Futures BTCUSDT | 24h | n/d | n/d% | n/d | n/d | n/d |
| Futures BTCUSDT | 7d | n/d | n/d% | n/d | n/d | n/d |
| Futures BTCUSDT | 30d | n/d | n/d% | n/d | n/d | n/d |

### Opzioni Deribit

- Stato: PARTIAL; open interest con ritardo provider di 8 ore.
- OI call/put: 230,119.5000 / 188,412.2000 BTC.
- Put/call OI: 0.8188.
- Put/call volume USD 24h: 0.9265.

| Scadenza | DTE | ATM IV % | OI call BTC | OI put BTC |
|---|---:|---:|---:|---:|
| 2026-11-23 | 1 | 61.69 | 2,078.10 | 2,513.90 |
| 2026-11-24 | 2 | 63.91 | 1,016.90 | 1,675.30 |
| 2026-11-25 | 3 | 63.91 | 535.90 | 154.00 |
| 2026-11-26 | 4 | 62.05 | 1.50 | 0.00 |
| 2026-11-27 | 5 | 59.48 | 57,566.70 | 54,080.30 |
| 2026-12-04 | 12 | 55.57 | 7,990.30 | 13,644.30 |
| 2026-12-11 | 19 | 54.74 | 3,678.70 | 2,903.20 |
| 2026-12-25 | 33 | 51.14 | 93,965.00 | 63,468.10 |
| 2027-01-29 | 68 | 48.53 | 10,718.40 | 11,707.10 |
| 2027-03-26 | 124 | 48.05 | 32,235.60 | 21,725.30 |
| 2027-06-25 | 215 | 46.77 | 12,236.30 | 10,850.20 |
| 2027-09-24 | 306 | 46.66 | 8,096.10 | 5,690.50 |

| Scadenza | 25Δ put IV % | 25Δ call IV % | Put-call skew vol points |
|---|---:|---:|---:|
| 2026-11-23 | n/d | n/d | n/d |
| 2026-11-24 | n/d | n/d | n/d |
| 2026-11-25 | n/d | n/d | n/d |
| 2026-11-26 | n/d | n/d | n/d |
- Gamma/dealer positioning: NOT_IDENTIFIABLE; Public open interest and option Greeks do not reveal whether dealers are net long or short; no dealer-side sign is inferred.

### ETF spot Bitcoin USA

- Stato: PASS; dati aggiornati al 2026-11-19 (circa 1 sessioni USA di ritardo).
- Flusso ultima sessione: -582,193,660.70 USD.
- AUM totale ultima sessione: 76,549,156,272.32 USD.
- Flusso cumulativo dalla partenza: 53,565,197,469.27 USD.
- Flusso ultime 21 sessioni: -4,443,756,055.77 USD.
- Flusso ultime 30 sessioni: -3,573,049,340.80 USD.
- Fonte/licenza: The Commoner Bitcoin ETF Tracker by TFTC, tftc.io/bitcoin-etf-flows / https://creativecommons.org/licenses/by/4.0/.

## 4. Macro e mercati USA

| Serie | Periodo osservato | Freschezza fino | Valore | Unità | Stato | Recuperato UTC | Fonte / metodo |
|---|---|---|---:|---|---|---|---|
| DGS2 — US Treasury 2Y yield | 2026-11-20 | 2026-11-20 | 4.6300 | percent | PASS | 2026-11-22T16:41:02.194360+00:00 | official Treasury daily par yield curve; independent of FRED transport |
| DGS10 — US Treasury 10Y yield | 2026-11-20 | 2026-11-20 | 4.9200 | percent | PASS | 2026-11-22T16:41:02.088393+00:00 | official Treasury daily par yield curve; independent of FRED transport |
| VIXCLS — CBOE VIX | 2026-11-20 | 2026-11-20 | 35.8900 | index points | PASS | 2026-11-22T16:44:02.945213+00:00 | Cboe official historical daily VIX close; independent of FRED transport |

Feed macro non acquisiti: {'DFII10': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=DFII10&cosd=2025-11-22&coed=2026-11-22 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'FEDFUNDS': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=FEDFUNDS&cosd=2021-11-23&coed=2026-11-22 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'CPIAUCSL': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=CPIAUCSL&cosd=2021-11-23&coed=2026-11-22 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'PCEPILFE': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=PCEPILFE&cosd=2021-11-23&coed=2026-11-22 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'UNRATE': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=UNRATE&cosd=2021-11-23&coed=2026-11-22 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'PAYEMS': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=PAYEMS&cosd=2021-11-23&coed=2026-11-22 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'DTWEXBGS': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=DTWEXBGS&cosd=2025-11-22&coed=2026-11-22 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'WALCL': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=WALCL&cosd=2025-11-22&coed=2026-11-22 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'RRPONTSYD': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=RRPONTSYD&cosd=2025-11-22&coed=2026-11-22 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'NFCI': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=NFCI&cosd=2025-11-22&coed=2026-11-22 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'SP500': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=SP500&cosd=2025-11-22&coed=2026-11-22 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'NASDAQCOM': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=NASDAQCOM&cosd=2025-11-22&coed=2026-11-22 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'M2SL': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=M2SL&cosd=2021-11-23&coed=2026-11-22 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))'}

## 5. Ciclo Bitcoin — confronto post-halving

- Stato: PASS; fonte: Bitstamp BTC/USD daily OHLCV; same venue and quote currency.
- Orizzonte corrente: 945 sessioni dal 20 aprile 2024.
- Limite: Descriptive comparison at the same elapsed days after halving; sample is small, cycles are structurally different, and this is not a timing forecast.
| Ciclo | Stato | Giorni/sessioni | Rendimento stesso orizzonte | Massimo rendimento | Giorni al picco | Drawdown massimo da picco |
|---|---|---:|---:|---:|---:|---:|
| 2012 cycle | INSUFFICIENT_HISTORY | n/d | n/d% | n/d% | n/d | n/d% |
| 2016 cycle | INSUFFICIENT_HISTORY | n/d | n/d% | n/d% | n/d | n/d% |
| 2020 cycle | PASS | 945 | 100.76% | 688.14% | 546 | -76.66% |
| 2024 cycle (current) | PASS | 945 | -7.56% | 91.92% | 534 | -53.08% |

## 6. Eventi, regolamentazione e geopolitica — feed descrittivi

- Stato: PARTIAL. Headlines and keyword tags are descriptive only; no sentiment, event-impact score or trading signal is inferred.
| Fonte | Stato | Acquisiti | Rilevanti nel report |
|---|---|---:|---:|
| Federal Reserve | PASS | 20 | 12 |
| SEC | PASS | 25 | 15 |
| White House | PASS | 30 | 4 |
| ECB | PASS | 15 | 5 |
| CFTC | NOT_CONFIGURED | n/d | 0 |
| GDELT | FAIL | n/d | 0 |
- 2026-11-20T22:57:43+00:00 — White House — WHAT THEY ARE SAYING: Send the Bipartisan American Affordability and Jobs Act to President Trump’s Desk [regulatory] — https://www.whitehouse.gov/releases/2026/11/what-they-are-saying-send-the-bipartisan-american-affordability-and-jobs-act-to-president-trumps-desk/
- 2026-11-20T21:15:00+00:00 — Federal Reserve — Federal Reserve announces College Fed Challenge winners [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/other20261120b.htm
- 2026-11-20T19:41:38+00:00 — White House — H.R. 10167 – Common Cents Act [macro_monetary] — https://www.whitehouse.gov/briefings-statements/2026/11/h-r-10167-common-cents-act/
- 2026-11-20T18:03:24+00:00 — SEC — SEC Issues Proposal to Restructure the Consolidated Audit Trail [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-117-sec-issues-proposal-restructure-consolidated-audit-trail
- 2026-11-20T15:00:00+00:00 — Federal Reserve — Federal Reserve Board releases results from survey of senior financial officers at banks about their strategies and practices for managing reserve balances [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/other20261120a.htm
- 2026-11-20T14:28:28+00:00 — SEC — SEC Charges Indianapolis-Based Backward Hat Capital and Its Co-Founders With $560 Million Dollar Offering Fraud and Obtains Emergency Relief [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-116-sec-charges-indianapolis-based-backward-hat-capital-its-co-founders-560-million-dollar-offering
- 2026-11-19T19:20:20+00:00 — White House — ICYMI: President Trump Talks China, Iran, Super Intelligence, and the Path Ahead in Exclusive Interview from Shenzhen [geopolitical] — https://www.whitehouse.gov/releases/2026/11/icymi-president-trump-talks-china-iran-super-intelligence-and-the-path-ahead-in-exclusive-interview-from-shenzhen/
- 2026-11-19T16:00:00+00:00 — Federal Reserve — Federal Reserve Board issues enforcement action with former employee of First Security Bancorp [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/enforcement20261119a.htm
- 2026-11-19T14:39:02+00:00 — SEC — SEC: Eight Entities Used Fake Crypto Asset Trading Platforms to Steal More Than $37 Million From U.S. Investors [regulatory, crypto] — https://www.sec.gov/newsroom/press-releases/2026-115-sec-eight-entities-used-fake-crypto-asset-trading-platforms-steal-more-37-million-us-investors
- 2026-11-19T13:53:04+00:00 — White House — U.S.-Russia-China Heads of State Declaration toward Peace [geopolitical] — https://www.whitehouse.gov/briefings-statements/2026/11/u-s-russia-china-heads-of-state-declaration-toward-peace/
- 2026-11-17T18:30:00+00:00 — ECB — Philip R. Lane: The practice and science of monetary policy communication: the ECB experience [macro_monetary] — https://www.ecb.europa.eu//press/key/date/2026/html/ecb.sp261117~7f5d3b1a0e.en.pdf
- 2026-11-13T16:57:00+00:00 — SEC — SEC Proposes Executive and Director Compensation Disclosure Reforms [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-114-sec-proposes-executive-director-compensation-disclosure-reforms

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
- Point forecast emessi in questo run: 4.
- Forecast maturati/scorati in questo run: 2.
- Probabilità calibrate pubblicate: False.
- Eventuali valori nel ledger sono point forecast sperimentali; non sono probabilità calibrate né segnali operativi.

## 8. Validazione quantitativa

Le metriche seguenti sono diagnostiche sul periodo storico già ispezionato; non sono prova prospettica né PnL eseguibile.

| Orizzonte | N | Zero MAE | Drift MAE | Momentum MAE | Ridge MAE |
|---:|---:|---:|---:|---:|---:|
| 1 sessioni | 362 | 0.015890 | 0.015951 | 0.027224 | 0.015946 |
| 3 sessioni | 360 | 0.028565 | 0.028794 | 0.048682 | 0.028802 |
| 7 sessioni | 356 | 0.043829 | 0.044723 | 0.076884 | 0.044539 |
| 30 sessioni | 333 | 0.105319 | 0.106796 | 0.184606 | 0.107769 |

## 9. Ledger e rischio

- Stato ledger: VERIFIED_IN_WORKSPACE_PENDING_WORKFLOW_COMMIT; eventi prima/dopo: 36 / 42.
- Nuove previsioni: 4; duplicate soppresse: 0; score maturati: 2.
- Campione prospettico: INSUFFICIENT_PROSPECTIVE_EVIDENCE.
- Rischio: paper_only; live trading: False; esposizione teorica: 0.00%.
- Champion congelato: zero-return. Ridge è challenger non promosso.
- Nessun PnL economico o probabilità calibrata è dichiarato.

## 10. Revisione critica e conclusione

- Gate pre-report: PASS; cicli completati: 7; fallimenti bloccanti: [].
- Fattore osservato: Variazione close-to-close = 2.1446 % (Binance spot BTCUSDT, 2026-11-21T00:00:00+00:00).
- Fattore osservato: Ampiezza intraday high-low/open = 9.9506 % (Binance spot BTCUSDT, 2026-11-21T00:00:00+00:00).
- Fattore osservato: Volume rispetto alla mediana precedente = 2.9779 multiplo (Binance spot BTCUSDT, 2026-11-21T00:00:00+00:00).
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
