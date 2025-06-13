import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from typing import Dict, Optional, Tuple
import joblib
import os
from datetime import datetime

class StockPricePredictor:
    def __init__(self, model_dir: str = 'ml_models'):
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        self.scaler = MinMaxScaler()
    
    def create_features(self, data: pd.DataFrame, window_size: int = 10) -> pd.DataFrame:
        """
        Crea características para el modelo de predicción.
        
        Args:
            data: DataFrame con datos históricos
            window_size: Tamaño de la ventana para características de series temporales
            
        Returns:
            DataFrame con características y objetivo
        """
        df = data.copy()
        
        # Crear características de series temporales
        for i in range(1, window_size + 1):
            df[f'lag_{i}'] = df['close'].shift(i)
        
        # Crear características estadísticas
        df['rolling_mean'] = df['close'].rolling(window=window_size).mean()
        df['rolling_std'] = df['close'].rolling(window=window_size).std()
        df['rolling_min'] = df['close'].rolling(window=window_size).min()
        df['rolling_max'] = df['close'].rolling(window=window_size).max()
        
        # Crear características de volatilidad
        df['daily_return'] = df['close'].pct_change()
        df['volatility'] = df['daily_return'].rolling(window=window_size).std()
        
        # Eliminar filas con NaN
        df.dropna(inplace=True)
        
        return df
    
    def train_model(self, ticker: str, data: pd.DataFrame, 
                    test_size: float = 0.2, window_size: int = 10,
                    save_model: bool = True) -> Dict:
        """
        Entrena un modelo para predecir precios de acciones.
        
        Args:
            ticker: Símbolo de la acción
            data: DataFrame con datos históricos
            test_size: Porcentaje de datos para prueba
            window_size: Tamaño de la ventana para características
            save_model: Si guardar el modelo entrenado
            
        Returns:
            Diccionario con métricas de evaluación y modelo
        """
        # Crear características
        feature_df = self.create_features(data, window_size)
        
        # Definir características (X) y objetivo (y)
        X = feature_df.drop(columns=['close'])
        y = feature_df['close']
        
        # Escalar características
        X_scaled = self.scaler.fit_transform(X)
        
        # Dividir en entrenamiento y prueba
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, shuffle=False
        )
        
        # Entrenar modelo
        model = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        
        # Evaluar modelo
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        # Guardar modelo si es necesario
        if save_model:
            model_path = os.path.join(
                self.model_dir, 
                f"{ticker}_model_{datetime.now().strftime('%Y%m%d')}.joblib"
            )
            joblib.dump(model, model_path)
            
            scaler_path = os.path.join(
                self.model_dir,
                f"{ticker}_scaler_{datetime.now().strftime('%Y%m%d')}.joblib"
            )
            joblib.dump(self.scaler, scaler_path)
        
        return {
            'model': model,
            'metrics': {
                'mae': mae,
                'rmse': rmse,
                'test_size': len(X_test)
            },
            'feature_importance': dict(zip(
                X.columns,
                model.feature_importances_
            ))
        }
    
    def predict_future_prices(self, ticker: str, model, 
                             last_known_data: pd.DataFrame,
                             days_to_predict: int = 5,
                             window_size: int = 10) -> pd.DataFrame:
        """
        Predice precios futuros usando el modelo entrenado.
        
        Args:
            ticker: Símbolo de la acción
            model: Modelo entrenado
            last_known_data: Últimos datos conocidos
            days_to_predict: Días a predecir
            window_size: Tamaño de la ventana usado en el entrenamiento
            
        Returns:
            DataFrame con predicciones
        """
        predictions = []
        current_data = last_known_data.copy()
        
        for _ in range(days_to_predict):
            # Crear características para el último punto de datos conocido
            feature_df = self.create_features(current_data, window_size)
            if feature_df.empty:
                break
                
            last_features = feature_df.iloc[[-1]].drop(columns=['close'])
            last_features_scaled = self.scaler.transform(last_features)
            
            # Hacer predicción
            pred_price = model.predict(last_features_scaled)[0]
            predictions.append(pred_price)
            
            # Actualizar datos con la predicción
            new_row = current_data.iloc[-1].copy()
            new_row['close'] = pred_price
            new_row.name = current_data.index[-1] + pd.Timedelta(days=1)
            current_data = pd.concat([current_data, pd.DataFrame([new_row])])
        
        # Crear DataFrame de resultados
        future_dates = pd.date_range(
            start=last_known_data.index[-1] + pd.Timedelta(days=1),
            periods=days_to_predict
        )
        
        return pd.DataFrame({
            'date': future_dates,
            'predicted_price': predictions[:len(future_dates)]
        }).set_index('date')
    
    def load_model(self, ticker: str, date: Optional[str] = None):
        """
        Carga un modelo previamente entrenado.
        
        Args:
            ticker: Símbolo de la acción
            date: Fecha del modelo (opcional, carga el más reciente)
            
        Returns:
            Tupla con (modelo, scaler) o None si no se encuentra
        """
        model_files = [
            f for f in os.listdir(self.model_dir) 
            if f.startswith(f"{ticker}_model") and f.endswith(".joblib")
        ]
        
        if not model_files:
            return None
        
        if date:
            model_file = f"{ticker}_model_{date}.joblib"
            scaler_file = f"{ticker}_scaler_{date}.joblib"
        else:
            # Ordenar por fecha y tomar el más reciente
            model_files.sort(reverse=True)
            model_file = model_files[0]
            scaler_file = model_file.replace("model", "scaler")
        
        model_path = os.path.join(self.model_dir, model_file)
        scaler_path = os.path.join(self.model_dir, scaler_file)
        
        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            return None
        
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        
        return model, scaler