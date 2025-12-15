from __future__ import annotations

import datetime as dt
import csv
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

try:  # Optional for offline mode
    import pandas as pd  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    pd = None

try:  # Optional for offline mode
    import yfinance as yf  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    yf = None

from .config import DataConfig

NASDAQ_LISTINGS_URL = "https://datahub.io/core/nasdaq-listings/r/nasdaq-listed-symbols.csv"


PriceSeries = List[Tuple[dt.datetime, float]]


def _load_sample_universe(config: DataConfig) -> List[str]:
    sample_path = config.sample_data_dir / "universe.csv"
    if not sample_path.exists():
        return []
    with sample_path.open() as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    filtered: List[str] = []
    for row in rows:
        symbol = (row.get("Symbol") or "").upper()
        try:
            market_cap = float(row.get("MarketCap", 0))
        except ValueError:
            continue
        if market_cap >= config.market_cap_threshold:
            filtered.append(symbol)
    if config.max_tickers:
        return filtered[: config.max_tickers]
    return filtered


def fetch_nasdaq_tickers(cache_dir: Path, max_tickers: Optional[int] = None) -> List[str]:
    if pd is None:
        raise ImportError("pandas is required for live universe fetching")
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
    if yf is None:
        raise ImportError("yfinance is required for live market cap filtering")
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


def _sample_earnings(symbol: str, config: DataConfig) -> List[dict]:
    path = config.sample_data_dir / f"earnings_{symbol}.csv"
    if not path.exists():
        return []
    events: List[dict] = []
    with path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                when = dt.datetime.fromisoformat(row["earnings_date"])
            except Exception:
                continue
            events.append({"earnings_date": when, "surprise": float(row.get("surprise", 0) or 0)})
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=365 * config.lookback_years)
    return [e for e in events if e["earnings_date"] >= cutoff]


def earnings_dates(symbol: str, config: DataConfig) -> List[dict]:
    if config.offline_mode:
        return _sample_earnings(symbol, config)
    if yf is None or pd is None:
        raise ImportError("pandas and yfinance are required for live earnings lookups")
    ticker = yf.Ticker(symbol)
    df = ticker.get_earnings_dates(limit=config.lookback_years * 4)
    if df is None:
        return []
    df = df.reset_index().rename(columns={"index": "earnings_date"})
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=365 * config.lookback_years)
    filtered = df[df["earnings_date"] >= pd.Timestamp(cutoff)]
    return [
        {
            "earnings_date": row["earnings_date"].to_pydatetime(),
            "surprise": float(row.get("surprise", 0.0) or 0.0),
        }
        for _, row in filtered.iterrows()
    ]


def _sample_prices(symbol: str, config: DataConfig) -> PriceSeries:
    path = config.sample_data_dir / f"prices_{symbol}.csv"
    if not path.exists():
        return []
    with path.open() as handle:
        reader = csv.DictReader(handle)
        prices: PriceSeries = []
        for row in reader:
            try:
                when = dt.datetime.fromisoformat(row["Date"])
                close = float(row.get("Close", 0.0) or 0.0)
            except Exception:
                continue
            prices.append((when, close))
    return sorted(prices, key=lambda x: x[0])


def price_on_dates(symbol: str, dates: List[dt.datetime], config: DataConfig) -> PriceSeries:
    if config.offline_mode:
        return _sample_prices(symbol, config)
    if yf is None or pd is None:
        raise ImportError("pandas and yfinance are required for live price history")
    if not dates:
        return []
    start = min(dates) - dt.timedelta(days=2)
    end = max(dates) + dt.timedelta(days=2)
    hist = yf.download(symbol, start=start, end=end, progress=False)
    if hist.empty:
        return []
    closes = hist["Close"]
    return [(idx.to_pydatetime(), float(val)) for idx, val in closes.items()]


def end_of_day_close(prices: PriceSeries, date: dt.datetime) -> Optional[tuple]:
    if not prices:
        return None
    pre_candidates = [price for ts, price in prices if ts <= date]
    post_candidates = [price for ts, price in prices if date < ts <= date + dt.timedelta(days=2)]
    pre_close = pre_candidates[-1] if pre_candidates else None
    post_close = post_candidates[0] if post_candidates else None
    return pre_close, post_close


def build_universe(config: DataConfig, cache_dir: Path) -> List[str]:
    if config.offline_mode:
        return _load_sample_universe(config)
    tickers = fetch_nasdaq_tickers(cache_dir, config.max_tickers)
    return filter_by_market_cap(tickers, config.market_cap_threshold)
