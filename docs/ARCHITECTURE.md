# Architecture

## Overview

CMC Strategy Engine is a 3-layer system that transforms raw market data into backtestable trading strategy specifications. Each layer is independent and testable.

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA LAYER (Fetcher)                        │
│                                                                 │
│  CoinMarketCap API ──→ Structured Market Data                   │
│  • Price, Volume, Market Cap                                     │
│  • 24h/7d Price Changes                                         │
│  • Rate Limiting & Error Handling                                │
│  • Mock Data Fallback for Testing                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ANALYSIS LAYER (Analyzer)                     │
│                                                                 │
│  Market Data ──→ 5 Independent Scores ──→ Composite Score       │
│                                                                 │
│  Factors:                                                       │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │  Momentum    │  Vol Profile │  Trend Str.  │ Volatility   │  │
│  │  (0-100)     │  (0-100)     │  (0-100)     │ (0-100)      │  │
│  │  bullish/    │  bullish/    │  bullish/    │ bullish/     │  │
│  │  bearish/    │  bearish/    │  bearish/    │ bearish/     │  │
│  │  neutral     │  neutral     │  neutral     │ neutral      │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
│  ┌──────────────┐                                               │
│  │  Narrative   │  Weighted Composite = Σ(factor × weight)     │
│  │  (0-100)     │                                               │
│  └──────────────┘                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                 GENERATION LAYER (Generator)                    │
│                                                                 │
│  Analysis Result ──→ Strategy Spec (JSON)                       │
│                                                                 │
│  Strategy Types:                                                │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │  Trend       │  Mean        │  Breakout    │  Momentum    │  │
│  │  Following   │  Reversion   │              │              │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
│                                                                 │
│  Each spec includes:                                            │
│  • Entry conditions (specific, testable)                        │
│  • Exit conditions (specific, testable)                         │
│  • Position sizing rules                                        │
│  • Stop loss / take profit levels                               │
│  • Confidence score & time horizon                              │
└─────────────────────────────────────────────────────────────────┘
```

## Layer 1: Data Layer (CMCFetcher)

**File:** `src/cmc_fetcher.py`

Responsible for fetching and normalizing market data from CoinMarketCap.

### Design Decisions

- **urllib over requests**: Zero external dependencies for the core fetcher. Uses only Python stdlib.
- **Graceful degradation**: Falls back to realistic mock data when API is unavailable (rate limited, no key, network error).
- **Rate limiting**: Enforces minimum 1-second intervals between requests with exponential backoff on 429 errors.
- **Structured output**: All data normalized to a common schema regardless of API response shape.

### Data Schema

```json
{
  "symbol": "BTC",
  "name": "Bitcoin",
  "price": 104500.0,
  "volume_24h": 28500000000,
  "market_cap": 2060000000000,
  "change_24h": 2.15,
  "change_7d": 5.3,
  "rank": 1
}
```

## Layer 2: Analysis Layer (StrategyAnalyzer)

**File:** `src/strategy_analyzer.py`

Multi-factor scoring engine that produces independent signals.

### Factor Design

Each factor is designed to capture a different market dimension:

| Factor | What It Measures | Primary Use |
|--------|-----------------|-------------|
| Momentum | Price velocity across timeframes | Directional bias |
| Volume Profile | Volume relative to market cap | Accumulation/distribution |
| Trend Strength | Alignment of multi-timeframe moves | Trend confirmation |
| Volatility | Magnitude of price swings | Position sizing |
| Narrative | Volume spikes as buzz proxy | Sentiment/attention |

### Scoring

- All factors output 0–100 score with bullish/bearish/neutral signal
- Composite score = weighted sum (configurable weights)
- Confidence = agreement between factor signals
- Thresholds: >60 = bullish, <40 = bearish, 40–60 = neutral

### Weight Configuration

Default weights (tunable):
- Momentum: 25%
- Trend Strength: 25%
- Volume Profile: 20%
- Volatility: 15%
- Narrative: 15%

## Layer 3: Generation Layer (StrategyGenerator)

**File:** `src/strategy_generator.py`

Transforms analysis scores into actionable, backtestable strategy specs.

### Strategy Archetypes

| Type | Entry Logic | Exit Logic | Best Market |
|------|------------|-----------|-------------|
| Trend Following | MA crossover + trend confirmation | Trend reversal signals | Strong trends |
| Mean Reversion | Price at Bollinger extremes | Return to mean | Range-bound |
| Breakout | Level break + volume confirmation | Failed breakout | Consolidation |
| Momentum | Acceleration + narrative | Momentum fade | Fast-moving |

### Strategy Spec Schema

Each generated strategy is a complete JSON spec:

```json
{
  "strategy_type": "trend_following",
  "symbol": "BTC",
  "direction": "long",
  "confidence": 0.72,
  "time_horizon": "1-4 weeks",
  "entry_conditions": ["..."],
  "exit_conditions": ["..."],
  "position_sizing": {"..."},
  "risk_management": {"..."},
  "signals": {"..."},
  "rationale": "..."
}
```

### Backtestability

Strategy specs are designed for backtesting:
- **Specific entry conditions**: Exact score thresholds, not vague descriptions
- **Defined exit rules**: Clear triggers for each exit type
- **Position sizing rules**: Quantified risk per trade and max position
- **Risk parameters**: Exact stop loss and take profit calculations

## Extension Points

### Adding a New Strategy Type

1. Add constant to `strategy_generator.py`
2. Implement `_gen_<type>()` method
3. Register in `_generators` dict in `__init__`

### Adding a New Analysis Factor

1. Implement `score_<name>()` in `StrategyAnalyzer`
2. Add weight to `FACTOR_WEIGHTS`
3. Update `_generators` to use new factor if relevant

### Custom Data Sources

Implement the same data schema as `CMCFetcher` and pass to `StrategyAnalyzer.analyze()`.

## Testing Strategy

- **Unit tests**: Each factor tested independently with known inputs
- **Integration tests**: Full pipeline fetch → analyze → generate
- **Mock data**: Deterministic test data for reproducible results
- **Boundary tests**: Edge cases (zero values, extreme values, missing data)

## Performance

- **Single coin analysis**: <1ms (pure computation, no I/O)
- **API fetch**: 1–30s depending on network and rate limits
- **Strategy generation**: <1ms per coin
- **Total pipeline**: Dominated by API fetch time
