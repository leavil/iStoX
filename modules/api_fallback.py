# modules/api_fallback.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class APIFallbackManager:
    def __init__(self):
        self.api_keys = {
            'alphavantage': [os.getenv(f'ALPHA_VANTAGE_API_KEY_{i}') for i in range(1, 9)],
            'finnhub': [os.getenv("FINNHUB_API_KEY")],
            'tiingo': [os.getenv("TIINGO_API_KEY")],
            'polygon': [os.getenv("POLYGON_API_KEY_")],   # por ejemplo hasta 3 keys
            'finage': [os.getenv("FINAGE_API_KEY")],
            'quandl': [os.getenv("QUANDL_API_KEY")]
        }

    def fetch_data_with_fallback(self, url_template: str, provider: str):
        keys = self.api_keys.get(provider, [])
        if not keys:
            raise Exception(f"No API keys found for provider: {provider}")

        for api_key in keys:
            if not api_key:
                continue
            url = url_template.format(api_key=api_key)
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()

                    if self._is_rate_limited(data):
                        print(f"🔁 API key {api_key[:6]}... rate limited. Trying next...")
                        continue

                    if self._is_empty_response(provider, data):
                        print(f"🔁 API key {api_key[:6]}... respuesta vacía o inválida. Intentando siguiente...")
                        continue

                    print(f"✅ Datos obtenidos con API key {api_key[:6]} para {provider}")
                    return data

                elif response.status_code == 429:
                    print(f"🔁 Status 429 (rate limit) con clave {api_key[:6]}... Intentando siguiente...")
                    continue

                else:
                    print(f"⚠️ Status {response.status_code} con clave {api_key[:6]}... Intentando siguiente...")
                    continue

            except Exception as e:
                print(f"⚠️ Error con API key {api_key[:6]}: {e}")
                continue

        raise Exception(f"❌ Todas las claves fallaron para el proveedor '{provider}'.")

    def _is_rate_limited(self, data):
        data_str = str(data).lower()
        return any(keyword in data_str for keyword in [
            "rate limit", "too many requests", "exceeded", "note", "limit", "error"
        ])

    def _is_empty_response(self, provider, data):
        if provider == "alphavantage":
            return "Time Series (Daily)" not in data or not data["Time Series (Daily)"]
        elif provider == "polygon":
            return "results" not in data or not data["results"]
        elif provider == "finage":
            return "results" not in data or not data["results"]
        elif provider == "quandl":
            return "dataset" not in data or not data["dataset"].get("data")
        elif provider == "tiingo":
            return not isinstance(data, list) or len(data) == 0
        elif provider == "finnhub":
            # Esta no usa fetch_data_with_fallback en tu código actual, por eso se puede omitir
            return False
        return False

