import streamlit as st
from modules.fetcher import StockDataFetcher
from modules.visualizer import StockVisualizer
from views.valuation_view import ValuationView
from views.home_view import HomeView
from modules.ticker_searcher import TickerSearcher
from datetime import datetime

st.set_page_config(page_title="iStoXClub", layout="wide")

class StockApp:
    def __init__(self):
        self.ticker_searcher = TickerSearcher()
        self.fetcher = None
        self.visualizer = StockVisualizer()
        self.home_view = None
        self.ticker = st.session_state.get("selected_ticker", "AAPL")

    def run(self):
        st.sidebar.title("Menú")
        view = st.sidebar.selectbox("Selecciona vista", ["Inicio", "Valuation"])
        
        # Asegurarse de tener ticker actualizado
        ticker = st.session_state.get("selected_ticker", "AAPL")
        
        # Crear objetos cuando se tiene ticker
        self.fetcher = StockDataFetcher(ticker)
        self.home_view = HomeView(self.ticker_searcher, self.fetcher, self.visualizer)

        if view == "Inicio":
            self.home_view.render()
        elif view == "Valuation":
            valuation_view = ValuationView(self.ticker)
            valuation_view.render()



if __name__ == "__main__":
    app = StockApp()
    app.run()

