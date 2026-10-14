# Live-data / forward-testing pathway (no orders)

The project now has a **read-only forward signal recorder**. It can consume
an updated UTC M1 CSV from a licensed live/delayed market-data feed, calculate
signals on fully closed M15/H1/H4 candles, and append idempotent JSONL
observations. It NEVER places orders, accesses brokerage credentials or
claims a paper account's fills.

## Requirements
- A provider supplying legally usable ongoing XAU/USD M1 data.
- Each row: timestamp (ISO UTC with Z or offset), open, high, low, close.
- Timestamp denotes the **start** of its one-minute candle.
- Do not assume the previous Dukascopy archive endpoint is live: the
  GitHub Actions smoke test returned HTTP 503.
- At least 210 **complete** candles at the target timeframe are required.
  For H4 this is over a month of trading data; the single-day sample is
  insufficient for H4 strategy warmup.
- Never include an in-progress candle; the recorder filters it.
- Missing minute slots invalidate their entire higher-timeframe candle.
- Observations are written locally to ignored `data/` and should be kept
  separately from publicly committed source code.

Example after a legitimate data feed has refreshed the CSV:
```bash
python -m strategy_lab.forward_test data/xauusd_live_m1.csv --strategy ema_cross --timeframe 15min
```

Run it again only after new data arrives. This records directional signals
only; a later component must simulate fills at actual bid/ask quotes, costs,
latency, position sizing and risk limits before performance can be evaluated.
No live market feed is connected yet. No orders are placed.
