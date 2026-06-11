"""
Unit Tests for Strategy Analyzer

Tests each scoring factor, composite score calculation,
and signal generation.
"""

import sys
import os
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from strategy_analyzer import StrategyAnalyzer, FactorResult, AnalysisResult


@pytest.fixture
def analyzer():
    """Create a fresh analyzer instance."""
    return StrategyAnalyzer()


@pytest.fixture
def strong_bullish_coin():
    """Fixture: strong bullish coin data."""
    return {
        "symbol": "BTC",
        "name": "Bitcoin",
        "price": 104500.0,
        "volume_24h": 28_500_000_000,
        "market_cap": 2_060_000_000_000,
        "change_24h": 5.2,
        "change_7d": 12.0,
        "rank": 1,
    }


@pytest.fixture
def strong_bearish_coin():
    """Fixture: strong bearish coin data."""
    return {
        "symbol": "DUMP",
        "name": "DumpCoin",
        "price": 50.0,
        "volume_24h": 500_000_000,
        "market_cap": 2_000_000_000,
        "change_24h": -8.5,
        "change_7d": -15.0,
        "rank": 100,
    }


@pytest.fixture
def neutral_coin():
    """Fixture: neutral/sideways coin data."""
    return {
        "symbol": "FLAT",
        "name": "FlatCoin",
        "price": 100.0,
        "volume_24h": 100_000_000,
        "market_cap": 1_000_000_000,
        "change_24h": 0.2,
        "change_7d": -0.1,
        "rank": 50,
    }


# ─── Momentum Tests ───────────────────────────────────────────

class TestMomentum:
    """Test momentum scoring factor."""
    
    def test_strong_bullish_momentum(self, analyzer):
        """Strong positive changes should yield bullish momentum."""
        result = analyzer.score_momentum(change_24h=10.0, change_7d=15.0)
        assert result.name == "momentum"
        assert result.score > 70, f"Expected score > 70, got {result.score}"
        assert result.signal == "bullish"
    
    def test_strong_bearish_momentum(self, analyzer):
        """Strong negative changes should yield bearish momentum."""
        result = analyzer.score_momentum(change_24h=-10.0, change_7d=-15.0)
        assert result.score < 30, f"Expected score < 30, got {result.score}"
        assert result.signal == "bearish"
    
    def test_neutral_momentum(self, analyzer):
        """Near-zero changes should yield neutral momentum."""
        result = analyzer.score_momentum(change_24h=0.0, change_7d=0.0)
        assert 45 <= result.score <= 55, f"Expected ~50, got {result.score}"
        assert result.signal == "neutral"
    
    def test_momentum_score_range(self, analyzer):
        """Momentum score should always be in [0, 100]."""
        test_cases = [
            (50.0, 50.0),   # Extreme positive
            (-50.0, -50.0), # Extreme negative
            (0.0, 0.0),     # Zero
        ]
        for change_24h, change_7d in test_cases:
            result = analyzer.score_momentum(change_24h, change_7d)
            assert 0 <= result.score <= 100, f"Score {result.score} out of range"


# ─── Volume Profile Tests ─────────────────────────────────────

class TestVolumeProfile:
    """Test volume profile scoring factor."""
    
    def test_high_volume_ratio(self, analyzer):
        """High volume/market_cap ratio should score well."""
        result = analyzer.score_volume_profile(
            volume_24h=150_000_000, market_cap=1_000_000_000
        )
        assert result.name == "volume_profile"
        assert result.score >= 65, f"Expected score >= 65, got {result.score}"
    
    def test_low_volume_ratio(self, analyzer):
        """Very low volume/market_cap ratio should score lower."""
        result = analyzer.score_volume_profile(
            volume_24h=5_000_000, market_cap=1_000_000_000
        )
        assert result.score <= 50, f"Expected score <= 50, got {result.score}"
    
    def test_zero_market_cap(self, analyzer):
        """Zero market cap should return neutral."""
        result = analyzer.score_volume_profile(
            volume_24h=1_000_000, market_cap=0
        )
        assert result.score == 50.0
        assert result.signal == "neutral"


# ─── Trend Strength Tests ─────────────────────────────────────

class TestTrendStrength:
    """Test trend strength scoring factor."""
    
    def test_aligned_uptrend(self, analyzer):
        """Both timeframes positive = strong bullish trend."""
        result = analyzer.score_trend_strength(change_24h=5.0, change_7d=8.0)
        assert result.score > 60, f"Expected > 60, got {result.score}"
        assert result.signal == "bullish"
    
    def test_aligned_downtrend(self, analyzer):
        """Both timeframes negative = strong bearish trend."""
        result = analyzer.score_trend_strength(change_24h=-5.0, change_7d=-8.0)
        assert result.score < 40, f"Expected < 40, got {result.score}"
        assert result.signal == "bearish"
    
    def test_conflicting_signals(self, analyzer):
        """Opposite direction signals = weak/neutral trend."""
        result = analyzer.score_trend_strength(change_24h=5.0, change_7d=-5.0)
        # Conflicting signals produce score = 50 - divergence*2 = 30
        assert result.score <= 55, f"Expected < 55, got {result.score}"
        assert result.signal in ("neutral", "bearish")


# ─── Volatility Tests ─────────────────────────────────────────

class TestVolatility:
    """Test volatility scoring factor."""
    
    def test_low_volatility(self, analyzer):
        """Small price changes = low volatility."""
        result = analyzer.score_volatility(change_24h=0.5, change_7d=0.3)
        assert result.score < 40, f"Expected < 40, got {result.score}"
        assert result.signal == "bullish"  # Low vol = easier to trade
    
    def test_high_volatility(self, analyzer):
        """Large price changes = high volatility."""
        result = analyzer.score_volatility(change_24h=15.0, change_7d=20.0)
        assert result.score > 70, f"Expected > 70, got {result.score}"
        assert result.signal == "bearish"  # High vol = risky


# ─── Narrative Tests ──────────────────────────────────────────

class TestNarrative:
    """Test narrative momentum scoring factor."""
    
    def test_strong_narrative(self, analyzer):
        """High volume + positive momentum = strong narrative."""
        result = analyzer.score_narrative(
            change_24h=8.0, change_7d=12.0,
            volume_24h=500_000_000, market_cap=2_000_000_000
        )
        assert result.score >= 70, f"Expected >= 70, got {result.score}"
    
    def test_weak_narrative(self, analyzer):
        """Low volume = weak narrative."""
        result = analyzer.score_narrative(
            change_24h=0.0, change_7d=0.0,
            volume_24h=10_000_000, market_cap=10_000_000_000
        )
        assert result.score <= 55, f"Expected <= 55, got {result.score}"


# ─── Composite Score Tests ────────────────────────────────────

class TestCompositeScore:
    """Test composite score calculation and signal generation."""
    
    def test_bullish_composite(self, analyzer, strong_bullish_coin):
        """Strong bullish data should produce bullish composite."""
        result = analyzer.analyze_single(strong_bullish_coin)
        assert result.composite_score > 60, f"Expected > 60, got {result.composite_score}"
        assert result.composite_signal == "bullish"
    
    def test_bearish_composite(self, analyzer, strong_bearish_coin):
        """Strong bearish data should produce bearish composite."""
        result = analyzer.analyze_single(strong_bearish_coin)
        assert result.composite_score < 40, f"Expected < 40, got {result.composite_score}"
        assert result.composite_signal == "bearish"
    
    def test_neutral_composite(self, analyzer, neutral_coin):
        """Flat data should produce neutral composite."""
        result = analyzer.analyze_single(neutral_coin)
        assert 40 <= result.composite_score <= 60, f"Expected ~50, got {result.composite_score}"
        assert result.composite_signal == "neutral"
    
    def test_composite_score_range(self, analyzer, strong_bullish_coin):
        """Composite score should always be in [0, 100]."""
        result = analyzer.analyze_single(strong_bullish_coin)
        assert 0 <= result.composite_score <= 100
    
    def test_confidence_range(self, analyzer, strong_bullish_coin):
        """Confidence should be in [0, 1]."""
        result = analyzer.analyze_single(strong_bullish_coin)
        assert 0 <= result.confidence <= 1.0
    
    def test_analysis_to_dict(self, analyzer, strong_bullish_coin):
        """AnalysisResult.to_dict() should return valid dict."""
        result = analyzer.analyze_single(strong_bullish_coin)
        d = result.to_dict()
        assert "symbol" in d
        assert "factors" in d
        assert "composite_score" in d
        assert len(d["factors"]) == 5
    
    def test_analyze_multiple(self, analyzer, strong_bullish_coin, strong_bearish_coin):
        """Analyzing multiple coins should return sorted results."""
        results = analyzer.analyze([strong_bullish_coin, strong_bearish_coin])
        assert len(results) == 2
        # Should be sorted by composite score descending
        assert results[0].composite_score >= results[1].composite_score
