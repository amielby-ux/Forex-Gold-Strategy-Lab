# Getting historical Gold data into Strategy Lab

The Dukascopy direct-download live smoke test returned HTTP 503 in GitHub
Actions on 2026-10-09. The decoder unit tests pass; **no successful live
download or historical backtest has been confirmed**.

## Immediate independent route: CSV export
1. Download a **licensed XAU/USD spot** historical OHLC CSV from Dukascopy's
   official historical-data export interface or your broker.
2. Identify the timezone and whether prices are bid, ask or midpoint. The
   current engine assumes midpoint OHLC with separately modeled constant spread.
3. Ensure the CSV contains columns:
   `timestamp,open,high,low,close`.
   Every timestamp must have a timezone designator, e.g.
   `2024-01-08T08:00:00Z`. Convert broker-local timestamps explicitly.
4. Keep the CSV outside the public GitHub repository. Use a local folder
   such as `data/` and add it to `.gitignore`.
5. Audit before use:

```bash
pip install -e '.[test]'
python -m pytest -q
python -m strategy_lab.data_quality data/xauusd.csv --frequency 1min
```

6. Investigate gaps: market closures are expected; irregular missing bars
   during liquid sessions warrant scrutiny. Cross-check prices with the
   original source. Do not treat synthetic sample data as real prices.
7. Run the existing research CLI only after confirming the data and realistic
   trading costs; it is still an **exploratory** engine, not production-grade.

## Data requirements before credible strategy comparison
- Several years of history and exact source/provenance.
- Consistent UTC timestamps, instrument, precision and session calendar.
- Bid/ask-aware execution and realistic varying spreads.
- No look-ahead, validation-only selection, untouched final test period.
- Equity-based risk and drawdown, risk-based position sizing, sensitivity tests.

Avoid storing provider credentials or proprietary datasets in GitHub.
