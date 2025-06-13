
import smtplib
from email.mime.text import MIMEText
from typing import Dict, List
import time
from threading import Thread
from modules.data_fetcher import DataFetcher
from modules.valuation import Valuation

class AlertManager:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.valuation = Valuation()
        self.active_alerts = {}
        self.alert_thread = None
        self.running = False
    
    def add_price_alert(self, ticker: str, target_price: float, 
                       condition: str = 'above', user_email: Optional[str] = None) -> str:
        """
        Añade una alerta de precio.
        
        Args:
            ticker: Símbolo de la acción
            target_price: Precio objetivo
            condition: 'above' o 'below'
            user_email: Email para notificación (opcional)
            
        Returns:
            ID de la alerta
        """
        alert_id = f"{ticker}_{target_price}_{condition}_{time.time()}"
        self.active_alerts[alert_id] = {
            'ticker': ticker,
            'target_price': target_price,
            'condition': condition,
            'user_email': user_email,
            'triggered': False
        }
        return alert_id
    
    def add_valuation_alert(self, ticker: str, threshold_pct: float = 10.0,
                           user_email: Optional[str] = None) -> str:
        """
        Añade una alerta de valuación.
        
        Args:
            ticker: Símbolo de la acción
            threshold_pct: Porcentaje de diferencia para activar
            user_email: Email para notificación (opcional)
            
        Returns:
            ID de la alerta
        """
        alert_id = f"valuation_{ticker}_{threshold_pct}_{time.time()}"
        self.active_alerts[alert_id] = {
            'ticker': ticker,
            'threshold_pct': threshold_pct,
            'type': 'valuation',
            'user_email': user_email,
            'triggered': False
        }
        return alert_id
    
    def remove_alert(self, alert_id: str) -> bool:
        """Elimina una alerta activa"""
        if alert_id in self.active_alerts:
            del self.active_alerts[alert_id]
            return True
        return False
    
    def start_monitoring(self, interval: int = 300) -> None:
        """Inicia el monitoreo de alertas en segundo plano"""
        if self.alert_thread is not None:
            self.stop_monitoring()
        
        self.running = True
        self.alert_thread = Thread(
            target=self._monitor_alerts,
            args=(interval,),
            daemon=True
        )
        self.alert_thread.start()
    
    def stop_monitoring(self) -> None:
        """Detiene el monitoreo de alertas"""
        self.running = False
        if self.alert_thread is not None:
            self.alert_thread.join()
            self.alert_thread = None
    
    def _monitor_alerts(self, interval: int) -> None:
        """Monitorea las alertas activas en intervalos regulares"""
        while self.running:
            for alert_id, alert in list(self.active_alerts.items()):
                if alert.get('triggered', False):
                    continue
                
                try:
                    current_price = self.data_fetcher.fetch_stock_data(
                        alert['ticker']
                    )['close'].iloc[-1]
                    
                    if alert.get('type') == 'valuation':
                        # Alerta de valuación
                        financials = self.data_fetcher.get_financial_statements(
                            alert['ticker']
                        )
                        
                        if financials is not None:
                            intrinsic_value = self.valuation.dcf_valuation(
                                free_cash_flow=financials['freeCashFlow']
                            )
                            diff_pct = (intrinsic_value - current_price) / current_price * 100
                            
                            if abs(diff_pct) >= alert['threshold_pct']:
                                self._trigger_alert(
                                    alert_id,
                                    f"Alerta de Valuación: {alert['ticker']} está "
                                    f"{'sobrevalorada' if diff_pct < 0 else 'subvalorada'} "
                                    f"en un {abs(diff_pct):.2f}%"
                                )
                    else:
                        # Alerta de precio
                        condition_met = (
                            (alert['condition'] == 'above' and current_price >= alert['target_price']) or
                            (alert['condition'] == 'below' and current_price <= alert['target_price'])
                        )
                        
                        if condition_met:
                            self._trigger_alert(
                                alert_id,
                                f"Alerta de Precio: {alert['ticker']} ha alcanzado "
                                f"{alert['target_price']} (actual: {current_price:.2f})"
                            )
                
                except Exception as e:
                    print(f"Error monitoreando alerta {alert_id}: {e}")
            
            time.sleep(interval)
    
    def _trigger_alert(self, alert_id: str, message: str) -> None:
        """Dispara una alerta y envía notificaciones"""
        if alert_id not in self.active_alerts:
            return
        
        alert = self.active_alerts[alert_id]
        alert['triggered'] = True
        print(f"ALERTA: {message}")
        
        if alert.get('user_email'):
            self._send_email_alert(alert['user_email'], message)
    
    def _send_email_alert(self, email: str, message: str) -> bool:
        """Envía una alerta por email"""
        try:
            # Configuración del servidor SMTP (ejemplo para Gmail)
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = "your_email@gmail.com"
            sender_password = "your_password"
            
            msg = MIMEText(message)
            msg['Subject'] = "iStoX - Alerta de Inversión"
            msg['From'] = sender_email
            msg['To'] = email
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, [email], msg.as_string())
            
            return True
        except Exception as e:
            print(f"Error enviando email: {e}")
            return False