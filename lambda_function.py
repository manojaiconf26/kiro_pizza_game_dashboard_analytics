"""
Simplified Lambda function handler for Pizza Game Dashboard
Handles basic data collection and storage without heavy analytics dependencies
"""
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import statistics

from src.data_collection import (
    DataCollectionSystem,
    create_api_config_from_env
)
from src.storage.s3_service import S3Service

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def calculate_basic_statistics(orders: List, matches: List) -> Dict[str, Any]:
    """Calculate basic statistics without pandas"""
    if not orders or not matches:
        return {}
    
    # Order statistics
    order_totals = [order.order_total for order in orders]
    order_stats = {
        'total_orders': len(orders),
        'total_revenue': sum(order_totals),
        'average_order_value': statistics.mean(order_totals) if order_totals else 0,
        'median_order_value': statistics.median(order_totals) if order_totals else 0,
        'real_orders': sum(1 for order in orders if order.data_source == 'real'),
        'mock_orders': sum(1 for order in orders if order.data_source == 'mock')
    }
    
    # Match statistics
    match_goals = [match.home_score + match.away_score for match in matches]
    match_stats = {
        'total_matches': len(matches),
        'total_goals': sum(match_goals),
        'average_goals_per_match': statistics.mean(match_goals) if match_goals else 0,
        'high_scoring_matches': sum(1 for goals in match_goals if goals >= 3),
        'real_matches': sum(1 for match in matches if match.data_source == 'real'),
        'mock_matches': sum(1 for match in matches if match.data_source == 'mock')
    }
    
    return {
        'order_statistics': order_stats,
        'match_statistics': match_stats,
        'data_quality': {
            'real_data_percentage': ((order_stats['real_orders'] + match_stats['real_matches']) / 
                                   (len(orders) + len(matches))) * 100 if (orders or matches) else 0
        }
    }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Simplified Lambda handler for the pizza game dashboard
    
    Executes basic pipeline:
    1. Data collection from external APIs (with fallback to mock data)
    2. Data storage to S3
    3. Basic statistics calculation
    4. Dashboard data preparation
    
    Args:
        event: Lambda event data
        context: Lambda context object
        
    Returns:
        Dict containing execution status and results
    """
    execution_id = context.aws_request_id if context else f'local-{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    try:
        logger.info(f"Starting Pizza Game Dashboard pipeline execution (ID: {execution_id})")
        
        # Extract parameters from event or use defaults
        date_range_days = event.get('date_range_days', 7)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range_days)
        
        logger.info(f"Processing data from {start_date} to {end_date}")
        
        # Initialize services
        s3_service = S3Service()
        
        # Step 1: Initialize data collection system with environment-based config
        logger.info("Initializing data collection system...")
        api_config = create_api_config_from_env()
        data_collector = DataCollectionSystem(api_config)
        
        # Step 2: Collect data from external APIs (with fallback to mock data)
        logger.info("Starting data collection...")
        pizza_orders, football_matches = data_collector.collect_all_data(start_date, end_date)
        
        logger.info(f"Collected {len(pizza_orders)} pizza orders and {len(football_matches)} football matches")
        
        if not pizza_orders or not football_matches:
            raise Exception("No data collected - cannot proceed with analysis")
        
        # Step 3: Store raw data to S3
        logger.info("Storing raw data to S3...")
        
        # Store pizza orders
        pizza_s3_key = s3_service.upload_dataclass_objects(
            pizza_orders,
            data_type='dominos-orders',
            data_source='mixed',  # Could be real or mock
            filename=f"orders_{execution_id}.json"
        )
        
        # Store football matches
        football_s3_key = s3_service.upload_dataclass_objects(
            football_matches,
            data_type='football-data',
            data_source='mixed',
            filename=f"matches_{execution_id}.json"
        )
        
        logger.info(f"Raw data stored: {pizza_s3_key}, {football_s3_key}")
        
        # Step 4: Calculate basic statistics
        logger.info("Calculating basic statistics...")
        stats = calculate_basic_statistics(pizza_orders, football_matches)
        
        # Step 5: Prepare dashboard data
        logger.info("Preparing dashboard data...")
        
        # Create dashboard-ready summary data
        dashboard_data = {
            'execution_summary': {
                'execution_id': execution_id,
                'execution_timestamp': datetime.utcnow().isoformat(),
                'data_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': date_range_days
                },
                'pipeline_version': 'simplified_v1.0'
            },
            'statistics': stats,
            'data_sources': {
                'pizza_orders': {
                    'real': sum(1 for order in pizza_orders if order.data_source == 'real'),
                    'mock': sum(1 for order in pizza_orders if order.data_source == 'mock')
                },
                'football_matches': {
                    'real': sum(1 for match in football_matches if match.data_source == 'real'),
                    'mock': sum(1 for match in football_matches if match.data_source == 'mock')
                }
            },
            'key_insights': [
                f"Collected {len(pizza_orders)} pizza orders with average value of ${stats.get('order_statistics', {}).get('average_order_value', 0):.2f}",
                f"Processed {len(football_matches)} football matches with {stats.get('match_statistics', {}).get('total_goals', 0)} total goals",
                f"Data quality: {stats.get('data_quality', {}).get('real_data_percentage', 0):.1f}% real data"
            ]
        }
        
        # Store dashboard data
        dashboard_key = s3_service.upload_json_data(
            dashboard_data,
            data_type='dashboard-data',
            data_source='processed',
            filename=f"dashboard_data_{execution_id}.json"
        )
        
        logger.info(f"Dashboard data prepared: {dashboard_key}")
        
        # Prepare final response
        result = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Pizza Game Dashboard pipeline completed successfully',
                'execution_id': execution_id,
                'execution_timestamp': datetime.utcnow().isoformat(),
                'analysis_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': date_range_days
                },
                'data_summary': {
                    'pizza_orders_collected': len(pizza_orders),
                    'football_matches_collected': len(football_matches),
                    'real_data_sources': {
                        'dominos': any(order.data_source == 'real' for order in pizza_orders),
                        'football': any(match.data_source == 'real' for match in football_matches)
                    },
                    'data_quality_percentage': stats.get('data_quality', {}).get('real_data_percentage', 0)
                },
                'processing_results': {
                    'raw_data_stored': [pizza_s3_key, football_s3_key],
                    'dashboard_data_key': dashboard_key
                },
                'statistics': stats,
                'next_steps': [
                    f"Review dashboard data at: s3://{os.getenv('S3_BUCKET_NAME', 'pizza-game-analytics')}/{dashboard_key}",
                    "Configure QuickSight to use the processed datasets for visualization",
                    "Consider upgrading to advanced analytics pipeline for correlation analysis"
                ]
            })
        }
        
        logger.info(f"Pipeline execution completed successfully (ID: {execution_id})")
        return result
        
    except Exception as e:
        logger.error(f"Pipeline execution failed (ID: {execution_id}): {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Pipeline execution failed',
                'execution_id': execution_id,
                'timestamp': datetime.utcnow().isoformat()
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