"""Data caching and storage management"""
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import pickle

from config import CACHE_TIMEOUT

logger = logging.getLogger(__name__)


class CacheManager:
    """Manage caching of weather data"""
    
    def __init__(self, cache_dir: str = './cache', timeout: int = CACHE_TIMEOUT):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory to store cache files
            timeout: Cache timeout in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.memory_cache = {}
    
    def get(self, key: str) -> Optional[Dict]:
        """
        Get data from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if expired/not found
        """
        # Check memory cache first
        if key in self.memory_cache:
            data, timestamp = self.memory_cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.timeout):
                logger.debug(f"Cache hit (memory): {key}")
                return data
            else:
                del self.memory_cache[key]
        
        # Check file cache
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            try:
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if datetime.now() - file_time < timedelta(seconds=self.timeout):
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                    logger.debug(f"Cache hit (file): {key}")
                    self.memory_cache[key] = (data, datetime.now())
                    return data
                else:
                    cache_file.unlink()
            except Exception as e:
                logger.error(f"Error reading cache file: {str(e)}")
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(self, key: str, data: Dict) -> None:
        """
        Store data in cache
        
        Args:
            key: Cache key
            data: Data to cache
        """
        try:
            # Store in memory cache
            self.memory_cache[key] = (data, datetime.now())
            
            # Store in file cache
            cache_file = self.cache_dir / f"{key}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            logger.debug(f"Data cached: {key}")
        except Exception as e:
            logger.error(f"Error writing cache: {str(e)}")
    
    def clear(self) -> None:
        """Clear all cache"""
        self.memory_cache.clear()
        for cache_file in self.cache_dir.glob('*.pkl'):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.error(f"Error deleting cache file: {str(e)}")
        logger.info("Cache cleared")
    
    def clear_expired(self) -> None:
        """Clear expired cache files"""
        now = datetime.now()
        for cache_file in self.cache_dir.glob('*.pkl'):
            try:
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if now - file_time > timedelta(seconds=self.timeout):
                    cache_file.unlink()
            except Exception as e:
                logger.error(f"Error processing cache file: {str(e)}")
        logger.info("Expired cache cleared")
    
    def get_cache_info(self) -> Dict:
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob('*.pkl'))
        total_size = sum(f.stat().st_size for f in cache_files) / 1024  # KB
        
        return {
            'cached_items': len(cache_files),
            'total_size_kb': round(total_size, 2),
            'memory_cache_items': len(self.memory_cache),
            'timeout': self.timeout
        }


class HistoryManager:
    """Manage weather history data"""
    
    def __init__(self, history_dir: str = './history'):
        """
        Initialize history manager
        
        Args:
            history_dir: Directory to store history files
        """
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def save_weather(self, city: str, weather_data: Dict) -> None:
        """
        Save weather data to history
        
        Args:
            city: City name
            weather_data: Weather data dictionary
        """
        try:
            history_file = self.history_dir / f"{city.lower()}_history.json"
            
            history = []
            if history_file.exists():
                with open(history_file, 'r') as f:
                    history = json.load(f)
            
            # Add timestamp to weather data
            record = {
                **weather_data,
                'recorded_at': datetime.now().isoformat()
            }
            
            history.append(record)
            
            # Keep only last 100 records
            history = history[-100:]
            
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2, default=str)
            
            logger.info(f"Weather history saved for {city}")
        except Exception as e:
            logger.error(f"Error saving weather history: {str(e)}")
    
    def get_history(self, city: str, limit: int = 50) -> List[Dict]:
        """
        Get weather history for a city
        
        Args:
            city: City name
            limit: Number of records to retrieve
            
        Returns:
            List of weather records
        """
        try:
            history_file = self.history_dir / f"{city.lower()}_history.json"
            
            if not history_file.exists():
                return []
            
            with open(history_file, 'r') as f:
                history = json.load(f)
            
            return history[-limit:]
        except Exception as e:
            logger.error(f"Error reading weather history: {str(e)}")
            return []
    
    def clear_history(self, city: Optional[str] = None) -> None:
        """
        Clear history for a city or all cities
        
        Args:
            city: City name (None to clear all)
        """
        try:
            if city:
                history_file = self.history_dir / f"{city.lower()}_history.json"
                if history_file.exists():
                    history_file.unlink()
                    logger.info(f"History cleared for {city}")
            else:
                for history_file in self.history_dir.glob('*.json'):
                    history_file.unlink()
                logger.info("All history cleared")
        except Exception as e:
            logger.error(f"Error clearing history: {str(e)}")
