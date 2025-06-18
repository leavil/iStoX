import os
import requests
import time
from dotenv import load_dotenv
from typing import Dict, Any, Optional

load_dotenv()

class APIFallbackManager:
    def __init__(self):
        self.api_keys = {
            'alphavantage': self._get_keys('ALPHA_VANTAGE_API_KEY', 8),
            'finnhub': [os.getenv("FINNHUB_API_KEY")],
            'tiingo': [os.getenv("TIINGO_API_KEY")],
            'polygon': [os.getenv("POLYGON_API_KEY")],
            'finage': [os.getenv("FINAGE_API_KEY")],
            'quandl': [os.getenv("QUANDL_API_KEY")]
        }
        self.last_request_time = {}
        self.request_delay = 0.2  # Delay between requests in seconds

    def _get_keys(self, base_name: str, count: int) -> list:
        """Get numbered API keys from environment variables"""
        return [os.getenv(f"{base_name}_{i+1}") for i in range(count) if os.getenv(f"{base_name}_{i+1}")]

    def fetch_data_with_fallback(self, url_template: str, provider: str) -> Optional[Dict[str, Any]]:
        """Fetch data with rate limit handling and automatic key rotation"""
        keys = self.api_keys.get(provider, [])
        if not keys:
            raise ValueError(f"No API keys configured for provider: {provider}")

        for api_key in keys:
            if not api_key:
                continue

            # Respect rate limits with delay between requests
            self._enforce_rate_limit(provider)

            url = url_template.format(api_key=api_key)
            try:
                response = requests.get(url)
                data = self._process_response(response, provider)

                if data is not None:
                    print(f"✅ Success with API key {api_key[:6]}... for {provider}")
                    return data

            except Exception as e:
                print(f"⚠️ Error with API key {api_key[:6]}...: {str(e)[:100]}")

        raise Exception(f"❌ All keys failed for provider '{provider}'")

    def _enforce_rate_limit(self, provider: str):
        """Ensure we don't exceed API rate limits"""
        now = time.time()
        last_time = self.last_request_time.get(provider, 0)
        
        if now - last_time < self.request_delay:
            time.sleep(self.request_delay - (now - last_time))
            
        self.last_request_time[provider] = time.time()

    def _process_response(self, response, provider: str) -> Optional[Dict[str, Any]]:
        """Process API response with provider-specific validation"""
        if response.status_code != 200:
            print(f"🔁 Status {response.status_code} with key {provider}")
            return None

        try:
            data = response.json()
            
            # Provider-specific validation
            if provider == "alphavantage":
                if "Note" in data or "Information" in data:
                    print(f"🔁 Rate limited for {provider}")
                    return None
                if not data.get("Time Series (Daily)", {}):
                    return None
                    
            elif provider == "polygon":
                if not data.get("results"):
                    return None
                    
            elif provider == "tiingo":
                if not isinstance(data, list):
                    return None
                    
            return data
            
        except ValueError:
            print(f"⚠️ Invalid JSON response from {provider}")
            return None