# Dukascopy integration — initial connector

This integration reads Dukascopy's public historical `.bi5` hourly tick archive,
decodes bid/ask ticks, and builds 1-minute **mid-price** OHLC candles plus
`bid_close`, `ask_close`, `spread_close` diagnostics.

**Status:** Connector code and synthetic decoding tests are added. A successful
live provider request has NOT been confirmed. Provider endpoints, point divisors,
availability, terms and licensing must be verified with a small real sample.
No real data is included in this repository.

## First controlled download (24 hours)
```bash
pip install -e '.[test]'
python -m pytest -q
python -m strategy_lab.dukascopy --symbol XAUUSD --start 2024-01-08T00:00:00Z --hours 24 --output data/xauusd_20240108_1min.csv
```

The default XAUUSD point divisor is a **hypothesis**, not verified against
live source quotes. If quotes appear off by 10x or 100x, stop and check the
instrument-specific point scale rather than silently adjusting results.

The downloader requests one hour at a time, waits 0.3 seconds between requests,
retries transient errors, and limits each batch to 168 hours. Missing hours
(including closed markets) are counted; a 404 is treated as empty and must be
investigated if it occurs during expected trading hours.

## Next integration work
- Verify a small live sample and timestamps against source quotes.
- Add persistent caching/checksums and a manifest of missing hours.
- Reconstruct true bid/ask OHLC execution (current backtester still uses mid
  OHLC with constant assumed spread).
- Define session-aware aggregation (avoid treating closed-market gaps as missing
  intraday candles).
- After validation, retrieve multi-year history into external storage, not Git.
- Obtain and respect Dukascopy redistribution and access conditions.

This is research infrastructure, not a live trade signal service.
