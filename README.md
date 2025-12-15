# options-prediction

A scaffolding project for experimenting with LLM-guided earnings prediction and post-earnings price movement backtesting using free data sources like `yfinance`.

## Features
- Build a NASDAQ ticker universe filtered by market cap (default > $1B).
- Fetch earnings dates and prices from Yahoo Finance.
- Heuristic LLM placeholder that uses EPS surprise and prior notes to predict direction.
- Backtesting loop that compares pre/post earnings-day closes.
- Iterative cycle that records notes and run logs for reuse in the next session.

## Installation
```bash
pip install -e .
```

## CLI usage
Run an iterative backtest (default 30 minutes, can be shorter for demos):
```bash
options-prediction backtest --duration-minutes 5 --max-tickers 5
```
Run a single pass without iteration:
```bash
options-prediction backtest --iterative false --max-tickers 5
```
Add a learning note for future prompts:
```bash
options-prediction add-note "Focus on EPS surprises over 5%"
```

## Configuration highlights
- Adjust market cap filters, lookback years, and ticker limits via CLI flags.
- Notes and run logs are stored locally under `notes/` by default.
- Swap in a real LLM provider by implementing `LLMClient` in `src/options_prediction/llm.py`.

## Caveats
- Network access is required for Yahoo Finance calls.
- The default predictor is heuristic; plug in a real model for production use.
