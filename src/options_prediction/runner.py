from __future__ import annotations

import datetime as dt
import time
from pathlib import Path
from typing import Iterable, List

from .backtest import Backtester, RunLogEntry, append_run_log
from .config import AppConfig, DEFAULT_CONFIG
from .data import build_universe
from .notes import append_notes


def run_once(config: AppConfig, tickers: Iterable[str]) -> List[RunLogEntry]:
    backtester = Backtester(config)
    log_entries: List[RunLogEntry] = []
    for symbol in tickers:
        results = backtester.backtest_symbol(symbol)
        summary = backtester.summarize(results)
        notes = f"Predictions={summary['total_predictions']} accuracy={summary['accuracy']:.2%}"
        log_entries.append(
            RunLogEntry(timestamp=dt.datetime.utcnow(), ticker=symbol, accuracy=summary["accuracy"], notes=notes)
        )
    append_run_log(config.run.log_path, log_entries)
    append_notes(
        config.run.notes_path,
        [f"Completed run for {len(log_entries)} tickers; average accuracy: {average_accuracy(log_entries):.2%}"],
    )
    return log_entries


def average_accuracy(entries: List[RunLogEntry]) -> float:
    if not entries:
        return 0.0
    return sum(e.accuracy for e in entries) / len(entries)


def iterative_cycle(config: AppConfig = DEFAULT_CONFIG, tickers: Iterable[str] | None = None) -> None:
    config.ensure_paths()
    start = time.monotonic()
    universe = list(tickers) if tickers is not None else build_universe(config.data, config.run.cache_dir)
    if config.data.max_tickers and tickers is None:
        universe = universe[: config.data.max_tickers]
    if not universe:
        append_notes(
            config.run.notes_path,
            ["No tickers available for backtest; verify network access and market cap filters."],
        )
        return
    while time.monotonic() - start < config.run.duration.total_seconds():
        run_once(config, universe)
        if not config.run.iterative:
            break


def backtest_once(config: AppConfig = DEFAULT_CONFIG, tickers: Iterable[str] | None = None) -> List[RunLogEntry]:
    config.ensure_paths()
    if tickers is None:
        tickers = build_universe(config.data, config.run.cache_dir)
    if not tickers:
        append_notes(
            config.run.notes_path,
            ["No tickers available for single-pass backtest; verify data filters or provide --tickers."],
        )
        return []
    return run_once(config, tickers)


def save_custom_notes(path: Path, lines: Iterable[str]) -> None:
    append_notes(path, lines)
