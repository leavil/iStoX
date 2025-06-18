import streamlit as st
import plotly.graph_objs as go
import pandas as pd

def plot_price_chart(df, ticker):
    st.success(f"✅ Datos cargados correctamente para {ticker}")

    # 🔧 Aplanar MultiIndex si es necesario
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]  # Solo el primer nivel

    fig = go.Figure()

    if 'Adj Close' in df.columns:
        price_col = 'Adj Close'
    elif 'Close' in df.columns:
        price_col = 'Close'
    else:
        st.error("No se encontró ni 'Adj Close' ni 'Close' en los datos descargados.")
        st.dataframe(df.head())  # para depurar
        st.stop()

    fig.add_trace(go.Scatter(x=df.index, y=df[price_col], mode='lines', name='Precio Ajustado'))

    fig.update_xaxes(rangeslider_visible=True)
    fig.update_layout(
        title=f"📊 Precio Histórico Ajustado - {ticker}",
        xaxis_title="Fecha",
        yaxis_title="Precio (USD)",
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Datos recientes")
    st.dataframe(df.tail(10))
