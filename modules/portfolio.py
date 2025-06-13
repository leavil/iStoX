import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from modules.data_fetcher import DataFetcher

class PortfolioManager:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.portfolio = {}
        self.transactions = []
    
    def add_transaction(self, ticker: str, quantity: float, 
                       price: float, date: datetime, 
                       transaction_type: str = 'buy') -> None:
        """
        Añade una transacción al portafolio.
        
        Args:
            ticker: Símbolo de la acción
            quantity: Cantidad de acciones
            price: Precio por acción
            date: Fecha de la transacción
            transaction_type: Tipo de transacción ('buy' o 'sell')
        """
        self.transactions.append({
            'ticker': ticker,
            'quantity': quantity,
            'price': price,
            'date': date,
            'type': transaction_type
        })
        
        # Actualizar portafolio
        if ticker not in self.portfolio:
            self.portfolio[ticker] = {
                'quantity': 0,
                'avg_price': 0,
                'total_invested': 0
            }
        
        if transaction_type == 'buy':
            total_quantity = self.portfolio[ticker]['quantity'] + quantity
            total_invested = self.portfolio[ticker]['total_invested'] + (quantity * price)
            
            self.portfolio[ticker]['quantity'] = total_quantity
            self.portfolio[ticker]['total_invested'] = total_invested
            self.portfolio[ticker]['avg_price'] = total_invested / total_quantity
        
        elif transaction_type == 'sell':
            self.portfolio[ticker]['quantity'] -= quantity
            self.portfolio[ticker]['total_invested'] -= quantity * self.portfolio[ticker]['avg_price']
    
    def get_portfolio_value(self) -> Dict[str, float]:
        """
        Calcula el valor actual del portafolio.
        
        Returns:
            Diccionario con valor total y desglose por activo
        """
        total_value = 0.0
        breakdown = {}
        
        for ticker, data in self.portfolio.items():
            if data['quantity'] <= 0:
                continue
                
            current_price = self.data_fetcher.fetch_stock_data(ticker)['close'].iloc[-1]
            position_value = data['quantity'] * current_price
            breakdown[ticker] = {
                'quantity': data['quantity'],
                'avg_price': data['avg_price'],
                'current_price': current_price,
                'position_value': position_value,
                'pnl': position_value - data['total_invested'],
                'pnl_pct': (position_value / data['total_invested'] - 1) * 100
            }
            total_value += position_value
        
        return {
            'total_value': total_value,
            'breakdown': breakdown
        }
    
    def get_performance(self) -> pd.DataFrame:
        """
        Calcula el rendimiento histórico del portafolio.
        
        Returns:
            DataFrame con rendimiento a lo largo del tiempo
        """
        # Implementar lógica para calcular rendimiento histórico
        pass