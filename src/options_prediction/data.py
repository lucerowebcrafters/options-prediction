from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd
import yfinance as yf

from .config import DataConfig

NASDAQ_LISTINGS_URL = "https://datahub.io/core/nasdaq-listings/r/nasdaq-listed-symbols.csv"


def fetch_nasdaq_tickers(cache_dir: Path, max_tickers: Optional[int] = None) -> List[str]:
    cache_path = cache_dir / "nasdaq_listings.csv"
    if cache_path.exists():
        listings = pd.read_csv(cache_path)
    else:
        listings = pd.read_csv(NASDAQ_LISTINGS_URL)
        cache_dir.mkdir(parents=True, exist_ok=True)
        listings.to_csv(cache_path, index=False)
    tickers = listings["Symbol"].dropna().astype(str).str.upper().tolist()
    if max_tickers:
        return tickers[:max_tickers]
    return tickers


def filter_by_market_cap(tickers: Iterable[str], threshold: float) -> List[str]:
    passed: List[str] = []
    for symbol in tickers:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        market_cap = getattr(info, "market_cap", None)
        if market_cap is None:
            continue
        if market_cap >= threshold:
            passed.append(symbol)
    return passed


def earnings_dates(symbol: str, lookback_years: int) -> pd.DataFrame:
    ticker = yf.Ticker(symbol)
    df = ticker.get_earnings_dates(limit=lookback_years * 4)
    if df is None:
        return pd.DataFrame()
    df = df.reset_index().rename(columns={"index": "earnings_date"})
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=365 * lookback_years)
    return df[df["earnings_date"] >= pd.Timestamp(cutoff)]


def price_on_dates(symbol: str, dates: List[pd.Timestamp]) -> pd.Series:
    if not dates:
        return pd.Series(dtype=float)
    start = min(dates) - pd.Timedelta(days=2)
    end = max(dates) + pd.Timedelta(days=2)
    hist = yf.download(symbol, start=start, end=end, progress=False)
    if hist.empty:
        return pd.Series(dtype=float)
    closes = hist["Close"]
    return closes


def end_of_day_close(prices: pd.Series, date: pd.Timestamp) -> Optional[tuple]:
    if prices.empty:
        return None
    ts = prices.index
    prev = ts[ts <= date]
    next_day = ts[(ts > date) & (ts <= date + pd.Timedelta(days=2))]
    pre_close = prices.loc[prev.max()] if not prev.empty else None
    post_close = prices.loc[next_day.min()] if not next_day.empty else None
    return pre_close, post_close


def build_universe(config: DataConfig, cache_dir: Path) -> List[str]:
    tickers = fetch_nasdaq_tickers(cache_dir, config.max_tickers)
    return filter_by_market_cap(tickers, config.market_cap_threshold)
