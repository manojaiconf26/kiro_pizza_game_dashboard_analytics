# Architecture Documentation

## System Overview

The Pizza Game Dashboard is a serverless analytics system built on AWS that correlates pizza ordering patterns with football match events. The system is designed for high availability, cost efficiency, and automatic scaling.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           External Data Sources                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   Domino's API  │    │ Football-Data   │    │  Mock Data Gen  │         │
│  │                 │    │     API         │    │                 │         │
│  │ • Order Data    │    │ • Match Scores  │    │ • Fallback Data │         │
│  │ • Timestamps    │    │ • Team Info     │    │ • Realistic     │         │
│  │ • Locations     │    │ • Events        │    │   Patterns      │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Data Collection System                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │ API Collectors  │    │  Rate Limiter   │    │ Error Handler   │         │
│  │                 │    │                 │    │                 │         │
│  │ • Auth Mgmt     │    │ • 10 req/min    │    │ • Retry Logic   │         │
│  │ • Request Mgmt  │    │ • Exponential   │    │ • Fallback      │         │
│  │ • Data Parsing  │    │   Backoff       │    │ • Logging       │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AWS Lambda Function                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │ Lambda Handler  │    │  ETL Pipeline   │    │ Correlation     │         │
│  │                 │    │                 │    │   Analyzer      │         │
│  │ • Event Trigger │    │ • Extract       │    │ • Statistical   │         │
│  │ • Orchestration │    │ • Transform     │    │   Analysis      │         │
│  │ • Error Mgmt    │    │ • Load          │    │ • Pattern Det.  │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Amazon S3 Storage                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   Raw Data      │    │ Processed Data  │    │ Dashboard Data  │         │
│  │                 │    │                 │    │                 │         │
│  │ • dominos-orders│    │ • merged-sets   │    │ • quicksight/   │         │
│  │   ├── real/     │    │ • correlation-  │    │   dashboard/    │         │
│  │   └── mock/     │    │   analysis/     │    │ • metadata/     │         │
│  │ • football-data │    │                 │    │                 │         │
│  │   ├── real/     │    │                 │    │                 │         │
│  │   └── mock/     │    │                 │    │                 │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Amazon QuickSight                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   Data Source   │    │   Dashboards    │    │   Analytics     │         │
│  │                 │    │                 │    │                 │         │
│  │ • S3 Connector  │    │ • Time Series   │    │ • Correlation   │         │
│  │ • Auto Refresh  │    │ • KPI Metrics   │    │   Insights      │         │
│  │ • Data Prep     │    │ • Interactive   │    │ • Statistical   │         │
│  │                 │    │   Filters       │    │   Significance  │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Collection System

#### External API Clients
- **DominosAPIClient**: Handles Domino's pizza order data collection
- **FootballAPIClient**: Manages football match data from football-data.org
- **MockDataGenerator**: Provides realistic fallback data when APIs are unavailable

#### Key Features:
- **Authentication Management**: Secure API key handling with environment variables
- **Rate Limiting**: Respects API limits (10 requests/minute for football-data.org)
- **Error Handling**: Automatic retry with exponential backoff
- **Fallback Strategy**: Seamless switch to mock data on API failures

#### API Integration Points:

**Football-data.org API**:
```python
# Endpoint: https://api.football-data.org/v4/competitions/2021/matches
# Authentication: X-Auth-Token header
# Rate Limit: 10 requests/minute (free tier)
# Data: Premier League matches with scores, teams, timestamps
```

**Domino's API** (Prepared but uses mock by default):
```python
# Endpoint: https://api.dominos.com/v1/orders (hypothetical)
# Authentication: Bearer token
# Rate Limit: Configurable
# Data: Order details, timestamps, locations, pizza types
```

### 2. ETL Pipeline

#### Extract Phase
- Retrieves data from S3 storage (both real and mock sources)
- Handles multiple file formats (JSON, CSV)
- Filters data by date range and source type
- Validates data integrity and completeness

#### Transform Phase
- **Data Normalization**: Consistent formats across sources
- **Timestamp Alignment**: UTC conversion and timezone handling
- **Data Enrichment**: Calculated fields and derived metrics
- **Quality Scoring**: Real vs mock data ratio tracking

#### Load Phase
- Stores processed data back to S3
- Creates QuickSight-compatible formats
- Maintains data lineage and metadata
- Organizes data with clear naming conventions

### 3. Correlation Analysis Engine

#### Statistical Methods
- **Pearson Correlation**: For continuous variables (order volumes, scores)
- **Point-Biserial Correlation**: For binary outcomes (win/loss vs order spikes)
- **Statistical Significance Testing**: P-value calculation with α = 0.05
- **Effect Size Analysis**: Practical significance beyond statistical significance

#### Time Window Analysis
- **Pre-match Period**: 2 hours before match start
- **During-match Period**: Match time ± 1 hour
- **Post-match Period**: 2 hours after match end
- **Extended Analysis**: 24-hour correlation windows

#### Pattern Detection
- **Order Spike Detection**: Statistical outliers in ordering patterns
- **Match Event Classification**: Goals, wins, tournament significance
- **Temporal Correlation**: Cross-period order pattern analysis
- **Anomaly Detection**: Unusual patterns with source attribution

### 4. Storage Architecture

#### S3 Bucket Organization
```
pizza-game-analytics-{suffix}/
├── raw-data/
│   ├── dominos-orders/
│   │   ├── real/
│   │   │   └── YYYY/MM/DD/
│   │   │       └── YYYYMMDD_HHMMSS_orders.json
│   │   └── mock/
│   │       └── YYYY/MM/DD/
│   │           └── YYYYMMDD_HHMMSS_mock_orders.json
│   └── football-data/
│       ├── real/
│       │   └── YYYY/MM/DD/
│       │       └── YYYYMMDD_HHMMSS_matches.json
│       └── mock/
│           └── YYYY/MM/DD/
│               └── YYYYMMDD_HHMMSS_mock_matches.json
├── processed-data/
│   ├── merged-datasets/
│   │   └── YYYY/MM/DD/
│   │       ├── YYYYMMDD_HHMMSS_merged_data.csv
│   │       └── YYYYMMDD_HHMMSS_merged_data.json
│   └── correlation-analysis/
│       └── YYYY/MM/DD/
│           ├── YYYYMMDD_HHMMSS_correlation_results.csv
│           ├── YYYYMMDD_HHMMSS_significant_correlations.csv
│           └── YYYYMMDD_HHMMSS_correlation_summary.json
└── quicksight-ready/
    ├── dashboard-data/
    │   └── YYYY/MM/DD/
    │       └── YYYYMMDD_HHMMSS_dashboard_data.json
    └── metadata/
        └── manifest.json
```

#### Data Lifecycle Management
- **Raw Data Retention**: 90 days for cost optimization
- **Processed Data**: 1 year for historical analysis
- **Dashboard Data**: Real-time updates with 30-day history
- **Metadata Preservation**: Complete lineage tracking

### 5. AWS Lambda Function

#### Function Configuration
- **Runtime**: Python 3.9
- **Memory**: 1024 MB (for data processing)
- **Timeout**: 15 minutes (maximum)
- **Execution Role**: PizzaDashboardRole with S3 and QuickSight permissions

#### Environment Variables
```python
{
    'S3_BUCKET_NAME': 'pizza-game-analytics-{suffix}',
    'FOOTBALL_API_KEY': '{optional-api-key}',
    'DOMINOS_API_KEY': '{optional-api-key}',
    'QUICKSIGHT_ACCOUNT_ID': '{aws-account-id}',
    'MAX_REQUESTS_PER_MINUTE': '10',
    'MAX_REQUESTS_PER_HOUR': '1000'
}
```

#### Execution Flow
1. **Initialization**: Load configuration and initialize services
2. **Data Collection**: Collect from APIs with fallback to mock data
3. **Data Processing**: Run ETL pipeline and correlation analysis
4. **Result Storage**: Upload processed data and analysis results
5. **Dashboard Update**: Refresh QuickSight data sources
6. **Monitoring**: Log execution metrics and errors

### 6. QuickSight Integration

#### Data Source Configuration
- **S3 Data Source**: Connected to quicksight-ready/ folder
- **Manifest File**: JSON manifest for data location and format
- **Auto Refresh**: Scheduled refresh after Lambda execution
- **Data Preparation**: Field mapping and type conversion

#### Dashboard Components
- **KPI Metrics**: Total orders, matches, correlation strength
- **Time Series Charts**: Order volumes over time with match overlays
- **Correlation Analysis**: Statistical relationships visualization
- **Interactive Filters**: Team, match type, data source, time period
- **Drill-down Capabilities**: From summary to detailed match analysis

## Security Architecture

### IAM Roles and Policies

#### PizzaDashboardRole
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

### API Security
- **API Keys**: Stored as environment variables, never in code
- **HTTPS Only**: All external API calls use TLS encryption
- **Rate Limiting**: Prevents API abuse and respects provider limits
- **Error Sanitization**: Sensitive information removed from logs

### Data Security
- **Encryption at Rest**: S3 server-side encryption enabled
- **Encryption in Transit**: All data transfers use HTTPS/TLS
- **Access Control**: IAM policies restrict access to necessary resources only
- **Data Classification**: Clear labeling of real vs mock data sources

## Monitoring and Observability

### CloudWatch Integration
- **Lambda Metrics**: Execution duration, memory usage, error rates
- **Custom Metrics**: Data collection success rates, correlation strengths
- **Log Aggregation**: Structured logging with correlation IDs
- **Alerting**: Notifications for failures and anomalies

### Performance Monitoring
- **API Response Times**: Track external API performance
- **Data Processing Metrics**: ETL pipeline execution times
- **Storage Metrics**: S3 usage and access patterns
- **Cost Tracking**: AWS cost allocation by service

### Error Tracking
- **Exception Handling**: Comprehensive error capture and logging
- **Retry Mechanisms**: Automatic recovery from transient failures
- **Fallback Monitoring**: Track real vs mock data usage ratios
- **Data Quality Metrics**: Validation failure rates and data completeness

## Scalability and Performance

### Horizontal Scaling
- **Lambda Concurrency**: Automatic scaling based on demand
- **S3 Performance**: Partitioned data structure for parallel access
- **API Rate Management**: Distributed rate limiting across executions

### Vertical Scaling
- **Memory Optimization**: Right-sized Lambda memory allocation
- **Processing Efficiency**: Optimized data structures and algorithms
- **Caching Strategy**: In-memory caching for repeated calculations

### Cost Optimization
- **Serverless Architecture**: Pay-per-execution model
- **S3 Lifecycle Policies**: Automatic data archival and deletion
- **QuickSight Usage**: Standard edition for cost-effective analytics
- **Resource Right-sizing**: Optimized Lambda configuration

## Disaster Recovery

### Data Backup Strategy
- **S3 Cross-Region Replication**: Optional for critical deployments
- **Version Control**: S3 versioning for data recovery
- **Code Backup**: Git repository with deployment automation

### Recovery Procedures
- **Lambda Function Recovery**: Automated deployment from code repository
- **Data Recovery**: S3 versioning and cross-region replication
- **Configuration Recovery**: Infrastructure as Code with CloudFormation
- **Dashboard Recovery**: QuickSight configuration backup and restore

### Business Continuity
- **Fallback Data Sources**: Mock data ensures continuous operation
- **Graceful Degradation**: System continues with reduced functionality
- **Monitoring and Alerting**: Proactive issue detection and response
- **Documentation**: Comprehensive runbooks for recovery procedures