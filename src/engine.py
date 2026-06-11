"""
CMC Strategy Engine — Main Orchestrator

CLI entry point that combines fetcher → analyzer → generator.
Supports --coins, --strategy-type, --output-format flags.
"""

import argparse
import json
import sys
import os
from typing import Any

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cmc_fetcher import CMCFetcher
from strategy_analyzer import StrategyAnalyzer
from strategy_generator import StrategyGenerator, VALID_STRATEGIES


BANNER = r"""
  ╔══════════════════════════════════════════════════════════╗
  ║           CMC STRATEGY ENGINE v1.0.0                    ║
  ║  Turn market data into backtestable trading strategies   ║
  ╚══════════════════════════════════════════════════════════╝
"""


def format_strategy_text(strategy: dict[str, Any]) -> str:
    """Pretty-print a strategy spec as human-readable text."""
    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"  STRATEGY: {strategy['strategy_type'].replace('_', ' ').upper()}")
    lines.append(f"  {strategy['name']} ({strategy['symbol']})")
    lines.append(f"{'='*60}")
    lines.append(f"  Direction:   {strategy['direction'].upper()}")
    lines.append(f"  Confidence:  {strategy['confidence']:.0%}")
    lines.append(f"  Horizon:     {strategy['time_horizon']}")
    lines.append(f"{'─'*60}")
    
    lines.append("\n  📊 ENTRY CONDITIONS:")
    for i, cond in enumerate(strategy['entry_conditions'], 1):
        lines.append(f"    {i}. {cond}")
    
    lines.append("\n  🚪 EXIT CONDITIONS:")
    for i, cond in enumerate(strategy['exit_conditions'], 1):
        lines.append(f"    {i}. {cond}")
    
    ps = strategy['position_sizing']
    lines.append("\n  💰 POSITION SIZING:")
    for k, v in ps.items():
        lines.append(f"    {k.replace('_', ' ').title()}: {v}")
    
    rm = strategy['risk_management']
    lines.append("\n  🛡️  RISK MANAGEMENT:")
    for k, v in rm.items():
        lines.append(f"    {k.replace('_', ' ').title()}: {v}")
    
    lines.append(f"\n{'─'*60}")
    lines.append("  📝 RATIONALE:")
    for line in strategy['rationale'].split('\n'):
        lines.append(f"    {line}")
    
    lines.append(f"{'='*60}\n")
    return "\n".join(lines)


def format_analysis_text(analysis: dict[str, Any]) -> str:
    """Pretty-print analysis results."""
    lines = []
    lines.append(f"\n  📈 ANALYSIS: {analysis['name']} ({analysis['symbol']})")
    lines.append(f"  Composite: {analysis['composite_score']:.1f}/100 ({analysis['composite_signal']})")
    lines.append(f"  Confidence: {analysis['confidence']:.0%}")
    
    for factor in analysis['factors']:
        bar_len = int(factor['score'] / 5)
        bar = '█' * bar_len + '░' * (20 - bar_len)
        signal_icon = {"bullish": "🟢", "bearish": "🔴", "neutral": "🟡"}
        icon = signal_icon.get(factor['signal'], "⚪")
        lines.append(f"    {icon} {factor['name']:18s} [{bar}] {factor['score']:5.1f} ({factor['signal']})")
    
    return "\n".join(lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CMC Strategy Engine — Generate backtestable trading strategies"
    )
    parser.add_argument(
        "--coins",
        type=str,
        default=None,
        help="Comma-separated coin symbols (e.g., BTC,ETH,BNB). Default: top 5 by market cap."
    )
    parser.add_argument(
        "--strategy-type",
        type=str,
        default="trend_following",
        choices=VALID_STRATEGIES,
        help=f"Strategy type. Default: trend_following. Options: {', '.join(VALID_STRATEGIES)}"
    )
    parser.add_argument(
        "--output-format",
        type=str,
        default="text",
        choices=["text", "json"],
        help="Output format. Default: text."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of top coins to analyze (default: 5)"
    )
    
    args = parser.parse_args()
    
    print(BANNER)
    
    # Step 1: Fetch
    print("  ⏳ Step 1/3: Fetching market data from CoinMarketCap...")
    fetcher = CMCFetcher()
    
    if args.coins:
        symbols = [s.strip().upper() for s in args.coins.split(",")]
        coins = fetcher.fetch_by_symbols(symbols)
    else:
        coins = fetcher.fetch_top_coins(args.count)
    
    print(f"  ✅ Fetched data for {len(coins)} coins\n")
    
    # Step 2: Analyze
    print("  ⏳ Step 2/3: Running multi-factor analysis...")
    analyzer = StrategyAnalyzer()
    analyses = analyzer.analyze(coins)
    
    if args.output_format == "text":
        for analysis in analyses:
            print(format_analysis_text(analysis.to_dict()))
    
    # Step 3: Generate
    print("  ⏳ Step 3/3: Generating strategy specifications...\n")
    generator = StrategyGenerator()
    
    strategies = []
    for analysis in analyses:
        strategy = generator.generate(analysis, strategy_type=args.strategy_type)
        strategies.append(strategy.to_dict())
    
    if args.output_format == "text":
        for strategy in strategies:
            print(format_strategy_text(strategy))
    else:
        # JSON output
        output = {
            "engine": "CMC Strategy Engine",
            "version": "1.0.0",
            "strategy_type": args.strategy_type,
            "strategies": strategies,
        }
        print(json.dumps(output, indent=2))
    
    print(f"  ✅ Generated {len(strategies)} strategy specifications")
    print(f"  📊 Strategy type: {args.strategy_type.replace('_', ' ').title()}")
    print(f"  🎯 Top pick: {strategies[0]['symbol']} ({strategies[0]['confidence']:.0%} confidence)")


if __name__ == "__main__":
    main()
