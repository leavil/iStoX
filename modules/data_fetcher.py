# modules/data_fetcher.py

import yfinance as yf
import pandas as pd
from modules.api_fallback import APIFallbackManager
import datetime
import os
import requests
from modules.cache_manager import load_from_cache, save_to_cache, init_cache

dotenv_path = os.path.join(os.path.dirname(__file__), '../.env')
from dotenv import load_dotenv
load_dotenv(dotenv_path)
 
fallback = APIFallbackManager()
init_cache()

def get_stock_data(ticker, start="2020-01-01", end=None):
    end = end or datetime.date.today().strftime("%Y-%m-%d")

    # 0. Intentar cargar desde caché
    cached_df = load_from_cache(ticker)
    if cached_df is not None:
        print(f"✅ Datos cargados desde caché para {ticker}")
        return cached_df

    # 1. Intentar con yfinance
    try:
        print(f"🟢 Usando yfinance para {ticker}")
        df = yf.download(ticker, start=start, end=end)
        if not df.empty:
            print(f"✅ Datos obtenidos exitosamente con yfinance para {ticker}")
            save_to_cache(ticker, df)  # Guardar en caché
            return df
        else:
            print("⚠️ yfinance devolvió un DataFrame vacío. Usando fallback.")
    except Exception as e:
        print(f"⚠️ Error con yfinance: {e}")

    # 2. Fallback en cascada entre proveedores con nombre para log
    proveedores = [
        ("Alpha Vantage", get_data_alphavantage),
        ("Finnhub", get_data_finnhub),
        ("Tiingo", get_data_tiingo),
        ("Polygon", get_data_polygon),
        ("Finage", get_data_finage),
        ("Quandl", get_data_quandl),
    ]

    for nombre, proveedor_func in proveedores:
        try:
            print(f"🔄 Intentando obtener datos desde {nombre}...")
            df = proveedor_func(ticker, start, end)
            if df is not None and not df.empty:
                print(f"✅ Datos obtenidos exitosamente con {nombre} para {ticker}")
                save_to_cache(ticker, df)  # Guardar en caché
                return df
            else:
                print(f"⚠️ {nombre} devolvió un DataFrame vacío. Probando siguiente proveedor...")
        except Exception as e:
            print(f"❌ {nombre} falló: {e}")

    print(f"❌ Todos los proveedores fallaron para el ticker {ticker}.")
    return pd.DataFrame()


### 🔻 FUNCIONES PARA CADA PROVEEDOR

def get_data_alphavantage(ticker, start, end):
    function = "TIME_SERIES_DAILY_ADJUSTED"
    url_template = f"https://www.alphavantage.co/query?function={function}&symbol={ticker}&outputsize=full&apikey={{api_key}}"
    data = fallback.fetch_data_with_fallback(url_template, "alphavantage")

    ts = data.get("Time Series (Daily)", {})
    if not ts:
        raise Exception("❌ No se encontraron datos en Alpha Vantage.")

    df = pd.DataFrame.from_dict(ts, orient="index", dtype=float)
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    df = df.loc[(df.index >= start) & (df.index <= end)]
    df.rename(columns={"5. adjusted close": "Adj Close"}, inplace=True)
    return df


def get_data_finnhub(ticker, start, end):
    import time
    token = os.getenv("FINNHUB_API_KEY")
    if not token:
        raise Exception("FINNHUB_API_KEY no encontrada.")

    start_unix = int(pd.Timestamp(start).timestamp())
    end_unix = int(pd.Timestamp(end).timestamp())

    url = f"https://finnhub.io/api/v1/stock/candle?symbol={ticker}&resolution=D&from={start_unix}&to={end_unix}&token={token}"
    r = requests.get(url)
    data = r.json()

    if data.get("s") != "ok":
        raise Exception("❌ Finnhub no devolvió datos válidos.")

    df = pd.DataFrame({
        "Adj Close": data["c"],
        "Date": pd.to_datetime(data["t"], unit="s")
    })
    df.set_index("Date", inplace=True)
    return df


def get_data_tiingo(ticker, start, end):
    token = os.getenv("TIINGO_API_KEY")
    url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices?startDate={start}&endDate={end}&token={token}"
    r = requests.get(url)
    data = r.json()
    if not isinstance(data, list):
        raise Exception("❌ Tiingo no devolvió lista de precios.")

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    df.rename(columns={"adjClose": "Adj Close"}, inplace=True)
    return df


def get_data_polygon(ticker, start, end):
    token = os.getenv("POLYGON_API_KEY")
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}?adjusted=true&sort=asc&limit=5000&apiKey={token}"
    r = requests.get(url)
    data = r.json()

    if "results" not in data:
        raise Exception("❌ Polygon no devolvió resultados.")

    df = pd.DataFrame(data["results"])
    df["t"] = pd.to_datetime(df["t"], unit="ms")
    df.set_index("t", inplace=True)
    df.rename(columns={"c": "Adj Close"}, inplace=True)
    return df


def get_data_finage(ticker, start, end):
    token = os.getenv("FINAGE_API_KEY")
    url = f"https://api.finage.co.uk/history/stock/{ticker}?from={start}&to={end}&apikey={token}"
    r = requests.get(url)
    data = r.json()

    if "results" not in data:
        raise Exception("❌ Finage no devolvió resultados.")

    df = pd.DataFrame(data["results"])
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    df.rename(columns={"close": "Adj Close"}, inplace=True)
    return df


def get_data_quandl(ticker, start, end):
    token = os.getenv("QUANDL_API_KEY")
    url = f"https://www.quandl.com/api/v3/datasets/WIKI/{ticker}.json?start_date={start}&end_date={end}&api_key={token}"
    r = requests.get(url)
    data = r.json()

    dataset = data.get("dataset")
    if not dataset:
        raise Exception("❌ Quandl no devolvió datos.")

    df = pd.DataFrame(dataset["data"], columns=dataset["column_names"])
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date", inplace=True)
    df.rename(columns={"Adj. Close": "Adj Close"}, inplace=True)
    return df
