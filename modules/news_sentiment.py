import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from typing import List, Dict
import pandas as pd
from datetime import datetime
from modules.api_fallback import APIFallbackSystem

nltk.download('vader_lexicon')

class NewsAnalyzer:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.api_fallback = APIFallbackSystem()
    
    def fetch_news(self, ticker: str, days: int = 7) -> List[Dict]:
        """
        Obtiene noticias relacionadas con un ticker.
        
        Args:
            ticker: Símbolo de la acción
            days: Número de días hacia atrás para buscar noticias
            
        Returns:
            Lista de diccionarios con noticias
        """
        # Usar el sistema de fallback para obtener noticias
        news = self.api_fallback.fetch_news(ticker, days=days)
        return news
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analiza el sentimiento de un texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Diccionario con puntuaciones de sentimiento
        """
        return self.sia.polarity_scores(text)
    
    def get_news_sentiment(self, ticker: str, days: int = 7) -> pd.DataFrame:
        """
        Obtiene noticias y analiza su sentimiento.
        
        Args:
            ticker: Símbolo de la acción
            days: Número de días hacia atrás para buscar noticias
            
        Returns:
            DataFrame con noticias y análisis de sentimiento
        """
        news = self.fetch_news(ticker, days=days)
        
        analyzed_news = []
        for item in news:
            sentiment = self.analyze_sentiment(item.get('headline', '') + " " + item.get('summary', ''))
            analyzed_news.append({
                'date': item.get('datetime', datetime.now()),
                'source': item.get('source', ''),
                'headline': item.get('headline', ''),
                'summary': item.get('summary', ''),
                'sentiment_neg': sentiment['neg'],
                'sentiment_neu': sentiment['neu'],
                'sentiment_pos': sentiment['pos'],
                'sentiment_compound': sentiment['compound']
            })
        
        df = pd.DataFrame(analyzed_news)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        return df