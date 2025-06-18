import pandas as pd
from rapidfuzz import process, fuzz
import yfinance as yf

class TickerSearcher:
    def __init__(self, filepath="cache/tickers/symbols_valid_meta.csv"):
        self.filepath = filepath
        self.df = pd.read_csv(self.filepath)
        self.df = self.df[["Symbol", "Security Name"]].dropna()
        self.df.columns = ["Ticker", "Nombre"]
        self.df["Combo"] = self.df["Nombre"] + " (" + self.df["Ticker"] + ")"
        self.valid_tickers = set(self.df["Ticker"].values)

    def buscar(self, query):
        query = query.strip().upper()

        if not query:
            return self.df["Combo"].tolist()[:20]

        # Buscar coincidencias exactas que empiecen con la query en Ticker o Nombre
        mask_ticker = self.df["Ticker"].str.startswith(query)
        mask_nombre = self.df["Nombre"].str.upper().str.startswith(query)

        df_filtered = self.df[mask_ticker | mask_nombre]
        if not df_filtered.empty:
            return df_filtered["Combo"].tolist()[:20]

        # Si no hay coincidencias exactas al inicio, hacer búsqueda fuzzy
        combos = self.df["Combo"].tolist()
        resultados = process.extract(query, combos, scorer=fuzz.WRatio, limit=20)
        opciones = [r[0] for r in resultados if r[1] > 40]

        # Si no hay coincidencias fuzzy, intentar agregar ticker directo si existe en yfinance
        if not opciones and self.validar_ticker(query):
            nombre = self.obtener_nombre_desde_yfinance(query)
            if nombre:
                self.agregar_ticker_a_csv(query, nombre)
                return [f"{nombre} ({query})"]

        return opciones


    def validar_ticker(self, ticker):
        try:
            data = yf.Ticker(ticker).info
            return bool(data and "shortName" in data)
        except Exception:
            return False

    def obtener_nombre_desde_yfinance(self, ticker):
        try:
            data = yf.Ticker(ticker).info
            return data.get("shortName", "Unknown")
        except Exception:
            return None

    def agregar_ticker_a_csv(self, ticker, nombre="Unknown"):
        nuevo = pd.DataFrame([[ticker, nombre]], columns=["Ticker", "Nombre"])
        nuevo["Combo"] = nuevo["Nombre"] + " (" + nuevo["Ticker"] + ")"
        self.df = pd.concat([self.df, nuevo], ignore_index=True)
        self.df.to_csv(self.filepath, index=False)
        self.valid_tickers.add(ticker)
