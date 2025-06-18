# modules/cache_manager.py

import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta

CACHE_DB_PATH = os.path.join(os.path.dirname(__file__), '../cache/stock_data.db')
YF_CACHE_DIR = os.path.join(os.path.dirname(__file__), '../cache/yfinance_cache')

os.makedirs(YF_CACHE_DIR, exist_ok=True)  # Asegurar que la carpeta exista

def init_cache():
    conn = sqlite3.connect(CACHE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_cache (
            ticker TEXT PRIMARY KEY,
            data TEXT,
            last_updated TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_to_cache(ticker, df):
    conn = sqlite3.connect(CACHE_DB_PATH)
    cursor = conn.cursor()
    df_str = df.to_json(date_format='iso')  
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT OR REPLACE INTO stock_cache (ticker, data, last_updated)
        VALUES (?, ?, ?)
    ''', (ticker.upper(), df_str, now))
    conn.commit()
    conn.close()

def load_from_cache(ticker, max_age_minutes=30):
    conn = sqlite3.connect(CACHE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT data, last_updated FROM stock_cache WHERE ticker = ?
    ''', (ticker.upper(),))
    row = cursor.fetchone()
    conn.close()

    if row:
        data_json, last_updated = row
        last_updated = datetime.fromisoformat(last_updated)
        if datetime.now() - last_updated < timedelta(minutes=max_age_minutes):
            df = pd.read_json(data_json)
            df.index = pd.to_datetime(df.index)  # Asegurar índice datetime
            return df
    return None

def save_to_cache_yf(ticker, df):
    cache_path = os.path.join(YF_CACHE_DIR, f"{ticker.upper()}.json")
    df.to_json(cache_path, date_format='iso')

def load_from_cache_yf(ticker):
    cache_path = os.path.join(YF_CACHE_DIR, f"{ticker.upper()}.json")
    if os.path.exists(cache_path):
        df = pd.read_json(cache_path)
        df.index = pd.to_datetime(df.index)
        return df
    return None
