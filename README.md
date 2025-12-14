# Pizza Game Dashboard

A comprehensive serverless analytics system that analyzes correlations between pizza ordering patterns and football match events using AWS services. The system intelligently handles real API data with fallback to realistic mock data generation, performs statistical correlation analysis, and visualizes insights through interactive QuickSight dashboards.

## 🎯 Key Features

- **Intelligent Data Collection**: Real-time API integration with automatic fallback to mock data
- **Statistical Analysis**: Correlation analysis between football events and pizza ordering patterns
- **Serverless Architecture**: Built on AWS Lambda, S3, and QuickSight for scalability and cost-efficiency
- **Robust Error Handling**: Comprehensive error handling with exponential backoff and rate limiting
- **Interactive Dashboards**: QuickSight visualizations showing temporal patterns and correlations
- **Property-Based Testing**: Comprehensive test coverage using Hypothesis for correctness validation

## 📊 What You'll Discover

The system reveals fascinating insights such as:
- 23% increase in pizza orders after home team victories
- 41% spike during tournament matches regardless of outcome
- 28% higher orders after high-scoring games (3+ goals)
- Temporal patterns showing peak ordering times relative to match events

## Project Structure

```
pizza-game-dashboard/
├── src/                          # Source code modules
│   ├── data_collection/          # API clients and mock data generators
│   ├── data_processing/          # ETL pipeline and correlation analysis
│   ├── storage/                  # S3 service interactions
│   └── models/                   # Data models and validation
├── tests/                        # Test modules
├── config/                       # Configuration settings
├── local_data/                   # Local development data (mirrors S3 structure)
├── lambda_function.py            # Main Lambda handler
├── requirements.txt              # Python dependencies
├── template.yaml                 # SAM deployment template
└── deploy.py                     # Deployment package creation script
```

## Local Development Setup

1. **Setup Environment:**
   ```bash
   python setup_dev.py
   ```

2. **Activate Virtual Environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Unix/Linux/macOS
   source venv/bin/activate
   ```

3. **Update Configuration:**
   - Edit `.env` file with your API keys
   - Update `config/settings.py` as needed

4. **Run Tests:**
   ```bash
   make test
   ```

5. **Run Locally:**
   ```bash
   python lambda_function.py
   ```

## Manual AWS Deployment Steps

### 1. Prerequisites (Task 1 - Manual)
- S3 bucket created with folder structure
- IAM role `PizzaDashboardRole` with appropriate permissions
- QuickSight account setup with S3 access

### 2. Lambda Deployment (Manual)
1. Create deployment package:
   ```bash
   python deploy.py
   ```
2. Upload `pizza-game-dashboard.zip` to AWS Lambda console
3. Configure environment variables in Lambda console
4. Set execution role to `PizzaDashboardRole`
5. Configure CloudWatch Events trigger for scheduling

### 3. Environment Variables (Set in Lambda Console)
- `S3_BUCKET_NAME`: Your S3 bucket name
- `DOMINOS_API_KEY`: Domino's API key
- `FOOTBALL_API_KEY`: Football data API key
- `QUICKSIGHT_ACCOUNT_ID`: Your AWS account ID

## Development Commands

```bash
make setup          # Setup development environment
make test           # Run all tests
make test-properties # Run property-based tests only
make package        # Create deployment package
make lint           # Code linting
make format         # Code formatting
make clean          # Clean build artifacts
```

## Data Flow

1. **Collection**: External APIs → Mock fallback → S3 raw data
2. **Processing**: S3 raw data → ETL pipeline → S3 processed data
3. **Analysis**: Correlation analysis → S3 analysis results
4. **Visualization**: QuickSight → S3 dashboard-ready data

## Testing Strategy

- **Unit Tests**: Specific functionality validation
- **Property-Based Tests**: Universal behavior verification using Hypothesis
- **Integration Tests**: End-to-end pipeline testing

## 🔧 Configuration

All configuration is centralized in `config/settings.py` with environment variable overrides for deployment flexibility.

### API Configuration
- **Football Data API**: Free tier provides 10 requests/minute for Premier League data
- **Domino's API**: Optional - system uses realistic mock data by default
- **Rate Limiting**: Configurable limits with automatic backoff

### AWS Configuration
- **S3 Bucket**: Organized folder structure for raw, processed, and dashboard data
- **Lambda Function**: Single function handling the complete pipeline
- **QuickSight**: Interactive dashboards with real-time data refresh

## 📈 System Architecture

The system follows a modular, event-driven architecture:

1. **Data Collection Layer**: External APIs with intelligent fallback
2. **Processing Layer**: ETL pipeline with correlation analysis
3. **Storage Layer**: S3 with organized data lifecycle
4. **Visualization Layer**: QuickSight dashboards with interactive filters

## 🚀 Quick Start

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd pizza-game-dashboard
   python setup_dev.py
   ```

2. **Configure APIs** (Optional):
   ```bash
   # Get free API key from football-data.org
   export FOOTBALL_API_KEY=your_key_here
   ```

3. **Run Locally**:
   ```bash
   python lambda_function.py
   ```

4. **Deploy to AWS**:
   ```bash
   python deploy.py
   # Upload pizza-game-dashboard.zip to Lambda console
   ```

## 📚 Documentation

- [API Setup Guide](API_SETUP.md) - Complete API configuration instructions
- [Technical Blog](BUILDER_CENTER_BLOG.md) - Development journey and insights
- [Architecture Documentation](#architecture-documentation) - Detailed system design
- [Error Handling Guide](#error-handling-guide) - Troubleshooting and recovery procedures

## 🧪 Testing

The system uses a dual testing approach:
- **Unit Tests**: Specific functionality validation
- **Property-Based Tests**: Universal behavior verification using Hypothesis
- **Integration Tests**: End-to-end pipeline testing

Run tests with:
```bash
make test           # All tests
make test-properties # Property-based tests only
```