# modules/fetcher.py

import os
import pandas as pd
import yfinance as yf
import datetime
import requests
from modules.cache_manager import load_from_cache, save_to_cache, init_cache, load_from_cache_yf, save_to_cache_yf
from modules.api_fallback import APIFallbackManager
from utils.utils import validar_columnas
from dotenv import load_dotenv
from typing import Optional, Dict, Any, Union, List, Tuple


class StockDataFetcher:
    def __init__(self, ticker: str):
        dotenv_path = os.path.join(os.path.dirname(__file__), '../.env')
        load_dotenv(dotenv_path)
        init_cache()
        self.fallback = APIFallbackManager()
        self.ticker = ticker.upper()
        self.yf_ticker = yf.Ticker(self.ticker)
        
        # List of price data providers and their methods
        self.price_providers = [
            ("YFinance", self._get_price_data_yfinance),
            ("Alpha Vantage", self._get_price_data_alphavantage),
            ("Finnhub", self._get_price_data_finnhub),
            ("Tiingo", self._get_price_data_tiingo),
            ("Polygon", self._get_price_data_polygon),
            ("Finage", self._get_price_data_finage),
            ("Quandl", self._get_price_data_quandl),
        ]
        
        # List of fundamental data providers and their methods
        self.fundamental_providers = [
            ("YFinance", self._get_fundamental_data_yfinance),
            ("Alpha Vantage", self._get_fundamental_data_alphavantage),
            ("Finnhub", self._get_fundamental_data_finnhub),
            ("Tiingo", self._get_fundamental_data_tiingo),
            ("Polygon", self._get_fundamental_data_polygon),
            ("Finage", self._get_fundamental_data_finage),
            ("Quandl", self._get_fundamental_data_quandl),
        ]

    # Public methods
    def get_price_data(self, start: Optional[str] = None, end: Optional[str] = None) -> pd.DataFrame:
        """Fetch price data from various sources with caching and fallback mechanism."""
        end = end or datetime.date.today().strftime("%Y-%m-%d")
        
        # Try loading from YFinance JSON cache
        df = self._try_load_from_cache(self.ticker, load_from_cache_yf, "YFinance JSON")
        if df is not None:
            return df
            
        # Try loading from SQLite cache
        df = self._try_load_from_cache(self.ticker, load_from_cache, "SQLite")
        if df is not None:
            return df
            
        # Try providers in order
        for provider_name, provider_func in self.price_providers:
            df = self._try_provider(provider_name, provider_func, start, end)
            if df is not None:
                return df
                
        print(f"❌ All providers failed for ticker {self.ticker}.")
        return pd.DataFrame()

    def get_fundamental_data(self) -> Dict[str, Any]:
        """Fetch fundamental data from various sources."""
        for provider_name, provider_func in self.fundamental_providers:
            try:
                print(f"🔄 Trying to get fundamental data from {provider_name}...")
                data = provider_func()
                if data:
                    print(f"✅ Fundamental data successfully obtained with {provider_name} for {self.ticker}")
                    return data
            except Exception as e:
                print(f"❌ {provider_name} failed: {e}")
        
        print(f"❌ All fundamental data providers failed for ticker {self.ticker}.")
        return {}

    # Helper methods
    def _try_load_from_cache(self, ticker: str, cache_func, cache_name: str) -> Optional[pd.DataFrame]:
        """Helper to try loading data from cache."""
        cached_df = cache_func(ticker)
        if cached_df is not None:
            if validar_columnas(cached_df):
                print(f"✅ Data loaded from {cache_name} cache for {ticker}")
                return cached_df
            print(f"⚠️ Data loaded from {cache_name} cache for {ticker}, but without useful columns. Ignoring.")
        return None

    def _try_provider(self, provider_name: str, provider_func, start: Optional[str], end: str) -> Optional[pd.DataFrame]:
        """Try to fetch data from a provider."""
        try:
            print(f"🔄 Trying to get data from {provider_name}...")
            df = provider_func(start, end)
            if df is not None and not df.empty and validar_columnas(df):
                print(f"✅ Data successfully obtained with {provider_name} for {self.ticker}")
                save_to_cache(self.ticker, df)
                save_to_cache_yf(self.ticker, df)
                return df
            print(f"⚠️ {provider_name} returned empty DataFrame or without valid columns.")
        except Exception as e:
            print(f"❌ {provider_name} failed: {e}")
        return None

    # Price data providers
    def _get_price_data_yfinance(self, start: Optional[str], end: str) -> Optional[pd.DataFrame]:
        """Try to fetch price data from yfinance."""
        try:
            df = yf.download(self.ticker, start=start, end=end, auto_adjust=False)
            if not df.empty and validar_columnas(df):
                return df
        except Exception as e:
            print(f"⚠️ Error with yfinance: {e}")
        return None

    def _get_price_data_alphavantage(self, start: str, end: str) -> Optional[pd.DataFrame]:
        """Fetch price data from Alpha Vantage."""
        token = self._get_api_key("ALPHAVANTAGE_API_KEY")
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={self.ticker}&outputsize=full&apikey={token}"
        data = self._fetch_json(url)
        return self._process_alphavantage_data(data, start, end)

    def _get_price_data_finnhub(self, start: str, end: str) -> pd.DataFrame:
        """Fetch price data from Finnhub."""
        token = self._get_api_key("FINNHUB_API_KEY")
        start_unix = int(pd.Timestamp(start).timestamp())
        end_unix = int(pd.Timestamp(end).timestamp())

        url = f"https://finnhub.io/api/v1/stock/candle?symbol={self.ticker}&resolution=D&from={start_unix}&to={end_unix}&token={token}"
        data = self._fetch_json(url)
        
        if data.get("s") != "ok":
            raise Exception("❌ Finnhub didn't return valid data.")

        return pd.DataFrame({
            "Adj Close": data["c"],
            "Date": pd.to_datetime(data["t"], unit="s")
        }).set_index("Date")

    def _get_price_data_tiingo(self, start: str, end: str) -> pd.DataFrame:
        """Fetch price data from Tiingo."""
        token = self._get_api_key("TIINGO_API_KEY")
        url = f"https://api.tiingo.com/tiingo/daily/{self.ticker}/prices?startDate={start}&endDate={end}&token={token}"
        data = self._fetch_json(url)
        
        if not isinstance(data, list):
            raise Exception("❌ Tiingo didn't return price list.")

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index("date").rename(columns={"adjClose": "Adj Close"})

    def _get_price_data_polygon(self, start: str, end: str) -> pd.DataFrame:
        """Fetch price data from Polygon."""
        token = self._get_api_key("POLYGON_API_KEY")
        url = f"https://api.polygon.io/v2/aggs/ticker/{self.ticker}/range/1/day/{start}/{end}?adjusted=true&sort=asc&limit=5000&apiKey={token}"
        data = self._fetch_json(url)

        if "results" not in data:
            raise Exception("❌ Polygon didn't return results.")

        df = pd.DataFrame(data["results"])
        df["t"] = pd.to_datetime(df["t"], unit="ms")
        return df.set_index("t").rename(columns={"c": "Adj Close"})

    def _get_price_data_finage(self, start: str, end: str) -> pd.DataFrame:
        """Fetch price data from Finage."""
        token = self._get_api_key("FINAGE_API_KEY")
        url = f"https://api.finage.co.uk/history/stock/{self.ticker}?from={start}&to={end}&apikey={token}"
        data = self._fetch_json(url)

        if "results" not in data:
            raise Exception("❌ Finage didn't return results.")

        df = pd.DataFrame(data["results"])
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index("date").rename(columns={"close": "Adj Close"})

    def _get_price_data_quandl(self, start: str, end: str) -> pd.DataFrame:
        """Fetch price data from Quandl."""
        token = self._get_api_key("QUANDL_API_KEY")
        url = f"https://www.quandl.com/api/v3/datasets/WIKI/{self.ticker}.json?start_date={start}&end_date={end}&api_key={token}"
        data = self._fetch_json(url)

        dataset = data.get("dataset")
        if not dataset:
            raise Exception("❌ Quandl didn't return data.")

        df = pd.DataFrame(dataset["data"], columns=dataset["column_names"])
        df["Date"] = pd.to_datetime(df["Date"])
        return df.set_index("Date").rename(columns={"Adj. Close": "Adj Close"})

    # Fundamental data providers
    def _get_fundamental_data_yfinance(self) -> Optional[Dict[str, Any]]:
        """Fetch fundamental data from Yahoo Finance."""
        try:
            info = self.yf_ticker.get_info()
            if not info or 'regularMarketPrice' not in info:
                raise ValueError(f"Ticker {self.ticker} not found or delisted in Yahoo Finance")

            income_stmt = self._get_statement_data(self.yf_ticker.income_stmt)
            cashflow_stmt = self._get_statement_data(self.yf_ticker.cashflow)
            
            return {
                "name": info.get("longName", self.ticker),
                "sector": info.get("sector", "N/A"),
                "price": info.get("currentPrice"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "dividend_yield": info.get("dividendYield"),
                "roe": info.get("returnOnEquity"),
                "roic": info.get("returnOnAssets"),  # ROIC proxy
                "beta": info.get("beta"),
                "eps_forward": info.get("forwardEps"),
                "analyst_target_price": info.get("targetMeanPrice"),
                "recommendation": info.get("recommendationKey", "N/A").capitalize(),
                "revenue": self._extract_statement_value(income_stmt, ["Total Revenue"]),
                "net_income": self._extract_statement_value(income_stmt, ["Net Income"]),
                "ebitda": self._extract_statement_value(income_stmt, ["EBITDA"]),
                "free_cash_flow": self._extract_statement_value(cashflow_stmt, 
                    ['Free Cash Flow', 'FreeCashFlow', 'Operating Cash Flow', 'Total Cash From Operating Activities'])
            }
        except Exception as e:
            print(f"❌ Error getting YFinance fundamental data for {self.ticker}: {e}")
            return None

    def _get_fundamental_data_alphavantage(self) -> Dict[str, Optional[float]]:
        """Fetch fundamental data from Alpha Vantage."""
        try:
            # Try both OVERVIEW and EARNINGS endpoints
            overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={self.ticker}&apikey={{api_key}}"
            earnings_url = f"https://www.alphavantage.co/query?function=EARNINGS&symbol={self.ticker}&apikey={{api_key}}"
            
            overview_data = self.fallback.fetch_data_with_fallback(overview_url, "alphavantage")
            earnings_data = self.fallback.fetch_data_with_fallback(earnings_url, "alphavantage")
            
            return self._combine_alpha_vantage_data(overview_data, earnings_data)
        except Exception as e:
            print(f"Alpha Vantage error: {e}")
            return {}

    def _get_fundamental_data_finnhub(self) -> Dict[str, Any]:
        """Fetch fundamental data from Finnhub."""
        token = self._get_api_key("FINNHUB_API_KEY")
        endpoint = f"https://finnhub.io/api/v1/stock/profile2?symbol={self.ticker}&token={token}"
        data = self._fetch_json(endpoint)
        
        if not data or "ticker" not in data:
            raise Exception("Data not found in Finnhub.")
            
        return {
            "name": data.get("name", self.ticker),
            "sector": data.get("finnhubIndustry", "N/A"),
            "market_cap": data.get("marketCapitalization"),
            "pe_ratio": None,
            "pb_ratio": None,
            "ev_ebitda": None,
            "dividend_yield": None
        }

    def _get_fundamental_data_tiingo(self) -> Dict[str, Any]:
        """Fetch fundamental data from Tiingo."""
        token = self._get_api_key("TIINGO_API_KEY")
        endpoint = f"https://api.tiingo.com/tiingo/daily/{self.ticker}/stats?token={token}"
        data = self._fetch_json(endpoint)
        
        if not data or "lastDividend" not in data:
            raise Exception("Data not found in Tiingo.")
            
        return {
            "trailingEps": data.get("eps"),
            "pe_ratio": data.get("peRatio"),
            "priceToBook": data.get("priceToBook"),
            "dividendRate": data.get("lastDividend"),
        }

    def _get_fundamental_data_polygon(self) -> Dict[str, Any]:
        """Fetch fundamental data from Polygon."""
        token = self._get_api_key("POLYGON_API_KEY")
        endpoint = f"https://api.polygon.io/v3/reference/tickers/{self.ticker}?apiKey={token}"
        data = self._fetch_json(endpoint)
        
        if not data or "results" not in data:
            raise Exception("Data not found in Polygon.")
            
        return {
            "name": data["results"].get("name", self.ticker),
            "sector": data["results"].get("sic_description", "N/A"),
            "market_cap": data["results"].get("market_cap"),
        }

    def _get_fundamental_data_finage(self) -> Dict[str, Any]:
        """Fetch fundamental data from Finage."""
        token = self._get_api_key("FINAGE_API_KEY")
        endpoint = f"https://api.finage.co.uk/stock/profile2?symbol={self.ticker}&apikey={token}"
        data = self._fetch_json(endpoint)
        
        if not data or "symbol" not in data:
            raise Exception("Data not found in Finage.")
            
        return {
            "name": data.get("name", self.ticker),
            "sector": data.get("industry", "N/A"),
            "market_cap": data.get("marketCapitalization"),
        }

    def _get_fundamental_data_quandl(self) -> Dict[str, Any]:
        """Fetch fundamental data from Quandl."""
        token = self._get_api_key("QUANDL_API_KEY")
        endpoint = f"https://www.quandl.com/api/v3/datasets/WIKI/{self.ticker}.json?api_key={token}"
        data = self._fetch_json(endpoint)
        
        if not data or "dataset" not in data:
            raise Exception("Data not found in Quandl.")
            
        return {
            "name": data["dataset"].get("name", self.ticker),
            "sector": "N/A",  # Quandl doesn't provide sector info
        }

    # Common processing methods
    def _process_alphavantage_data(self, data: Dict, start: str, end: str) -> pd.DataFrame:
        ts = data.get("Time Series (Daily)", {})
        if not ts:
            raise Exception("❌ No data found in Alpha Vantage.")

        df = pd.DataFrame.from_dict(ts, orient="index", dtype=float)
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        df = df.loc[(df.index >= start) & (df.index <= end)]
        df.rename(columns={"5. adjusted close": "Adj Close"}, inplace=True)
        return df

    def _combine_alpha_vantage_data(self, overview: Dict, earnings: Dict) -> Dict[str, Optional[float]]:
        """Combine data from multiple Alpha Vantage endpoints"""
        def safe_float(val: Any) -> Optional[float]:
            try:
                return float(val) if val and str(val).replace('.','').isdigit() else None
            except (ValueError, AttributeError):
                return None

        combined = {
            "trailingEps": safe_float(overview.get("EPS")),
            "freeCashflow": safe_float(overview.get("FreeCashflow")),
            "dividendRate": safe_float(overview.get("DividendPerShare")),
            "trailingPE": safe_float(overview.get("PERatio")),
            "priceToBook": safe_float(overview.get("PriceToBookRatio")),
            "priceToSalesTrailing12Months": safe_float(overview.get("PriceToSalesRatioTTM")),
            "enterpriseToEbitda": safe_float(overview.get("EVToEBITDA")),
            "sharesOutstanding": safe_float(overview.get("SharesOutstanding")),
            "marketCap": safe_float(overview.get("MarketCapitalization")),
        }
        
        # Add earnings data if available
        if earnings and isinstance(earnings.get("quarterlyEarnings"), list):
            latest_quarter = earnings["quarterlyEarnings"][0] if earnings["quarterlyEarnings"] else {}
            combined["reportedEPS"] = safe_float(latest_quarter.get("reportedEPS"))
            
        return combined

    def _get_statement_data(self, statement: Union[pd.DataFrame, Any]) -> pd.DataFrame:
        """Convert statement to DataFrame if not already."""
        return statement if isinstance(statement, pd.DataFrame) else pd.DataFrame()

    def _extract_statement_value(self, statement: pd.DataFrame, possible_keys: List[str]) -> Optional[Any]:
        """Extract value from statement using possible keys."""
        for key in possible_keys:
            if key in statement.index:
                return statement.loc[key]
        return None

    def _get_api_key(self, key_name: str) -> str:
        """Get API key from environment variables."""
        token = os.getenv(key_name)
        if not token:
            raise Exception(f"{key_name} not found.")
        return token

    def _fetch_json(self, url: str) -> Any:
        """Fetch JSON data from URL."""
        response = requests.get(url)
        response.raise_for_status()
        return response.json()