from __future__ import annotations

import dataclasses
import datetime as dt
from pathlib import Path
from typing import Optional


@dataclasses.dataclass
class DataConfig:
    """Configuration for data retrieval."""

    market_cap_threshold: float = 1_000_000_000.0
    lookback_years: int = 2
    exchange: str = "NASDAQ"
    max_tickers: Optional[int] = None


@dataclasses.dataclass
class LLMConfig:
    """Configuration for the LLM backend."""

    provider: str = "local"
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_tokens: int = 256
    request_budget: int = 1000


@dataclasses.dataclass
class RunConfig:
    """Configuration for iterative runs and backtests."""

    duration: dt.timedelta = dt.timedelta(minutes=30)
    iterative: bool = True
    notes_path: Path = Path("notes/learning_notes.txt")
    log_path: Path = Path("notes/run_log.csv")
    cache_dir: Path = Path(".cache")


@dataclasses.dataclass
class AppConfig:
    data: DataConfig = DataConfig()
    llm: LLMConfig = LLMConfig()
    run: RunConfig = RunConfig()

    def ensure_paths(self) -> None:
        self.run.notes_path.parent.mkdir(parents=True, exist_ok=True)
        self.run.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.run.cache_dir.mkdir(parents=True, exist_ok=True)


DEFAULT_CONFIG = AppConfig()
DEFAULT_CONFIG.ensure_paths()
