"""Flask web application for weather dashboard"""
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
from datetime import datetime

from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, ENABLE_FORECAST, ENABLE_ALERTS
from weather_api import WeatherAPIClient
from cache_manager import CacheManager, HistoryManager
from logger_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Initialize managers
api_client = WeatherAPIClient()
cache_manager = CacheManager()
history_manager = HistoryManager()


@app.route('/')
def index():
    """Render main dashboard page"""
    return render_template('index.html')


@app.route('/api/weather/current', methods=['GET'])
def get_current_weather():
    """
    API endpoint for current weather
    
    Query parameters:
    - city: City name (required)
    - country: Country code (optional)
    """
    try:
        city = request.args.get('city')
        country = request.args.get('country')
        
        if not city:
            return jsonify({'error': 'City parameter required'}), 400
        
        # Check cache
        cache_key = f"weather_{city}_{country}" if country else f"weather_{city}"
        cached_data = cache_manager.get(cache_key)
        
        if cached_data:
            return jsonify({
                'success': True,
                'data': cached_data,
                'from_cache': True
            })
        
        # Fetch from API
        weather_data = api_client.get_current_weather(city, country)
        
        if weather_data:
            # Cache the data
            cache_manager.set(cache_key, weather_data)
            
            # Save to history
            history_manager.save_weather(city, weather_data)
            
            return jsonify({
                'success': True,
                'data': weather_data,
                'from_cache': False
            })
        else:
            return jsonify({'error': 'Failed to fetch weather data'}), 500
    
    except Exception as e:
        logger.error(f"Error in get_current_weather: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/weather/forecast', methods=['GET'])
def get_forecast():
    """
    API endpoint for weather forecast
    
    Query parameters:
    - city: City name (required)
    - days: Number of days (optional, default 5)
    - country: Country code (optional)
    """
    try:
        if not ENABLE_FORECAST:
            return jsonify({'error': 'Forecast feature is disabled'}), 403
        
        city = request.args.get('city')
        days = int(request.args.get('days', 5))
        country = request.args.get('country')
        
        if not city:
            return jsonify({'error': 'City parameter required'}), 400
        
        # Check cache
        cache_key = f"forecast_{city}_{country}_{days}" if country else f"forecast_{city}_{days}"
        cached_data = cache_manager.get(cache_key)
        
        if cached_data:
            return jsonify({
                'success': True,
                'data': cached_data,
                'from_cache': True
            })
        
        # Fetch from API
        forecast_data = api_client.get_forecast(city, days, country)
        
        if forecast_data:
            cache_manager.set(cache_key, forecast_data)
            
            return jsonify({
                'success': True,
                'data': forecast_data,
                'from_cache': False
            })
        else:
            return jsonify({'error': 'Failed to fetch forecast data'}), 500
    
    except Exception as e:
        logger.error(f"Error in get_forecast: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/weather/air-quality', methods=['GET'])
def get_air_quality():
    """
    API endpoint for air quality
    
    Query parameters:
    - city: City name (required)
    - country: Country code (optional)
    """
    try:
        city = request.args.get('city')
        country = request.args.get('country')
        
        if not city:
            return jsonify({'error': 'City parameter required'}), 400
        
        # Get coordinates
        coords = api_client.get_coordinates_by_city(city, country)
        
        if not coords:
            return jsonify({'error': 'City not found'}), 404
        
        lat, lon = coords
        
        # Check cache
        cache_key = f"air_quality_{lat}_{lon}"
        cached_data = cache_manager.get(cache_key)
        
        if cached_data:
            return jsonify({
                'success': True,
                'data': cached_data,
                'from_cache': True
            })
        
        # Fetch from API
        air_quality_data = api_client.get_air_quality(lat, lon)
        
        if air_quality_data:
            cache_manager.set(cache_key, air_quality_data)
            
            return jsonify({
                'success': True,
                'data': air_quality_data,
                'from_cache': False
            })
        else:
            return jsonify({'error': 'Failed to fetch air quality data'}), 500
    
    except Exception as e:
        logger.error(f"Error in get_air_quality: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/weather/history', methods=['GET'])
def get_history():
    """
    API endpoint for weather history
    
    Query parameters:
    - city: City name (required)
    - limit: Number of records (optional, default 50)
    """
    try:
        city = request.args.get('city')
        limit = int(request.args.get('limit', 50))
        
        if not city:
            return jsonify({'error': 'City parameter required'}), 400
        
        history = history_manager.get_history(city, limit)
        
        return jsonify({
            'success': True,
            'data': history
        })
    
    except Exception as e:
        logger.error(f"Error in get_history: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/info', methods=['GET'])
def cache_info():
    """Get cache information"""
    try:
        info = cache_manager.get_cache_info()
        return jsonify({
            'success': True,
            'data': info
        })
    except Exception as e:
        logger.error(f"Error in cache_info: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cache"""
    try:
        cache_manager.clear()
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        })
    except Exception as e:
        logger.error(f"Error in clear_cache: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    logger.info(f"Starting Weather Dashboard on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
