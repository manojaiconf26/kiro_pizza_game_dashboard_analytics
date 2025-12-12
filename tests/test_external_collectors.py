"""
Tests for external API collectors with fallback mechanisms.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests
import json

from src.data_collection.external_collectors import (
    APIConfig,
    RateLimiter,
    ExternalDataCollector,
    DominosAPIClient,
    FootballAPIClient,
    DataCollectionSystem,
    create_default_api_config
)
from src.models.pizza_order import DominosOrder
from src.models.football_match import FootballMatch


class TestAPIConfig:
    """Test cases for API configuration."""
    
    def test_default_config_creation(self):
        """Test creating default API configuration."""
        config = APIConfig()
        
        assert config.dominos_api_url == "https://api.dominos.com/v1"
        assert config.football_api_url == "https://api.football-data.org/v4"
        assert config.max_requests_per_minute == 60
        assert config.max_retries == 3
        assert 429 in config.retry_status_codes
    
    def test_custom_config_creation(self):
        """Test creating custom API configuration."""
        config = APIConfig(
            dominos_api_key="test_key",
            max_requests_per_minute=30,
            request_timeout=60
        )
        
        assert config.dominos_api_key == "test_key"
        assert config.max_requests_per_minute == 30
        assert config.request_timeout == 60
    
    def test_create_default_api_config_function(self):
        """Test the create_default_api_config helper function."""
        config = create_default_api_config(
            dominos_api_key="test_key",
            football_api_key="football_key"
        )
        
        assert isinstance(config, APIConfig)
        assert config.dominos_api_key == "test_key"
        assert config.football_api_key == "football_key"


class TestRateLimiter:
    """Test cases for rate limiting functionality."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(max_per_minute=30, max_per_hour=500)
        
        assert limiter.max_per_minute == 30
        assert limiter.max_per_hour == 500
        assert len(limiter.minute_requests) == 0
        assert len(limiter.hour_requests) == 0
    
    @patch('time.time')
    @patch('time.sleep')
    def test_rate_limiter_no_wait_needed(self, mock_sleep, mock_time):
        """Test rate limiter when no waiting is needed."""
        mock_time.return_value = 1000.0
        
        limiter = RateLimiter(max_per_minute=60, max_per_hour=1000)
        limiter.wait_if_needed()
        
        mock_sleep.assert_not_called()
        assert len(limiter.minute_requests) == 1
        assert len(limiter.hour_requests) == 1
    
    @patch('time.time')
    @patch('time.sleep')
    def test_rate_limiter_minute_limit_reached(self, mock_sleep, mock_time):
        """Test rate limiter when minute limit is reached."""
        mock_time.return_value = 1000.0
        
        limiter = RateLimiter(max_per_minute=2, max_per_hour=1000)
        
        # Fill up the minute limit
        limiter.minute_requests = [999.0, 999.5]  # Two requests in the last minute
        limiter.wait_if_needed()
        
        # Should sleep for the remaining time in the minute
        mock_sleep.assert_called_once()
        sleep_time = mock_sleep.call_args[0][0]
        assert sleep_time > 0


class TestExternalDataCollector:
    """Test cases for base external data collector."""
    
    def test_collector_initialization(self):
        """Test external data collector initialization."""
        config = APIConfig()
        collector = ExternalDataCollector(config)
        
        assert collector.config == config
        assert isinstance(collector.rate_limiter, RateLimiter)
        assert collector.session is not None
        assert collector.mock_generator is None
    
    @patch('requests.Session.get')
    def test_make_request_success(self, mock_get):
        """Test successful API request."""
        # Setup mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        config = APIConfig()
        collector = ExternalDataCollector(config)
        
        response = collector._make_request("https://api.example.com/test")
        
        assert response == mock_response
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_make_request_failure(self, mock_get):
        """Test failed API request."""
        # Setup mock to raise exception
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        config = APIConfig()
        collector = ExternalDataCollector(config)
        
        response = collector._make_request("https://api.example.com/test")
        
        assert response is None
    
    def test_get_mock_generator(self):
        """Test mock generator creation."""
        config = APIConfig()
        collector = ExternalDataCollector(config)
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        generator = collector._get_mock_generator(start_date, end_date)
        
        assert generator is not None
        assert collector.mock_generator == generator


class TestDominosAPIClient:
    """Test cases for Domino's API client."""
    
    def test_client_initialization(self):
        """Test Domino's API client initialization."""
        config = APIConfig(dominos_api_key="test_key", dominos_store_id="store123")
        client = DominosAPIClient(config)
        
        assert isinstance(client, ExternalDataCollector)
        assert client.config.dominos_api_key == "test_key"
    
    @patch.object(DominosAPIClient, '_fetch_real_orders')
    def test_collect_dominos_data_success(self, mock_fetch):
        """Test successful Domino's data collection."""
        # Setup mock orders
        mock_orders = [
            DominosOrder(
                order_id="ORD123",
                timestamp=datetime(2024, 1, 15, 18, 30),
                location="Test Location",
                order_total=25.99,
                pizza_types=["Pepperoni"],
                quantity=1,
                data_source="real"
            )
        ]
        mock_fetch.return_value = mock_orders
        
        config = APIConfig(dominos_api_key="test_key", dominos_store_id="store123")
        client = DominosAPIClient(config)
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        orders = client.collect_dominos_data(start_date, end_date)
        
        assert len(orders) == 1
        assert orders[0].data_source == "real"
        mock_fetch.assert_called_once_with(start_date, end_date)
    
    @patch.object(DominosAPIClient, '_fallback_to_mock_orders')
    def test_collect_dominos_data_no_credentials(self, mock_fallback):
        """Test Domino's data collection without credentials."""
        mock_orders = [
            DominosOrder(
                order_id="MOCK123",
                timestamp=datetime(2024, 1, 15, 18, 30),
                location="Mock Location",
                order_total=20.99,
                pizza_types=["Margherita"],
                quantity=1,
                data_source="mock"
            )
        ]
        mock_fallback.return_value = mock_orders
        
        config = APIConfig()  # No API credentials
        client = DominosAPIClient(config)
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        orders = client.collect_dominos_data(start_date, end_date)
        
        assert len(orders) == 1
        assert orders[0].data_source == "mock"
        mock_fallback.assert_called_once_with(start_date, end_date)
    
    def test_parse_dominos_response(self):
        """Test parsing Domino's API response."""
        config = APIConfig()
        client = DominosAPIClient(config)
        
        # Mock API response data
        api_data = {
            "orders": [
                {
                    "order_id": "DOM123",
                    "timestamp": "2024-01-15T18:30:00",
                    "store_location": "123 Main St",
                    "total_amount": 25.99,
                    "items": [
                        {"category": "pizza", "name": "Pepperoni", "quantity": 1},
                        {"category": "pizza", "name": "Margherita", "quantity": 1}
                    ]
                }
            ]
        }
        
        orders = client._parse_dominos_response(api_data)
        
        assert len(orders) == 1
        order = orders[0]
        assert order.order_id == "DOM123"
        assert order.location == "123 Main St"
        assert order.order_total == 25.99
        assert "Pepperoni" in order.pizza_types
        assert "Margherita" in order.pizza_types
        assert order.quantity == 2
        assert order.data_source == "real"
    
    @patch.object(DominosAPIClient, '_get_mock_generator')
    def test_fallback_to_mock_orders(self, mock_get_generator):
        """Test fallback to mock orders."""
        # Setup mock generator
        mock_generator = Mock()
        mock_orders = [
            DominosOrder(
                order_id="MOCK123",
                timestamp=datetime(2024, 1, 15, 18, 30),
                location="Mock Location",
                order_total=20.99,
                pizza_types=["Hawaiian"],
                quantity=1,
                data_source="mock"
            )
        ]
        mock_generator.generate_pizza_orders.return_value = mock_orders
        mock_get_generator.return_value = mock_generator
        
        config = APIConfig()
        client = DominosAPIClient(config)
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        orders = client._fallback_to_mock_orders(start_date, end_date)
        
        assert len(orders) == 1
        assert orders[0].data_source == "mock"
        mock_generator.generate_pizza_orders.assert_called_once()


class TestFootballAPIClient:
    """Test cases for Football API client."""
    
    def test_client_initialization(self):
        """Test Football API client initialization."""
        config = APIConfig(football_api_key="test_key")
        client = FootballAPIClient(config)
        
        assert isinstance(client, ExternalDataCollector)
        assert client.config.football_api_key == "test_key"
    
    @patch.object(FootballAPIClient, '_fetch_real_matches')
    def test_collect_football_data_success(self, mock_fetch):
        """Test successful football data collection."""
        # Setup mock matches
        mock_matches = [
            FootballMatch(
                match_id="MATCH123",
                timestamp=datetime(2024, 1, 15, 15, 0),
                home_team="Arsenal",
                away_team="Chelsea",
                home_score=2,
                away_score=1,
                event_type="win",
                match_significance="regular",
                data_source="real"
            )
        ]
        mock_fetch.return_value = mock_matches
        
        config = APIConfig(football_api_key="test_key")
        client = FootballAPIClient(config)
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        matches = client.collect_football_data(start_date, end_date)
        
        assert len(matches) == 1
        assert matches[0].data_source == "real"
        mock_fetch.assert_called_once_with(start_date, end_date)
    
    def test_parse_football_response(self):
        """Test parsing football API response."""
        config = APIConfig()
        client = FootballAPIClient(config)
        
        # Mock API response data (football-data.org format)
        api_data = {
            "matches": [
                {
                    "id": 12345,
                    "utcDate": "2024-01-15T15:00:00Z",
                    "homeTeam": {"name": "Arsenal"},
                    "awayTeam": {"name": "Chelsea"},
                    "score": {
                        "fullTime": {"home": 2, "away": 1}
                    },
                    "stage": "REGULAR_SEASON"
                }
            ]
        }
        
        matches = client._parse_football_response(api_data)
        
        assert len(matches) == 1
        match = matches[0]
        assert match.match_id == "12345"
        assert match.home_team == "Arsenal"
        assert match.away_team == "Chelsea"
        assert match.home_score == 2
        assert match.away_score == 1
        assert match.event_type == "win"
        assert match.match_significance == "regular"
        assert match.data_source == "real"


class TestDataCollectionSystem:
    """Test cases for the main data collection system."""
    
    def test_system_initialization(self):
        """Test data collection system initialization."""
        config = APIConfig()
        system = DataCollectionSystem(config)
        
        assert system.config == config
        assert isinstance(system.dominos_client, DominosAPIClient)
        assert isinstance(system.football_client, FootballAPIClient)
    
    @patch.object(DominosAPIClient, 'collect_dominos_data')
    @patch.object(FootballAPIClient, 'collect_football_data')
    def test_collect_all_data(self, mock_football, mock_dominos):
        """Test collecting all data from both sources."""
        # Setup mock data
        mock_orders = [
            DominosOrder(
                order_id="ORD123",
                timestamp=datetime(2024, 1, 15, 18, 30),
                location="Test Location",
                order_total=25.99,
                pizza_types=["Pepperoni"],
                quantity=1,
                data_source="mock"
            )
        ]
        
        mock_matches = [
            FootballMatch(
                match_id="MATCH123",
                timestamp=datetime(2024, 1, 15, 15, 0),
                home_team="Arsenal",
                away_team="Chelsea",
                home_score=2,
                away_score=1,
                event_type="win",
                match_significance="regular",
                data_source="mock"
            )
        ]
        
        mock_dominos.return_value = mock_orders
        mock_football.return_value = mock_matches
        
        config = APIConfig()
        system = DataCollectionSystem(config)
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        orders, matches = system.collect_all_data(start_date, end_date)
        
        assert len(orders) == 1
        assert len(matches) == 1
        assert orders[0].order_id == "ORD123"
        assert matches[0].match_id == "MATCH123"
        
        mock_dominos.assert_called_once_with(start_date, end_date)
        mock_football.assert_called_once_with(start_date, end_date)
    
    def test_handle_api_errors_rate_limit(self):
        """Test handling rate limit errors."""
        config = APIConfig()
        system = DataCollectionSystem(config)
        
        # Mock response with rate limit
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '60'}
        
        with patch('time.sleep') as mock_sleep:
            should_retry = system.handle_api_errors(mock_response)
            
            assert should_retry is True
            mock_sleep.assert_called_once_with(60)
    
    def test_handle_api_errors_server_error(self):
        """Test handling server errors."""
        config = APIConfig()
        system = DataCollectionSystem(config)
        
        # Mock response with server error
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch('time.sleep') as mock_sleep:
            should_retry = system.handle_api_errors(mock_response)
            
            assert should_retry is True
            mock_sleep.assert_called_once()
    
    def test_handle_api_errors_auth_error(self):
        """Test handling authentication errors."""
        config = APIConfig()
        system = DataCollectionSystem(config)
        
        # Mock response with auth error
        mock_response = Mock()
        mock_response.status_code = 401
        
        should_retry = system.handle_api_errors(mock_response)
        
        assert should_retry is False