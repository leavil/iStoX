from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime

class BrokerAPI(ABC):
    @abstractmethod
    def connect(self, api_key: str, account_id: Optional[str] = None) -> bool:
        """Conecta con la API del broker"""
        pass
    
    @abstractmethod
    def get_account_balance(self) -> Dict[str, float]:
        """Obtiene el balance de la cuenta"""
        pass
    
    @abstractmethod
    def get_positions(self) -> Dict[str, Dict]:
        """Obtiene las posiciones actuales"""
        pass
    
    @abstractmethod
    def get_historical_orders(self, days: int = 30) -> pd.DataFrame:
        """Obtiene el historial de órdenes"""
        pass
    
    @abstractmethod
    def place_order(self, ticker: str, quantity: float, 
                   order_type: str = 'market', 
                   side: str = 'buy', limit_price: Optional[float] = None) -> bool:
        """Coloca una orden"""
        pass

class AlpacaAPI(BrokerAPI):
    def __init__(self):
        self.connected = False
    
    def connect(self, api_key: str, account_id: Optional[str] = None) -> bool:
        """Conecta con la API de Alpaca"""
        try:
            # Implementar lógica de conexión real aquí
            self.api_key = api_key
            self.account_id = account_id
            self.connected = True
            return True
        except Exception:
            return False
    
    def get_account_balance(self) -> Dict[str, float]:
        """Obtiene el balance de la cuenta de Alpaca"""
        if not self.connected:
            raise Exception("No conectado a Alpaca")
        
        # Implementar lógica real aquí
        return {
            'cash': 10000.0,
            'portfolio_value': 15000.0,
            'buying_power': 20000.0
        }
    
    def get_positions(self) -> Dict[str, Dict]:
        """Obtiene las posiciones actuales de Alpaca"""
        if not self.connected:
            raise Exception("No conectado a Alpaca")
        
        # Implementar lógica real aquí
        return {
            'AAPL': {
                'quantity': 10,
                'avg_price': 150.0,
                'current_price': 170.0
            }
        }
    
    def get_historical_orders(self, days: int = 30) -> pd.DataFrame:
        """Obtiene el historial de órdenes de Alpaca"""
        if not self.connected:
            raise Exception("No conectado a Alpaca")
        
        # Implementar lógica real aquí
        data = {
            'date': [datetime.now() - timedelta(days=i) for i in range(days)],
            'ticker': ['AAPL', 'MSFT', 'GOOGL'][:days],
            'side': ['buy', 'sell'] * (days // 2),
            'quantity': [10, 5] * (days // 2),
            'price': [170.0, 250.0] * (days // 2)
        }
        
        return pd.DataFrame(data)
    
    def place_order(self, ticker: str, quantity: float, 
                   order_type: str = 'market', 
                   side: str = 'buy', limit_price: Optional[float] = None) -> bool:
        """Coloca una orden en Alpaca"""
        if not self.connected:
            raise Exception("No conectado a Alpaca")
        
        # Implementar lógica real aquí
        print(f"Orden {side} de {quantity} acciones de {ticker} a {order_type} order")
        return True

class BrokerManager:
    def __init__(self):
        self.brokers = {
            'alpaca': AlpacaAPI()
            # Agregar otros brokers aquí
        }
        self.active_broker = None
    
    def connect_broker(self, broker_name: str, api_key: str, 
                      account_id: Optional[str] = None) -> bool:
        """Conecta con un broker específico"""
        if broker_name not in self.brokers:
            raise ValueError(f"Broker no soportado: {broker_name}")
        
        self.active_broker = self.brokers[broker_name]
        return self.active_broker.connect(api_key, account_id)
    
    def get_account_balance(self) -> Dict[str, float]:
        """Obtiene el balance de la cuenta activa"""
        if not self.active_broker:
            raise Exception("Ningún broker conectado")
        
        return self.active_broker.get_account_balance()
    
    def sync_portfolio(self, portfolio_manager) -> bool:
        """Sincroniza el portafolio local con el broker"""
        if not self.active_broker:
            raise Exception("Ningún broker conectado")
        
        positions = self.active_broker.get_positions()
        
        for ticker, position in positions.items():
            portfolio_manager.add_transaction(
                ticker=ticker,
                quantity=position['quantity'],
                price=position['avg_price'],
                date=datetime.now(),
                transaction_type='buy'  # Asumimos que todas son compras por simplicidad
            )
        
        return True