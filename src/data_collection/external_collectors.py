"""
External API collectors for pizza orders and football data.

This module provides comprehensive API integration for collecting real-time data from:
- Football-data.org API (Premier League matches, scores, events)
- Domino's API (pizza orders, timestamps, locations) - prepared but uses mock by default

Key Features:
- Intelligent fallback to realistic mock data when APIs are unavailable
- Rate limiting compliance (10 requests/minute for football-data.org free tier)
- Exponential backoff retry logic for transient failures
- Comprehensive error handling with detailed logging
- Authentication management with environment variable configuration
- Data source labeling throughout the pipeline for analysis transparency

Authentication Methods:
- Football API: X-Auth-Token header with API key from football-data.org
- Domino's API: Bearer token authentication (requires business partnership)
- Environment variables: FOOTBALL_API_KEY, DOMINOS_API_KEY, DOMINOS_STORE_ID

Error Handling Strategy:
1. Network errors → Retry with exponential backoff (max 3 attempts)
2. Rate limiting → Wait for Retry-After header or implement backoff
3. Authentication errors → Log error and fall back to mock data
4. API unavailable → Seamlessly switch to mock data generation
5. Data parsing errors → Skip invalid records, continue processing

Requirements Satisfied:
- 1.1, 1.3, 2.1, 2.3: API fallback consistency
- 1.4, 2.2: Complete data extraction
- 1.2, 4.3: Robust error handling
- 1.5: Rate limiting compliance
"""

import time
import random
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

from ..models.pizza_order import DominosOrder
from ..models.football_match import FootballMatch
from .mock_generators import MockDataGenerator, GeneratorConfig, create_default_config


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """Configuration for external API clients."""
    
    # Domino's API configuration
    dominos_api_url: str = "https://api.dominos.com/v1"
    dominos_api_key: Optional[str] = None
    dominos_store_id: Optional[str] = None
    
    # Football API configuration
    football_api_url: str = "https://api.football-data.org/v4"
    football_api_key: Optional[str] = None
    
    # Rate limiting configuration
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    
    # Retry configuration
    max_retries: int = 3
    backoff_factor: float = 1.0
    retry_status_codes: List[int] = None
    
    # Timeout configuration
    request_timeout: int = 30
    
    def __post_init__(self):
        """Set default retry status codes if not provided."""
        if self.retry_status_codes is None:
            self.retry_status_codes = [429, 500, 502, 503, 504]


class RateLimiter:
    """
    Rate limiter to ensure API usage stays within provider limits.
    
    Implements sliding window rate limiting for both minute and hour intervals.
    This is crucial for the football-data.org free tier which allows only
    10 requests per minute. Exceeding limits results in 429 errors and
    temporary API access suspension.
    
    Algorithm:
    1. Maintain lists of request timestamps for minute and hour windows
    2. Before each request, clean expired timestamps from tracking lists
    3. Check if current request count would exceed limits
    4. If limit would be exceeded, calculate sleep time and wait
    5. Record successful request timestamp for future limit calculations
    
    Thread Safety: Not thread-safe. Use separate instances for concurrent access.
    """
    
    def __init__(self, max_per_minute: int = 60, max_per_hour: int = 1000):
        """
        Initialize rate limiter with configurable limits.
        
        Args:
            max_per_minute: Maximum requests per minute (default: 60)
                          For football-data.org free tier, this should be 10
            max_per_hour: Maximum requests per hour (default: 1000)
                         For football-data.org free tier, this should be 600
        
        Note: Default values are conservative. Actual API limits may be lower.
        """
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        
        # Track request timestamps in sliding windows
        # Each list contains Unix timestamps of recent requests
        self.minute_requests = []  # Requests in last 60 seconds
        self.hour_requests = []    # Requests in last 3600 seconds
    
    def wait_if_needed(self) -> None:
        """
        Wait if necessary to respect rate limits using sliding window algorithm.
        
        This method implements proactive rate limiting to prevent 429 errors:
        1. Clean expired timestamps from tracking windows
        2. Check if making a request now would exceed limits
        3. If so, calculate minimum wait time and sleep
        4. Record the request timestamp for future calculations
        
        The algorithm ensures we never exceed limits by waiting for the oldest
        request in the window to expire before making a new request.
        
        Performance Note: This method blocks the calling thread when rate limits
        are approached. For high-throughput scenarios, consider async alternatives.
        """
        now = time.time()
        
        # Clean expired requests from sliding windows
        # Remove requests older than 60 seconds from minute window
        self.minute_requests = [req_time for req_time in self.minute_requests 
                               if now - req_time < 60]
        
        # Remove requests older than 3600 seconds (1 hour) from hour window
        self.hour_requests = [req_time for req_time in self.hour_requests 
                             if now - req_time < 3600]
        
        # Check minute-level rate limit
        if len(self.minute_requests) >= self.max_per_minute:
            # Calculate how long to wait for oldest request to expire
            oldest_request = self.minute_requests[0]
            sleep_time = 60 - (now - oldest_request)
            
            if sleep_time > 0:
                logger.info(f"Minute rate limit reached ({len(self.minute_requests)}/{self.max_per_minute}), "
                           f"sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                
                # Update 'now' after sleeping
                now = time.time()
        
        # Check hour-level rate limit
        if len(self.hour_requests) >= self.max_per_hour:
            # Calculate how long to wait for oldest request to expire
            oldest_request = self.hour_requests[0]
            sleep_time = 3600 - (now - oldest_request)
            
            if sleep_time > 0:
                logger.info(f"Hourly rate limit reached ({len(self.hour_requests)}/{self.max_per_hour}), "
                           f"sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                
                # Update 'now' after sleeping
                now = time.time()
        
        # Record this request timestamp in both windows
        # This ensures future calls will account for this request
        self.minute_requests.append(now)
        self.hour_requests.append(now)


class ExternalDataCollector:
    """
    Base class for external API data collection with error handling and fallback.
    """
    
    def __init__(self, config: APIConfig):
        """
        Initialize the external data collector.
        
        Args:
            config: API configuration parameters
        """
        self.config = config
        self.rate_limiter = RateLimiter(
            config.max_requests_per_minute,
            config.max_requests_per_hour
        )
        
        # Configure HTTP session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=config.max_retries,
            backoff_factor=config.backoff_factor,
            status_forcelist=config.retry_status_codes,
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Initialize mock data generator for fallback
        self.mock_generator = None
    
    def _make_request(self, url: str, headers: Dict[str, str] = None, 
                     params: Dict[str, Any] = None) -> Optional[requests.Response]:
        """
        Make a rate-limited HTTP request with error handling.
        
        Args:
            url: Request URL
            headers: Request headers
            params: Request parameters
            
        Returns:
            Response object or None if request failed
        """
        self.rate_limiter.wait_if_needed()
        
        try:
            response = self.session.get(
                url,
                headers=headers or {},
                params=params or {},
                timeout=self.config.request_timeout
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def _get_mock_generator(self, start_date: datetime, end_date: datetime) -> MockDataGenerator:
        """
        Get or create mock data generator for fallback.
        
        Args:
            start_date: Start date for mock data
            end_date: End date for mock data
            
        Returns:
            MockDataGenerator instance
        """
        if self.mock_generator is None:
            config = create_default_config(start_date, end_date)
            self.mock_generator = MockDataGenerator(config)
        return self.mock_generator


class DominosAPIClient(ExternalDataCollector):
    """
    Client for collecting Domino's pizza order data from external APIs.
    """
    
    def collect_dominos_data(self, start_date: datetime, end_date: datetime) -> List[DominosOrder]:
        """
        Collect Domino's order data from external API with fallback to mock data.
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            
        Returns:
            List of DominosOrder objects
        """
        logger.info(f"Collecting Domino's data from {start_date} to {end_date}")
        
        # Check if API credentials are available
        if not self.config.dominos_api_key or not self.config.dominos_store_id:
            logger.warning("Domino's API credentials not available, using mock data")
            return self._fallback_to_mock_orders(start_date, end_date)
        
        try:
            orders = self._fetch_real_orders(start_date, end_date)
            if orders:
                logger.info(f"Successfully collected {len(orders)} real Domino's orders")
                return orders
            else:
                logger.warning("No real orders retrieved, falling back to mock data")
                return self._fallback_to_mock_orders(start_date, end_date)
                
        except Exception as e:
            logger.error(f"Failed to collect real Domino's data: {e}")
            return self._fallback_to_mock_orders(start_date, end_date)
    
    def _fetch_real_orders(self, start_date: datetime, end_date: datetime) -> List[DominosOrder]:
        """
        Fetch real order data from Domino's API.
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            
        Returns:
            List of DominosOrder objects from real API
        """
        orders = []
        
        # Prepare API request headers
        headers = {
            'Authorization': f'Bearer {self.config.dominos_api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Iterate through date range (API might have daily limits)
        current_date = start_date
        while current_date <= end_date:
            next_date = min(current_date + timedelta(days=1), end_date)
            
            # Prepare request parameters
            params = {
                'store_id': self.config.dominos_store_id,
                'start_date': current_date.isoformat(),
                'end_date': next_date.isoformat(),
                'include_details': 'true'
            }
            
            # Make API request
            url = f"{self.config.dominos_api_url}/orders"
            response = self._make_request(url, headers, params)
            
            if response:
                try:
                    data = response.json()
                    daily_orders = self._parse_dominos_response(data)
                    orders.extend(daily_orders)
                    
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Failed to parse Domino's API response: {e}")
            
            current_date = next_date
        
        return orders
    
    def _parse_dominos_response(self, api_data: Dict[str, Any]) -> List[DominosOrder]:
        """
        Parse Domino's API response into DominosOrder objects.
        
        Args:
            api_data: Raw API response data
            
        Returns:
            List of parsed DominosOrder objects
        """
        orders = []
        
        # Expected API response structure (this would need to match real Domino's API)
        for order_data in api_data.get('orders', []):
            try:
                # Parse pizza types from order items
                pizza_types = []
                for item in order_data.get('items', []):
                    if item.get('category') == 'pizza':
                        pizza_types.append(item.get('name', 'Unknown Pizza'))
                
                # Calculate total quantity
                total_quantity = sum(item.get('quantity', 1) for item in order_data.get('items', []))
                
                order = DominosOrder(
                    order_id=order_data['order_id'],
                    timestamp=datetime.fromisoformat(order_data['timestamp']),
                    location=order_data.get('store_location', 'Unknown Location'),
                    order_total=float(order_data.get('total_amount', 0.0)),
                    pizza_types=pizza_types or ['Unknown Pizza'],
                    quantity=max(1, total_quantity),
                    data_source='real'
                )
                
                orders.append(order)
                
            except (KeyError, ValueError, TypeError) as e:
                logger.error(f"Failed to parse order data: {e}")
                continue
        
        return orders
    
    def _fallback_to_mock_orders(self, start_date: datetime, end_date: datetime) -> List[DominosOrder]:
        """
        Generate mock Domino's orders as fallback.
        
        Args:
            start_date: Start date for mock data
            end_date: End date for mock data
            
        Returns:
            List of mock DominosOrder objects
        """
        logger.info("Generating mock Domino's orders as fallback")
        
        mock_generator = self._get_mock_generator(start_date, end_date)
        orders = mock_generator.generate_pizza_orders()
        
        logger.info(f"Generated {len(orders)} mock Domino's orders")
        return orders


class FootballAPIClient(ExternalDataCollector):
    """
    Client for collecting football match data from external APIs.
    """
    
    def collect_football_data(self, start_date: datetime, end_date: datetime) -> List[FootballMatch]:
        """
        Collect football match data from external API with fallback to mock data.
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            
        Returns:
            List of FootballMatch objects
        """
        logger.info(f"Collecting football data from {start_date} to {end_date}")
        
        # Check if API credentials are available
        if not self.config.football_api_key:
            logger.warning("Football API credentials not available, using mock data")
            return self._fallback_to_mock_matches(start_date, end_date)
        
        try:
            matches = self._fetch_real_matches(start_date, end_date)
            if matches:
                logger.info(f"Successfully collected {len(matches)} real football matches")
                return matches
            else:
                logger.warning("No real matches retrieved, falling back to mock data")
                return self._fallback_to_mock_matches(start_date, end_date)
                
        except Exception as e:
            logger.error(f"Failed to collect real football data: {e}")
            return self._fallback_to_mock_matches(start_date, end_date)
    
    def _fetch_real_matches(self, start_date: datetime, end_date: datetime) -> List[FootballMatch]:
        """
        Fetch real match data from football API.
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            
        Returns:
            List of FootballMatch objects from real API
        """
        matches = []
        
        # Prepare API request headers
        headers = {
            'X-Auth-Token': self.config.football_api_key,
            'Content-Type': 'application/json'
        }
        
        # Get matches from Premier League (competition ID 2021 in football-data.org API)
        params = {
            'dateFrom': start_date.strftime('%Y-%m-%d'),
            'dateTo': end_date.strftime('%Y-%m-%d'),
            'status': 'FINISHED'  # Only get completed matches
        }
        
        # Make API request
        url = f"{self.config.football_api_url}/competitions/2021/matches"
        response = self._make_request(url, headers, params)
        
        if response:
            try:
                data = response.json()
                matches = self._parse_football_response(data)
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Failed to parse football API response: {e}")
        
        return matches
    
    def _parse_football_response(self, api_data: Dict[str, Any]) -> List[FootballMatch]:
        """
        Parse football API response into FootballMatch objects.
        
        Args:
            api_data: Raw API response data
            
        Returns:
            List of parsed FootballMatch objects
        """
        matches = []
        
        # Expected API response structure (football-data.org format)
        for match_data in api_data.get('matches', []):
            try:
                # Parse match details
                home_team = match_data['homeTeam']['name']
                away_team = match_data['awayTeam']['name']
                home_score = match_data['score']['fullTime']['home']
                away_score = match_data['score']['fullTime']['away']
                
                # Determine event type based on scores
                if home_score > away_score:
                    event_type = 'win'
                elif away_score > home_score:
                    event_type = 'loss'
                else:
                    event_type = 'draw'
                
                # Determine match significance
                competition_stage = match_data.get('stage', 'REGULAR_SEASON')
                if 'FINAL' in competition_stage:
                    match_significance = 'final'
                elif competition_stage != 'REGULAR_SEASON':
                    match_significance = 'tournament'
                else:
                    match_significance = 'regular'
                
                match = FootballMatch(
                    match_id=str(match_data['id']),
                    timestamp=datetime.fromisoformat(match_data['utcDate'].replace('Z', '+00:00')),
                    home_team=home_team,
                    away_team=away_team,
                    home_score=home_score,
                    away_score=away_score,
                    event_type=event_type,
                    match_significance=match_significance,
                    data_source='real'
                )
                
                matches.append(match)
                
            except (KeyError, ValueError, TypeError) as e:
                logger.error(f"Failed to parse match data: {e}")
                continue
        
        return matches
    
    def _fallback_to_mock_matches(self, start_date: datetime, end_date: datetime) -> List[FootballMatch]:
        """
        Generate mock football matches as fallback.
        
        Args:
            start_date: Start date for mock data
            end_date: End date for mock data
            
        Returns:
            List of mock FootballMatch objects
        """
        logger.info("Generating mock football matches as fallback")
        
        mock_generator = self._get_mock_generator(start_date, end_date)
        matches = mock_generator.generate_football_matches()
        
        logger.info(f"Generated {len(matches)} mock football matches")
        return matches


class DataCollectionSystem:
    """
    Main system for coordinating data collection from multiple sources.
    """
    
    def __init__(self, config: APIConfig):
        """
        Initialize the data collection system.
        
        Args:
            config: API configuration parameters
        """
        self.config = config
        self.dominos_client = DominosAPIClient(config)
        self.football_client = FootballAPIClient(config)
    
    def collect_all_data(self, start_date: datetime, end_date: datetime) -> Tuple[List[DominosOrder], List[FootballMatch]]:
        """
        Collect both pizza orders and football matches for the specified date range.
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            
        Returns:
            Tuple of (pizza_orders, football_matches)
        """
        logger.info(f"Starting data collection from {start_date} to {end_date}")
        
        # Collect pizza orders
        pizza_orders = self.dominos_client.collect_dominos_data(start_date, end_date)
        
        # Collect football matches
        football_matches = self.football_client.collect_football_data(start_date, end_date)
        
        logger.info(f"Data collection complete: {len(pizza_orders)} orders, {len(football_matches)} matches")
        
        return pizza_orders, football_matches
    
    def handle_api_errors(self, response: requests.Response) -> bool:
        """
        Handle API errors and determine if retry is appropriate.
        
        Args:
            response: HTTP response object
            
        Returns:
            True if retry is recommended, False otherwise
        """
        if response.status_code == 429:  # Rate limit exceeded
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                sleep_time = int(retry_after)
                logger.warning(f"Rate limit exceeded, waiting {sleep_time} seconds")
                time.sleep(sleep_time)
                return True
        
        elif response.status_code in [500, 502, 503, 504]:  # Server errors
            # Exponential backoff for server errors
            sleep_time = self.config.backoff_factor * (2 ** random.randint(0, 3))
            logger.warning(f"Server error {response.status_code}, waiting {sleep_time} seconds")
            time.sleep(sleep_time)
            return True
        
        elif response.status_code == 401:  # Authentication error
            logger.error("Authentication failed - check API credentials")
            return False
        
        elif response.status_code == 403:  # Forbidden
            logger.error("Access forbidden - check API permissions")
            return False
        
        else:
            logger.error(f"Unhandled API error: {response.status_code}")
            return False


def create_default_api_config(**kwargs) -> APIConfig:
    """
    Create a default API configuration with sensible defaults.
    
    Args:
        **kwargs: Configuration parameters to override defaults
        
    Returns:
        APIConfig with specified parameters
    """
    return APIConfig(**kwargs)


def create_api_config_from_env() -> APIConfig:
    """
    Create API configuration from environment variables.
    
    This function reads configuration from environment variables,
    which is the recommended approach for Lambda functions.
    
    Returns:
        APIConfig configured from environment variables
    """
    import os
    
    try:
        from config.settings import (
            DOMINOS_API_CONFIG, 
            FOOTBALL_API_CONFIG, 
            RATE_LIMIT_CONFIG
        )
        
        return APIConfig(
            # Domino's API configuration
            dominos_api_url=DOMINOS_API_CONFIG['base_url'],
            dominos_api_key=DOMINOS_API_CONFIG['api_key'] or None,
            dominos_store_id=DOMINOS_API_CONFIG.get('store_id') or None,
            
            # Football API configuration
            football_api_url=FOOTBALL_API_CONFIG['base_url'],
            football_api_key=FOOTBALL_API_CONFIG['api_key'] or None,
            
            # Rate limiting configuration
            max_requests_per_minute=RATE_LIMIT_CONFIG['max_requests_per_minute'],
            max_requests_per_hour=RATE_LIMIT_CONFIG['max_requests_per_hour'],
            max_retries=RATE_LIMIT_CONFIG['max_retries'],
            backoff_factor=RATE_LIMIT_CONFIG['backoff_factor'],
            
            # Timeout configuration
            request_timeout=DOMINOS_API_CONFIG['timeout']
        )
        
    except ImportError:
        # Fallback if config module is not available
        logger.warning("Config module not available, using environment variables directly")
        
        return APIConfig(
            dominos_api_url=os.environ.get('DOMINOS_API_URL', 'https://api.dominos.com/v1'),
            dominos_api_key=os.environ.get('DOMINOS_API_KEY'),
            dominos_store_id=os.environ.get('DOMINOS_STORE_ID'),
            football_api_url=os.environ.get('FOOTBALL_API_URL', 'https://api.football-data.org/v4'),
            football_api_key=os.environ.get('FOOTBALL_API_KEY'),
            max_requests_per_minute=int(os.environ.get('MAX_REQUESTS_PER_MINUTE', '60')),
            max_requests_per_hour=int(os.environ.get('MAX_REQUESTS_PER_HOUR', '1000')),
            max_retries=int(os.environ.get('MAX_API_RETRIES', '3')),
            backoff_factor=float(os.environ.get('BACKOFF_FACTOR', '1.0')),
            request_timeout=int(os.environ.get('API_TIMEOUT', '30'))
        )