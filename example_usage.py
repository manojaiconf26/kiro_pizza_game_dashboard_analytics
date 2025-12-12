#!/usr/bin/env python3
"""
Example usage of the external API collectors for Pizza Game Dashboard.

This script demonstrates how to use the external collectors with your API keys.
Set the FOOTBALL_API_KEY environment variable before running this script.
"""

import os
import sys
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, 'src')

from src.data_collection import (
    DataCollectionSystem,
    create_api_config_from_env,
    APIConfig
)

def main():
    """Main function to demonstrate API usage."""
    
    # Method 1: Using environment variables (recommended for Lambda)
    print("=== Method 1: Using Environment Variables ===")
    
    # Check if football API key is set
    football_api_key = os.environ.get('FOOTBALL_API_KEY')
    if not football_api_key:
        print("⚠️  FOOTBALL_API_KEY environment variable not set!")
        print("   Set it with: export FOOTBALL_API_KEY='your_api_key_here'")
        print("   Or on Windows: set FOOTBALL_API_KEY=your_api_key_here")
        print()
    
    try:
        # Create config from environment variables
        config = create_api_config_from_env()
        print(f"✅ Configuration loaded from environment")
        print(f"   Football API URL: {config.football_api_url}")
        print(f"   Football API Key: {'***' + config.football_api_key[-4:] if config.football_api_key else 'Not set'}")
        print(f"   Dominos API Key: {'***' + config.dominos_api_key[-4:] if config.dominos_api_key else 'Not set'}")
        print()
        
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        print()
    
    # Method 2: Direct configuration (for testing)
    print("=== Method 2: Direct Configuration ===")
    
    # You can set your API key directly here for testing
    your_football_api_key = football_api_key or "your_football_api_key_here"
    
    config = APIConfig(
        football_api_key=your_football_api_key,
        dominos_api_key=None,  # Will fall back to mock data
        max_requests_per_minute=60,
        max_requests_per_hour=1000
    )
    
    # Create data collection system
    collector = DataCollectionSystem(config)
    
    # Set date range (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print(f"📅 Collecting data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print()
    
    try:
        # Collect data
        print("🔄 Starting data collection...")
        pizza_orders, football_matches = collector.collect_all_data(start_date, end_date)
        
        print("✅ Data collection completed!")
        print(f"   📊 Pizza orders collected: {len(pizza_orders)}")
        print(f"   ⚽ Football matches collected: {len(football_matches)}")
        print()
        
        # Show data source breakdown
        if pizza_orders:
            real_orders = sum(1 for order in pizza_orders if order.data_source == 'real')
            mock_orders = len(pizza_orders) - real_orders
            print(f"   🍕 Pizza orders - Real: {real_orders}, Mock: {mock_orders}")
        
        if football_matches:
            real_matches = sum(1 for match in football_matches if match.data_source == 'real')
            mock_matches = len(football_matches) - real_matches
            print(f"   ⚽ Football matches - Real: {real_matches}, Mock: {mock_matches}")
        
        print()
        
        # Show sample data
        if football_matches:
            print("📋 Sample football match:")
            match = football_matches[0]
            print(f"   {match.home_team} vs {match.away_team}")
            print(f"   Score: {match.home_score}-{match.away_score}")
            print(f"   Date: {match.timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Source: {match.data_source}")
            print()
        
        if pizza_orders:
            print("📋 Sample pizza order:")
            order = pizza_orders[0]
            print(f"   Order ID: {order.order_id}")
            print(f"   Total: £{order.order_total}")
            print(f"   Pizzas: {', '.join(order.pizza_types)}")
            print(f"   Date: {order.timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Source: {order.data_source}")
            print()
        
    except Exception as e:
        print(f"❌ Error during data collection: {e}")
        print()

if __name__ == "__main__":
    print("🍕⚽ Pizza Game Dashboard - External API Collectors Example")
    print("=" * 60)
    print()
    
    main()
    
    print("💡 Tips:")
    print("   - Get your football API key from: https://www.football-data.org/client/register")
    print("   - The free tier allows 10 requests per minute")
    print("   - If no API key is provided, the system will use mock data")
    print("   - For Lambda deployment, set environment variables in the SAM template")