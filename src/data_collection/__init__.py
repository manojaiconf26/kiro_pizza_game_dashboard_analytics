"""
Data collection module for pizza game dashboard.

This module provides functionality for collecting data from both external APIs
and mock data generators for pizza orders and football matches.
"""

from .mock_generators import (
    MockDataGenerator,
    GeneratorConfig,
    create_default_config,
    generate_correlated_dataset
)

from .external_collectors import (
    ExternalDataCollector,
    DominosAPIClient,
    FootballAPIClient,
    DataCollectionSystem,
    APIConfig,
    RateLimiter,
    create_default_api_config,
    create_api_config_from_env
)

__all__ = [
    'MockDataGenerator',
    'GeneratorConfig', 
    'create_default_config',
    'generate_correlated_dataset',
    'ExternalDataCollector',
    'DominosAPIClient',
    'FootballAPIClient',
    'DataCollectionSystem',
    'APIConfig',
    'RateLimiter',
    'create_default_api_config',
    'create_api_config_from_env'
]