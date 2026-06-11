"""
Multi-Factor Strategy Analyzer

Computes 5 independent analysis factors from market data:
- Momentum (RSI-like price velocity)
- Volume Profile (accumulation/distribution)
- Trend Strength (MA alignment)
- Volatility (position sizing guidance)
- Narrative Momentum (volume spike buzz proxy)

Each factor outputs a 0–100 score with bullish/bearish/neutral signal.
Composite score is a weighted combination of all factors.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


# Weight configuration for composite score
FACTOR_WEIGHTS = {
    "momentum": 0.25,
    "volume_profile": 0.20,
    "trend_strength": 0.25,
    "volatility": 0.15,
    "narrative": 0.15,
}

# Thresholds for signal classification
BULLISH_THRESHOLD = 60
BEARISH_THRESHOLD = 40


@dataclass
class FactorResult:
    """Result of a single analysis factor."""
    name: str
    score: float  # 0-100
    signal: str   # "bullish", "bearish", or "neutral"
    detail: str   # Human-readable explanation
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 2),
            "signal": self.signal,
            "detail": self.detail,
        }


@dataclass
class AnalysisResult:
    """Complete analysis result for a coin."""
    symbol: str
    name: str
    factors: list[FactorResult] = field(default_factory=list)
    composite_score: float = 0.0
    composite_signal: str = "neutral"
    confidence: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "factors": [f.to_dict() for f in self.factors],
            "composite_score": round(self.composite_score, 2),
            "composite_signal": self.composite_signal,
            "confidence": round(self.confidence, 2),
        }


class StrategyAnalyzer:
    """
    Multi-factor strategy analyzer.
    
    Analyzes market data using 5 independent scoring factors
    and combines them into a composite score.
    
    Example:
        >>> analyzer = StrategyAnalyzer()
        >>> result = analyzer.analyze_single(coin_data)
        >>> print(result.composite_signal)
        'bullish'
    """
    
    def __init__(self, weights: Optional[dict[str, float]] = None):
        """
        Initialize analyzer with optional custom weights.
        
        Args:
            weights: Custom factor weights. Must sum to 1.0.
                     Defaults to FACTOR_WEIGHTS.
        """
        self.weights = weights or FACTOR_WEIGHTS.copy()
        # Normalize weights to sum to 1.0
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
    
    def _classify_signal(self, score: float) -> str:
        """Classify score into signal."""
        if score >= BULLISH_THRESHOLD:
            return "bullish"
        elif score <= BEARISH_THRESHOLD:
            return "bearish"
        return "neutral"
    
    def _clamp(self, value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
        """Clamp value to range."""
        return max(min_val, min(max_val, value))
    
    def score_momentum(self, change_24h: float, change_7d: float) -> FactorResult:
        """
        Compute momentum score from price changes.
        
        Uses a blend of 24h and 7d changes with velocity weighting.
        Strong recent momentum (24h) is weighted higher than 7d.
        
        Args:
            change_24h: 24-hour price change percentage
            change_7d: 7-day price change percentage
            
        Returns:
            FactorResult with score 0-100 and signal
        """
        # Weighted momentum: 60% 24h, 40% 7d
        raw = change_24h * 0.6 + change_7d * 0.4
        
        # Map from typical range [-20, +20] to [0, 100]
        # Center at 50 (neutral)
        score = self._clamp(50 + raw * 2.5)
        
        if raw > 5:
            detail = f"Strong upward momentum: 24h {change_24h:+.1f}%, 7d {change_7d:+.1f}%"
        elif raw > 1:
            detail = f"Moderate bullish momentum: 24h {change_24h:+.1f}%, 7d {change_7d:+.1f}%"
        elif raw < -5:
            detail = f"Strong downward momentum: 24h {change_24h:+.1f}%, 7d {change_7d:+.1f}%"
        elif raw < -1:
            detail = f"Moderate bearish momentum: 24h {change_24h:+.1f}%, 7d {change_7d:+.1f}%"
        else:
            detail = f"Neutral momentum: 24h {change_24h:+.1f}%, 7d {change_7d:+.1f}%"
        
        return FactorResult(
            name="momentum",
            score=score,
            signal=self._classify_signal(score),
            detail=detail,
        )
    
    def score_volume_profile(self, volume_24h: float, market_cap: float) -> FactorResult:
        """
        Compute volume profile score (accumulation vs distribution).
        
        High volume relative to market cap suggests strong interest.
        Very high volume can signal distribution (selling pressure).
        Moderate-high volume with positive price action = accumulation.
        
        Args:
            volume_24h: 24-hour trading volume in USD
            market_cap: Market capitalization in USD
            
        Returns:
            FactorResult with score 0-100 and signal
        """
        if market_cap <= 0:
            return FactorResult(
                name="volume_profile", score=50.0, signal="neutral",
                detail="Insufficient data for volume analysis"
            )
        
        # Volume/MC ratio (typical range: 0.01 to 0.30)
        vol_ratio = volume_24h / market_cap
        
        # Map ratio to score: sweet spot around 0.05-0.15
        if vol_ratio < 0.02:
            score = 35  # Very low volume, disinterest
            detail = f"Very low volume ratio ({vol_ratio:.3f}), low market interest"
        elif vol_ratio < 0.05:
            score = 50  # Normal low volume
            detail = f"Below-average volume ratio ({vol_ratio:.3f})"
        elif vol_ratio < 0.15:
            score = 70  # Healthy accumulation zone
            detail = f"Healthy volume ratio ({vol_ratio:.3f}), potential accumulation"
        elif vol_ratio < 0.25:
            score = 75  # Strong volume, active trading
            detail = f"Strong volume ratio ({vol_ratio:.3f}), active market"
        else:
            # Very high volume can be distribution
            score = 55
            detail = f"Very high volume ratio ({vol_ratio:.3f}), possible distribution"
        
        score = self._clamp(score)
        return FactorResult(
            name="volume_profile",
            score=score,
            signal=self._classify_signal(score),
            detail=detail,
        )
    
    def score_trend_strength(self, change_24h: float, change_7d: float) -> FactorResult:
        """
        Compute trend strength from price change alignment.
        
        Both 24h and 7d in same direction = strong trend.
        Conflicting signals = weak/neutral trend.
        
        Args:
            change_24h: 24-hour price change percentage
            change_7d: 7-day price change percentage
            
        Returns:
            FactorResult with score 0-100 and signal
        """
        # Direction alignment
        aligned = (change_24h > 0 and change_7d > 0) or (change_24h < 0 and change_7d < 0)
        
        # Magnitude of both changes
        avg_change = (abs(change_24h) + abs(change_7d)) / 2
        
        if aligned:
            # Strong aligned trend
            if change_24h > 0:
                score = self._clamp(55 + min(avg_change * 3, 40))
                detail = f"Strong uptrend: both timeframes aligned bullish"
            else:
                score = self._clamp(45 - min(avg_change * 3, 40))
                detail = f"Strong downtrend: both timeframes aligned bearish"
        else:
            # Conflicting signals = weak trend
            divergence = abs(change_24h - change_7d)
            score = self._clamp(50 - divergence * 2)
            detail = f"Conflicting signals: 24h {change_24h:+.1f}% vs 7d {change_7d:+.1f}%"
        
        return FactorResult(
            name="trend_strength",
            score=score,
            signal=self._classify_signal(score),
            detail=detail,
        )
    
    def score_volatility(self, change_24h: float, change_7d: float) -> FactorResult:
        """
        Compute volatility score for position sizing guidance.
        
        Higher volatility = larger potential moves = needs tighter stops.
        Score indicates volatility level, NOT direction.
        
        Args:
            change_24h: 24-hour price change percentage
            change_7d: 7-day price change percentage
            
        Returns:
            FactorResult with score 0-100 and signal
        """
        # Volatility = magnitude of moves (not direction)
        abs_24h = abs(change_24h)
        abs_7d = abs(change_7d)
        
        # Average absolute change
        avg_abs = (abs_24h + abs_7d) / 2
        
        # Map to 0-100 volatility scale
        # Low: <1%, Medium: 1-5%, High: 5-10%, Very High: >10%
        if avg_abs < 1:
            score = 20
            detail = f"Low volatility (avg {avg_abs:.1f}%), suitable for larger positions"
        elif avg_abs < 3:
            score = 40
            detail = f"Moderate volatility (avg {avg_abs:.1f}%), standard position sizing"
        elif avg_abs < 6:
            score = 65
            detail = f"Elevated volatility (avg {avg_abs:.1f}%), reduce position size"
        elif avg_abs < 10:
            score = 80
            detail = f"High volatility (avg {avg_abs:.1f}%), significant position reduction"
        else:
            score = 95
            detail = f"Extreme volatility (avg {avg_abs:.1f}%), minimal position size"
        
        # Note: For volatility, higher = more volatile (not bullish/bearish)
        # We use bullish when low vol (easier to trade), bearish when extreme
        if score < 40:
            signal = "bullish"  # Low vol = easier to manage
        elif score > 75:
            signal = "bearish"  # High vol = risky
        else:
            signal = "neutral"
        
        return FactorResult(
            name="volatility",
            score=score,
            signal=signal,
            detail=detail,
        )
    
    def score_narrative(self, change_24h: float, change_7d: float,
                       volume_24h: float, market_cap: float) -> FactorResult:
        """
        Compute narrative momentum (social/market buzz proxy).
        
        Uses volume spikes relative to market cap as a proxy for
        social sentiment and market attention.
        A coin with high volume relative to its cap is getting attention.
        
        Args:
            change_24h: 24-hour price change percentage
            change_7d: 7-day price change percentage
            volume_24h: 24-hour trading volume
            market_cap: Market capitalization
            
        Returns:
            FactorResult with score 0-100 and signal
        """
        if market_cap <= 0:
            return FactorResult(
                name="narrative", score=50.0, signal="neutral",
                detail="Insufficient data for narrative analysis"
            )
        
        vol_ratio = volume_24h / market_cap
        momentum = change_24h + change_7d * 0.5
        
        # Narrative = volume attention × direction
        if vol_ratio > 0.1 and momentum > 3:
            score = 85
            detail = f"Strong narrative momentum: high volume ({vol_ratio:.1%}) with bullish price action"
        elif vol_ratio > 0.08 and momentum > 1:
            score = 72
            detail = f"Building narrative: above-average volume with positive momentum"
        elif vol_ratio > 0.05 and momentum > 0:
            score = 60
            detail = f"Moderate narrative interest: steady volume and mild bullishness"
        elif vol_ratio > 0.1 and momentum < -3:
            score = 30
            detail = f"Negative narrative: high volume with bearish price action (sell-off)"
        elif vol_ratio < 0.03:
            score = 35
            detail = f"Low narrative interest: minimal volume relative to market cap"
        else:
            score = 50
            detail = f"Neutral narrative: average volume and mixed signals"
        
        score = self._clamp(score)
        return FactorResult(
            name="narrative",
            score=score,
            signal=self._classify_signal(score),
            detail=detail,
        )
    
    def analyze_single(self, coin: dict[str, Any]) -> AnalysisResult:
        """
        Analyze a single coin's market data.
        
        Args:
            coin: Coin data dict with keys: symbol, name, price,
                  volume_24h, market_cap, change_24h, change_7d
                  
        Returns:
            AnalysisResult with all factors and composite score
        """
        factors = [
            self.score_momentum(coin["change_24h"], coin["change_7d"]),
            self.score_volume_profile(coin["volume_24h"], coin["market_cap"]),
            self.score_trend_strength(coin["change_24h"], coin["change_7d"]),
            self.score_volatility(coin["change_24h"], coin["change_7d"]),
            self.score_narrative(
                coin["change_24h"], coin["change_7d"],
                coin["volume_24h"], coin["market_cap"]
            ),
        ]
        
        # Compute weighted composite score
        composite = sum(
            f.score * self.weights.get(f.name, 0.2)
            for f in factors
        )
        composite = self._clamp(composite)
        
        # Confidence = agreement between factors
        signals = [f.signal for f in factors]
        bullish_count = signals.count("bullish")
        bearish_count = signals.count("bearish")
        max_agreement = max(bullish_count, bearish_count)
        confidence = max_agreement / len(signals)
        
        return AnalysisResult(
            symbol=coin["symbol"],
            name=coin["name"],
            factors=factors,
            composite_score=composite,
            composite_signal=self._classify_signal(composite),
            confidence=confidence,
        )
    
    def analyze(self, coins: list[dict[str, Any]]) -> list[AnalysisResult]:
        """
        Analyze multiple coins.
        
        Args:
            coins: List of coin data dicts
            
        Returns:
            List of AnalysisResult, sorted by composite score (descending)
        """
        results = [self.analyze_single(coin) for coin in coins]
        results.sort(key=lambda r: r.composite_score, reverse=True)
        return results
