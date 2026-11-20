# BTC Quant Desk — report giornaliero

- Protocollo: **V5.6**
- Stato: **COMPLETE_NOT_PROMOTED**
- Avvio UTC: 2026-11-20T16:52:49.197023+00:00
- Fine UTC: 2026-11-20T16:57:50.530844+00:00
- Commit: `e74441bf62101af0c205a04cdd30024048799b86`
- Workflow run: 44777689198

> I valori di mercato sono distinti tra osservazioni live, snapshot e candele chiuse. USD e USDT non sono convertiti né uniti.

## 1. Acquisizione e qualità dati

| Feed | Stato | Evidenza / dettaglio |
|---|---|---|
| binance_acquisition_and_qa | PASS | righe=3382, gap=0, duplicati=0, ultima candela=2026-11-19T00:00:00+00:00 |
| bitstamp_acquisition_and_qa | PASS | righe=3650, gap=0, duplicati=0, ultima candela=2026-11-19T00:00:00+00:00 |
| coinbase_recent_cross_check | PASS | righe=300, gap=0, duplicati=0, ultima candela=2026-11-19T00:00:00+00:00 |
| kraken_recent_cross_check | PASS | righe=720, gap=0, duplicati=0, ultima candela=2026-11-19T00:00:00+00:00 |
| supplemental_market_context | PASS | PASS |
| walk_forward | SCORED_NOT_PROMOTED | SCORED_NOT_PROMOTED |

## 2. Prezzi spot — ultime candele giornaliere chiuse

| Venue | Strumento | Candela UTC | Close | 1D | 7D | 30D | Range intraday | Vol 1D BTC | Vol 7D BTC | Vol 30D BTC |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Binance | BTCUSDT (USDT) | 2026-11-19T00:00:00+00:00 | 61,986.73 | -1.715% | -13.257% | -25.343% | 4.206% | 19,879.64 | 180,380.00 | 518,323.05 |
| Bitstamp | BTC/USD (USD) | 2026-11-19T00:00:00+00:00 | 61,914.05 | -1.687% | -13.254% | -25.356% | 4.206% | 1,223.94 | 9,903.10 | 49,573.77 |

### Quotazioni spot — ultimo scambio osservato

| Venue | Stato | Prezzo | Variazione 24h | Volume base 24h | Timestamp ultimo scambio UTC | Età sec |
|---|---|---:|---:|---:|---|---:|
| Bitstamp_BTCUSD_USD | PASS | 59,407.33 | -4.042% | 1,916.08 BTC | 2026-11-20T16:53:30+00:00 | 1.4 |

### Livelli tecnici descrittivi — non segnali

| Venue | SMA20 | SMA50 | SMA200 | Massimo 20D | Minimo 20D | ATR14 |
|---|---:|---:|---:|---:|---:|---:|
| Binance | 72,035.04 | 78,236.29 | 72,693.73 | 81,196.01 | 61,428.26 | 2,642.34 |
| Bitstamp | 71,940.98 | 78,147.09 | 72,636.73 | 81,105.28 | 61,365.00 | 2,633.57 |

## 3. Copertura dei dati supplementari

| Categoria | Stato | Nota / limite |
|---|---|---|
| spot_ohlcv | PASS | Primary Binance/Bitstamp acquisition is reported separately. |
| spot_live_quotes | PARTIAL |  |
| per_exchange_derivatives | PARTIAL |  |
| options | PASS |  |
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
- Snapshot acquisito UTC: 2026-11-20T16:53:45.171677+00:00.
- Ultimo prezzo: 59,478.30 USDT (ticker 2026-11-20T16:53:43.652000+00:00).
- Volume 24h: 214,410.85 BTC (21,441,085.26 contratti).
- Open interest snapshot: 34,746.17 BTC (2,065,784,702 USD; snapshot 2026-11-20T16:53:44.605000+00:00).
- OI storico giornaliero UTC: 1D 4.17%; 7D 3.22%; 30D 11.68% (ultimo punto 2026-11-20T00:00:00+00:00).
- Funding previsto per il prossimo settlement (2026-11-21T00:00:00+00:00): 0.00001767 (frazione per intervallo).
- Ultimo funding effettivamente settled: 0.00003840 al 2026-11-20T16:00:00+00:00 (stato settled).
- Settlement successivo dopo il periodo corrente: 2026-11-21T08:00:00+00:00.
- Storico funding: 100 settlement acquisiti.
- Delta taker futures BTC (buy − sell, barre UTC chiuse): 1D -2,657.63 BTC; 7D -20,634.34 BTC; 30D n/d BTC.
- Copertura delta taker: 29 barre UTC complete su 30 scaricate.
- Nota CVD: OKX BTC-USDT perpetual contract taker volume in BTC; buy minus sell. Completed UTC daily bars only; exchange-specific derivatives delta proxy, not spot CVD or total-market CVD.
- Liquidazioni: NOT_ACQUIRED; nessuna stima ricavata da endpoint non pertinenti.
- Copertura per venue: Binance FAIL; Bybit FAIL; OKX PASS.

### CVD orario Binance — delta taker aggregato

- Stato: PARTIAL. Hourly Binance kline taker-buy base volume minus inferred taker-sell base volume for rolling 24h/7d/30d windows; not tick-level order-book delta.
| Mercato | Finestra | Delta BTC | Delta / volume % | Volume BTC | Buy BTC | Sell BTC |
|---|---:|---:|---:|---:|---:|---:|
| Spot BTCUSDT | 24h | -2,242.78 | -7.85% | 28,568.47 | 13,162.85 | 15,405.63 |
| Spot BTCUSDT | 7d | -4,018.41 | -2.31% | 173,917.58 | 84,949.58 | 88,968.00 |
| Spot BTCUSDT | 30d | 1,454.92 | 0.28% | 526,544.87 | 263,999.89 | 262,544.97 |
| Futures BTCUSDT | 24h | n/d | n/d% | n/d | n/d | n/d |
| Futures BTCUSDT | 7d | n/d | n/d% | n/d | n/d | n/d |
| Futures BTCUSDT | 30d | n/d | n/d% | n/d | n/d | n/d |

### Opzioni Deribit

- Stato: PASS; open interest con ritardo provider di 8 ore.
- OI call/put: 210,285.2000 / 171,490.9000 BTC.
- Put/call OI: 0.8155.
- Put/call volume USD 24h: 3.6322.

| Scadenza | DTE | ATM IV % | OI call BTC | OI put BTC |
|---|---:|---:|---:|---:|
| 2026-11-21 | 1 | 71.72 | 1,288.00 | 1,832.20 |
| 2026-11-22 | 2 | 53.69 | 497.80 | 306.20 |
| 2026-11-23 | 3 | 54.36 | 439.90 | 665.50 |
| 2026-11-24 | 4 | 53.54 | 1.30 | 38.00 |
| 2026-11-27 | 7 | 53.31 | 52,986.70 | 51,549.90 |
| 2026-12-04 | 14 | 49.30 | 5,518.10 | 10,624.90 |
| 2026-12-11 | 21 | 48.73 | 503.00 | 1,452.20 |
| 2026-12-25 | 35 | 46.38 | 90,544.10 | 62,650.00 |
| 2027-01-29 | 70 | 45.11 | 9,062.10 | 8,271.90 |
| 2027-03-26 | 126 | 44.55 | 29,848.90 | 19,340.30 |
| 2027-06-25 | 217 | 43.78 | 12,021.10 | 10,143.10 |
| 2027-09-24 | 308 | 43.54 | 7,574.20 | 4,616.70 |

| Scadenza | 25Δ put IV % | 25Δ call IV % | Put-call skew vol points |
|---|---:|---:|---:|
| 2026-11-21 | n/d | n/d | n/d |
| 2026-11-22 | n/d | n/d | n/d |
| 2026-11-23 | n/d | n/d | n/d |
| 2026-11-24 | 65.24 | 48.44 | 16.80 |
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
| DGS2 — US Treasury 2Y yield | 2026-11-19 | 2026-11-19 | 4.7600 | percent | PASS | 2026-11-20T16:54:49.683006+00:00 | official Treasury daily par yield curve; independent of FRED transport |
| DGS10 — US Treasury 10Y yield | 2026-11-19 | 2026-11-19 | 5.0400 | percent | PASS | 2026-11-20T16:54:49.778976+00:00 | official Treasury daily par yield curve; independent of FRED transport |
| VIXCLS — CBOE VIX | 2026-11-19 | 2026-11-19 | 28.4400 | index points | PASS | 2026-11-20T16:57:50.328955+00:00 | Cboe official historical daily VIX close; independent of FRED transport |

Feed macro non acquisiti: {'DFII10': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=DFII10&cosd=2025-11-20&coed=2026-11-20 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'FEDFUNDS': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=FEDFUNDS&cosd=2021-11-21&coed=2026-11-20 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'CPIAUCSL': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=CPIAUCSL&cosd=2021-11-21&coed=2026-11-20 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'PCEPILFE': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=PCEPILFE&cosd=2021-11-21&coed=2026-11-20 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'UNRATE': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=UNRATE&cosd=2021-11-21&coed=2026-11-20 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'PAYEMS': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=PAYEMS&cosd=2021-11-21&coed=2026-11-20 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'DTWEXBGS': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=DTWEXBGS&cosd=2025-11-20&coed=2026-11-20 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'WALCL': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=WALCL&cosd=2025-11-20&coed=2026-11-20 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'RRPONTSYD': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=RRPONTSYD&cosd=2025-11-20&coed=2026-11-20 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'NFCI': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=NFCI&cosd=2025-11-20&coed=2026-11-20 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'SP500': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=SP500&cosd=2025-11-20&coed=2026-11-20 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'NASDAQCOM': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=NASDAQCOM&cosd=2025-11-20&coed=2026-11-20 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))', 'M2SL': 'ConnectionError: HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Max retries exceeded with url: /graph/fredgraph.csv?id=M2SL&cosd=2021-11-21&coed=2026-11-20 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'fred.stlouisfed.org\', port=443): Read timed out. (read timeout=30)"))'}

## 5. Ciclo Bitcoin — confronto post-halving

- Stato: PASS; fonte: Bitstamp BTC/USD daily OHLCV; same venue and quote currency.
- Orizzonte corrente: 943 sessioni dal 20 aprile 2024.
- Limite: Descriptive comparison at the same elapsed days after halving; sample is small, cycles are structurally different, and this is not a timing forecast.
| Ciclo | Stato | Giorni/sessioni | Rendimento stesso orizzonte | Massimo rendimento | Giorni al picco | Drawdown massimo da picco |
|---|---|---:|---:|---:|---:|---:|
| 2012 cycle | INSUFFICIENT_HISTORY | n/d | n/d% | n/d% | n/d | n/d% |
| 2016 cycle | INSUFFICIENT_HISTORY | n/d | n/d% | n/d% | n/d | n/d% |
| 2020 cycle | PASS | 943 | 99.81% | 688.14% | 546 | -76.66% |
| 2024 cycle (current) | PASS | 943 | -4.73% | 91.92% | 534 | -53.08% |

## 6. Eventi, regolamentazione e geopolitica — feed descrittivi

- Stato: PARTIAL. Headlines and keyword tags are descriptive only; no sentiment, event-impact score or trading signal is inferred.
| Fonte | Stato | Acquisiti | Rilevanti nel report |
|---|---|---:|---:|
| Federal Reserve | PASS | 20 | 12 |
| SEC | PASS | 25 | 15 |
| White House | PASS | 30 | 2 |
| ECB | PASS | 15 | 5 |
| CFTC | NOT_CONFIGURED | n/d | 0 |
| GDELT | FAIL | n/d | 0 |
- 2026-11-20T15:00:00+00:00 — Federal Reserve — Federal Reserve Board releases results from survey of senior financial officers at banks about their strategies and practices for managing reserve balances [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/other20261120a.htm
- 2026-11-20T14:28:28+00:00 — SEC — SEC Charges Indianapolis-Based Backward Hat Capital and Its Co-Founders With $560 Million Dollar Offering Fraud and Obtains Emergency Relief [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-116-sec-charges-indianapolis-based-backward-hat-capital-its-co-founders-560-million-dollar-offering
- 2026-11-19T19:20:20+00:00 — White House — ICYMI: President Trump Talks China, Iran, Super Intelligence, and the Path Ahead in Exclusive Interview from Shenzhen [geopolitical] — https://www.whitehouse.gov/releases/2026/11/icymi-president-trump-talks-china-iran-super-intelligence-and-the-path-ahead-in-exclusive-interview-from-shenzhen/
- 2026-11-19T16:00:00+00:00 — Federal Reserve — Federal Reserve Board issues enforcement action with former employee of First Security Bancorp [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/enforcement20261119a.htm
- 2026-11-19T14:39:02+00:00 — SEC — SEC: Eight Entities Used Fake Crypto Asset Trading Platforms to Steal More Than $37 Million From U.S. Investors [regulatory, crypto] — https://www.sec.gov/newsroom/press-releases/2026-115-sec-eight-entities-used-fake-crypto-asset-trading-platforms-steal-more-37-million-us-investors
- 2026-11-19T13:53:04+00:00 — White House — U.S.-Russia-China Heads of State Declaration toward Peace [geopolitical] — https://www.whitehouse.gov/briefings-statements/2026/11/u-s-russia-china-heads-of-state-declaration-toward-peace/
- 2026-11-17T18:30:00+00:00 — ECB — Philip R. Lane: The practice and science of monetary policy communication: the ECB experience [macro_monetary] — https://www.ecb.europa.eu//press/key/date/2026/html/ecb.sp261117~7f5d3b1a0e.en.pdf
- 2026-11-13T16:57:00+00:00 — SEC — SEC Proposes Executive and Director Compensation Disclosure Reforms [regulatory] — https://www.sec.gov/newsroom/press-releases/2026-114-sec-proposes-executive-director-compensation-disclosure-reforms
- 2026-11-12T18:30:00+00:00 — Federal Reserve — Federal Reserve Board announces pricing, effective January 1, 2027, for payment services the Federal Reserve Banks provide to banks and credit unions, and changes to streamline and adjust their check services [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/other20261112a.htm
- 2026-11-12T17:45:00+00:00 — Federal Reserve — Federal Reserve announces revised tentative schedule of Federal Open Market Committee meetings in 2027 [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/monetary20261112a.htm
- 2026-11-12T16:00:00+00:00 — Federal Reserve — Federal Reserve Board issues enforcement action with former employee of United Community Bank [macro_monetary] — https://www.federalreserve.gov/newsevents/pressreleases/enforcement20261112a.htm
- 2026-11-10T16:45:00+00:00 — ECB — Philip R. Lane: The science and practice of monetary policy communication: the ECB experience [macro_monetary] — https://www.ecb.europa.eu//press/key/date/2026/html/ecb.sp261110_1~9725b7aa07.en.html

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
- Supplemental feed options: PASS.
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
- Forecast maturati/scorati in questo run: 1.
- Probabilità calibrate pubblicate: False.
- Eventuali valori nel ledger sono point forecast sperimentali; non sono probabilità calibrate né segnali operativi.

## 8. Validazione quantitativa

Le metriche seguenti sono diagnostiche sul periodo storico già ispezionato; non sono prova prospettica né PnL eseguibile.

| Orizzonte | N | Zero MAE | Drift MAE | Momentum MAE | Ridge MAE |
|---:|---:|---:|---:|---:|---:|
| 1 sessioni | 362 | 0.015783 | 0.015842 | 0.027312 | 0.015842 |
| 3 sessioni | 360 | 0.028356 | 0.028557 | 0.048950 | 0.028621 |
| 7 sessioni | 356 | 0.043394 | 0.044229 | 0.077180 | 0.044137 |
| 30 sessioni | 333 | 0.103631 | 0.104794 | 0.184777 | 0.105961 |

## 9. Ledger e rischio

- Stato ledger: VERIFIED_IN_WORKSPACE_PENDING_WORKFLOW_COMMIT; eventi prima/dopo: 25 / 30.
- Nuove previsioni: 4; duplicate soppresse: 0; score maturati: 1.
- Campione prospettico: INSUFFICIENT_PROSPECTIVE_EVIDENCE.
- Rischio: paper_only; live trading: False; esposizione teorica: 0.00%.
- Champion congelato: zero-return. Ridge è challenger non promosso.
- Nessun PnL economico o probabilità calibrata è dichiarato.

## 10. Revisione critica e conclusione

- Gate pre-report: PASS; cicli completati: 7; fallimenti bloccanti: [].
- Fattore osservato: Variazione close-to-close = -1.7148 % (Binance spot BTCUSDT, 2026-11-19T00:00:00+00:00).
- Fattore osservato: Ampiezza intraday high-low/open = 4.2058 % (Binance spot BTCUSDT, 2026-11-19T00:00:00+00:00).
- Fattore osservato: Volume rispetto alla mediana precedente = 1.2490 multiplo (Binance spot BTCUSDT, 2026-11-19T00:00:00+00:00).
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
