# views/valuation_view.py
# views/valuation_view.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.valuation import Valuation
from modules.fetcher import StockDataFetcher
from typing import Optional, Dict
import datetime
import yfinance as yf

class ValuationView:
    def __init__(self, ticker: str = "AAPL"):
        self.ticker = ticker
        try:
            self.valuation = Valuation(self.ticker)
            self.fetcher = StockDataFetcher(self.ticker)
        except Exception as e:
            st.error(f"Error initializing valuation: {str(e)}")
            self.valuation = None
            self.fetcher = None

    def render(self):
        if not self.ticker:
            st.warning("No ticker selected")
            return
            
        try:
            data = self._get_fundamental_data_safely()
            if not data:
                return
                
            self._render_header(data)
            self._render_valuation_tabs(data)
            
        except Exception as e:
            st.error(f"Error rendering valuation: {str(e)}")

    def _get_fundamental_data_safely(self) -> Optional[Dict]:
        """Safely get fundamental data with error handling"""
        try:
            if not self.fetcher:
                raise ValueError("Data fetcher not initialized")
                
            data = self.fetcher.get_fundamental_data()
            if not data:
                st.warning("No fundamental data available")
                return None
                
            # Ensure required fields exist
            required_fields = ['name', 'price', 'market_cap']
            for field in required_fields:
                if field not in data:
                    st.warning(f"Missing required field: {field}")
                    return None
                    
            return data
            
        except Exception as e:
            st.error(f"Error getting fundamental data: {str(e)}")
            return None

    def _render_header(self, data: Dict):
        """Render the header section with company info"""
        st.title(f"📈 {data.get('name', self.ticker)} ({self.ticker})")
        st.caption(f"Sector: {data.get('sector', 'N/A')}")

        # HEADER CARDS
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Precio Actual", 
                   f"${data.get('price', 0):.2f}",
                   help="Current market price")
                   
        market_cap = data.get('market_cap', 0)
        col2.metric("📊 Market Cap", 
                   f"${market_cap/1e9:.2f}B" if market_cap else "N/A",
                   help="Market capitalization")
                   
        target_price = data.get('analyst_target_price')
        col3.metric("🎯 Valor Objetivo", 
                   f"${target_price:.2f}" if target_price else "N/A",
                   help="Analyst target price")

        self._render_metrics(data)
        self._render_analyst_recommendation(data)

    def _render_metrics(self, data: Dict):
        """Render financial metrics sections"""
        st.markdown("### 📌 Múltiplos")
        col1, col2, col3 = st.columns(3)
        col1.metric("P/E", 
                   f"{data.get('pe_ratio', 'N/A')}",
                   help="Price-to-Earnings ratio")
        col2.metric("EV/EBITDA", 
                   f"{data.get('ev_ebitda', 'N/A')}",
                   help="Enterprise Value to EBITDA")
        col3.metric("P/B", 
                   f"{data.get('pb_ratio', 'N/A')}",
                   help="Price-to-Book ratio")

        # Dividendos y ROE/ROIC
        st.markdown("### 💸 Dividendos y Rentabilidad")
        col1, col2, col3 = st.columns(3)
        col1.metric("Dividend Yield", 
                   f"{(data.get('dividend_yield', 0) or 0)*100:.2f}%",
                   help="Annual dividend yield")
        col2.metric("ROE", 
                   f"{(data.get('roe', 0) or 0)*100:.2f}%",
                   help="Return on Equity")
        col3.metric("ROIC (Proxy)", 
                   f"{(data.get('roic', 0) or 0)*100:.2f}%",
                   help="Return on Invested Capital")

        # EPS y Proyecciones
        st.markdown("### 📈 Proyecciones")
        eps_forward = data.get('eps_forward')
        st.metric("EPS Forward", 
                 f"${eps_forward:.2f}" if eps_forward else "N/A",
                 help="Forward Earnings Per Share")

    def _render_analyst_recommendation(self, data: Dict):
        """Render analyst recommendation section"""
        st.markdown("### 🧠 Recomendación de Analistas")
        recommendation = data.get('recommendation', 'N/A')
        if recommendation != 'N/A':
            st.success(f"Recomendación: **{recommendation.capitalize()}**")
        else:
            st.info("No analyst recommendation available")
            
        st.caption(f"Actualizado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # Valuation verdict
        price = data.get('price')
        target = data.get('analyst_target_price')
        
        if price and target:
            if price < 0.85 * target:
                st.markdown("## 🟢 Infravalorada 🚀 (Buy)")
            elif 0.85 * target <= price <= target:
                st.markdown("## ⚖️ Valor Justo (Hold)")
            else:
                st.markdown("## 🔴 Sobrevalorada 🛑 (Sell)")
        else:
            st.warning("Insufficient data for valuation verdict")

    def _render_valuation_tabs(self, data: Dict):
        """Render the valuation tabs"""
        tabs = st.tabs(["Valor Intrínseco", "Múltiplos Financieros", "Crecimiento"])

        with tabs[0]:
            self._show_intrinsic_values(data.get('price'))

        with tabs[1]:
            self._show_multiples()

        with tabs[2]:
            self._show_growth_chart()

    def _show_intrinsic_values(self, current_price: Optional[float] = None):
        st.subheader("📊 Valor Intrínseco vs Precio Actual")
        
        # Get current price if not provided
        price = current_price or self.valuation.current_price()
        if price is None:
            st.warning("No se pudo obtener el precio actual.")
            return
            
        st.metric("💵 Precio Actual", f"${price:.2f}")

        # Valuation method selection
        method = st.selectbox(
            "Selecciona el modelo de valoración",
            ["DCF", "PER", "Gordon Growth"],
            index=0,
            help="Select valuation methodology"
        )

        # Calculate based on selected method
        val = None
        if method == "DCF":
            with st.expander("🔧 Parámetros del modelo DCF", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    growth = st.slider("📈 Crecimiento FCF (%)", 1, 30, 8) / 100
                with col2:
                    terminal = st.slider("🏁 Crecimiento Terminal (%)", 1, 6, 3) / 100
                with col3:
                    years = st.slider("📆 Años proyectados", 3, 10, 5)

            val = self.valuation.intrinsic_value_dcf(
                growth_rate=growth,
                terminal_growth=terminal,
                years=years
            )
        elif method == "PER":
            val = self.valuation.intrinsic_value_per()
        else:  # Gordon
            val = self.valuation.intrinsic_value_gordon()

        # Display results
        if val is not None:
            self._display_valuation_result(price, val, method)
            self._show_comparison_table(price)
        else:
            st.info("No fue posible calcular el valor intrínseco con los datos disponibles.")

    def _display_valuation_result(self, current_price: float, intrinsic_value: float, method: str):
        """Helper to display valuation results consistently"""
        diff = intrinsic_value - current_price
        pct = (diff / current_price) * 100
        estado = "🟢 Infravalorada" if diff > 0 else "🔴 Sobrevalorada"
        
        st.metric(
            f"Valor Intrínseco ({method})", 
            f"${intrinsic_value:.2f}", 
            delta=f"{pct:.2f}% {estado}"
        )

    def _show_comparison_table(self, current_price: float):
        """Show comparison table of all valuation methods"""
        st.markdown("---")
        st.subheader("Comparación de Modelos")
        
        models = {
            "DCF": self.valuation.intrinsic_value_dcf(),
            "PER": self.valuation.intrinsic_value_per(),
            "Gordon": self.valuation.intrinsic_value_gordon()
        }

        data = []
        for name, val in models.items():
            if val is not None:
                diff = val - current_price
                pct = (diff / current_price) * 100
                estado = "🟢 Infravalorada" if diff > 0 else "🔴 Sobrevalorada"
                data.append({
                    "Modelo": name,
                    "Valor Intrínseco": f"${val:.2f}",
                    "Diferencia": f"${diff:.2f}",
                    "Variación %": f"{pct:.2f}%",
                    "Estado": estado
                })

        if data:
            df = pd.DataFrame(data)
            st.table(df)
        else:
            st.info("No se pudo calcular ningún modelo de valoración.")

    def _show_multiples(self):
        st.subheader("🔎 Múltiplos Financieros")
        multiples = self.valuation.multiples_analysis()

        if not multiples:
            st.info("No hay múltiplos financieros disponibles.")
            return

        df = pd.DataFrame.from_dict(multiples, orient="index", columns=["Valor"])
        df = df.fillna("N/A")

        # Crear columna auxiliar numérica
        df["Valor_num"] = pd.to_numeric(df["Valor"], errors="coerce")

        def color_negative_red(val):
            try:
                val = float(val)
                return 'color: red' if val < 0 else 'color: green'
            except (ValueError, TypeError):
                return ''  # Sin estilo si no se puede convertir


        def format_values(val):
            try:
                val_float = float(val)
                return f"${val_float:,.2f}"
            except (ValueError, TypeError):
                return val

        styled_df = (
            df.style
            .applymap(color_negative_red, subset=["Valor"])
            .format(format_values)
        )
        # Eliminar la columna auxiliar para mostrar solo "Valor"
        df_display = df.drop(columns=["Valor_num"])
        st.dataframe(styled_df.hide(axis="columns", subset=["Valor_num"]))  # pandas >= 1.4


    def _show_growth_chart(self):
        st.subheader("📈 Crecimiento del Flujo de Caja Libre")
        
        try:
            ticker_obj = yf.Ticker(self.ticker)
            cf = ticker_obj.cashflow

            # Try different possible cash flow labels
            possible_keys = [
                'Free Cash Flow',
                'FreeCashFlow',
                'Operating Cash Flow',
                'Total Cash From Operating Activities',
                'Net Cash Provided by Operating Activities'
            ]

            cash_flow = None
            for key in possible_keys:
                if key in cf.index:
                    cash_flow = cf.loc[key].dropna()
                    break

            if cash_flow is None or cash_flow.empty:
                st.info("No se encontraron datos de flujo de caja.")
                return

            # Create the chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=cash_flow.index.astype(str),
                y=cash_flow.values,
                name="Flujo de Caja"
            ))
            
            fig.update_layout(
                title="Flujo de Caja Histórico",
                xaxis_title="Año",
                yaxis_title="Flujo de Caja (en millones)",
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.info(f"No se pudo generar el gráfico de crecimiento: {str(e)}")