# Implementation Plan

- [x] 1. Create AWS resources via AWS Console






  - **S3 Bucket Setup:**
    1. Navigate to S3 in AWS Console
    2. Click "Create bucket"
    3. Name: `pizza-game-analytics-[your-unique-suffix]`
    4. Region: Choose your preferred region (e.g., us-east-1)
    5. Keep default settings for Block Public Access (recommended)
    6. Click "Create bucket"
    7. Inside the bucket, create folder structure:
       - `raw-data/dominos-orders/real/`
       - `raw-data/dominos-orders/mock/`
       - `raw-data/football-data/real/`
       - `raw-data/football-data/mock/`
       - `processed-data/merged-datasets/`
       - `processed-data/correlation-analysis/`
       - `quicksight-ready/dashboard-data/`
       - `quicksight-ready/metadata/`
  - **IAM Role Setup:**
    1. Navigate to IAM in AWS Console
    2. Click "Roles" → "Create role"
    3. Select "AWS service" as trusted entity type
    4. Choose "Lambda" (serverless functions for quick, cost-effective processing)
    5. Click "Next"
    6. Attach permission policies:
       - Search and select `AmazonS3FullAccess`
       - For QuickSight, you'll need to create a custom policy (see step 12 below)
    7. Click "Next"
    8. Role name: `PizzaDashboardRole`
    9. Description: "Role for Pizza Game Dashboard with S3 and QuickSight access"
    10. Click "Create role"
    11. **Create Custom QuickSight Policy:**
        - Go back to IAM → Policies → "Create policy"
        - Click "JSON" tab and paste this policy:
        ```json
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "quicksight:CreateDataSet",
                        "quicksight:CreateDataSource",
                        "quicksight:UpdateDataSet",
                        "quicksight:UpdateDataSource",
                        "quicksight:DescribeDataSet",
                        "quicksight:DescribeDataSource",
                        "quicksight:PassDataSet",
                        "quicksight:PassDataSource"
                    ],
                    "Resource": "*"
                }
            ]
        }
        ```
        - Name: `QuickSightDataAccess`
        - Click "Create policy"
    12. **Attach Custom Policy to Role:**
        - Go back to your `PizzaDashboardRole`
        - Click "Attach policies"
        - Search and select `QuickSightDataAccess`
        - Click "Attach policy"
    13. **Lambda Function Setup:**
        - You'll create **one Lambda function** that handles the complete pipeline:
          - `pizza-game-dashboard`: Collects data, processes it, and updates QuickSight
        - This function will automatically use the `PizzaDashboardRole` when created
        - Simpler to manage and deploy than multiple functions
  - **QuickSight Setup:**
    1. Navigate to QuickSight in AWS Console
    2. If first time: Click "Sign up for QuickSight"
    3. Choose "Standard" edition (free for first 30 days, then $9/month per user)
    4. Create QuickSight account name (must be unique across all AWS)
    5. Enter notification email address
    6. **Important**: Check "Amazon S3" in the list of AWS services
    7. Click "Choose S3 buckets" → Select your `pizza-game-analytics-[suffix]` bucket
    8. Click "Select buckets" then "Finish"
    9. Wait for account creation (may take a few minutes)
    10. You'll be redirected to QuickSight console when ready
  - _Requirements: 4.1, 4.3, 6.1_

- [x] 2. Set up project structure and Lambda deployment



  - Create Python project directory structure for Lambda functions
  - Install required dependencies: boto3, pandas, requests (Lambda-compatible versions)
  - Create deployment packages for each Lambda function
  - Set up local development environment with SAM CLI or serverless framework
  - Create configuration files for API endpoints and S3 bucket settings
  - _Requirements: 1.5, 4.5_

- [x] 3. Implement data models and validation





  - Create DominosOrder dataclass with validation methods
  - Create FootballMatch dataclass with validation methods  
  - Create CorrelationResult dataclass for analysis outputs
  - Implement data serialization/deserialization for CSV and JSON formats
  - _Requirements: 1.4, 2.2, 5.5_

- [ ]* 3.1 Write property test for data model serialization
  - **Property 9: Data Source Labeling**
  - **Validates: Requirements 3.5, 4.2, 5.5**

- [x] 4. Build mock data generators





  - Implement realistic Domino's order generator with statistical distributions
  - Implement football match generator with realistic scores and timing
  - Create temporal alignment logic to correlate orders with match events
  - Add configurable parameters for data volume and time ranges
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ]* 4.1 Write property test for mock data realism
  - **Property 7: Mock Data Realism**
  - **Validates: Requirements 3.1, 3.2, 3.3**

- [ ]* 4.2 Write property test for temporal alignment
  - **Property 8: Temporal Alignment**
  - **Validates: Requirements 3.4**

- [x] 5. Implement external API collectors






  - Create Domino's API client with authentication and error handling
  - Create football data API client with rate limiting
  - Implement fallback mechanism to mock data when APIs fail
  - Add retry logic with exponential backoff for transient failures
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.3_

- [ ]* 5.1 Write property test for API fallback consistency
  - **Property 1: API Fallback Consistency**
  - **Validates: Requirements 1.1, 1.3, 2.1, 2.3**

- [ ]* 5.2 Write property test for complete data extraction
  - **Property 2: Complete Data Extraction**
  - **Validates: Requirements 1.4, 2.2**

- [ ]* 5.3 Write property test for error handling
  - **Property 3: Robust Error Handling**
  - **Validates: Requirements 1.2, 4.3**

- [ ]* 5.4 Write property test for rate limiting compliance
  - **Property 4: Rate Limiting Compliance**
  - **Validates: Requirements 1.5**

- [x] 6. Create S3 storage service





  - Implement S3 client with proper authentication and error handling
  - Create bucket organization logic with clear naming conventions
  - Add file upload/download methods with metadata preservation
  - Implement data source labeling throughout storage operations
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ]* 6.1 Write property test for S3 storage organization
  - **Property 10: S3 Storage Organization**
  - **Validates: Requirements 4.1, 4.4**

- [ ]* 6.2 Write property test for data retrieval reliability
  - **Property 11: Data Retrieval Reliability**
  - **Validates: Requirements 5.1**

- [x] 7. Build data processing engine





  - Implement ETL pipeline to retrieve data from S3
  - Create timestamp-based alignment logic for merging datasets
  - Add data normalization for consistent formats across sources
  - Implement source-agnostic processing for real and mock data
  - _Requirements: 5.1, 5.2, 5.3, 2.5_

- [ ]* 7.1 Write property test for timestamp-based alignment
  - **Property 12: Timestamp-Based Alignment**
  - **Validates: Requirements 5.2**

- [ ]* 7.2 Write property test for source-agnostic processing
  - **Property 13: Source-Agnostic Processing**
  - **Validates: Requirements 5.3**

- [ ]* 7.3 Write property test for data format consistency
  - **Property 6: Data Format Consistency**
  - **Validates: Requirements 2.5**

- [x] 8. Implement correlation analysis engine





  - Create metric calculation for pre-match, during-match, and post-match order volumes
  - Implement correlation coefficient calculations between match outcomes and order spikes
  - Add statistical significance testing for pattern detection
  - Create event classification logic for football match events
  - _Requirements: 5.4, 7.1, 7.2, 2.4_

- [ ]* 7.1 Write property test for comprehensive metric calculation
  - **Property 14: Comprehensive Metric Calculation**
  - **Validates: Requirements 5.4**

- [ ]* 7.2 Write property test for correlation coefficient accuracy
  - **Property 15: Correlation Coefficient Accuracy**
  - **Validates: Requirements 7.1**

- [ ]* 7.3 Write property test for statistical significance detection
  - **Property 16: Statistical Significance Detection**
  - **Validates: Requirements 7.2**

- [ ]* 7.4 Write property test for event classification accuracy
  - **Property 5: Event Classification Accuracy**
  - **Validates: Requirements 2.4**

- [x] 8. Create insight generation system





  - Implement temporal pattern analysis across match periods
  - Create summary statistics generation for all available data
  - Add anomaly detection with source distinction capabilities
  - Generate comprehensive analysis reports with data quality indicators
  - _Requirements: 7.3, 7.4, 7.5_

- [ ]* 8.1 Write property test for temporal pattern analysis
  - **Property 17: Temporal Pattern Analysis**
  - **Validates: Requirements 7.3**

- [ ]* 8.2 Write property test for insight generation completeness
  - **Property 18: Insight Generation Completeness**
  - **Validates: Requirements 7.4**

- [ ]* 8.3 Write property test for anomaly detection with source distinction
  - **Property 19: Anomaly Detection with Source Distinction**
  - **Validates: Requirements 7.5**

- [-] 9. Checkpoint - Ensure all tests pass



  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Create and deploy Lambda function
  - **Create Single Lambda Function:**
    1. Go to Lambda Console → "Create function"
    2. Function name: `pizza-game-dashboard`
    3. Runtime: Python 3.9 or later
    4. Execution role: Use existing role → `PizzaDashboardRole`
    5. Upload your complete pipeline code as deployment package
    6. Set timeout to 15 minutes (maximum)
    7. Set memory to 1024 MB (for data processing)
    8. Configure environment variables:
       - `S3_BUCKET_NAME`: Your bucket name
       - `QUICKSIGHT_ACCOUNT_ID`: Your AWS account ID
  - **Set up trigger:**
    - CloudWatch Events/EventBridge for scheduled execution (e.g., daily at 6 PM)
  - _Requirements: 5.5, 6.1, 6.2, 6.3, 6.4_

- [ ] 11. Configure Lambda scheduling and monitoring
  - Set up EventBridge rule to trigger Lambda on schedule (e.g., daily at 6 PM when games typically end)
  - Configure CloudWatch monitoring and logging for the Lambda function
  - Set up CloudWatch alarms for function failures or timeouts
  - Test the complete serverless pipeline end-to-end
  - _Requirements: 5.5, 6.1, 6.2, 6.3, 6.4_

- [ ]* 11.1 Write integration tests for Lambda pipeline
  - Test full workflow from data collection through analysis in single function
  - Verify QuickSight data format compatibility
  - Test error handling and retry logic within the function
  - _Requirements: 5.5, 6.1, 6.2, 6.3, 6.4_

- [ ] 12. Create QuickSight dashboard setup
  - Create QuickSight data source configuration for S3
  - Design dashboard layout with time series and correlation charts
  - Implement interactive filters for teams, match types, and data sources
  - Add drill-down capabilities for detailed analysis
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 13. Add comprehensive documentation and comments
  - Document all API integration points and authentication methods
  - Add detailed comments explaining data transformation logic
  - Create usage documentation with examples and configuration guides
  - Document error handling procedures and troubleshooting steps
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Clean up AWS resources (when project is complete)
  - **S3 Cleanup:**
    1. Navigate to S3 in AWS Console
    2. Select your `pizza-game-analytics-[suffix]` bucket
    3. Click "Empty" to delete all objects
    4. Confirm by typing "permanently delete"
    5. Click "Delete bucket" and confirm by typing bucket name
  - **QuickSight Cleanup:**
    1. Navigate to QuickSight in AWS Console
    2. Go to "Manage QuickSight" → "Account settings"
    3. Click "Delete account" if no longer needed
    4. Or keep account but delete datasets: Go to "Datasets" → Select dashboard datasets → "Delete"
  - **IAM Role Cleanup:**
    1. Navigate to IAM in AWS Console
    2. Click "Roles" → Select `PizzaDashboardRole`
    3. First delete all Lambda functions that use this role
    4. Click "Delete role" and confirm deletion
  - **Cost Verification:**
    1. Navigate to AWS Billing Dashboard
    2. Check for any remaining charges
    3. Verify all resources are properly deleted
  - _Note: Only perform this task when the project is completely finished and you no longer need the resources_