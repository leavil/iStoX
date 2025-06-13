import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from io import BytesIO

class ReportGenerator:
    def __init__(self):
        pass
    
    def generate_pdf_report(self, report_data: Dict, filename: Optional[str] = None) -> bytes:
        """
        Genera un informe PDF con los resultados del análisis.
        
        Args:
            report_data: Diccionario con datos para el informe
            filename: Nombre del archivo (opcional)
            
        Returns:
            Bytes del archivo PDF
        """
        # Implementar generación de PDF usando ReportLab o similar
        pass
    
    def generate_html_report(self, report_data: Dict) -> str:
        """
        Genera un informe HTML con los resultados del análisis.
        
        Args:
            report_data: Diccionario con datos para el informe
            
        Returns:
            String con el HTML generado
        """
        # Crear figura con subplots
        fig = make_subplots(
            rows=2, cols=2,
            specs=[
                [{"type": "xy", "colspan": 2}, None],
                [{"type": "xy"}, {"type": "xy"}]
            ],
            subplot_titles=(
                "Precio Histórico y Valor Intrínseco",
                "Análisis de Sentimiento de Noticias",
                "Indicadores Técnicos"
            )
        )
        
        # Gráfico de precios
        fig.add_trace(
            go.Scatter(
                x=report_data['historical_data'].index,
                y=report_data['historical_data']['close'],
                name='Precio de Cierre',
                line=dict(color='royalblue', width=2)
            ),
            row=1, col=1
        )
        
        if 'intrinsic_value' in report_data:
            fig.add_hline(
                y=report_data['intrinsic_value'],
                line=dict(color='firebrick', width=2, dash='dash'),
                annotation_text="Valor Intrínseco",
                annotation_position="bottom right",
                row=1, col=1
            )
        
        # Gráfico de sentimiento de noticias
        if 'news_sentiment' in report_data:
            fig.add_trace(
                go.Scatter(
                    x=report_data['news_sentiment'].index,
                    y=report_data['news_sentiment']['sentiment_compound'],
                    name='Sentimiento',
                    line=dict(color='green', width=2)
                ),
                row=2, col=1
            )
        
        # Gráfico de RSI
        if 'ta_data' in report_data and 'RSI_14' in report_data['ta_data']:
            fig.add_trace(
                go.Scatter(
                    x=report_data['ta_data'].index,
                    y=report_data['ta_data']['RSI_14'],
                    name='RSI 14 días',
                    line=dict(color='purple', width=2)
                ),
                row=2, col=2
            )
            fig.add_hline(
                y=70, line=dict(color='red', width=1, dash='dash'),
                annotation_text="Sobrecompra", row=2, col=2
            )
            fig.add_hline(
                y=30, line=dict(color='green', width=1, dash='dash'),
                annotation_text="Sobreventa", row=2, col=2
            )
        
        fig.update_layout(
            height=800,
            showlegend=True,
            title_text=f"Informe de Análisis - {report_data.get('ticker', '')}"
        )
        
        # Convertir figura a HTML
        plot_html = fig.to_html(full_html=False)
        
        # Crear HTML completo
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Informe de Análisis - {report_data.get('ticker', '')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }}
                .metric-card {{ background: #f8f9fa; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #3498db; }}
                .plot {{ margin: 30px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Informe de Análisis - {report_data.get('ticker', '')}</h1>
                <p>Generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                
                <div class="metrics">
                    <div class="metric-card">
                        <h3>Precio Actual</h3>
                        <p class="metric-value">${report_data.get('current_price', 0):.2f}</p>
                    </div>
                    <div class="metric-card">
                        <h3>Valor Intrínseco</h3>
                        <p class="metric-value">${report_data.get('intrinsic_value', 0):.2f}</p>
                    </div>
                    <div class="metric-card">
                        <h3>Diferencia</h3>
                        <p class="metric-value">{report_data.get('valuation_diff', 0):.2f}%</p>
                    </div>
                </div>
                
                <div class="plot">
                    {plot_html}
                </div>
                
                <h2>Recomendación</h2>
                <p>{report_data.get('recommendation', '')}</p>
                
                <h2>Análisis de Riesgo</h2>
                <ul>
                    <li>Volatilidad: {report_data.get('volatility', 0):.2f}%</li>
                    <li>Beta: {report_data.get('beta', 0):.2f}</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def plot_to_image(self, fig) -> str:
        """Convierte un gráfico Plotly a una imagen base64"""
        buf = BytesIO()
        fig.write_image(buf, format='png')
        return base64.b64encode(buf.getvalue()).decode('utf-8')