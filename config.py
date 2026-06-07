"""Configuration for Weather Dashboard"""
import os
from dotenv import load_dotenv

load_dotenv()

# Weather API Configuration
WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', 'YOUR_API_KEY_HERE')
WEATHER_API_URL = 'https://api.openweathermap.org/data/2.5'
GEO_API_URL = 'https://api.openweathermap.org/geo/1.0'

# Flask Configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', True)
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

# Cache Configuration
CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 600))  # 10 minutes
CACHE_TYPE = 'simple'

# Units Configuration
TEMPERATURE_UNIT = os.getenv('TEMPERATURE_UNIT', 'metric')  # 'metric', 'imperial', 'standard'
WIND_UNIT = os.getenv('WIND_UNIT', 'mps')  # m/s, km/h, mph
PRESSURE_UNIT = os.getenv('PRESSURE_UNIT', 'hpa')  # hPa, mb, inHg

# Location Configuration
DEFAULT_CITY = os.getenv('DEFAULT_CITY', 'Tehran')
DEFAULT_COUNTRY = os.getenv('DEFAULT_COUNTRY', 'IR')

# UI Configuration
THEME = os.getenv('THEME', 'dark')  # 'light', 'dark'
DISPLAY_MODE = os.getenv('DISPLAY_MODE', 'web')  # 'web', 'cli', 'both'

# Timeout Configuration
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 10))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', './logs/weather_dashboard.log')

# Features
ENABLE_FORECAST = os.getenv('ENABLE_FORECAST', 'true').lower() == 'true'
ENABLE_ALERTS = os.getenv('ENABLE_ALERTS', 'true').lower() == 'true'
ENABLE_HISTORY = os.getenv('ENABLE_HISTORY', 'true').lower() == 'true'
ENABLE_CHARTS = os.getenv('ENABLE_CHARTS', 'true').lower() == 'true'
