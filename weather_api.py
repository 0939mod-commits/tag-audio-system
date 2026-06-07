"""Weather API client for fetching weather data"""
import requests
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from functools import lru_cache
import json

from config import (
    WEATHER_API_KEY, WEATHER_API_URL, GEO_API_URL,
    REQUEST_TIMEOUT, MAX_RETRIES, TEMPERATURE_UNIT
)

logger = logging.getLogger(__name__)


class WeatherAPIClient:
    """Client for OpenWeatherMap API"""
    
    def __init__(self, api_key: str = WEATHER_API_KEY):
        """
        Initialize weather API client
        
        Args:
            api_key: OpenWeatherMap API key
        """
        self.api_key = api_key
        self.base_url = WEATHER_API_URL
        self.geo_url = GEO_API_URL
        self.timeout = REQUEST_TIMEOUT
        self.max_retries = MAX_RETRIES
        
        if not api_key or api_key == 'YOUR_API_KEY_HERE':
            logger.warning('API key not configured. Please set OPENWEATHER_API_KEY')
    
    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        Make HTTP request with retry logic
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response JSON or None if failed
        """
        url = f"{self.base_url}/{endpoint}"
        params['appid'] = self.api_key
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}/{self.max_retries}")
                if attempt == self.max_retries - 1:
                    raise
            except requests.exceptions.RequestException as e:
                logger.error(f"API request error: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
        
        return None
    
    def get_current_weather(self, city: str, country_code: Optional[str] = None) -> Optional[Dict]:
        """
        Get current weather for a city
        
        Args:
            city: City name
            country_code: ISO 3166 country code (optional)
            
        Returns:
            Weather data dictionary
        """
        try:
            location = city
            if country_code:
                location = f"{city},{country_code}"
            
            params = {
                'q': location,
                'units': TEMPERATURE_UNIT
            }
            
            data = self._make_request('weather', params)
            
            if data:
                logger.info(f"Successfully fetched weather for {city}")
                return self._parse_weather_data(data)
            return None
        
        except Exception as e:
            logger.error(f"Error fetching current weather: {str(e)}")
            return None
    
    def get_coordinates_by_city(self, city: str, country_code: Optional[str] = None) -> Optional[Tuple[float, float]]:
        """
        Get coordinates (lat, lon) for a city
        
        Args:
            city: City name
            country_code: ISO 3166 country code (optional)
            
        Returns:
            Tuple of (latitude, longitude) or None
        """
        try:
            location = city
            if country_code:
                location = f"{city},{country_code}"
            
            params = {
                'q': location,
                'limit': 1
            }
            
            response = requests.get(f"{self.geo_url}/direct", params=params, 
                                  timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data:
                return (data[0]['lat'], data[0]['lon'])
            return None
        
        except Exception as e:
            logger.error(f"Error fetching coordinates: {str(e)}")
            return None
    
    def get_weather_by_coordinates(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Get weather by latitude and longitude
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Weather data dictionary
        """
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'units': TEMPERATURE_UNIT
            }
            
            data = self._make_request('weather', params)
            
            if data:
                logger.info(f"Successfully fetched weather for ({lat}, {lon})")
                return self._parse_weather_data(data)
            return None
        
        except Exception as e:
            logger.error(f"Error fetching weather by coordinates: {str(e)}")
            return None
    
    def get_forecast(self, city: str, days: int = 5, country_code: Optional[str] = None) -> Optional[Dict]:
        """
        Get weather forecast
        
        Args:
            city: City name
            days: Number of days (5 or 16 for free tier)
            country_code: ISO 3166 country code (optional)
            
        Returns:
            Forecast data dictionary
        """
        try:
            location = city
            if country_code:
                location = f"{city},{country_code}"
            
            params = {
                'q': location,
                'units': TEMPERATURE_UNIT,
                'cnt': days * 8  # 8 forecasts per day (3-hour intervals)
            }
            
            data = self._make_request('forecast', params)
            
            if data:
                logger.info(f"Successfully fetched forecast for {city}")
                return self._parse_forecast_data(data)
            return None
        
        except Exception as e:
            logger.error(f"Error fetching forecast: {str(e)}")
            return None
    
    def get_air_quality(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Get air quality data
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Air quality data dictionary
        """
        try:
            params = {
                'lat': lat,
                'lon': lon
            }
            
            response = requests.get(f"{WEATHER_API_URL}/air_pollution", 
                                  params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data and 'list' in data:
                logger.info(f"Successfully fetched air quality for ({lat}, {lon})")
                return self._parse_air_quality(data['list'][0])
            return None
        
        except Exception as e:
            logger.error(f"Error fetching air quality: {str(e)}")
            return None
    
    @staticmethod
    def _parse_weather_data(data: Dict) -> Dict:
        """Parse raw weather data into formatted dictionary"""
        return {
            'city': data.get('name', 'Unknown'),
            'country': data.get('sys', {}).get('country', 'Unknown'),
            'temperature': data.get('main', {}).get('temp', 0),
            'feels_like': data.get('main', {}).get('feels_like', 0),
            'temp_min': data.get('main', {}).get('temp_min', 0),
            'temp_max': data.get('main', {}).get('temp_max', 0),
            'pressure': data.get('main', {}).get('pressure', 0),
            'humidity': data.get('main', {}).get('humidity', 0),
            'description': data.get('weather', [{}])[0].get('description', 'Unknown'),
            'main': data.get('weather', [{}])[0].get('main', 'Unknown'),
            'icon': data.get('weather', [{}])[0].get('icon', '01d'),
            'wind_speed': data.get('wind', {}).get('speed', 0),
            'wind_deg': data.get('wind', {}).get('deg', 0),
            'wind_gust': data.get('wind', {}).get('gust', 0),
            'clouds': data.get('clouds', {}).get('all', 0),
            'visibility': data.get('visibility', 0),
            'rainfall': data.get('rain', {}).get('1h', 0),
            'snowfall': data.get('snow', {}).get('1h', 0),
            'uvi': data.get('uvi', 0),
            'sunrise': datetime.fromtimestamp(data.get('sys', {}).get('sunrise', 0)),
            'sunset': datetime.fromtimestamp(data.get('sys', {}).get('sunset', 0)),
            'timestamp': datetime.fromtimestamp(data.get('dt', 0))
        }
    
    @staticmethod
    def _parse_forecast_data(data: Dict) -> Dict:
        """Parse raw forecast data"""
        forecasts = []
        for item in data.get('list', []):
            forecasts.append({
                'time': datetime.fromtimestamp(item.get('dt', 0)),
                'temperature': item.get('main', {}).get('temp', 0),
                'feels_like': item.get('main', {}).get('feels_like', 0),
                'humidity': item.get('main', {}).get('humidity', 0),
                'pressure': item.get('main', {}).get('pressure', 0),
                'description': item.get('weather', [{}])[0].get('description', ''),
                'main': item.get('weather', [{}])[0].get('main', ''),
                'icon': item.get('weather', [{}])[0].get('icon', '01d'),
                'wind_speed': item.get('wind', {}).get('speed', 0),
                'clouds': item.get('clouds', {}).get('all', 0),
                'rainfall': item.get('rain', {}).get('3h', 0),
                'snowfall': item.get('snow', {}).get('3h', 0),
            })
        
        return {
            'city': data.get('city', {}).get('name', 'Unknown'),
            'country': data.get('city', {}).get('country', 'Unknown'),
            'forecasts': forecasts
        }
    
    @staticmethod
    def _parse_air_quality(data: Dict) -> Dict:
        """Parse air quality data"""
        aqi = data.get('main', {}).get('aqi', 0)
        components = data.get('components', {})
        
        aqi_names = {1: 'Good', 2: 'Fair', 3: 'Moderate', 4: 'Poor', 5: 'Very Poor'}
        
        return {
            'aqi': aqi,
            'aqi_level': aqi_names.get(aqi, 'Unknown'),
            'pm25': components.get('pm2_5', 0),
            'pm10': components.get('pm10', 0),
            'o3': components.get('o3', 0),
            'no2': components.get('no2', 0),
            'so2': components.get('so2', 0),
            'co': components.get('co', 0),
            'timestamp': datetime.fromtimestamp(data.get('dt', 0))
        }
