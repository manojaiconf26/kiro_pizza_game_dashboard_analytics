# Usage Guide and Configuration Examples

## Overview

This guide provides comprehensive instructions for setting up, configuring, and using the Pizza Game Dashboard system. Whether you're running it locally for development or deploying to AWS for production, this guide covers all the essential steps.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Local Development Setup](#local-development-setup)
3. [Configuration Guide](#configuration-guide)
4. [AWS Deployment](#aws-deployment)
5. [Usage Examples](#usage-examples)
6. [Data Analysis Workflows](#data-analysis-workflows)
7. [Dashboard Configuration](#dashboard-configuration)
8. [Maintenance and Monitoring](#maintenance-and-monitoring)

## Quick Start

### Prerequisites
- Python 3.9 or higher
- AWS account (for deployment)
- Git for version control

### 5-Minute Setup
```bash
# 1. Clone the repository
git clone <repository-url>
cd pizza-game-dashboard

# 2. Set up development environment
python setup_dev.py

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Unix/Linux/macOS:
source venv/bin/activate

# 4. Run locally with mock data
python lambda_function.py

# 5. Check results
ls local_data/  # See generated data files
```

This will run the complete pipeline using mock data and save results locally.

## Local Development Setup

### 1. Environment Setup

#### Automated Setup (Recommended)
```bash
python setup_dev.py
```

This script automatically:
- Creates a Python virtual environment
- Installs all dependencies
- Sets up local data directories
- Creates sample configuration files
- Runs initial tests

#### Manual Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Unix/Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create local data directories
mkdir -p local_data/raw-data/dominos-orders/mock
mkdir -p local_data/raw-data/football-data/mock
mkdir -p local_data/processed-data/merged-datasets
mkdir -p local_data/processed-data/correlation-analysis
```

### 2. Configuration Files

#### Environment Variables (.env file)
Create a `.env` file in the project root:
```bash
# API Configuration (Optional - system works with mock data)
FOOTBALL_API_KEY=your_football_api_key_here
DOMINOS_API_KEY=your_dominos_api_key_here
DOMINOS_STORE_ID=your_store_id_here

# AWS Configuration (for deployment)
S3_BUCKET_NAME=pizza-game-analytics-your-suffix
AWS_REGION=us-east-1
QUICKSIGHT_ACCOUNT_ID=123456789012

# Rate Limiting Configuration
MAX_REQUESTS_PER_MINUTE=10
MAX_REQUESTS_PER_HOUR=1000
MAX_API_RETRIES=3
BACKOFF_FACTOR=1.0
API_TIMEOUT=30

# Local Development Settings
LOCAL_DATA_PATH=./local_data
LOG_LEVEL=INFO
```

#### Configuration Module (config/settings.py)
The system uses a centralized configuration approach:
```python
import os
from typing import Dict, Any

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# S3 Configuration
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'pizza-game-analytics-default')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# API Configuration
DOMINOS_API_CONFIG = {
    'base_url': os.environ.get('DOMINOS_API_URL', 'https://api.dominos.com/v1'),
    'api_key': os.environ.get('DOMINOS_API_KEY'),
    'store_id': os.environ.get('DOMINOS_STORE_ID'),
    'timeout': int(os.environ.get('API_TIMEOUT', '30'))
}

FOOTBALL_API_CONFIG = {
    'base_url': os.environ.get('FOOTBALL_API_URL', 'https://api.football-data.org/v4'),
    'api_key': os.environ.get('FOOTBALL_API_KEY'),
    'timeout': int(os.environ.get('API_TIMEOUT', '30'))
}

# Rate Limiting Configuration
RATE_LIMIT_CONFIG = {
    'max_requests_per_minute': int(os.environ.get('MAX_REQUESTS_PER_MINUTE', '10')),
    'max_requests_per_hour': int(os.environ.get('MAX_REQUESTS_PER_HOUR', '1000')),
    'max_retries': int(os.environ.get('MAX_API_RETRIES', '3')),
    'backoff_factor': float(os.environ.get('BACKOFF_FACTOR', '1.0'))
}

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
```

### 3. Development Commands

#### Using Makefile (Recommended)
```bash
# Setup development environment
make setup

# Run all tests
make test

# Run only property-based tests
make test-properties

# Run linting
make lint

# Format code
make format

# Create deployment package
make package

# Clean build artifacts
make clean

# Run locally
make run-local
```

#### Direct Python Commands
```bash
# Run the main pipeline
python lambda_function.py

# Run specific components
python -m src.data_collection.external_collectors
python -m src.data_processing.etl_pipeline
python -m src.data_processing.correlation_analyzer

# Run tests
python -m pytest tests/
python -m pytest tests/test_properties.py  # Property-based tests only

# Generate mock data
python -c "
from src.data_collection.mock_generators import generate_correlated_dataset
from datetime import datetime, timedelta
start = datetime.now() - timedelta(days=7)
end = datetime.now()
orders, matches = generate_correlated_dataset(start, end)
print(f'Generated {len(orders)} orders and {len(matches)} matches')
"
```

## Configuration Guide

### 1. API Configuration

#### Football Data API Setup
1. **Get API Key**:
   - Visit [football-data.org](https://www.football-data.org/client/register)
   - Register for free account
   - Copy API key from dashboard

2. **Configure Environment**:
   ```bash
   export FOOTBALL_API_KEY=your_api_key_here
   ```

3. **Test Configuration**:
   ```python
   from src.data_collection.external_collectors import create_api_config_from_env
   
   config = create_api_config_from_env()
   print(f"Football API configured: {bool(config.football_api_key)}")
   ```

#### Domino's API Configuration (Optional)
Since real Domino's APIs require business partnerships, this is typically left unconfigured:
```bash
# Only set if you have access to real Domino's APIs
export DOMINOS_API_KEY=your_api_key_here
export DOMINOS_STORE_ID=your_store_id_here
```

### 2. AWS Configuration

#### S3 Bucket Setup
```bash
# Create S3 bucket
aws s3 mb s3://pizza-game-analytics-your-unique-suffix

# Set bucket name in environment
export S3_BUCKET_NAME=pizza-game-analytics-your-unique-suffix

# Create folder structure (optional - created automatically)
aws s3api put-object --bucket pizza-game-analytics-your-unique-suffix --key raw-data/dominos-orders/real/
aws s3api put-object --bucket pizza-game-analytics-your-unique-suffix --key raw-data/dominos-orders/mock/
aws s3api put-object --bucket pizza-game-analytics-your-unique-suffix --key raw-data/football-data/real/
aws s3api put-object --bucket pizza-game-analytics-your-unique-suffix --key raw-data/football-data/mock/
```

#### IAM Role Configuration
Create IAM role with required permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::pizza-game-analytics-*",
                "arn:aws:s3:::pizza-game-analytics-*/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "quicksight:CreateDataSet",
                "quicksight:UpdateDataSet",
                "quicksight:DescribeDataSet"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

### 3. Local vs Production Configuration

#### Local Development Configuration
```python
# config/local_settings.py
LOCAL_DATA_PATH = './local_data'
USE_LOCAL_STORAGE = True
ENABLE_DEBUG_LOGGING = True
MOCK_DATA_ONLY = True  # Force mock data for testing
SKIP_S3_OPERATIONS = True
```

#### Production Configuration
```python
# Deployed via environment variables
S3_BUCKET_NAME = 'pizza-game-analytics-prod'
USE_LOCAL_STORAGE = False
ENABLE_DEBUG_LOGGING = False
MOCK_DATA_ONLY = False
LOG_LEVEL = 'INFO'
```

## AWS Deployment

### 1. Manual Deployment (Recommended for Learning)

#### Step 1: Create Deployment Package
```bash
# Create deployment package
python deploy.py

# This creates pizza-game-dashboard.zip with:
# - All source code
# - Dependencies
# - Configuration files
```

#### Step 2: Create Lambda Function
1. Go to AWS Lambda Console
2. Click "Create function"
3. Choose "Author from scratch"
4. Function name: `pizza-game-dashboard`
5. Runtime: Python 3.9
6. Execution role: Use existing role → `PizzaDashboardRole`

#### Step 3: Upload Code
1. In Lambda function configuration
2. Code source → Upload from → .zip file
3. Upload `pizza-game-dashboard.zip`
4. Click "Save"

#### Step 4: Configure Environment Variables
In Lambda function configuration → Environment variables:
```
S3_BUCKET_NAME = pizza-game-analytics-your-suffix
FOOTBALL_API_KEY = your_api_key_here
QUICKSIGHT_ACCOUNT_ID = your_aws_account_id
MAX_REQUESTS_PER_MINUTE = 10
```

#### Step 5: Configure Function Settings
- Memory: 1024 MB
- Timeout: 15 minutes
- Dead letter queue: (optional) SQS queue for failed executions

#### Step 6: Set Up Triggers
Create CloudWatch Events rule for scheduling:
```bash
aws events put-rule \
    --name pizza-dashboard-schedule \
    --schedule-expression "rate(6 hours)" \
    --description "Run pizza dashboard every 6 hours"

aws lambda add-permission \
    --function-name pizza-game-dashboard \
    --statement-id pizza-dashboard-schedule \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:region:account:rule/pizza-dashboard-schedule

aws events put-targets \
    --rule pizza-dashboard-schedule \
    --targets "Id"="1","Arn"="arn:aws:lambda:region:account:function:pizza-game-dashboard"
```

### 2. SAM Deployment (Advanced)

#### SAM Template (template.yaml)
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Parameters:
  FootballApiKey:
    Type: String
    Default: ""
    Description: Football API key (optional)
  
  S3BucketName:
    Type: String
    Default: pizza-game-analytics-default
    Description: S3 bucket for data storage

Resources:
  PizzaDashboardFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: lambda_function.lambda_handler
      Runtime: python3.9
      MemorySize: 1024
      Timeout: 900
      Environment:
        Variables:
          S3_BUCKET_NAME: !Ref S3BucketName
          FOOTBALL_API_KEY: !Ref FootballApiKey
          QUICKSIGHT_ACCOUNT_ID: !Ref AWS::AccountId
      Events:
        ScheduleEvent:
          Type: Schedule
          Properties:
            Schedule: rate(6 hours)
      Policies:
        - S3FullAccessPolicy:
            BucketName: !Ref S3BucketName
        - Version: "2012-10-17"
          Statement:
            - Effect: Allow
              Action:
                - quicksight:CreateDataSet
                - quicksight:UpdateDataSet
                - quicksight:DescribeDataSet
              Resource: "*"

  DataBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref S3BucketName
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldRawData
            Status: Enabled
            ExpirationInDays: 90
            Prefix: raw-data/
```

#### Deploy with SAM
```bash
# Build SAM application
sam build

# Deploy with parameters
sam deploy --guided \
    --parameter-overrides \
    FootballApiKey=your_api_key_here \
    S3BucketName=pizza-game-analytics-your-suffix
```

## Usage Examples

### 1. Basic Data Collection

#### Collect Data for Last 7 Days
```python
from datetime import datetime, timedelta
from src.data_collection.external_collectors import DataCollectionSystem, create_api_config_from_env

# Initialize system
config = create_api_config_from_env()
collector = DataCollectionSystem(config)

# Define date range
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

# Collect data
pizza_orders, football_matches = collector.collect_all_data(start_date, end_date)

print(f"Collected {len(pizza_orders)} pizza orders")
print(f"Collected {len(football_matches)} football matches")

# Show sample data
if pizza_orders:
    print(f"Sample order: {pizza_orders[0]}")
if football_matches:
    print(f"Sample match: {football_matches[0]}")
```

#### Generate Mock Data with Specific Parameters
```python
from src.data_collection.mock_generators import MockDataGenerator, GeneratorConfig
from datetime import datetime, timedelta

# Create custom configuration
config = GeneratorConfig(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    base_orders_per_day=200,  # Higher volume
    match_day_multiplier=2.5,  # Stronger correlation
    matches_per_week=4  # More matches
)

# Generate data
generator = MockDataGenerator(config)
orders = generator.generate_pizza_orders()
matches = generator.generate_football_matches()

# Apply temporal correlation
correlated_orders, correlated_matches = generator.correlate_data_timing(orders, matches)

print(f"Generated {len(correlated_orders)} correlated orders")
print(f"Generated {len(correlated_matches)} matches")
```

### 2. Data Processing and Analysis

#### Run ETL Pipeline
```python
from src.data_processing.etl_pipeline import ETLPipeline
from src.storage.s3_service import S3Service

# Initialize services
s3_service = S3Service()  # Uses local storage in development
pipeline = ETLPipeline(s3_service)

# Run complete pipeline
try:
    result_key = pipeline.run_full_pipeline(
        data_source=None,  # Both real and mock
        date_range=(start_date, end_date),
        time_window_hours=6
    )
    print(f"Pipeline completed successfully: {result_key}")
except Exception as e:
    print(f"Pipeline failed: {str(e)}")
```

#### Perform Correlation Analysis
```python
from src.data_processing.correlation_analyzer import CorrelationAnalyzer

# Initialize analyzer
analyzer = CorrelationAnalyzer()

# Calculate match period metrics
metrics_df = analyzer.calculate_match_period_metrics(
    orders=pizza_orders,
    matches=football_matches,
    pre_match_hours=2,
    during_match_hours=2,
    post_match_hours=2
)

print(f"Calculated metrics for {len(metrics_df)} matches")
print(metrics_df.head())

# Calculate correlations
correlation_results = analyzer.calculate_correlation_coefficients(metrics_df)
print(f"Found {len(correlation_results)} correlations")

# Find significant patterns
significant_results = analyzer.detect_statistical_significance(correlation_results)
print(f"Found {len(significant_results)} statistically significant patterns")

# Display results
for result in significant_results[:5]:  # Top 5 results
    print(f"Correlation: {result.correlation_coefficient:.3f}")
    print(f"P-value: {result.statistical_significance:.3f}")
    print(f"Pattern: {result.pattern_description}")
    print("---")
```

### 3. Data Storage and Retrieval

#### Upload Data to S3
```python
from src.storage.s3_service import S3Service
from datetime import datetime

s3_service = S3Service()

# Upload pizza orders
orders_key = s3_service.upload_dataclass_objects(
    objects=pizza_orders,
    data_type='dominos-orders',
    data_source='mock',  # or 'real'
    filename='daily_orders',
    timestamp=datetime.now()
)

print(f"Uploaded orders to: {orders_key}")

# Upload football matches
matches_key = s3_service.upload_dataclass_objects(
    objects=football_matches,
    data_type='football-data',
    data_source='mock',
    filename='daily_matches',
    timestamp=datetime.now()
)

print(f"Uploaded matches to: {matches_key}")
```

#### Retrieve and Analyze Stored Data
```python
# List available files
files = s3_service.list_files(
    data_type='dominos-orders',
    data_source='mock'
)

print(f"Found {len(files)} order files:")
for file_info in files[:5]:  # Show first 5
    print(f"  {file_info['key']} ({file_info['size']} bytes)")

# Download specific file
if files:
    data = s3_service.download_json_data(files[0]['key'])
    print(f"Downloaded {len(data)} records from {files[0]['key']}")
```

### 4. Custom Analysis Workflows

#### Analyze Specific Team Performance
```python
def analyze_team_performance(team_name: str, matches: List[FootballMatch], 
                           orders: List[DominosOrder]) -> Dict[str, Any]:
    """Analyze pizza ordering patterns for a specific team's matches."""
    
    # Filter matches for the team
    team_matches = [
        match for match in matches 
        if team_name.lower() in match.home_team.lower() or 
           team_name.lower() in match.away_team.lower()
    ]
    
    if not team_matches:
        return {"error": f"No matches found for team: {team_name}"}
    
    # Analyze order patterns around team matches
    results = {
        "team": team_name,
        "total_matches": len(team_matches),
        "wins": len([m for m in team_matches if m.event_type == 'win']),
        "losses": len([m for m in team_matches if m.event_type == 'loss']),
        "draws": len([m for m in team_matches if m.event_type == 'draw']),
        "order_patterns": {}
    }
    
    # Calculate order volumes around matches
    for match in team_matches:
        match_time = match.timestamp
        
        # Orders 2 hours before match
        pre_match_orders = [
            order for order in orders
            if match_time - timedelta(hours=2) <= order.timestamp < match_time
        ]
        
        # Orders 2 hours after match
        post_match_orders = [
            order for order in orders
            if match_time < order.timestamp <= match_time + timedelta(hours=2)
        ]
        
        results["order_patterns"][match.match_id] = {
            "match_outcome": match.event_type,
            "pre_match_orders": len(pre_match_orders),
            "post_match_orders": len(post_match_orders),
            "order_spike": len(post_match_orders) - len(pre_match_orders)
        }
    
    return results

# Example usage
team_analysis = analyze_team_performance("Manchester United", football_matches, pizza_orders)
print(f"Analysis for {team_analysis['team']}:")
print(f"Matches: {team_analysis['total_matches']} (W:{team_analysis['wins']} L:{team_analysis['losses']} D:{team_analysis['draws']})")
```

#### Time-of-Day Analysis
```python
def analyze_ordering_patterns_by_hour(orders: List[DominosOrder]) -> Dict[int, Dict[str, Any]]:
    """Analyze pizza ordering patterns by hour of day."""
    
    hourly_patterns = {}
    
    for hour in range(24):
        hour_orders = [
            order for order in orders 
            if order.timestamp.hour == hour
        ]
        
        if hour_orders:
            hourly_patterns[hour] = {
                "total_orders": len(hour_orders),
                "total_revenue": sum(order.order_total for order in hour_orders),
                "avg_order_value": sum(order.order_total for order in hour_orders) / len(hour_orders),
                "total_pizzas": sum(order.quantity for order in hour_orders)
            }
        else:
            hourly_patterns[hour] = {
                "total_orders": 0,
                "total_revenue": 0.0,
                "avg_order_value": 0.0,
                "total_pizzas": 0
            }
    
    return hourly_patterns

# Example usage
hourly_analysis = analyze_ordering_patterns_by_hour(pizza_orders)

# Find peak hours
peak_hour = max(hourly_analysis.keys(), key=lambda h: hourly_analysis[h]["total_orders"])
print(f"Peak ordering hour: {peak_hour}:00 with {hourly_analysis[peak_hour]['total_orders']} orders")

# Show hourly breakdown
print("\nHourly Order Patterns:")
for hour in range(24):
    pattern = hourly_analysis[hour]
    print(f"{hour:2d}:00 - {pattern['total_orders']:3d} orders, £{pattern['total_revenue']:6.2f} revenue")
```

## Data Analysis Workflows

### 1. Complete Analysis Pipeline

```python
def run_complete_analysis(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Run complete pizza-football correlation analysis."""
    
    results = {
        "analysis_period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "duration_days": (end_date - start_date).days
        },
        "data_collection": {},
        "correlation_analysis": {},
        "insights": {}
    }
    
    try:
        # 1. Data Collection
        print("Step 1: Collecting data...")
        config = create_api_config_from_env()
        collector = DataCollectionSystem(config)
        pizza_orders, football_matches = collector.collect_all_data(start_date, end_date)
        
        results["data_collection"] = {
            "pizza_orders_collected": len(pizza_orders),
            "football_matches_collected": len(football_matches),
            "real_data_percentage": calculate_real_data_percentage(pizza_orders, football_matches)
        }
        
        # 2. Data Processing
        print("Step 2: Processing and normalizing data...")
        s3_service = S3Service()
        pipeline = ETLPipeline(s3_service)
        
        orders_df, matches_df = pipeline.normalize_data_formats(pizza_orders, football_matches)
        aligned_df = pipeline.align_datasets_by_timestamp(orders_df, matches_df)
        processed_df = pipeline.process_source_agnostic(aligned_df)
        
        # 3. Correlation Analysis
        print("Step 3: Performing correlation analysis...")
        analyzer = CorrelationAnalyzer()
        
        metrics_df = analyzer.calculate_match_period_metrics(pizza_orders, football_matches)
        correlation_results = analyzer.calculate_correlation_coefficients(metrics_df)
        significant_results = analyzer.detect_statistical_significance(correlation_results)
        
        results["correlation_analysis"] = {
            "total_correlations_calculated": len(correlation_results),
            "statistically_significant": len(significant_results),
            "significance_rate": len(significant_results) / len(correlation_results) * 100 if correlation_results else 0
        }
        
        # 4. Generate Insights
        print("Step 4: Generating insights...")
        insights = generate_business_insights(correlation_results, significant_results, processed_df)
        results["insights"] = insights
        
        # 5. Store Results
        print("Step 5: Storing results...")
        pipeline.load_processed_data(processed_df, f"complete_analysis_{start_date.strftime('%Y%m%d')}")
        
        print("Analysis completed successfully!")
        return results
        
    except Exception as e:
        results["error"] = str(e)
        print(f"Analysis failed: {str(e)}")
        return results

def generate_business_insights(correlation_results: List[CorrelationResult], 
                             significant_results: List[CorrelationResult],
                             processed_df: pd.DataFrame) -> Dict[str, Any]:
    """Generate business insights from correlation analysis."""
    
    insights = {
        "key_findings": [],
        "recommendations": [],
        "data_quality": {},
        "statistical_summary": {}
    }
    
    # Key findings from significant correlations
    for result in significant_results[:5]:  # Top 5 significant results
        if result.correlation_coefficient > 0.3:  # Strong positive correlation
            insights["key_findings"].append({
                "type": "positive_correlation",
                "description": result.pattern_description,
                "strength": "strong" if abs(result.correlation_coefficient) > 0.5 else "moderate",
                "business_impact": "Order volumes increase significantly during this scenario"
            })
    
    # Business recommendations
    if any(r.time_window == 'post_match' and r.correlation_coefficient > 0.2 for r in significant_results):
        insights["recommendations"].append({
            "category": "inventory_management",
            "recommendation": "Increase pizza inventory and staff scheduling for 2 hours after major football matches",
            "expected_impact": "Capture increased demand during post-match ordering spikes"
        })
    
    if any('tournament' in r.pattern_description.lower() for r in significant_results):
        insights["recommendations"].append({
            "category": "marketing",
            "recommendation": "Develop targeted marketing campaigns for tournament matches",
            "expected_impact": "Leverage higher engagement during tournament periods"
        })
    
    # Data quality assessment
    if not processed_df.empty:
        insights["data_quality"] = {
            "total_data_points": len(processed_df),
            "real_vs_mock_ratio": processed_df['data_quality_score'].mean(),
            "data_completeness": (processed_df.notna().sum() / len(processed_df)).mean(),
            "temporal_coverage_days": (processed_df['match_timestamp'].max() - processed_df['match_timestamp'].min()).days
        }
    
    return insights

# Example usage
start_date = datetime.now() - timedelta(days=30)
end_date = datetime.now()

analysis_results = run_complete_analysis(start_date, end_date)
print(json.dumps(analysis_results, indent=2, default=str))
```

### 2. Automated Reporting

```python
def generate_weekly_report() -> str:
    """Generate automated weekly analysis report."""
    
    # Calculate date range (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Run analysis
    results = run_complete_analysis(start_date, end_date)
    
    # Generate report
    report = f"""
# Pizza Game Dashboard - Weekly Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}

## Data Collection Summary
- Pizza Orders: {results['data_collection']['pizza_orders_collected']}
- Football Matches: {results['data_collection']['football_matches_collected']}
- Real Data Percentage: {results['data_collection']['real_data_percentage']:.1f}%

## Correlation Analysis
- Total Correlations: {results['correlation_analysis']['total_correlations_calculated']}
- Statistically Significant: {results['correlation_analysis']['statistically_significant']}
- Significance Rate: {results['correlation_analysis']['significance_rate']:.1f}%

## Key Insights
"""
    
    for finding in results['insights']['key_findings']:
        report += f"- {finding['description']}\n"
    
    report += "\n## Recommendations\n"
    for rec in results['insights']['recommendations']:
        report += f"- **{rec['category'].title()}**: {rec['recommendation']}\n"
    
    return report

# Generate and save report
weekly_report = generate_weekly_report()
with open(f"reports/weekly_report_{datetime.now().strftime('%Y%m%d')}.md", 'w') as f:
    f.write(weekly_report)

print("Weekly report generated successfully!")
```

## Dashboard Configuration

### 1. QuickSight Setup

#### Data Source Configuration
```json
{
    "manifest": {
        "fileLocations": [
            {
                "URIs": [
                    "s3://pizza-game-analytics-your-suffix/quicksight-ready/dashboard-data/"
                ]
            }
        ],
        "globalUploadSettings": {
            "format": "JSON",
            "delimiter": ",",
            "textqualifier": "\"",
            "containsHeader": "true"
        }
    }
}
```

#### Dashboard Components Configuration
```python
def create_quicksight_dashboard_config() -> Dict[str, Any]:
    """Create QuickSight dashboard configuration."""
    
    return {
        "dashboard_name": "Pizza Game Analytics Dashboard",
        "data_sets": [
            {
                "name": "Pizza Orders Dataset",
                "source": "s3://pizza-game-analytics-your-suffix/quicksight-ready/dashboard-data/",
                "refresh_schedule": "every_6_hours"
            }
        ],
        "visuals": [
            {
                "type": "KPI",
                "title": "Total Orders",
                "metric": "order_count",
                "comparison": "previous_period"
            },
            {
                "type": "line_chart",
                "title": "Orders Over Time",
                "x_axis": "timestamp",
                "y_axis": "order_count",
                "color": "data_source"
            },
            {
                "type": "bar_chart",
                "title": "Orders by Match Outcome",
                "x_axis": "match_outcome",
                "y_axis": "avg_order_count",
                "color": "match_significance"
            },
            {
                "type": "scatter_plot",
                "title": "Correlation Analysis",
                "x_axis": "match_goals",
                "y_axis": "post_match_orders",
                "size": "correlation_strength"
            }
        ],
        "filters": [
            {
                "field": "data_source",
                "type": "dropdown",
                "options": ["real", "mock", "all"]
            },
            {
                "field": "date_range",
                "type": "date_picker",
                "default": "last_30_days"
            },
            {
                "field": "team",
                "type": "multi_select",
                "options": "dynamic_from_data"
            }
        ]
    }
```

### 2. Custom Dashboard Metrics

```python
def calculate_dashboard_metrics(processed_df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate key metrics for dashboard display."""
    
    if processed_df.empty:
        return {"error": "No data available for metrics calculation"}
    
    metrics = {
        "summary": {
            "total_orders": int(processed_df['order_amount_count'].sum()),
            "total_revenue": float(processed_df['order_amount_sum'].sum()),
            "total_matches": int(processed_df['match_id'].nunique()),
            "avg_order_value": float(processed_df['order_amount_mean'].mean()),
            "data_quality_score": float(processed_df['data_quality_score'].mean())
        },
        "correlations": {
            "strongest_positive": None,
            "strongest_negative": None,
            "most_significant": None
        },
        "temporal_patterns": {
            "peak_ordering_hour": None,
            "match_day_effect": None,
            "weekend_vs_weekday": None
        },
        "team_performance": {}
    }
    
    # Calculate temporal patterns
    processed_df['hour'] = processed_df['order_timestamp'].dt.hour
    hourly_orders = processed_df.groupby('hour')['order_amount_count'].sum()
    metrics["temporal_patterns"]["peak_ordering_hour"] = int(hourly_orders.idxmax())
    
    # Calculate match day effects
    match_day_orders = processed_df[processed_df['time_period'].isin(['pre_match', 'during_match', 'post_match'])]
    non_match_day_orders = processed_df[~processed_df['time_period'].isin(['pre_match', 'during_match', 'post_match'])]
    
    if not match_day_orders.empty and not non_match_day_orders.empty:
        match_day_avg = match_day_orders['order_amount_count'].mean()
        non_match_day_avg = non_match_day_orders['order_amount_count'].mean()
        metrics["temporal_patterns"]["match_day_effect"] = float((match_day_avg - non_match_day_avg) / non_match_day_avg * 100)
    
    return metrics

# Example usage
dashboard_metrics = calculate_dashboard_metrics(processed_df)
print(json.dumps(dashboard_metrics, indent=2, default=str))
```

## Maintenance and Monitoring

### 1. Health Checks

```python
def perform_system_health_check() -> Dict[str, Any]:
    """Perform comprehensive system health check."""
    
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "components": {}
    }
    
    # Check API connectivity
    try:
        config = create_api_config_from_env()
        if config.football_api_key:
            # Test API call
            client = FootballAPIClient(config)
            test_matches = client.collect_football_data(
                datetime.now() - timedelta(days=1),
                datetime.now()
            )
            health_status["components"]["football_api"] = {
                "status": "healthy",
                "last_successful_call": datetime.now().isoformat(),
                "data_source": "real" if test_matches and test_matches[0].data_source == 'real' else "mock"
            }
        else:
            health_status["components"]["football_api"] = {
                "status": "not_configured",
                "message": "API key not provided, using mock data"
            }
    except Exception as e:
        health_status["components"]["football_api"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["overall_status"] = "degraded"
    
    # Check S3 connectivity
    try:
        s3_service = S3Service()
        files = s3_service.list_files()
        health_status["components"]["s3_storage"] = {
            "status": "healthy",
            "total_files": len(files),
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        health_status["components"]["s3_storage"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["overall_status"] = "unhealthy"
    
    # Check data processing
    try:
        pipeline = ETLPipeline()
        # Test with minimal data
        test_orders = [DominosOrder(
            order_id="test_001",
            timestamp=datetime.now(),
            location="test_location",
            order_total=15.99,
            pizza_types=["Margherita"],
            quantity=1,
            data_source="mock"
        )]
        test_matches = [FootballMatch(
            match_id="test_001",
            timestamp=datetime.now(),
            home_team="Test Home",
            away_team="Test Away",
            home_score=2,
            away_score=1,
            event_type="win",
            match_significance="regular",
            data_source="mock"
        )]
        
        orders_df, matches_df = pipeline.normalize_data_formats(test_orders, test_matches)
        health_status["components"]["data_processing"] = {
            "status": "healthy",
            "test_result": "normalization_successful"
        }
    except Exception as e:
        health_status["components"]["data_processing"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["overall_status"] = "unhealthy"
    
    return health_status

# Example usage
health_check = perform_system_health_check()
print(f"System Status: {health_check['overall_status']}")
for component, status in health_check['components'].items():
    print(f"  {component}: {status['status']}")
```

### 2. Automated Monitoring

```python
def setup_monitoring_alerts():
    """Set up monitoring and alerting for the system."""
    
    monitoring_config = {
        "cloudwatch_alarms": [
            {
                "name": "PizzaDashboard-LambdaErrors",
                "metric": "AWS/Lambda/Errors",
                "threshold": 1,
                "comparison": "GreaterThanOrEqualToThreshold",
                "evaluation_periods": 1,
                "period": 300
            },
            {
                "name": "PizzaDashboard-LambdaDuration",
                "metric": "AWS/Lambda/Duration",
                "threshold": 600000,  # 10 minutes
                "comparison": "GreaterThanThreshold",
                "evaluation_periods": 2,
                "period": 300
            },
            {
                "name": "PizzaDashboard-S3Errors",
                "metric": "AWS/S3/4xxErrors",
                "threshold": 5,
                "comparison": "GreaterThanThreshold",
                "evaluation_periods": 1,
                "period": 300
            }
        ],
        "custom_metrics": [
            {
                "name": "DataCollectionSuccessRate",
                "namespace": "PizzaDashboard/DataCollection",
                "unit": "Percent"
            },
            {
                "name": "CorrelationStrength",
                "namespace": "PizzaDashboard/Analysis",
                "unit": "None"
            },
            {
                "name": "DataQualityScore",
                "namespace": "PizzaDashboard/Quality",
                "unit": "Percent"
            }
        ]
    }
    
    return monitoring_config

# Log custom metrics
def log_custom_metrics(metrics: Dict[str, float]):
    """Log custom metrics to CloudWatch."""
    
    try:
        import boto3
        cloudwatch = boto3.client('cloudwatch')
        
        for metric_name, value in metrics.items():
            cloudwatch.put_metric_data(
                Namespace='PizzaDashboard/Custom',
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': 'None',
                        'Timestamp': datetime.now()
                    }
                ]
            )
        
        print(f"Logged {len(metrics)} custom metrics to CloudWatch")
        
    except Exception as e:
        print(f"Failed to log metrics: {str(e)}")

# Example usage
custom_metrics = {
    'DataCollectionSuccessRate': 95.5,
    'CorrelationStrength': 0.34,
    'DataQualityScore': 78.2
}

log_custom_metrics(custom_metrics)
```

This comprehensive usage guide provides everything needed to successfully deploy, configure, and operate the Pizza Game Dashboard system. From basic setup to advanced analysis workflows, users can follow these examples to get the most value from the system.