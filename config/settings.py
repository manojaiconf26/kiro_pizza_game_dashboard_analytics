"""
Configuration settings for Pizza Game Dashboard
"""
import os

# S3 Configuration
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'pizza-game-analytics-default')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# S3 Folder Structure
S3_FOLDERS = {
    'raw_dominos_real': 'raw-data/dominos-orders/real/',
    'raw_dominos_mock': 'raw-data/dominos-orders/mock/',
    'raw_football_real': 'raw-data/football-data/real/',
    'raw_football_mock': 'raw-data/football-data/mock/',
    'processed_merged': 'processed-data/merged-datasets/',
    'processed_correlation': 'processed-data/correlation-analysis/',
    'quicksight_data': 'quicksight-ready/dashboard-data/',
    'quicksight_metadata': 'quicksight-ready/metadata/'
}

# API Configuration
DOMINOS_API_CONFIG = {
    'base_url': os.environ.get('DOMINOS_API_URL', 'https://api.dominos.com/v1'),
    'api_key': os.environ.get('DOMINOS_API_KEY', ''),
    'store_id': os.environ.get('DOMINOS_STORE_ID', ''),
    'rate_limit': int(os.environ.get('DOMINOS_RATE_LIMIT', '100')),  # requests per minute
    'timeout': int(os.environ.get('API_TIMEOUT', '30'))  # seconds
}

FOOTBALL_API_CONFIG = {
    'base_url': os.environ.get('FOOTBALL_API_URL', 'https://api.football-data.org/v4'),
    'api_key': os.environ.get('FOOTBALL_API_KEY', ''),
    'rate_limit': int(os.environ.get('FOOTBALL_RATE_LIMIT', '60')),  # requests per minute
    'timeout': int(os.environ.get('API_TIMEOUT', '30'))  # seconds
}

# Rate Limiting Configuration
RATE_LIMIT_CONFIG = {
    'max_requests_per_minute': int(os.environ.get('MAX_REQUESTS_PER_MINUTE', '60')),
    'max_requests_per_hour': int(os.environ.get('MAX_REQUESTS_PER_HOUR', '1000')),
    'max_retries': int(os.environ.get('MAX_API_RETRIES', '3')),
    'backoff_factor': float(os.environ.get('BACKOFF_FACTOR', '1.0'))
}

# QuickSight Configuration
QUICKSIGHT_CONFIG = {
    'account_id': os.environ.get('QUICKSIGHT_ACCOUNT_ID', ''),
    'region': AWS_REGION,
    'namespace': 'default'
}

# Lambda Configuration
LAMBDA_CONFIG = {
    'timeout': 900,  # 15 minutes (maximum)
    'memory': 1024,  # MB
    'runtime': 'python3.9'
}

# Data Processing Configuration
PROCESSING_CONFIG = {
    'correlation_window_hours': 3,  # Hours before/after match to analyze orders
    'min_correlation_significance': 0.05,  # p-value threshold
    'mock_data_days': 30,  # Days of mock data to generate
    'mock_orders_per_day': 500  # Average orders per day for mock data
}