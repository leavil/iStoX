import os
import json
from typing import Dict, Any
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file: str = 'config.json'):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo o crea uno por defecto"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            default_config = {
                'general': {
                    'default_ticker': 'AAPL',
                    'default_valuation_method': 'dcf',
                    'timezone': 'UTC'
                },
                'apis': {
                    'primary': 'yfinance',
                    'fallback_order': ['alpha_vantage', 'finnhub', 'tiingo']
                },
                'ui': {
                    'theme': 'light',
                    'chart_style': 'plotly_white'
                },
                'notifications': {
                    'email_alerts': False,
                    'price_alerts': True
                }
            }
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Guarda la configuración en el archivo"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración"""
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Establece un valor de configuración"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._save_config(self.config)
    
    def reset_to_default(self) -> None:
        """Restablece la configuración a los valores por defecto"""
        os.remove(self.config_file)
        self.config = self._load_config()