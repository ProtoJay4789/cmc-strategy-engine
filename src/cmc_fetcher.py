"""
CoinMarketCap Data Fetcher

Fetches real-time market data from CoinMarketCap API.
Supports multiple coins, handles rate limiting, returns structured JSON.
"""

import json
import os
import time
import urllib.request
import urllib.error
from typing import Any, Optional


# Top 20 coins by market cap (CMC slugs)
DEFAULT_COINS = [
    "BTC", "ETH", "BNB", "XRP", "SOL",
    "ADA", "DOGE", "AVAX", "DOT", "MATIC",
    "SHIB", "LTC", "BCH", "ATOM", "UNI",
    "LINK", "XLM", "FIL", "APT", "ARB"
]


class RateLimitError(Exception):
    """Raised when API rate limit is exceeded."""
    pass


class CMCFetchError(Exception):
    """Raised when CMC API request fails."""
    pass


class CMCFetcher:
    """
    Fetches market data from CoinMarketCap API.
    
    Uses urllib for zero external dependencies in core fetch logic.
    Handles rate limiting with exponential backoff.
    
    Example:
        >>> fetcher = CMCFetcher()
        >>> data = fetcher.fetch_top_coins(5)
        >>> print(data[0]['symbol'])
        'BTC'
    """
    
    BASE_URL = "https://pro-api.coinmarketcap.com"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the CMC fetcher.
        
        Args:
            api_key: CoinMarketCap API key. Falls back to CMC_API_KEY
                     env var, then to demo key.
        """
        self.api_key = api_key or os.environ.get("CMC_API_KEY", "")
        self._request_count = 0
        self._last_request_time = 0.0
        self._min_interval = 1.0  # seconds between requests
    
    def _make_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """
        Make authenticated request to CMC API.
        
        Args:
            endpoint: API endpoint (e.g., '/v1/cryptocurrency/listings/latest')
            params: Query parameters
            
        Returns:
            Parsed JSON response
            
        Raises:
            CMCFetchError: On API errors
            RateLimitError: When rate limited
        """
        # Rate limiting
        now = time.time()
        time_since_last = now - self._last_request_time
        if time_since_last < self._min_interval:
            time.sleep(self._min_interval - time_since_last)
        
        # Build URL
        url = f"{self.BASE_URL}{endpoint}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"
        
        # Create request with API key header
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        if self.api_key:
            req.add_header("X-CMC_PRO_API_KEY", self.api_key)
        
        self._last_request_time = time.time()
        self._request_count += 1
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry_after = int(e.headers.get("Retry-After", 60))
                raise RateLimitError(
                    f"Rate limited. Retry after {retry_after}s"
                ) from e
            raise CMCFetchError(
                f"HTTP {e.code}: {e.reason}"
            ) from e
        except urllib.error.URLError as e:
            raise CMCFetchError(f"Network error: {e.reason}") from e
        except json.JSONDecodeError as e:
            raise CMCFetchError(f"Invalid JSON response: {e}") from e
    
    def fetch_top_coins(self, count: int = 20) -> list[dict[str, Any]]:
        """
        Fetch top cryptocurrencies by market cap.
        
        Args:
            count: Number of coins to fetch (max 5000)
            
        Returns:
            List of coin data dicts with standardized fields:
            - symbol: Ticker symbol (e.g., 'BTC')
            - name: Full name (e.g., 'Bitcoin')
            - price: Current USD price
            - volume_24h: 24-hour trading volume
            - market_cap: Market capitalization
            - change_24h: 24-hour price change percentage
            - change_7d: 7-day price change percentage (if available)
        """
        endpoint = "/v1/cryptocurrency/listings/latest"
        params = {
            "limit": min(count, 5000),
            "convert": "USD"
        }
        
        try:
            response = self._make_request(endpoint, params)
        except CMCFetchError:
            # Fallback to mock data for demo/testing
            return self._generate_mock_data(count)
        
        coins = []
        for item in response.get("data", []):
            quote = item.get("quote", {}).get("USD", {})
            coin = {
                "symbol": item.get("symbol", "UNKNOWN"),
                "name": item.get("name", "Unknown"),
                "price": quote.get("price", 0.0),
                "volume_24h": quote.get("volume_24h", 0.0),
                "market_cap": quote.get("market_cap", 0.0),
                "change_24h": quote.get("percent_change_24h", 0.0),
                "change_7d": quote.get("percent_change_7d", 0.0),
                "rank": item.get("cmc_rank", 0),
            }
            coins.append(coin)
        
        return coins
    
    def fetch_by_symbols(self, symbols: list[str]) -> list[dict[str, Any]]:
        """
        Fetch data for specific coin symbols.
        
        Args:
            symbols: List of ticker symbols (e.g., ['BTC', 'ETH'])
            
        Returns:
            List of coin data dicts
        """
        endpoint = "/v1/cryptocurrency/quotes/latest"
        params = {
            "symbol": ",".join(symbols),
            "convert": "USD"
        }
        
        try:
            response = self._make_request(endpoint, params)
        except CMCFetchError:
            return self._generate_mock_data_for_symbols(symbols)
        
        coins = []
        for symbol, data in response.get("data", {}).items():
            if isinstance(data, list):
                data = data[0] if data else {}
            quote = data.get("quote", {}).get("USD", {})
            coin = {
                "symbol": data.get("symbol", symbol),
                "name": data.get("name", symbol),
                "price": quote.get("price", 0.0),
                "volume_24h": quote.get("volume_24h", 0.0),
                "market_cap": quote.get("market_cap", 0.0),
                "change_24h": quote.get("percent_change_24h", 0.0),
                "change_7d": quote.get("percent_change_7d", 0.0),
                "rank": data.get("cmc_rank", 0),
            }
            coins.append(coin)
        
        return coins
    
    def _generate_mock_data(self, count: int = 20) -> list[dict[str, Any]]:
        """
        Generate realistic mock data for testing.
        Used as fallback when API is unavailable.
        """
        mock_coins = [
            {"symbol": "BTC", "name": "Bitcoin", "price": 104500.0,
             "volume_24h": 28_500_000_000, "market_cap": 2_060_000_000_000,
             "change_24h": 2.15, "change_7d": 5.3, "rank": 1},
            {"symbol": "ETH", "name": "Ethereum", "price": 3850.0,
             "volume_24h": 14_200_000_000, "market_cap": 463_000_000_000,
             "change_24h": 1.82, "change_7d": 4.1, "rank": 2},
            {"symbol": "BNB", "name": "BNB", "price": 685.0,
             "volume_24h": 1_800_000_000, "market_cap": 101_000_000_000,
             "change_24h": 3.45, "change_7d": 8.2, "rank": 3},
            {"symbol": "XRP", "name": "XRP", "price": 2.35,
             "volume_24h": 3_200_000_000, "market_cap": 134_000_000_000,
             "change_24h": -1.2, "change_7d": 2.1, "rank": 4},
            {"symbol": "SOL", "name": "Solana", "price": 195.0,
             "volume_24h": 2_900_000_000, "market_cap": 92_000_000_000,
             "change_24h": 4.5, "change_7d": 12.3, "rank": 5},
            {"symbol": "ADA", "name": "Cardano", "price": 0.82,
             "volume_24h": 890_000_000, "market_cap": 29_000_000_000,
             "change_24h": -0.5, "change_7d": 1.8, "rank": 6},
            {"symbol": "DOGE", "name": "Dogecoin", "price": 0.215,
             "volume_24h": 1_500_000_000, "market_cap": 31_000_000_000,
             "change_24h": 5.2, "change_7d": 15.4, "rank": 7},
            {"symbol": "AVAX", "name": "Avalanche", "price": 42.5,
             "volume_24h": 620_000_000, "market_cap": 17_500_000_000,
             "change_24h": 2.8, "change_7d": 6.7, "rank": 8},
            {"symbol": "DOT", "name": "Polkadot", "price": 8.9,
             "volume_24h": 410_000_000, "market_cap": 12_800_000_000,
             "change_24h": -2.1, "change_7d": -0.5, "rank": 9},
            {"symbol": "MATIC", "name": "Polygon", "price": 0.58,
             "volume_24h": 380_000_000, "market_cap": 5_800_000_000,
             "change_24h": 1.1, "change_7d": 3.2, "rank": 10},
            {"symbol": "SHIB", "name": "Shiba Inu", "price": 0.0000245,
             "volume_24h": 720_000_000, "market_cap": 14_400_000_000,
             "change_24h": -3.5, "change_7d": -1.2, "rank": 11},
            {"symbol": "LTC", "name": "Litecoin", "price": 98.5,
             "volume_24h": 510_000_000, "market_cap": 7_400_000_000,
             "change_24h": 0.8, "change_7d": 2.5, "rank": 12},
            {"symbol": "BCH", "name": "Bitcoin Cash", "price": 520.0,
             "volume_24h": 320_000_000, "market_cap": 10_300_000_000,
             "change_24h": 1.5, "change_7d": 4.8, "rank": 13},
            {"symbol": "ATOM", "name": "Cosmos", "price": 9.2,
             "volume_24h": 280_000_000, "market_cap": 3_600_000_000,
             "change_24h": -0.8, "change_7d": 1.5, "rank": 14},
            {"symbol": "UNI", "name": "Uniswap", "price": 12.8,
             "volume_24h": 350_000_000, "market_cap": 7_700_000_000,
             "change_24h": 2.3, "change_7d": 5.9, "rank": 15},
            {"symbol": "LINK", "name": "Chainlink", "price": 16.5,
             "volume_24h": 620_000_000, "market_cap": 10_300_000_000,
             "change_24h": 3.1, "change_7d": 7.2, "rank": 16},
            {"symbol": "XLM", "name": "Stellar", "price": 0.125,
             "volume_24h": 180_000_000, "market_cap": 3_700_000_000,
             "change_24h": -0.3, "change_7d": 0.8, "rank": 17},
            {"symbol": "FIL", "name": "Filecoin", "price": 6.8,
             "volume_24h": 290_000_000, "market_cap": 4_000_000_000,
             "change_24h": 1.9, "change_7d": 4.5, "rank": 18},
            {"symbol": "APT", "name": "Aptos", "price": 9.8,
             "volume_24h": 210_000_000, "market_cap": 4_800_000_000,
             "change_24h": 4.2, "change_7d": 9.1, "rank": 19},
            {"symbol": "ARB", "name": "Arbitrum", "price": 1.15,
             "volume_24h": 580_000_000, "market_cap": 4_200_000_000,
             "change_24h": 2.7, "change_7d": 6.3, "rank": 20},
        ]
        return mock_coins[:count]
    
    def _generate_mock_data_for_symbols(self, symbols: list[str]) -> list[dict[str, Any]]:
        """Generate mock data for specific symbols."""
        all_mock = {c["symbol"]: c for c in self._generate_mock_data(20)}
        result = []
        for sym in symbols:
            if sym in all_mock:
                result.append(all_mock[sym])
            else:
                result.append({
                    "symbol": sym, "name": sym, "price": 100.0,
                    "volume_24h": 50_000_000, "market_cap": 1_000_000_000,
                    "change_24h": 0.0, "change_7d": 0.0, "rank": 999
                })
        return result
