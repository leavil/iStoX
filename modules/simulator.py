import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from modules.data_fetcher import DataFetcher

class TradingSimulator:
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}
        self.trade_history = []
        self.data_fetcher = DataFetcher()
    
    def execute_trade(self, ticker: str, quantity: float, 
                     price: float, date: datetime, 
                     trade_type: str = 'buy') -> bool:
        """
        Ejecuta una operación en el simulador.
        
        Args:
            ticker: Símbolo de la acción
            quantity: Cantidad de acciones
            price: Precio por acción
            date: Fecha de la operación
            trade_type: Tipo de operación ('buy' o 'sell')
            
        Returns:
            True si la operación fue exitosa, False si no
        """
        cost = quantity * price
        
        if trade_type == 'buy':
            if self.current_capital < cost:
                return False  # No hay suficiente capital
            
            self.current_capital -= cost
            
            if ticker in self.positions:
                self.positions[ticker]['quantity'] += quantity
                self.positions[ticker]['total_cost'] += cost
                self.positions[ticker]['avg_price'] = (
                    self.positions[ticker]['total_cost'] / 
                    self.positions[ticker]['quantity']
                )
            else:
                self.positions[ticker] = {
                    'quantity': quantity,
                    'avg_price': price,
                    'total_cost': cost
                }
        
        elif trade_type == 'sell':
            if ticker not in self.positions or self.positions[ticker]['quantity'] < quantity:
                return False  # No hay suficientes acciones para vender
            
            self.current_capital += cost
            self.positions[ticker]['quantity'] -= quantity
            self.positions[ticker]['total_cost'] -= quantity * self.positions[ticker]['avg_price']
            
            if self.positions[ticker]['quantity'] <= 0:
                del self.positions[ticker]
        
        # Registrar la operación en el historial
        self.trade_history.append({
            'date': date,
            'ticker': ticker,
            'type': trade_type,
            'quantity': quantity,
            'price': price,
            'cost': cost if trade_type == 'buy' else -cost
        })
        
        return True
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> Dict:
        """
        Calcula el valor actual del portafolio.
        
        Args:
            current_prices: Diccionario con precios actuales por ticker
            
        Returns:
            Diccionario con valor total y desglose por activo
        """
        total_value = self.current_capital
        breakdown = {}
        
        for ticker, position in self.positions.items():
            current_price = current_prices.get(ticker, 0.0)
            position_value = position['quantity'] * current_price
            breakdown[ticker] = {
                'quantity': position['quantity'],
                'avg_price': position['avg_price'],
                'current_price': current_price,
                'position_value': position_value,
                'pnl': position_value - position['total_cost'],
                'pnl_pct': (position_value / position['total_cost'] - 1) * 100
            }
            total_value += position_value
        
        return {
            'total_value': total_value,
            'cash': self.current_capital,
            'invested_value': total_value - self.current_capital,
            'pnl': total_value - self.initial_capital,
            'pnl_pct': (total_value / self.initial_capital - 1) * 100,
            'breakdown': breakdown
        }
    
    def backtest_strategy(self, strategy_function, 
                          ticker: str, start_date: datetime, 
                          end_date: datetime, **kwargs) -> pd.DataFrame:
        """
        Ejecuta un backtest de una estrategia de trading.
        
        Args:
            strategy_function: Función que implementa la estrategia
            ticker: Símbolo de la acción
            start_date: Fecha de inicio
            end_date: Fecha de fin
            **kwargs: Argumentos adicionales para la estrategia
            
        Returns:
            DataFrame con resultados del backtest
        """
        # Obtener datos históricos
        data = self.data_fetcher.fetch_stock_data(ticker, start_date, end_date)
        
        # Reiniciar simulador
        self.__init__(self.initial_capital)
        
        # Ejecutar estrategia día por día
        results = []
        for date, row in data.iterrows():
            signal = strategy_function(data[:date], **kwargs)
            
            if signal == 'buy' and self.current_capital >= row['close']:
                max_shares = int(self.current_capital // row['close'])
                if max_shares > 0:
                    self.execute_trade(
                        ticker, max_shares, row['close'], date, 'buy'
                    )
            elif signal == 'sell' and ticker in self.positions:
                self.execute_trade(
                    ticker, self.positions[ticker]['quantity'], 
                    row['close'], date, 'sell'
                )
            
            # Registrar resultados diarios
            current_value = self.get_portfolio_value({ticker: row['close']})
            results.append({
                'date': date,
                'signal': signal,
                'portfolio_value': current_value['total_value'],
                'cash': current_value['cash'],
                'shares': self.positions.get(ticker, {}).get('quantity', 0),
                'price': row['close']
            })
        
        return pd.DataFrame(results).set_index('date')