import streamlit as st
import plotly.graph_objs as go
import pandas as pd

class StockVisualizer:
    def __init__(self):
        pass

    def plot_price_chart(self, df, ticker, hide_range_slider=False):
        # 🔧 Validar índice temporal
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # 🔧 Aplanar MultiIndex si es necesario
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        # 🔍 Elegir columna de precios
        if 'Adj Close' in df.columns:
            price_col = 'Adj Close'
        elif 'Close' in df.columns:
            price_col = 'Close'
        else:
            st.error("No se encontró ni 'Adj Close' ni 'Close'.")
            st.dataframe(df.head())
            return

        # 📈 Crear figura
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df[price_col], mode='lines', name='Precio'))

        # 🎛️ Opciones del eje X
        fig.update_layout(
            title=f"📊 Precio Histórico - {ticker}",
            xaxis_title="Fecha",
            yaxis_title="Precio (USD)",
            template="plotly_white",
        )

        if not hide_range_slider:
            fig.update_xaxes(
                rangeslider_visible=True,
                rangeselector=dict(
                    buttons=[
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="1A", step="year", stepmode="backward"),
                        dict(step="all", label="Todo")
                    ]
                )
            )
        else:
            fig.update_xaxes(rangeslider_visible=False, rangeselector=dict(visible=False))

        # ✅ Mostrar gráfico y datos
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("📋 Datos recientes")
        st.dataframe(df.tail(10))
