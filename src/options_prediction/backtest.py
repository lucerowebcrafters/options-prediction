from __future__ import annotations

import csv
import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .config import AppConfig
from .data import earnings_dates, end_of_day_close, price_on_dates
from .predictor import Predictor


@dataclass
class BacktestResult:
    ticker: str
    earnings_date: dt.datetime
    pre_close: float | None
    post_close: float | None
    direction: str
    predicted_direction: str
    confidence: float
    rationale: str

    @property
    def actual_direction(self) -> str:
        if self.pre_close is None or self.post_close is None:
            return "unknown"
        if self.post_close > self.pre_close:
            return "up"
        if self.post_close < self.pre_close:
            return "down"
        return "flat"

    @property
    def correct(self) -> bool:
        if self.actual_direction == "unknown":
            return False
        if self.predicted_direction == "flat":
            return self.actual_direction == "flat"
        return self.predicted_direction == self.actual_direction


class Backtester:
    def __init__(self, config: AppConfig):
        self.config = config
        self.predictor = Predictor(config)

    def backtest_symbol(self, symbol: str) -> List[BacktestResult]:
        results: List[BacktestResult] = []
        events = earnings_dates(symbol, self.config.data)
        if not events:
            return results
        earnings_days = [event["earnings_date"] for event in events]
        prices = price_on_dates(symbol, earnings_days, self.config.data)
        for event in events:
            date = event["earnings_date"]
            eps_surprise = float(event.get("surprise", 0.0) or 0.0)
            closes = end_of_day_close(prices, date)
            if closes is None:
                continue
            pre_close, post_close = closes
            prediction = self.predictor.predict(symbol, eps_surprise)
            results.append(
                BacktestResult(
                    ticker=symbol,
                    earnings_date=date,
                    pre_close=pre_close,
                    post_close=post_close,
                    direction="unknown",  # derived via property
                    predicted_direction=prediction.direction,
                    confidence=prediction.confidence,
                    rationale=prediction.rationale,
                )
            )
        return results

    def summarize(self, results: List[BacktestResult]) -> dict:
        total = len(results)
        correct = sum(1 for r in results if r.correct)
        accuracy = correct / total if total else 0.0
        return {
            "total_predictions": total,
            "correct": correct,
            "accuracy": accuracy,
        }

    def export_results(self, results: List[BacktestResult], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "ticker",
                    "earnings_date",
                    "pre_close",
                    "post_close",
                    "actual_direction",
                    "predicted_direction",
                    "confidence",
                    "rationale",
                ]
            )
            for r in results:
                writer.writerow(
                    [
                        r.ticker,
                        r.earnings_date,
                        r.pre_close,
                        r.post_close,
                        r.actual_direction,
                        r.predicted_direction,
                        r.confidence,
                        r.rationale,
                    ]
                )


@dataclass
class RunLogEntry:
    timestamp: dt.datetime
    ticker: str
    accuracy: float
    notes: str


def append_run_log(path: Path, entries: List[RunLogEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if header:
            writer.writerow(["timestamp", "ticker", "accuracy", "notes"])
        for entry in entries:
            writer.writerow([entry.timestamp.isoformat(), entry.ticker, entry.accuracy, entry.notes])
