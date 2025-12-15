from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import Optional

from .checks import MissingDependencyError, require_packages
from .config import AppConfig, DataConfig, LLMConfig, RunConfig
from .runner import backtest_once, iterative_cycle, save_custom_notes


def build_config(
    duration_minutes: int = 30,
    iterative: bool = True,
    notes_path: Path = Path("notes/learning_notes.txt"),
    log_path: Path = Path("notes/run_log.csv"),
    market_cap: float = 1_000_000_000,
    lookback_years: int = 2,
    max_tickers: Optional[int] = None,
    offline: bool = False,
    sample_data_dir: Path = Path("sample_data"),
) -> AppConfig:
    run_cfg = RunConfig(duration=dt.timedelta(minutes=duration_minutes), iterative=iterative, notes_path=notes_path, log_path=log_path)
    data_cfg = DataConfig(
        market_cap_threshold=market_cap,
        lookback_years=lookback_years,
        max_tickers=max_tickers,
        offline_mode=offline,
        sample_data_dir=sample_data_dir,
    )
    llm_cfg = LLMConfig()
    config = AppConfig(data=data_cfg, llm=llm_cfg, run=run_cfg)
    config.ensure_paths()
    return config


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LLM-driven earnings prediction toolkit.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backtest = subparsers.add_parser("backtest", help="Run a backtest across NASDAQ tickers.")
    backtest.add_argument("--duration-minutes", type=int, default=30, help="Maximum minutes to run (iterative cycles only).")
    backtest.add_argument("--iterative", type=lambda x: x.lower() == "true", default=True, help="Run iterative cycles until duration or a single pass.")
    backtest.add_argument("--market-cap", type=float, default=1_000_000_000, help="Minimum market cap filter.")
    backtest.add_argument("--lookback-years", type=int, default=2, help="Years of history for earnings events.")
    backtest.add_argument("--max-tickers", type=int, default=None, help="Limit number of tickers for quick runs.")
    backtest.add_argument("--tickers", type=str, default=None, help="Comma-separated tickers to override universe selection.")
    backtest.add_argument("--offline", action="store_true", help="Run in offline mode using bundled sample data.")
    backtest.add_argument("--sample-data-dir", type=Path, default=Path("sample_data"), help="Path to offline sample data.")

    add_note = subparsers.add_parser("add-note", help="Append a learning note for future prompts.")
    add_note.add_argument("note", type=str, help="Note to save.")
    add_note.add_argument("--notes-path", type=Path, default=Path("notes/learning_notes.txt"), help="Path to notes file.")

    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if args.command == "backtest":
        config = build_config(
            duration_minutes=args.duration_minutes,
            iterative=args.iterative,
            max_tickers=args.max_tickers,
            market_cap=args.market_cap,
            lookback_years=args.lookback_years,
            offline=args.offline,
            sample_data_dir=args.sample_data_dir,
        )
        custom_tickers = [t.strip().upper() for t in args.tickers.split(",")] if args.tickers else None
        required = [] if args.offline else ["pandas", "yfinance"]
        try:
            require_packages(required)
        except MissingDependencyError as exc:  # pragma: no cover - CLI safety path
            print(exc)
            return
        if args.iterative:
            iterative_cycle(config, tickers=custom_tickers)
        else:
            backtest_once(config, tickers=custom_tickers)
    elif args.command == "add-note":
        save_custom_notes(args.notes_path, [args.note])
        print(f"Saved note to {args.notes_path}")


if __name__ == "__main__":
    main()
