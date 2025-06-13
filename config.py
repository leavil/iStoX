import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_KEY")
    ALPHA_VANTAGE_API_KEY_1 = os.getenv("ALPHA_VANTAGE_KEY_1")
    FINNHUB_API_KEY = "d15iqtpr01qhqto64c20d15iqtpr01qhqto64c2g"
    
    # Parámetros globales
    DEFAULT_START_DATE = "2020-01-01"
    RISK_FREE_RATE = 0.042  # Tasa libre de riesgo (ej: bono US 10y)