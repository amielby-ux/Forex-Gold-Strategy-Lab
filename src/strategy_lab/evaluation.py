"""Reproducible research evaluation with a held-out test period.

Do not select a strategy using test results. Select on validation only.
This module deliberately does NOT claim risk-adjusted percentage returns.
"""
from dataclasses import dataclass
import pandas as pd
from .core import STRATEGIES, CostModel, backtest, chronological_split, signals, validate_bars

@dataclass(frozen=True)
class Evaluation:
    strategy: str
    train: dict
    validation: dict
    test: dict

def evaluate_candidates(df: pd.DataFrame, costs: CostModel, strategies=STRATEGIES):
    """Train/validation/test for inspection; test is NOT for tuning."""
    df = validate_bars(df)
    train, validation, test = chronological_split(df)
    results = []
    for name in strategies:
        position = signals(df, name)
        splits = []
        for segment in (train, validation, test):
            # Segment boundaries force a flat book; first bar has no trade.
            splits.append(backtest(segment, position.loc[segment.index], costs))
        results.append(Evaluation(name, *splits))
    return results

def validation_ranking(results: list[Evaluation], minimum_trades: int = 20) -> list[Evaluation]:
    """Rank by validation net P&L among candidates with enough trades.

    P&L is per unit of quote currency, so only compare within ONE instrument.
    Ranking is exploratory, not a statistically validated strategy selector.
    """
    eligible = [r for r in results if r.validation["count"] >= minimum_trades]
    return sorted(eligible, key=lambda r: r.validation["net_pnl_quote_per_unit"], reverse=True)
