"""
Main Lambda function handler for Pizza Game Dashboard
Handles the complete pipeline: data collection, processing, and QuickSight updates
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from src.data_collection import (
    DataCollectionSystem,
    create_api_config_from_env
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for the pizza game dashboard pipeline
    
    Args:
        event: Lambda event data
        context: Lambda context object
        
    Returns:
        Dict containing execution status and results
    """
    try:
        logger.info("Starting Pizza Game Dashboard pipeline execution")
        
        # Extract parameters from event or use defaults
        date_range_days = event.get('date_range_days', 7)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range_days)
        
        logger.info(f"Processing data from {start_date} to {end_date}")
        
        # Step 1: Initialize data collection system with environment-based config
        api_config = create_api_config_from_env()
        data_collector = DataCollectionSystem(api_config)
        
        # Step 2: Collect data from external APIs (with fallback to mock data)
        logger.info("Starting data collection...")
        pizza_orders, football_matches = data_collector.collect_all_data(start_date, end_date)
        
        logger.info(f"Collected {len(pizza_orders)} pizza orders and {len(football_matches)} football matches")
        
        # Step 3: Data processing and correlation analysis (to be implemented in subsequent tasks)
        # Step 4: QuickSight data preparation and updates (to be implemented in subsequent tasks)
        
        result = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data collection completed successfully',
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'execution_id': context.aws_request_id if context else 'local-test',
                'data_summary': {
                    'pizza_orders_collected': len(pizza_orders),
                    'football_matches_collected': len(football_matches),
                    'real_data_sources': {
                        'dominos': any(order.data_source == 'real' for order in pizza_orders),
                        'football': any(match.data_source == 'real' for match in football_matches)
                    }
                }
            })
        }
        
        logger.info("Pipeline execution completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Pipeline execution failed'
            })
        }

if __name__ == "__main__":
    # For local testing
    test_event = {
        'date_range_days': 7
    }
    
    class MockContext:
        aws_request_id = 'local-test-123'
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))