import pandas as pd

def validar_columnas(df):
    # Si el DataFrame está vacío o no tiene columnas válidas, se rechaza
    if df.empty:
        return False

    # Si columnas son tipo MultiIndex, validamos la existencia de 'Adj Close' o 'Close'
    if isinstance(df.columns, pd.MultiIndex):
        return any(col[0] in ['Adj Close', 'Close'] for col in df.columns)

    # Si columnas normales
    return any(col in ['Adj Close', 'Close'] for col in df.columns)
