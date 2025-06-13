import pandas as pd
import numpy as np
from typing import Dict, List
from modules.data_fetcher import DataFetcher

class RiskAnalyzer:
    def __init__(self):
        self.data_fetcher = DataFetcher()
    
    def calculate_volatility(self, ticker: str, window: int = 252) -> float:
        """
        Calcula la volatilidad anualizada de una acción.
        
        Args:
            ticker: Símbolo de la acción
            window: Número de días para cálculo (por defecto 252 días de trading)
            
        Returns:
            Volatilidad anualizada como porcentaje
        """
        data = self.data_fetcher.fetch_stock_data(ticker)
        returns = data['close'].pct_change().dropna()
        return returns.std() * np.sqrt(window) * 100
    
    def calculate_beta(self, ticker: str, benchmark: str = '^GSPC', 
                      window: int = 252) -> float:
        """
        Calcula el beta de una acción respecto a un benchmark.
        
        Args:
            ticker: Símbolo de la acción
            benchmark: Símbolo del benchmark (por defecto S&P 500)
            window: Número de días para cálculo
            
        Returns:
            Valor de beta
        """
        stock_data = self.data_fetcher.fetch_stock_data(ticker)
        benchmark_data = self.data_fetcher.fetch_stock_data(benchmark)
        
        merged = pd.merge(
            stock_data['close'].pct_change().dropna(),
            benchmark_data['close'].pct_change().dropna(),
            left_index=True,
            right_index=True,
            suffixes=('_stock', '_benchmark')
        )
        
        cov_matrix = merged.cov()
        beta = cov_matrix.iloc[0, 1] / merged['close_benchmark'].var()
        
        return beta
    
    def analyze_portfolio_risk(self, portfolio: Dict[str, float]) -> Dict:
        """
        Analiza el riesgo de un portafolio.
        
        Args:
            portfolio: Diccionario con tickers y pesos (ej: {'AAPL': 0.5, 'MSFT': 0.5})
            
        Returns:
            Diccionario con métricas de riesgo
        """
        # Obtener datos para todos los activos en el portafolio
        returns_data = {}
        for ticker in portfolio.keys():
            data = self.data_fetcher.fetch_stock_data(ticker)
            returns_data[ticker] = data['close'].pct_change().dropna()
        
        # Crear DataFrame de retornos
        returns_df = pd.DataFrame(returns_data)
        
        # Calcular matriz de covarianza
        cov_matrix = returns_df.cov() * 252  # Anualizar
        
        # Calcular volatilidad del portafolio
        weights = np.array(list(portfolio.values()))
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * 100
        
        # Calcular Value at Risk (VaR) histórico al 95%
        portfolio_returns = (returns_df * weights).sum(axis=1)
        var_95 = np.percentile(portfolio_returns, 5) * 100
        
        return {
            'portfolio_volatility': portfolio_volatility,
            'var_95': var_95,
            'covariance_matrix': cov_matrix,
            'individual_volatilities': {ticker: self.calculate_volatility(ticker) for ticker in portfolio},
            'individual_betas': {ticker: self.calculate_beta(ticker) for ticker in portfolio}
        }
    def calculate_sharpe_ratio(self, ticker: str, risk_free_rate: float = 0.01, window: int = 252) -> float:
        """        Calcula el ratio de Sharpe de una acción.
        Args:
            ticker: Símbolo de la acción
            risk_free_rate: Tasa libre de riesgo (por defecto 1%)
            window: Número de días para cálculo (por defecto 252 días de trading)
        Returns:
            Ratio de Sharpe como un valor numérico
        """
        data = self.data_fetcher.fetch_stock_data(ticker)
        returns = data['close'].pct_change().dropna()
        
        excess_returns = returns - risk_free_rate / window
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(window)
        
        return sharpe_ratio
    def calculate_max_drawdown(self, ticker: str) -> float:
        """        Calcula el drawdown máximo de una acción.
        Args:
            ticker: Símbolo de la acción        
        Returns:
            Drawdown máximo como un porcentaje
        """
        data = self.data_fetcher.fetch_stock_data(ticker)
        cumulative_returns = (1 + data['close'].pct_change()).cumprod()
        peak = cumulative_returns.cummax()
        drawdown = (cumulative_returns - peak) / peak
        
        return drawdown.min() * 100
    