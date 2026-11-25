# BTC Quant Desk — report giornaliero

- Protocollo: **V5.6**
- Stato: **COMPLETE_NOT_PROMOTED**
- Avvio UTC: 2026-11-25T16:59:02.381470+00:00
- Fine UTC: 2026-11-25T17:03:58.920474+00:00
- Commit: `ffbb0e2225cedd45e6e6d3db6f9ba8edf791f3d4`
- Workflow run: 45659731420

> I valori di mercato sono distinti tra osservazioni live, snapshot e candele chiuse. USD e USDT non sono convertiti né uniti.

## 1. Acquisizione e qualità dati

| Feed | Stato | Evidenza / dettaglio |
|---|---|---|
| binance_acquisition_and_qa | PASS | righe=3387, gap=0, duplicati=0, ultima candela=2026-11-24T00:00:00+00:00 |
| bitstamp_acquisition_and_qa | PASS | righe=3650, gap=0, duplicati=0, ultima candela=2026-11-24T00:00:00+00:00 |
| coinbase_recent_cross_check | PASS | righe=300, gap=0, duplicati=0, ultima candela=2026-11-24T00:00:00+00:00 |
| kraken_recent_cross_check | PASS | righe=720, gap=0, duplicati=0, ultima candela=2026-11-24T00:00:00+00:00 |
| supplemental_market_context | PASS | PASS |
| walk_forward | SCORED_NOT_PROMOTED | SCORED_NOT_PROMOTED |

## 2. Prezzi spot — ultime candele giornaliere chiuse

| Venue | Strumento | Candela UTC | Close | 1D | 7D | 30D | Range intraday | Vol 1D BTC | Vol 7D BTC | Vol 30D BTC |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Binance | BTCUSDT (USDT) | 2026-11-24T00:00:00+00:00 | 59,832.00 | -2.348% | -7.876% | -25.354% | 3.953% | 19,707.40 | 192,601.78 | 605,883.62 |
| Bitstamp | BTC/USD (USD) | 2026-11-24T00:00:00+00:00 | 59,743.50 | -2.395% | -7.913% | -25.366% | 3.912% | 1,261.82 | 11,350.33 | 50,262.32 |

### Quotazioni spot — ultimo scambio osservato

| Venue | Stato | Prezzo | Variazione 24h | Volume base 24h | Timestamp ultimo scambio UTC | Età sec |
|---|---|---:|---:|---:|---|---:|
| Bitstamp_BTCUSD_USD | PASS | 58,501.62 | -2.079% | 1,612.07 BTC | 2026-11-25T16:59:40+00:00 | 0.6 |

### Livelli tecnici descrittivi — non segnali

| Venue | SMA20 | SMA50 | SMA200 | Massimo 20D | Minimo 20D | ATR14 |
|---|---:|---:|---:|---:|---:|---:|
| Binance | 67,576.61 | 75,738.14 | 72,189.38 | 80,918.01 | 55,130.00 | 3,049.20 |
| Bitstamp | 67,485.88 | 75,640.05 | 72,129.70 | 80,821.81 | 55,081.31 | 3,040.25 |

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
- Snapshot acquisito UTC: 2026-11-25T16:59:54.387509+00:00.
- Ultimo prezzo: 58,571.10 USDT (ticker 2026-11-25T16:59:52.366000+00:00).
- Volume 24h: 142,709.24 BTC (14,270,924.04 contratti).
- Open interest snapshot: 31,299.06 BTC (1,833,508,600 USD; snapshot 2026-11-25T16:59:53.563000+00:00).
- OI storico giornaliero UTC: 1D 1.85%; 7D -5.09%; 30D -1.65% (ultimo punto 2026-11-25T00:00:00+00:00).
- Funding previsto per il prossimo settlement (2026-11-26T00:00:00+00:00): 0.00005697 (frazione per intervallo).
- Ultimo funding effettivamente settled: 0.00003840 al 2026-11-25T16:00:00+00:00 (stato settled).
- Settlement successivo dopo il periodo corrente: 2026-11-26T08:00:00+00:00.
- Storico funding: 100 settlement acquisiti.
- Delta taker futures BTC (buy − sell, barre UTC chiuse): 1D -209.86 BTC; 7D -5,056.55 BTC; 30D n/d BTC.
- Copertura delta taker: 29 barre UTC complete su 30 scaricate.
- Nota CVD: OKX BTC-USDT perpetual contract taker volume in BTC; buy minus sell. Completed UTC daily bars only; exchange-specific derivatives delta proxy, not spot CVD or total-market CVD.
- Liquidazioni: NOT_ACQUIRED; nessuna stima ricavata da endpoint non pertinenti.
- Copertura per venue: Binance FAIL; Bybit FAIL; OKX PASS.

### CVD orario Binance — delta taker aggregato

- Stato: PARTIAL. Hourly Binance kline taker-buy base volume minus inferred taker-sell base volume for rolling 24h/7d/30d windows; not tick-level order-book delta.
| Mercato | Finestra | Delta BTC | Delta / volume % | Volume BTC | Buy BTC | Sell BTC |
|---|---:|---:|---:|---:|---:|---:|
| Spot BTCUSDT | 24h | 708.07 | 3.08% | 22,983.85 | 11,845.96 | 11,137.89 |
| Spot BTCUSDT | 7d | -6,794.94 | -3.39% | 200,270.11 | 96,737.59 | 103,532.53 |
| Spot BTCUSDT | 30d | -859.68 | -0.14% | 612,951.21 | 306,045.76 | 306,905.45 |
| Futures BTCUSDT | 24h | n/d | n/d% | n/d | n/d | n/d |
| Futures BTCUSDT | 7d | n/d | n/d% | n/d | n/d | n/d |
| Futures BTCUSDT | 30d | n/d | n/d% | n/d | n/d | n/d |

### Opzioni Deribit

- Stato: PARTIAL; open interest con ritardo provider di 8 ore.
- OI call/put: 242,175.9000 / 195,355.6000 BTC.
- Put/call OI: 0.8067.
- Put/call volume USD 24h: 3.3854.

| Scadenza | DTE | ATM IV % | OI call BTC | OI put BTC |
|---|---:|---:|---:|---:|
| 2026-11-26 | 1 | 63.17 | 858.70 | 1,749.10 |
| 2026-11-27 | 2 | 62.00 | 59,935.20 | 52,706.70 |
| 2026-11-28 | 3 | 61.56 | 418.10 | 367.90 |
| 2026-11-29 | 4 | 55.68 | 19.70 | 30.60 |
| 2026-12-04 | 9 | 57.10 | 9,992.30 | 14,918.00 |
| 2026-12-11 | 16 | 56.85 | 4,482.70 | 5,134.80 |
| 2026-12-25 | 30 | 53.23 | 97,264.40 | 66,193.20 |
| 2027-01-29 | 65 | 49.21 | 13,228.50 | 13,665.50 |
| 2027-03-26 | 121 | 47.97 | 34,187.70 | 22,985.00 |
| 2027-06-25 | 212 | 47.46 | 12,848.40 | 11,182.60 |
| 2027-09-24 | 303 | 46.90 | 8,940.20 | 6,422.20 |

| Scadenza | 25Δ put IV % | 25Δ call IV % | Put-call skew vol points |
|---|---:|---:|---:|
| 2026-11-26 | n/d | n/d | n/d |
| 2026-11-27 | n/d | n/d | n/d |
| 2026-11-28 | n/d | n/d | n/d |
| 2026-11-29 | n/d | n/d | n/d |
- Gamma/dealer positioning: NOT_IDENTIFIABLE; Public open interest and option Greeks do not reveal whether dealers are net long or short; no dealer-side sign is inferred.

### ETF spot Bitcoin USA

- Stato: PASS; dati aggiornati al 2026-11-24 (circa 1 sessioni USA di ritardo).
- Flusso ultima sessione: -231,556,490.07 USD.
- AUM totale ultima sessione: 72,009,917,872.68 USD.
- Flusso cumulativo dalla partenza: 52,094,739,283.78 USD.
- Flusso ultime 21 sessioni: -5,251,129,357.05 USD.
- Flusso ultime 30 sessioni: -5,174,852,012.08 USD.
- Fonte/licenza: The Commoner Bitcoin ETF Tracker by TFTC, tftc.io/bitcoin-etf-flows / https://creativecommons.org/licenses/by/4.0/.

## 4. Macro e mercati USA

| Serie | Periodo osservato | Freschezza fino | Valore | Unità | Stato | Recuperato UTC | Fonte / metodo |
|---|---|---|---:|---|---|---|---|
| DGS2 — US Treasury 2Y yield | 2026-11-24 | 2026-11-24 | 4.6300 | percent | PASS | 2026-11-25T17:00:58.016200+00:00 | official Treasury daily par yield curve; independent of FRED transport |
| DGS10 — US Treasury 10Y yield | 2026-11-24 | 2026-11-24 | 4.9100 | percent | PASS | 2026-11-25T17:00:58.096242+00:00 | official Treasury daily par yield curve; independent of FRED transport |
| VIXCLS — CBOE VIX | 2026-11-24 | 2026-11-24 | 26.3600 | index points | PASS | 2026-11-25T17:03:58.573026+00:00 | Cboe official historical daily VIX close; independent of FRED transport |

Feed macro non acquisiti: {'DFII10': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=DFII10&cosd=2025-11-25&coed=2026-11-25 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'FEDFUNDS': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=FEDFUNDS&cosd=2021-11-26&coed=2026-11-25 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'CPIAUCSL': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=CPIAUCSL&cosd=2021-11-26&coed=2026-11-25 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'PCEPILFE': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=PCEPILFE&cosd=2021-11-26&coed=2026-11-25 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'UNRATE': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=UNRATE&cosd=2021-11-26&coed=2026-11-25 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'PAYEMS': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=PAYEMS&cosd=2021-11-26&coed=2026-11-25 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'DTWEXBGS': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=DTWEXBGS&cosd=2025-11-25&coed=2026-11-25 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'WALCL': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=WALCL&cosd=2025-11-25&coed=2026-11-25 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'RRPONTSYD': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=RRPONTSYD&cosd=2025-11-25&coed=2026-11-25 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'NFCI': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=NFCI&cosd=2025-11-25&coed=2026-11-25 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'SP500': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=SP500&cosd=2025-11-25&coed=2026-11-25 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'NASDAQCOM': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=NASDAQCOM&cosd=2025-11-25&coed=2026-11-25 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'M2SL': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=M2SL&cosd=2021-11-26&coed=2026-11-25 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))'}

## 5. Ciclo Bitcoin — confronto post-halving

- Stato: PASS; fonte: Bitstamp BTC/USD daily OHLCV; same venue and quote currency.
- Orizzonte corrente: 948 sessioni dal 20 aprile 2024.
- Limite: Descriptive comparison at the same elapsed days after halving; sample is small, cycles are structurally different, and this is not a timing forecast.
| Ciclo | Stato | Giorni/sessioni | Rendimento stesso orizzonte | Massimo rendimento | Giorni al picco | Drawdown massimo da picco |
|---|---|---:|---:|---:|---:|---:|
| 2012 cycle | INSUFFICIENT_HISTORY | n/d | n/d% | n/d% | n/d | n/d% |
| 2016 cycle | INSUFFICIENT_HISTORY | n/d | n/d% | n/d% | n/d | n/d% |
| 2020 cycle | PASS | 948 | 102.54% | 688.14% | 546 | -76.66% |
| 2024 cycle (current) | PASS | 948 | -8.07% | 91.92% | 534 | -53.08% |

## 6. Eventi, regolamentazione e geopolitica — feed descrittivi

- Stato: PARTIAL. Headlines and keyword tags are descriptive only; no sentiment, event-impact score or trading signal is inferred.
| Fonte | Stato | Acquisiti | Rilevanti nel report |
|---|---|---:|---:|
| Federal Reserve | PASS | 20 | 11 |
| SEC | PASS | 25 | 15 |
| White House | PASS | 30 | 2 |
| ECB | PASS | 15 | 5 |
| CFTC | NOT_CONFIGURED | n/d | 0 |
| GDELT | FAIL | n/d | 0 |
- 2026-11-25T14:10:24+00:00 — SEC — SEC Investor Advisory Committee to Host Dec. 3 Virtual Meeting [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-118-sec-investor-advisory-committee-host-dec-3-virtual-meeting
- 2026-11-25T12:01:00+00:00 — White House — First Lady Melania Trump Secures Reunification of Nine Additional Children with their Families [geopolitical] — https://www.whitehouse.gov/briefings-statements/2026/11/first-lady-melania-trump-secures-reunification-of-nine-additional-children-with-their-families/
- 2026-11-23T22:33:50+00:00 — White House — President Trump Stands with Victims’ Families as Newsom Grants Mass Clemency to Depraved Killers [geopolitical] — https://www.whitehouse.gov/releases/2026/11/president-trump-stands-with-victims-families-as-newsom-grants-mass-clemency-to-depraved-killers/
- 2026-11-23T14:30:00+00:00 — ECB — Philip R. Lane: Climate change and monetary policy [macro_monetary] — https://www.ecb.europa.eu//press/key/date/2026/html/ecb.sp261123~b5816801a0.en.pdf
- 2026-11-23T10:00:00+00:00 — ECB — ECB expands acceptance of DLT-based assets as eligible Eurosystem collateral [macro_monetary] — https://www.ecb.europa.eu//press/pr/date/2026/html/ecb.pr261123~76b6f57b74.en.html
- 2026-11-20T21:15:00+00:00 — Federal Reserve — Federal Reserve announces College Fed Challenge winners [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/other20261120b.htm
- 2026-11-20T18:03:24+00:00 — SEC — SEC Issues Proposal to Restructure the Consolidated Audit Trail [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-117-sec-issues-proposal-restructure-consolidated-audit-trail
- 2026-11-20T15:00:00+00:00 — Federal Reserve — Federal Reserve Board releases results from survey of senior financial officers at banks about their strategies and practices for managing reserve balances [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/other20261120a.htm
- 2026-11-20T14:28:28+00:00 — SEC — SEC Charges Indianapolis-Based Backward Hat Capital and Its Co-Founders With $560 Million Dollar Offering Fraud and Obtains Emergency Relief [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-116-sec-charges-indianapolis-based-backward-hat-capital-its-co-founders-560-million-dollar-offering
- 2026-11-19T16:00:00+00:00 — Federal Reserve — Federal Reserve Board issues enforcement action with former employee of First Security Bancorp [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/enforcement20261119a.htm
- 2026-11-19T14:39:02+00:00 — SEC — SEC: Eight Entities Used Fake Crypto Asset Trading Platforms to Steal More Than $37 Million From U.S. Investors [regulatory, crypto] — https://www.sec.gov/newsroom/press-releases/2026-115-sec-eight-entities-used-fake-crypto-asset-trading-platforms-steal-more-37-million-us-investors
- 2026-11-17T18:30:00+00:00 — ECB — Philip R. Lane: The practice and science of monetary policy communication: the ECB experience [macro_monetary] — https://www.ecb.europa.eu//press/key/date/2026/html/ecb.sp261117~7f5d3b1a0e.en.pdf

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
- Forecast maturati/scorati in questo run: 3.
- Probabilità calibrate pubblicate: False.
- Eventuali valori nel ledger sono point forecast sperimentali; non sono probabilità calibrate né segnali operativi.

## 8. Validazione quantitativa

Le metriche seguenti sono diagnostiche sul periodo storico già ispezionato; non sono prova prospettica né PnL eseguibile.

| Orizzonte | N | Zero MAE | Drift MAE | Momentum MAE | Ridge MAE |
|---:|---:|---:|---:|---:|---:|
| 1 sessioni | 362 | 0.015824 | 0.015885 | 0.027210 | 0.015889 |
| 3 sessioni | 360 | 0.028515 | 0.028767 | 0.048338 | 0.028746 |
| 7 sessioni | 356 | 0.044049 | 0.044996 | 0.076222 | 0.044703 |
| 30 sessioni | 333 | 0.107855 | 0.109324 | 0.184436 | 0.110472 |

## 9. Ledger e rischio

- Stato ledger: VERIFIED_IN_WORKSPACE_PENDING_WORKFLOW_COMMIT; eventi prima/dopo: 54 / 61.
- Nuove previsioni: 4; duplicate soppresse: 0; score maturati: 3.
- Campione prospettico: INSUFFICIENT_PROSPECTIVE_EVIDENCE.
- Rischio: paper_only; live trading: False; esposizione teorica: 0.00%.
- Champion congelato: zero-return. Ridge è challenger non promosso.
- Nessun PnL economico o probabilità calibrata è dichiarato.

## 10. Revisione critica e conclusione

- Gate pre-report: PASS; cicli completati: 7; fallimenti bloccanti: [].
- Fattore osservato: Variazione close-to-close = -2.3485 % (Binance spot BTCUSDT, 2026-11-24T00:00:00+00:00).
- Fattore osservato: Ampiezza intraday high-low/open = 3.9530 % (Binance spot BTCUSDT, 2026-11-24T00:00:00+00:00).
- Fattore osservato: Volume rispetto alla mediana precedente = 1.0977 multiplo (Binance spot BTCUSDT, 2026-11-24T00:00:00+00:00).
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
