# CMC Strategy Engine

> **Turn market data into backtestable trading strategies**

A CoinMarketCap-powered trading strategy generator that transforms real-time market data into actionable, backtestable strategy specifications. Built for the **BNB HACK: AI Trading Agent Edition** (Track 2: Strategy Skills).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CMC STRATEGY ENGINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │  CMC Fetcher │───▶│ Strategy Analyzer │───▶│   Generator   │  │
│  │              │    │                  │    │               │  │
│  │ • Price      │    │ • Momentum       │    │ • Trend       │  │
│  │ • Volume     │    │ • Volume Profile │    │ • Mean Rev.   │  │
│  │ • Market Cap │    │ • Trend Strength │    │ • Breakout    │  │
│  │ • 24h Δ      │    │ • Volatility     │    │ • Momentum    │  │
│  │ • 7d Δ       │    │ • Narrative      │    │               │  │
│  └──────────────┘    │ • Composite      │    └───────┬───────┘  │
│                      └──────────────────┘            │          │
│                                                      ▼          │
│                                              ┌───────────────┐  │
│                                              │ Strategy Spec │  │
│                                              │   (JSON)      │  │
│                                              └───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## How It Works

### Step 1: Fetch
Pull real-time market data from CoinMarketCap API — price, volume, market cap, 24h and 7d price changes for top cryptocurrencies.

### Step 2: Analyze
Multi-factor analysis engine computes 5 independent signals:
- **Momentum Score** — RSI-like price velocity (0–100)
- **Volume Profile** — Accumulation vs distribution detection (0–100)
- **Trend Strength** — Moving average alignment scoring (0–100)
- **Volatility Score** — Position sizing guidance (0–100)
- **Narrative Momentum** — Volume spike buzz proxy (0–100)

Each factor produces a score (0–100) and signal (bullish/bearish/neutral). Combined into a weighted composite score.

### Step 3: Generate
Transform analysis into backtestable strategy specifications with entry/exit conditions, position sizing rules, stop loss, and take profit levels. Supports 4 strategy archetypes.

## Installation

```bash
# Clone the repo
git clone https://github.com/your-org/cmc-strategy-engine.git
cd cmc-strategy-engine

# Install dependencies
pip install -r requirements.txt

# Set your CMC API key (optional, uses demo key if not set)
export CMC_API_KEY="your-api-key-here"
```

## Usage

### CLI Usage

```bash
# Generate strategy for top 5 coins (default: Trend Following)
python src/engine.py

# Analyze specific coins
python src/engine.py --coins BTC,ETH,BNB

# Use specific strategy type
python src/engine.py --strategy-type breakout

# Output as raw JSON
python src/engine.py --output-format json

# Combine options
python src/engine.py --coins BTC,ETH,SOL --strategy-type momentum --output-format json
```

### Python API

```python
from src.cmc_fetcher import CMCFetcher
from src.strategy_analyzer import StrategyAnalyzer
from src.strategy_generator import StrategyGenerator

# Fetch market data
fetcher = CMCFetcher()
market_data = fetcher.fetch_top_coins(5)

# Analyze
analyzer = StrategyAnalyzer()
analysis = analyzer.analyze(market_data)

# Generate strategy
generator = StrategyGenerator()
strategy = generator.generate(analysis, strategy_type="trend_following")

print(strategy)
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Data Source | CoinMarketCap API |
| HTTP Client | urllib (stdlib) |
| Testing | pytest |
| Output | JSON (backtestable specs) |

## Strategy Types

| Type | Best For | Signal Logic |
|------|----------|-------------|
| **Trend Following** | Strong directional moves | Enter on MA crossover confirmation |
| **Mean Reversion** | Range-bound markets | Enter at Bollinger Band extremes |
| **Breakout** | Consolidation patterns | Enter on volume-confirmed breakout |
| **Momentum** | Fast-moving markets | Enter on momentum acceleration |

## Hackathon Submission

- **Competition**: BNB HACK: AI Trading Agent Edition
- **Track**: 2 — Strategy Skills ($6K prize pool)
- **Submission**: CMC Strategy Engine
- **Date**: June 2026
- **Team**: [Team Name]

## License

MIT
