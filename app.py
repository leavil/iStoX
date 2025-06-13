import streamlit as st
from modules.data_fetcher import get_stock_data
import plotly.graph_objs as go
from datetime import datetime
from modules.views import show_valuation_view  # <-- importamos la nueva vista

st.set_page_config(page_title="iStoXClub", layout="wide")

def main():
    st.sidebar.title("Menú")
    option = st.sidebar.selectbox("Selecciona vista", ["Inicio", "Valuation"])

    if option == "Inicio":
        st.title("iStoX")

        ticker = st.text_input("🔍 Ingresa el ticker de la acción", "AAPL")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("📅 Fecha de inicio", datetime(2023, 1, 1))
        with col2:
            end_date = st.date_input("📅 Fecha de fin", datetime.today())

        if ticker:
            with st.spinner(f"Buscando datos históricos para {ticker}..."):
                df = get_stock_data(ticker, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))

            if df.empty:
                st.error("❌ No se pudieron obtener los datos de esta acción. Intenta con otro ticker.")
            else:
                st.success(f"✅ Datos cargados correctamente para {ticker}")

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df.index, y=df['Adj Close'], mode='lines', name='Precio Ajustado'))
                fig.update_layout(
                    title=f"📊 Precio Histórico Ajustado - {ticker}",
                    xaxis_title="Fecha",
                    yaxis_title="Precio (USD)",
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("📋 Datos recientes")
                st.dataframe(df.tail(10))

    elif option == "Valuation":
        show_valuation_view()

if __name__ == "__main__":
    main()
