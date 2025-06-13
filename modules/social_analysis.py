import pandas as pd
from typing import List, Dict
from datetime import datetime, timedelta
from textblob import TextBlob
from modules.api_fallback import APIFallbackSystem

class SocialMediaAnalyzer:
    def __init__(self):
        self.api_fallback = APIFallbackSystem()
    
    def fetch_twitter_sentiment(self, ticker: str, days: int = 7) -> pd.DataFrame:
        """
        Obtiene y analiza tweets relacionados con un ticker.
        
        Args:
            ticker: Símbolo de la acción
            days: Número de días hacia atrás para buscar tweets
            
        Returns:
            DataFrame con tweets y análisis de sentimiento
        """
        # Usar sistema de fallback para obtener tweets
        tweets = self.api_fallback.fetch_twitter_data(ticker, days=days)
        
        analyzed_tweets = []
        for tweet in tweets:
            analysis = TextBlob(tweet['text'])
            analyzed_tweets.append({
                'date': tweet['date'],
                'text': tweet['text'],
                'user': tweet['user'],
                'retweets': tweet['retweets'],
                'likes': tweet['likes'],
                'sentiment_polarity': analysis.sentiment.polarity,
                'sentiment_subjectivity': analysis.sentiment.subjectivity
            })
        
        df = pd.DataFrame(analyzed_tweets)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        return df
    
    def analyze_reddit_sentiment(self, ticker: str, days: int = 7) -> pd.DataFrame:
        """
        Obtiene y analiza posts de Reddit relacionados con un ticker.
        
        Args:
            ticker: Símbolo de la acción
            days: Número de días hacia atrás para buscar posts
            
        Returns:
            DataFrame con posts y análisis de sentimiento
        """
        # Usar sistema de fallback para obtener posts de Reddit
        reddit_posts = self.api_fallback.fetch_reddit_data(ticker, days=days)
        
        analyzed_posts = []
        for post in reddit_posts:
            analysis = TextBlob(post['title'] + " " + post['text'])
            analyzed_posts.append({
                'date': post['date'],
                'title': post['title'],
                'text': post['text'],
                'subreddit': post['subreddit'],
                'upvotes': post['upvotes'],
                'comments': post['comments'],
                'sentiment_polarity': analysis.sentiment.polarity,
                'sentiment_subjectivity': analysis.sentiment.subjectivity
            })
        
        df = pd.DataFrame(analyzed_posts)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        return df
    
    def get_social_sentiment_trend(self, ticker: str, days: int = 7) -> Dict:
        """
        Obtiene el sentimiento combinado de redes sociales.
        
        Args:
            ticker: Símbolo de la acción
            days: Número de días hacia atrás para buscar
            
        Returns:
            Diccionario con métricas de sentimiento agregadas
        """
        twitter_data = self.fetch_twitter_sentiment(ticker, days)
        reddit_data = self.analyze_reddit_sentiment(ticker, days)
        
        twitter_avg = twitter_data['sentiment_polarity'].mean()
        reddit_avg = reddit_data['sentiment_polarity'].mean()
        
        return {
            'twitter_sentiment': twitter_avg,
            'reddit_sentiment': reddit_avg,
            'combined_sentiment': (twitter_avg + reddit_avg) / 2,
            'twitter_volume': len(twitter_data),
            'reddit_volume': len(reddit_data)
        }