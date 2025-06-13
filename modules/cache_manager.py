# modules/cache_manager.py

import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta

CACHE_DB_PATH = os.path.join(os.path.dirname(__file__), '../cache/stock_data.db')

def init_cache():
    conn = sqlite3.connect(CACHE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_cache (
            ticker TEXT,
            data TEXT,
            last_updated TIMESTAMP,
            PRIMARY KEY (ticker)
        )
    ''')
    conn.commit()
    conn.close()

def save_to_cache(ticker, df):
    conn = sqlite3.connect(CACHE_DB_PATH)
    cursor = conn.cursor()
    df_str = df.to_json()
    now = datetime.now()
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
            return df
    return None
