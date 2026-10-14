# Phase 1: Research baseline

## Universe
XAUUSD, EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD. Intended bar frequencies: 15min, 1h, 4h.

## Ten deterministic candidate strategy families
trend, ema_cross, breakout, rsi_reversion, bollinger, macd,
support_resistance, candlestick_trend, trend_pullback, multi_factor.

## How to run
Install: `pip install -e '.[test]'`
Tests: `pytest -q`
Research: `python -m strategy_lab.cli path/to/ohlc.csv --spread 0.0002`
For gold and JPY pairs use an instrument-appropriate spread in **price units**.

CSV needs `timestamp,open,high,low,close` with explicit UTC timestamps.

## Critical limitations
- This is a **working research scaffold**, NOT validated trading signals.
- User must supply real, properly licensed market data; no data has been downloaded or backtested.
- Mid-price OHLC only; constant spread/slippage; no bid/ask time series yet.
- Positions: -1, 0, +1 base unit; P&L in quote currency per base unit.
- Not a margin-aware portfolio simulator; no swaps, financing, lot sizes, FX conversions, stop-loss, take-profit, partial fills or order-book constraints.
- No Sharpe ratio or percentage-return claims until capital/risk sizing is specified.
- Chronological 60/20/20 split is illustrative. Final test data should remain untouched during actual model selection. The CLI currently reports all three splits for inspection and MUST NOT be used for iterative optimization against the final split.
- Warm-up indicators use past bars only. Entries execute on the next bar open. Positions are force-closed at the last bar close.
- Early baseline rules are intentionally simple and subject to revision; they do not establish profitability.
- Compare strategies using a normalized risk/capital model before selecting winners.
