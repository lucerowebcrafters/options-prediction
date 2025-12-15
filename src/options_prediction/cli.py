from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Optional

import typer

from .checks import MissingDependencyError, require_packages
from .config import AppConfig, DataConfig, LLMConfig, RunConfig
from .runner import backtest_once, iterative_cycle, save_custom_notes

app = typer.Typer(help="LLM-driven earnings prediction toolkit.")


def build_config(
    duration_minutes: int = 30,
    iterative: bool = True,
    notes_path: Path = Path("notes/learning_notes.txt"),
    log_path: Path = Path("notes/run_log.csv"),
    market_cap: float = 1_000_000_000,
    lookback_years: int = 2,
    max_tickers: Optional[int] = None,
) -> AppConfig:
    run_cfg = RunConfig(duration=dt.timedelta(minutes=duration_minutes), iterative=iterative, notes_path=notes_path, log_path=log_path)
    data_cfg = DataConfig(market_cap_threshold=market_cap, lookback_years=lookback_years, max_tickers=max_tickers)
    llm_cfg = LLMConfig()
    config = AppConfig(data=data_cfg, llm=llm_cfg, run=run_cfg)
    config.ensure_paths()
    return config


@app.command()
def backtest(
    duration_minutes: int = typer.Option(30, help="Maximum minutes to run (iterative cycles only)."),
    iterative: bool = typer.Option(True, help="Run iterative cycles until duration or a single pass."),
    market_cap: float = typer.Option(1_000_000_000, help="Minimum market cap filter."),
    lookback_years: int = typer.Option(2, help="Years of history for earnings events."),
    max_tickers: Optional[int] = typer.Option(None, help="Limit number of tickers for quick runs."),
    tickers: Optional[str] = typer.Option(None, help="Comma-separated tickers to override universe selection."),
) -> None:
    """Run a backtest across NASDAQ tickers."""
    config = build_config(duration_minutes, iterative, max_tickers=max_tickers, market_cap=market_cap, lookback_years=lookback_years)
    custom_tickers = [t.strip().upper() for t in tickers.split(",")] if tickers else None
    try:
        require_packages(["pandas", "yfinance"])
    except MissingDependencyError as exc:  # pragma: no cover - CLI safety path
        typer.echo(str(exc))
        raise typer.Exit(code=1)

    if iterative:
        iterative_cycle(config, tickers=custom_tickers)
    else:
        backtest_once(config, tickers=custom_tickers)


@app.command()
def add_note(note: str, notes_path: Path = typer.Option(Path("notes/learning_notes.txt"), help="Path to notes file.")) -> None:
    """Append a learning note that will be used in future prompts."""
    save_custom_notes(notes_path, [note])
    typer.echo(f"Saved note to {notes_path}")


if __name__ == "__main__":
    app()
