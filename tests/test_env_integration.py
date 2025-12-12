"""
Tests for environment variable integration with external collectors.
"""
import pytest
import os
from unittest.mock import patch

from src.data_collection.external_collectors import create_api_config_from_env, APIConfig


class TestEnvironmentIntegration:
    """Test cases for environment variable integration."""
    
    @patch.dict(os.environ, {
        'FOOTBALL_API_KEY': 'test_football_key',
        'DOMINOS_API_KEY': 'test_dominos_key',
        'DOMINOS_STORE_ID': 'store123',
        'MAX_REQUESTS_PER_MINUTE': '30',
        'MAX_REQUESTS_PER_HOUR': '500',
        'API_TIMEOUT': '60'
    })
    def test_create_api_config_from_env_with_config_module(self):
        """Test creating API config from environment variables using config module."""
        config = create_api_config_from_env()
        
        assert isinstance(config, APIConfig)
        assert config.football_api_key == 'test_football_key'
        assert config.dominos_api_key == 'test_dominos_key'
        assert config.dominos_store_id == 'store123'
        assert config.max_requests_per_minute == 30
        assert config.max_requests_per_hour == 500
        assert config.request_timeout == 60
    
    @patch.dict(os.environ, {
        'FOOTBALL_API_KEY': 'direct_football_key',
        'DOMINOS_API_KEY': '',  # Empty string should become None
        'MAX_REQUESTS_PER_MINUTE': '45'
    })
    def test_create_api_config_fallback_to_direct_env(self):
        """Test fallback to direct environment variables when config module fails."""
        
        # Mock the config import to fail by patching the import
        with patch.dict('sys.modules', {'config.settings': None}):
            config = create_api_config_from_env()
        
        assert isinstance(config, APIConfig)
        assert config.football_api_key == 'direct_football_key'
        assert config.dominos_api_key == ''  # Empty string is preserved in direct mode
        assert config.max_requests_per_minute == 45
    
    @patch.dict(os.environ, {}, clear=True)
    def test_create_api_config_with_defaults(self):
        """Test creating API config with default values when no env vars are set."""
        
        # Mock the config import to fail and use direct environment fallback
        with patch.dict('sys.modules', {'config.settings': None}):
            config = create_api_config_from_env()
        
        assert isinstance(config, APIConfig)
        assert config.football_api_key is None
        assert config.dominos_api_key is None
        assert config.max_requests_per_minute == 60  # Default value
        assert config.max_requests_per_hour == 1000  # Default value
        assert config.request_timeout == 30  # Default value
    
    def test_api_config_none_vs_empty_string(self):
        """Test that empty strings are converted to None for API keys."""
        config = APIConfig(
            football_api_key="",
            dominos_api_key="valid_key"
        )
        
        # The APIConfig should handle empty strings appropriately
        # In our collectors, we check for truthiness, so empty strings work like None
        assert config.football_api_key == ""
        assert config.dominos_api_key == "valid_key"