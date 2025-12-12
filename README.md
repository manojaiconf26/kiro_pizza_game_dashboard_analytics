# Pizza Game Dashboard

A serverless analytics system that correlates pizza ordering patterns with football match events using AWS services.

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

## Configuration

All configuration is centralized in `config/settings.py` with environment variable overrides for deployment flexibility.