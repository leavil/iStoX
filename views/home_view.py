import streamlit as st
from datetime import datetime, timedelta
from modules.ticker_searcher import TickerSearcher
from utils.format import format_percent  # Asegúrate de tener esta función
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from modules.fetcher import StockDataFetcher


class HomeView:
    def __init__(self, ticker_searcher, fetcher, visualizer):
        self.ticker_searcher = ticker_searcher
        self.fetcher = fetcher
        self.visualizer = visualizer

    def render(self):
        st.title("📊 iStoX - Análisis Histórico de Acciones")

        query = st.text_input("🔎 Buscar por nombre o ticker")

        if not query.strip():
            st.info("Introduce el nombre o ticker para empezar.")
            return

        opciones = self.ticker_searcher.buscar(query)

        if not opciones:
            st.warning("❌ No se encontraron resultados.")
            return

        seleccion = st.selectbox("📈 Selecciona una empresa", opciones)

        if not seleccion:
            return

        ticker = seleccion.split("(")[-1].replace(")", "").strip()
        nombre = seleccion.split("(")[0].strip()
        st.session_state["selected_ticker"] = ticker

        start, end = self._get_date_range()

        with st.spinner("Cargando datos..."):
            df = self.fetcher.get_price_data(start=start, end=end)

        if df.empty:
            st.error("❌ No se pudieron obtener datos.")
        else:
            rendimiento_pct = self._calcular_rendimiento(df)
            self._mostrar_rendimiento(nombre, ticker, rendimiento_pct)
            self.visualizer.plot_price_chart(df, ticker)

    def _get_date_range(self):
        today = datetime.today()
        options = {
            "1M": today - timedelta(days=30),
            "3M": today - timedelta(days=90),
            "6M": today - timedelta(days=180),
            "YTD": datetime(today.year, 1, 1),
            "1Y": today - timedelta(days=365),
            "Máximo": datetime(2000, 1, 1)
        }

        st.markdown("### ⏱️ Rango rápido")
        selected_range = st.radio(
            "Selecciona el periodo:",
            list(options.keys()),
            index=list(options.keys()).index(st.session_state.get("selected_range", "3M")),
            horizontal=True,
            key="selected_range_radio"
        )
        st.session_state["selected_range"] = selected_range

        start_default = options[selected_range]

        col1, col2 = st.columns(2)
        start = col1.date_input("📅 Fecha inicio", value=start_default)
        end = col2.date_input("📅 Fecha fin", value=today)

        return start, end

    def _calcular_rendimiento(self, df):
        if 'Adj Close' in df.columns:
            precio_inicio = df['Adj Close'].iloc[0]
            precio_fin = df['Adj Close'].iloc[-1]
        elif 'Close' in df.columns:
            precio_inicio = df['Close'].iloc[0]
            precio_fin = df['Close'].iloc[-1]
        else:
            return None

        try:
            precio_inicio = float(precio_inicio)
            precio_fin = float(precio_fin)
        except (ValueError, TypeError):
            return None

        if precio_inicio != 0:
            return ((precio_fin - precio_inicio) / precio_inicio) * 100
        return None



    def _mostrar_rendimiento(self, nombre, ticker, rendimiento_pct):
        st.subheader(f"📌 {nombre} ({ticker})")

        if rendimiento_pct is not None:
            color = "green" if rendimiento_pct > 0 else "red"
            st.markdown(
                f"<h4>📈 Rendimiento en el periodo: <span style='color:{color}'>{rendimiento_pct:.2f}%</span></h4>",
                unsafe_allow_html=True
            )
