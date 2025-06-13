import streamlit as st
from modules.valuation import Valuation

def show_valuation_view():
    st.title("🧠 Valoración Fundamental de Acciones")

    ticker = st.text_input("Ticker de la empresa", "AAPL")

    if ticker:
        val = Valuation(ticker)

        st.subheader("📊 Valor Intrínseco")
        col1, col2, col3 = st.columns(3)
        with col1:
            per_val = val.intrinsic_value_per()
            st.metric("PER Estimado", f"${per_val:.2f}" if per_val else "N/A")

        with col2:
            dcf_val = val.intrinsic_value_dcf()
            st.metric("DCF", f"${dcf_val:.2f}" if dcf_val else "N/A")

        with col3:
            gordon_val = val.intrinsic_value_gordon()
            st.metric("Modelo Gordon", f"${gordon_val:.2f}" if gordon_val else "N/A")

        st.divider()

        st.subheader("🔎 Múltiplos Financieros")
        multiples = val.multiples_analysis()
        st.write(multiples)

        st.divider()
        st.markdown("📥 *Próximamente: exportar informe en PDF / Markdown*")
