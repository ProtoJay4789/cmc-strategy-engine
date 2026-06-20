<p align="center">
  <img src="https://blockrun.ai/api/media/media/images/2026/06/20/1052956f-9a07-4cb2-8293-f93041f8c738.png" alt="CMC Strategy Engine" width="600">
</p>

<h3 align="center">Turn market data into backtestable trading strategies</h3>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/tests-21%2F21-brightgreen" alt="Tests">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/BNB%20HACK-track%202-f7931a" alt="BNB HACK">
</p>

---

A CoinMarketCap-powered trading strategy generator that transforms real-time market data into actionable, backtestable strategy specifications. Built for the **BNB HACK: AI Trading Agent Edition** (Track 2: Strategy Skills).

## The Problem

Market data is everywhere — but turning it into a trading strategy is hard:

- **📊 Noisy Data** — Thousands of metrics with no signal extraction
- **⏱ Manual Analysis** — Hours computing indicators; by the time you act, the move is gone
- **🎯 No Backtesting** — Strategies exist as ideas with no structured specs to validate

## The Solution

Three steps from raw data to backtestable strategy:

```
Fetch → Analyze → Generate
```

### Step 1: Fetch
Pull real-time data from CoinMarketCap — price, volume, market cap, 24h and 7d price changes for top cryptocurrencies.

### Step 2: Analyze
Multi-factor analysis engine computes 5 independent signals:

| Signal | What It Measures | Range |
|--------|-----------------|-------|
| **Momentum** | RSI-like price velocity | 0–100 |
| **Volume Profile** | Accumulation vs distribution | 0–100 |
| **Trend Strength** | Moving average alignment | 0–100 |
| **Volatility** | Position sizing guidance | 0–100 |
| **Narrative** | Volume spike buzz proxy | 0–100 |

Each factor produces a score and signal (bullish/bearish/neutral), combined into a weighted composite.

### Step 3: Generate
Transform analysis into backtestable strategy specs with entry/exit conditions, position sizing, stop loss, and take profit.

## Quick Start

```bash
# Clone
git clone https://github.com/ProtoJay4789/cmc-strategy-engine.git
cd cmc-strategy-engine

# Install
pip install -r requirements.txt

# Run (uses demo CMC key if none set)
export CMC_API_KEY="your-key"  # optional
python src/engine.py --coins BTC,ETH,BNB
```

## Usage

```bash
# Default: top 5 coins, trend following
python src/engine.py

# Specific coins + strategy type
python src/engine.py --coins BTC,ETH,SOL --strategy-type momentum

# JSON output for agent integration
python src/engine.py --output-format json
```

### Python API

```python
from src.cmc_fetcher import CMCFetcher
from src.strategy_analyzer import StrategyAnalyzer
from src.strategy_generator import StrategyGenerator

# Fetch → Analyze → Generate
fetcher = CMCFetcher()
analyzer = StrategyAnalyzer()
generator = StrategyGenerator()

data = fetcher.fetch_top_coins(5)
analysis = analyzer.analyze(data)
strategy = generator.generate(analysis, strategy_type="trend_following")

print(strategy)
```

## Strategy Types

| Type | Best For | Signal Logic |
|------|----------|-------------|
| **Trend Following** | Strong directional moves | Enter on MA crossover confirmation |
| **Mean Reversion** | Range-bound markets | Enter at Bollinger Band extremes |
| **Breakout** | Consolidation patterns | Enter on volume-confirmed breakout |
| **Momentum** | Fast-moving markets | Enter on momentum acceleration |

## Sample Output

```json
{
  "coin": "BTC",
  "composite_score": 74,
  "signal": "bullish",
  "strategy": {
    "type": "trend_following",
    "entry": "RSI < 30 + MACD cross",
    "exit": "RSI > 70 or -5% SL",
    "position_size": "2% risk per trade",
    "timeframe": "4h"
  },
  "risk": {
    "stop_loss": "-4.2%",
    "take_profit": "+12.6%",
    "risk_reward": "3:1"
  }
}
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 CMC STRATEGY ENGINE                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌──────────┐   │
│  │   CMC    │───▶│   Strategy   │───▶│Generator │   │
│  │  Fetcher │    │   Analyzer   │    │          │   │
│  │          │    │              │    │ • Trend  │   │
│  │ • Price  │    │ • Momentum   │    │ • Mean R │   │
│  │ • Volume │    │ • Volume     │    │ • Break  │   │
│  │ • MCap   │    │ • Trend      │    │ • Mom.   │   │
│  │ • 24h Δ  │    │ • Volatility │    └────┬─────┘   │
│  │ • 7d Δ   │    │ • Narrative  │         │         │
│  └──────────┘    └──────────────┘         ▼         │
│                                    ┌────────────┐   │
│                                    │ Strategy   │   │
│                                    │   Spec     │   │
│                                    │  (JSON)    │   │
│                                    └────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Data Source | CoinMarketCap API |
| HTTP Client | urllib (stdlib) |
| Testing | pytest (21/21 passing) |
| Output | JSON (backtestable specs) |

## Project Structure

```
cmc-strategy-engine/
├── src/
│   ├── engine.py              # Main CLI entry point
│   ├── cmc_fetcher.py         # CoinMarketCap data fetcher
│   ├── strategy_analyzer.py   # Multi-factor analysis engine
│   └── strategy_generator.py  # Strategy spec generator
├── tests/
│   ├── test_fetcher.py
│   ├── test_analyzer.py
│   └── test_generator.py
├── requirements.txt
└── README.md
```

## BNB HACK Submission

- **Competition:** BNB HACK: AI Trading Agent Edition
- **Track:** 2 — Strategy Skills ($6K prize pool)
- **Date:** June 2026

## License

MIT — use it, fork it, build on it.

---

<p align="center">
  Built by <a href="https://github.com/ProtoJay4789">GenTech Labs</a>
</p>
