import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Clase de configuración para la aplicación.
    Carga variables de entorno desde un archivo .env.
    """
    
    # Rutas de directorios
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    MODEL_DIR = os.path.join(BASE_DIR, 'models')
    CACHE_DIR = os.path.join(BASE_DIR, 'cache')

    # Variables de entorno
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
    TIINGO_API_KEY = os.getenv('TIINGO_API_KEY')
    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
    FINAGE_API_KEY = os.getenv('FINAGE_API_KEY')
    QUANDL_API_KEY = os.getenv('QUANDL_API_KEY')

    # Configuración de caché
    CACHE_DB_PATH = os.path.join(CACHE_DIR, 'stock_data.db')
    
    @staticmethod
    def init_app(app):
        """
        Método estático para inicializar la aplicación con la configuración.
        """
        app.config.from_object(Config)
        if not os.path.exists(Config.DATA_DIR):
            os.makedirs(Config.DATA_DIR)
        if not os.path.exists(Config.MODEL_DIR):
            os.makedirs(Config.MODEL_DIR)
        if not os.path.exists(Config.CACHE_DIR):
            os.makedirs(Config.CACHE_DIR)
        if not os.path.exists(Config.CACHE_DB_PATH):
            with open(Config.CACHE_DB_PATH, 'w') as f:
                pass
        app.config['CACHE_DB_PATH'] = Config.CACHE_DB_PATH
        app.config['DATA_DIR'] = Config.DATA_DIR    
        app.config['MODEL_DIR'] = Config.MODEL_DIR
        app.config['CACHE_DIR'] = Config.CACHE_DIR
        app.config['ALPHA_VANTAGE_API_KEY'] = Config.ALPHA_VANTAGE_API_KEY
        app.config['FINNHUB_API_KEY'] = Config.FINNHUB_API_KEY
        app.config['TIINGO_API_KEY'] = Config.TIINGO_API_KEY
        app.config['POLYGON_API_KEY'] = Config.POLYGON_API_KEY
        app.config['FINAGE_API_KEY'] = Config.FINAGE_API_KEY    
        app.config['QUANDL_API_KEY'] = Config.QUANDL_API_KEY
        app.config['CACHE_DB_PATH'] = Config.CACHE_DB_PATH
     




                        
    