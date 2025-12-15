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

If you are in an offline or firewalled environment, use the bundled sample data to exercise the pipeline:
```bash
options-prediction backtest --iterative false --offline true --duration-minutes 1
```
When running directly from the source tree without installing the package, set `PYTHONPATH=src` and invoke the module:
```bash
PYTHONPATH=src python -m options_prediction.cli backtest --offline true --iterative false
```
Add a learning note for future prompts:
```bash
options-prediction add-note "Focus on EPS surprises over 5%"
```

If you want to bypass universe construction and target explicit tickers, pass a comma-separated list:
```bash
options-prediction backtest --iterative false --tickers AAPL,MSFT,GOOGL
```

## Configuration highlights
- Adjust market cap filters, lookback years, and ticker limits via CLI flags.
- Notes and run logs are stored locally under `notes/` by default.
- Swap in a real LLM provider by implementing `LLMClient` in `src/options_prediction/llm.py`.
- The CLI now checks for `pandas` and `yfinance` before running and will exit early with a clear message if they are missing.
- Offline mode uses curated AAPL/MSFT sample earnings and price data under `sample_data/` so the program can run without network access.

## Caveats
- Network access is required for Yahoo Finance calls.
- The default predictor is heuristic; plug in a real model for production use.
