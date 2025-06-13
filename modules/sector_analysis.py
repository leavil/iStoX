
import pandas as pd
from typing import Dict, List, Optional
from modules.data_fetcher import DataFetcher

class SectorAnalyzer:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.sector_mapping = {
            'Technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'],
            'Financial': ['JPM', 'BAC', 'GS', 'C', 'MS'],
            'Healthcare': ['PFE', 'JNJ', 'UNH', 'MRK', 'ABT']
            # Agregar más sectores y tickers
        }
    
    def get_sector_performance(self, sector: str, days: int = 30) -> Dict:
        """
        Calcula el rendimiento de un sector.
        
        Args:
            sector: Nombre del sector
            days: Número de días para el análisis
            
        Returns:
            Diccionario con métricas de rendimiento del sector
        """
        if sector not in self.sector_mapping:
            raise ValueError(f"Sector no válido: {sector}")
        
        tickers = self.sector_mapping[sector]
        performance = {}
        
        for ticker in tickers:
            try:
                data = self.data_fetcher.fetch_stock_data(ticker)
                if len(data) >= days:
                    start_price = data['close'].iloc[-days]
                    end_price = data['close'].iloc[-1]
                    performance[ticker] = (end_price / start_price - 1) * 100
            except Exception as e:
                print(f"Error obteniendo datos para {ticker}: {e}")
        
        avg_performance = sum(performance.values()) / len(performance) if performance else 0
        
        return {
            'sector': sector,
            'performance': performance,
            'average_performance': avg_performance,
            'top_performer': max(performance.items(), key=lambda x: x[1]) if performance else None,
            'worst_performer': min(performance.items(), key=lambda x: x[1]) if performance else None
        }
    
    def compare_to_sector(self, ticker: str, days: int = 30) -> Dict:
        """
        Compara el rendimiento de una acción con su sector.
        
        Args:
            ticker: Símbolo de la acción
            days: Número de días para el análisis
            
        Returns:
            Diccionario con resultados de la comparación
        """
        # Encontrar el sector de la acción
        sector = None
        for s, tickers in self.sector_mapping.items():
            if ticker in tickers:
                sector = s
                break
        
        if sector is None:
            raise ValueError(f"No se encontró sector para {ticker}")
        
        # Obtener rendimiento de la acción
        ticker_data = self.data_fetcher.fetch_stock_data(ticker)
        ticker_start = ticker_data['close'].iloc[-days]
        ticker_end = ticker_data['close'].iloc[-1]
        ticker_perf = (ticker_end / ticker_start - 1) * 100
        
        # Obtener rendimiento del sector
        sector_perf = self.get_sector_performance(sector, days)
        
        return {
            'ticker': ticker,
            'sector': sector,
            'ticker_performance': ticker_perf,
            'sector_average_performance': sector_perf['average_performance'],
            'outperformance': ticker_perf - sector_perf['average_performance'],
            'sector_performance_details': sector_perf
        }
    
    def get_sector_valuation_metrics(self, sector: str) -> Dict[str, float]:
        """
        Obtiene métricas de valuación promedio para un sector.
        
        Args:
            sector: Nombre del sector
            
        Returns:
            Diccionario con métricas promedio del sector
        """
        if sector not in self.sector_mapping:
            raise ValueError(f"Sector no válido: {sector}")
        
        metrics = {
            'pe_ratio': [],
            'pb_ratio': [],
            'ev_ebitda': [],
            'dividend_yield': []
        }
        
        for ticker in self.sector_mapping[sector]:
            try:
                # Obtener ratios para cada compañía en el sector
                # (implementar lógica real para obtener estos datos)
                pass
            except Exception:
                continue
        
        # Calcular promedios
        avg_metrics = {
            'pe_ratio': sum(metrics['pe_ratio']) / len(metrics['pe_ratio']) if metrics['pe_ratio'] else 0,
            'pb_ratio': sum(metrics['pb_ratio']) / len(metrics['pb_ratio']) if metrics['pb_ratio'] else 0,
            'ev_ebitda': sum(metrics['ev_ebitda']) / len(metrics['ev_ebitda']) if metrics['ev_ebitda'] else 0,
            'dividend_yield': sum(metrics['dividend_yield']) / len(metrics['dividend_yield']) if metrics['dividend_yield'] else 0,
            'num_companies': len(self.sector_mapping[sector])
        }
        
        return avg_metrics