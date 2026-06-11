"""
Strategy Spec Generator

Transforms analysis results into backtestable strategy specifications.
Supports 4 strategy archetypes:
- Trend Following
- Mean Reversion
- Breakout
- Momentum

Each strategy includes entry/exit conditions, position sizing,
stop loss, take profit, and confidence metrics.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from strategy_analyzer import AnalysisResult


# Strategy type constants
TREND_FOLLOWING = "trend_following"
MEAN_REVERSION = "mean_reversion"
BREAKOUT = "breakout"
MOMENTUM = "momentum"

VALID_STRATEGIES = [TREND_FOLLOWING, MEAN_REVERSION, BREAKOUT, MOMENTUM]


@dataclass
class StrategySpec:
    """A complete, backtestable strategy specification."""
    strategy_type: str
    symbol: str
    name: str
    direction: str  # "long", "short", or "neutral"
    confidence: float
    time_horizon: str
    entry_conditions: list[str]
    exit_conditions: list[str]
    position_sizing: dict[str, Any]
    risk_management: dict[str, Any]
    signals: dict[str, Any]
    rationale: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_type": self.strategy_type,
            "symbol": self.symbol,
            "name": self.name,
            "direction": self.direction,
            "confidence": round(self.confidence, 3),
            "time_horizon": self.time_horizon,
            "entry_conditions": self.entry_conditions,
            "exit_conditions": self.exit_conditions,
            "position_sizing": self.position_sizing,
            "risk_management": self.risk_management,
            "signals": self.signals,
            "rationale": self.rationale,
        }


class StrategyGenerator:
    """
    Generates backtestable strategy specifications from analysis data.
    
    Each strategy type has specific entry/exit logic derived from
    the multi-factor analysis scores.
    
    Example:
        >>> generator = StrategyGenerator()
        >>> strategy = generator.generate(analysis, strategy_type="momentum")
        >>> print(strategy.to_dict())
    """
    
    def __init__(self):
        """Initialize the strategy generator."""
        self._generators = {
            TREND_FOLLOWING: self._gen_trend_following,
            MEAN_REVERSION: self._gen_mean_reversion,
            BREAKOUT: self._gen_breakout,
            MOMENTUM: self._gen_momentum,
        }
    
    def generate(
        self,
        analysis: AnalysisResult,
        strategy_type: str = TREND_FOLLOWING,
    ) -> StrategySpec:
        """
        Generate a strategy spec from analysis results.
        
        Args:
            analysis: AnalysisResult from StrategyAnalyzer
            strategy_type: One of TREND_FOLLOWING, MEAN_REVERSION,
                          BREAKOUT, MOMENTUM
                          
        Returns:
            StrategySpec with complete strategy details
        """
        if strategy_type not in self._generators:
            raise ValueError(
                f"Unknown strategy type: {strategy_type}. "
                f"Valid: {VALID_STRATEGIES}"
            )
        
        return self._generators[strategy_type](analysis)
    
    def _determine_direction(self, analysis: AnalysisResult) -> str:
        """Determine trade direction from composite signal."""
        if analysis.composite_signal == "bullish":
            return "long"
        elif analysis.composite_signal == "bearish":
            return "short"
        return "neutral"
    
    def _time_horizon(self, strategy_type: str) -> str:
        """Get appropriate time horizon for strategy type."""
        horizons = {
            TREND_FOLLOWING: "1-4 weeks",
            MEAN_REVERSION: "1-7 days",
            BREAKOUT: "3-14 days",
            MOMENTUM: "1-5 days",
        }
        return horizons.get(strategy_type, "1-7 days")
    
    def _gen_trend_following(self, analysis: AnalysisResult) -> StrategySpec:
        """
        Generate trend following strategy.
        
        Logic: Enter when trend is confirmed by multiple timeframes.
        Uses trend strength and momentum as primary signals.
        """
        direction = self._determine_direction(analysis)
        
        # Get factor scores
        trend = self._get_factor(analysis, "trend_strength")
        momentum = self._get_factor(analysis, "momentum")
        
        # Entry conditions based on trend alignment
        entry_conditions = []
        exit_conditions = []
        
        if direction == "long":
            entry_conditions = [
                f"Trend strength score >= 55 (current: {trend['score']})",
                f"Momentum score >= 50 (current: {momentum['score']})",
                "Price above 20-period moving average",
                "24h change positive AND 7d change positive",
                "Volume above 20-period average (confirmation)",
            ]
            exit_conditions = [
                "Trend strength drops below 45",
                "Price closes below 20-period MA",
                "Momentum score drops below 40",
                "Stop loss triggered",
                "Take profit triggered",
            ]
        elif direction == "short":
            entry_conditions = [
                f"Trend strength score <= 45 (current: {trend['score']})",
                f"Momentum score <= 50 (current: {momentum['score']})",
                "Price below 20-period moving average",
                "24h change negative AND 7d change negative",
                "Volume above 20-period average (confirmation)",
            ]
            exit_conditions = [
                "Trend strength rises above 55",
                "Price closes above 20-period MA",
                "Momentum score rises above 60",
                "Stop loss triggered",
                "Take profit triggered",
            ]
        else:
            entry_conditions = [
                "No clear trend — wait for confirmation",
                f"Trend strength: {trend['score']}, Momentum: {momentum['score']}",
            ]
            exit_conditions = ["Do not enter until direction clarifies"]
        
        confidence = analysis.confidence * (trend["score"] / 100)
        
        return StrategySpec(
            strategy_type=TREND_FOLLOWING,
            symbol=analysis.symbol,
            name=analysis.name,
            direction=direction,
            confidence=confidence,
            time_horizon=self._time_horizon(TREND_FOLLOWING),
            entry_conditions=entry_conditions,
            exit_conditions=exit_conditions,
            position_sizing={
                "method": "fixed_fractional",
                "risk_per_trade": "2%",
                "max_position_size": "5% of portfolio",
                "scale_in": "Split into 2-3 entries on pullbacks",
            },
            risk_management={
                "stop_loss": "ATR-based: 2x ATR from entry" if direction != "neutral" else "N/A",
                "take_profit": "Risk:reward minimum 1:2" if direction != "neutral" else "N/A",
                "trailing_stop": "Move stop to breakeven after 1R profit",
                "max_drawdown": "Exit if position drawdown exceeds 6%",
            },
            signals={
                "trend_strength": trend,
                "momentum": momentum,
                "composite": {
                    "score": analysis.composite_score,
                    "signal": analysis.composite_signal,
                },
            },
            rationale=self._build_rationale(analysis, TREND_FOLLOWING),
        )
    
    def _gen_mean_reversion(self, analysis: AnalysisResult) -> StrategySpec:
        """
        Generate mean reversion strategy.
        
        Logic: Enter when price has deviated significantly from mean.
        Uses volatility and momentum extremes as signals.
        """
        direction = self._determine_direction(analysis)
        volatility = self._get_factor(analysis, "volatility")
        momentum = self._get_factor(analysis, "momentum")
        
        # Mean reversion is contrarian
        entry_conditions = []
        exit_conditions = []
        
        if direction == "long":
            # Oversold bounce
            entry_conditions = [
                f"Momentum indicates oversold (score: {momentum['score']})",
                f"Volatility elevated (score: {volatility['score']}) — potential reversal zone",
                "Price below lower Bollinger Band (2 std dev)",
                "RSI < 30 or equivalent oversold signal",
                "Volume spike on down candle (capitulation)",
            ]
            exit_conditions = [
                "Price returns to 20-period SMA",
                "RSI crosses above 50",
                "Momentum score returns to neutral zone (45-55)",
                "Stop loss triggered",
                "Target: 50% reversion of recent move",
            ]
        elif direction == "short":
            # Overbought fade
            entry_conditions = [
                f"Momentum indicates overbought (score: {momentum['score']})",
                f"Volatility elevated (score: {volatility['score']})",
                "Price above upper Bollinger Band (2 std dev)",
                "RSI > 70 or equivalent overbought signal",
                "Volume spike on up candle (euphoria)",
            ]
            exit_conditions = [
                "Price returns to 20-period SMA",
                "RSI crosses below 50",
                "Momentum score returns to neutral zone",
                "Stop loss triggered",
                "Target: 50% reversion of recent move",
            ]
        else:
            entry_conditions = [
                "No clear mean reversion setup",
                f"Volatility: {volatility['score']}, Momentum: {momentum['score']}",
            ]
            exit_conditions = ["Do not enter"]
        
        confidence = analysis.confidence * 0.8  # Mean reversion is inherently riskier
        
        return StrategySpec(
            strategy_type=MEAN_REVERSION,
            symbol=analysis.symbol,
            name=analysis.name,
            direction=direction,
            confidence=confidence,
            time_horizon=self._time_horizon(MEAN_REVERSION),
            entry_conditions=entry_conditions,
            exit_conditions=exit_conditions,
            position_sizing={
                "method": "fixed_fractional",
                "risk_per_trade": "1.5%",
                "max_position_size": "3% of portfolio",
                "scale_in": "Single entry at extreme, or DCA at -1 std dev intervals",
            },
            risk_management={
                "stop_loss": "1.5x ATR beyond entry" if direction != "neutral" else "N/A",
                "take_profit": "50% reversion of prior move, or R1 pivot" if direction != "neutral" else "N/A",
                "trailing_stop": "None — fixed target exit",
                "max_drawdown": "Exit if position loss exceeds 4%",
            },
            signals={
                "volatility": volatility,
                "momentum": momentum,
                "composite": {
                    "score": analysis.composite_score,
                    "signal": analysis.composite_signal,
                },
            },
            rationale=self._build_rationale(analysis, MEAN_REVERSION),
        )
    
    def _gen_breakout(self, analysis: AnalysisResult) -> StrategySpec:
        """
        Generate breakout strategy.
        
        Logic: Enter when price breaks key levels with volume confirmation.
        Uses volume profile and trend strength as primary signals.
        """
        direction = self._determine_direction(analysis)
        volume = self._get_factor(analysis, "volume_profile")
        trend = self._get_factor(analysis, "trend_strength")
        
        entry_conditions = []
        exit_conditions = []
        
        if direction == "long":
            entry_conditions = [
                f"Volume profile strong (score: {volume['score']}) — confirms breakout",
                f"Trend aligned (score: {trend['score']})",
                "Price breaks above resistance / upper range",
                "Breakout candle closes above level with conviction",
                "Volume 1.5x+ above 20-period average on breakout",
            ]
            exit_conditions = [
                "Price falls back below breakout level (failed breakout)",
                "Volume dries up after breakout (weak follow-through)",
                "Target 1: 1x risk (take 50% profit)",
                "Target 2: 2x risk (trail remaining 50%)",
                "Stop loss triggered",
            ]
        elif direction == "short":
            entry_conditions = [
                f"Volume profile shows distribution (score: {volume['score']})",
                f"Trend weakening (score: {trend['score']})",
                "Price breaks below support / lower range",
                "Breakout candle closes below level",
                "Volume spike on breakdown",
            ]
            exit_conditions = [
                "Price reclaims breakout level (failed breakdown)",
                "Volume decreases after breakdown",
                "Target 1: 1x risk",
                "Target 2: 2x risk with trailing stop",
                "Stop loss triggered",
            ]
        else:
            entry_conditions = [
                "No clear breakout level identified",
                f"Volume: {volume['score']}, Trend: {trend['score']}",
            ]
            exit_conditions = ["Do not enter"]
        
        confidence = analysis.confidence * (volume["score"] / 100)
        
        return StrategySpec(
            strategy_type=BREAKOUT,
            symbol=analysis.symbol,
            name=analysis.name,
            direction=direction,
            confidence=confidence,
            time_horizon=self._time_horizon(BREAKOUT),
            entry_conditions=entry_conditions,
            exit_conditions=exit_conditions,
            position_sizing={
                "method": "fixed_fractional",
                "risk_per_trade": "1.5%",
                "max_position_size": "4% of portfolio",
                "scale_in": "Full position on confirmed breakout",
            },
            risk_management={
                "stop_loss": "Below breakout level by 0.5x ATR" if direction != "neutral" else "N/A",
                "take_profit": "2x risk (R:R 1:2 minimum)" if direction != "neutral" else "N/A",
                "trailing_stop": "Trail at 1x ATR after 1R profit",
                "max_drawdown": "Exit if failed breakout confirmed (close back in range)",
            },
            signals={
                "volume_profile": volume,
                "trend_strength": trend,
                "composite": {
                    "score": analysis.composite_score,
                    "signal": analysis.composite_signal,
                },
            },
            rationale=self._build_rationale(analysis, BREAKOUT),
        )
    
    def _gen_momentum(self, analysis: AnalysisResult) -> StrategySpec:
        """
        Generate momentum strategy.
        
        Logic: Enter on acceleration of price movement.
        Uses momentum and narrative as primary signals.
        """
        direction = self._determine_direction(analysis)
        momentum = self._get_factor(analysis, "momentum")
        narrative = self._get_factor(analysis, "narrative")
        
        entry_conditions = []
        exit_conditions = []
        
        if direction == "long":
            entry_conditions = [
                f"Momentum accelerating (score: {momentum['score']})",
                f"Narrative building (score: {narrative['score']})",
                "24h change > 3% and 7d change > 5%",
                "Volume increasing for 2+ consecutive periods",
                "Price making higher highs and higher lows",
            ]
            exit_conditions = [
                "Momentum score drops below 50",
                "Volume declining while price rises (divergence)",
                "Narrative score drops below 40",
                "Stop loss triggered",
                "Take profit: trail at 3% below recent high",
            ]
        elif direction == "short":
            entry_conditions = [
                f"Momentum negative (score: {momentum['score']})",
                f"Narrative weakening (score: {narrative['score']})",
                "24h change < -3% and 7d change < -5%",
                "Volume increasing on down moves",
                "Price making lower highs and lower lows",
            ]
            exit_conditions = [
                "Momentum score rises above 50",
                "Volume declining on down moves",
                "Narrative score rises above 60",
                "Stop loss triggered",
                "Take profit: trail at 3% above recent low",
            ]
        else:
            entry_conditions = [
                "No clear momentum setup",
                f"Momentum: {momentum['score']}, Narrative: {narrative['score']}",
            ]
            exit_conditions = ["Do not enter"]
        
        # Momentum strategies need high confidence
        confidence = analysis.confidence * (momentum["score"] / 100) * 0.9
        
        return StrategySpec(
            strategy_type=MOMENTUM,
            symbol=analysis.symbol,
            name=analysis.name,
            direction=direction,
            confidence=confidence,
            time_horizon=self._time_horizon(MOMENTUM),
            entry_conditions=entry_conditions,
            exit_conditions=exit_conditions,
            position_sizing={
                "method": "momentum-scaled",
                "risk_per_trade": "1% (momentum = higher risk)",
                "max_position_size": "3% of portfolio",
                "scale_in": "Pyramid: add on continuation, never add to losers",
            },
            risk_management={
                "stop_loss": "Tight: 1x ATR from entry" if direction != "neutral" else "N/A",
                "take_profit": "Trailing stop at 3% or 1.5x ATR" if direction != "neutral" else "N/A",
                "trailing_stop": "Aggressive: trail every new high/low by 2%",
                "max_drawdown": "Exit entire position if daily loss > 3%",
            },
            signals={
                "momentum": momentum,
                "narrative": narrative,
                "composite": {
                    "score": analysis.composite_score,
                    "signal": analysis.composite_signal,
                },
            },
            rationale=self._build_rationale(analysis, MOMENTUM),
        )
    
    def _get_factor(self, analysis: AnalysisResult, name: str) -> dict[str, Any]:
        """Extract factor result as dict."""
        for f in analysis.factors:
            if f.name == name:
                return f.to_dict()
        return {"name": name, "score": 50, "signal": "neutral", "detail": "N/A"}
    
    def _build_rationale(self, analysis: AnalysisResult, strategy_type: str) -> str:
        """Build human-readable rationale for the strategy."""
        parts = [
            f"Strategy: {strategy_type.replace('_', ' ').title()} for {analysis.symbol}",
            f"Composite Score: {analysis.composite_score:.1f}/100 ({analysis.composite_signal})",
            f"Confidence: {analysis.confidence:.0%}",
            "",
            "Factor Breakdown:",
        ]
        for f in analysis.factors:
            parts.append(f"  - {f.name}: {f.score:.0f}/100 ({f.signal}) — {f.detail}")
        
        parts.append("")
        
        # Add strategy-specific rationale
        if strategy_type == TREND_FOLLOWING:
            parts.append("Rationale: Multi-timeframe trend alignment supports directional trade.")
        elif strategy_type == MEAN_REVERSION:
            parts.append("Rationale: Price extended from mean; expecting reversion.")
        elif strategy_type == BREAKOUT:
            parts.append("Rationale: Key level break confirmed by volume; expecting continuation.")
        elif strategy_type == MOMENTUM:
            parts.append("Rationale: Strong momentum and narrative support continuation play.")
        
        return "\n".join(parts)
