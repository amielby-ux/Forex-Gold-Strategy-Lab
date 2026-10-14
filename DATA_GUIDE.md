# Gold historical data acquisition

## What is verified
- Automated Python CI tests have passed on the development branch.
- No real XAU/USD price history has been imported or backtested yet.
- The project does not bundle price files or credentials.

## Data to obtain
For the first Gold experiment, obtain licensed **XAU/USD spot** historical prices,
ideally bid and ask OHLC or ticks with explicit UTC timestamps, and broker-specific
trading session information. Prefer several years including multiple market regimes.

Potential data vendors to evaluate include Dukascopy historical market data and
your intended broker's export. Verify symbol naming, available periods, licensing,
spread conventions, timestamp alignment, missing bars, weekends and daylight saving.

Do not substitute GC futures for XAU/USD spot without explicitly changing the
experiment: contract structure, roll, and pricing differ.

## Current importer contract
CSV columns: `timestamp,open,high,low,close`
Timestamp examples: `2024-01-02T08:00:00Z` or `2024-01-02T10:00:00+02:00`.
Prices are assumed **mid** OHLC. You MUST specify an instrument-appropriate full
spread in price units. Spread and slippage are constant in this baseline.

Example after obtaining a suitable file:

```bash
pip install -e '.[test]'
pytest -q
python -m strategy_lab.cli data/xauusd_1h.csv --spread 0.30 --slippage 0.05
```

Numbers in the example are **illustrative, not recommended or observed costs**.

## Quality gates before reporting performance
1. Confirm whether the source is XAU/USD spot or a different instrument.
2. Check licensing and timestamp timezone.
3. Check for missing/duplicate bars, outliers and OHLC consistency.
4. Verify data granularity and bid/ask conventions.
5. Cross-check sample candles with source.
6. Obtain variable bid/ask spreads if possible; current engine does not support
   that yet and must be upgraded before production-grade conclusions.
7. Keep a frozen, genuinely untouched final test set.

Never upload proprietary market data to a public GitHub repository unless its
license explicitly permits redistribution.
