# Error Handling and Troubleshooting Guide

## Overview

The Pizza Game Dashboard implements comprehensive error handling across all system components to ensure reliable operation even when external dependencies fail. This guide covers error scenarios, recovery procedures, and troubleshooting steps.

## Error Handling Architecture

### 1. Layered Error Handling Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                            │
│  • Business Logic Errors                                       │
│  • Data Validation Errors                                      │
│  • Correlation Analysis Errors                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Integration Layer                            │
│  • API Connection Errors                                       │
│  • Authentication Failures                                     │
│  • Rate Limiting Errors                                        │
│  • Data Format Errors                                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                         │
│  • AWS Service Errors                                          │
│  • Network Connectivity Issues                                 │
│  • Resource Limit Errors                                       │
│  • Permission Errors                                           │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Error Classification System

#### Critical Errors (System Halt)
- AWS credential failures
- S3 bucket access denied
- Lambda timeout exceeded
- Memory allocation failures

#### Recoverable Errors (Automatic Retry)
- Network timeouts
- API rate limiting
- Temporary service unavailability
- Transient AWS service errors

#### Degraded Operation Errors (Fallback)
- External API unavailability
- Partial data collection failures
- Non-critical validation errors
- Mock data generation issues

## API Integration Error Handling

### 1. Football Data API Errors

#### Common Error Scenarios

**Rate Limiting (429 Too Many Requests)**
```python
def handle_rate_limit_error(self, response: requests.Response) -> bool:
    """
    Handle API rate limiting with intelligent backoff.
    
    The football-data.org API allows 10 requests per minute.
    When rate limited, we implement exponential backoff.
    """
    if response.status_code == 429:
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            sleep_time = int(retry_after)
            self.logger.warning(f"Rate limit exceeded, waiting {sleep_time} seconds")
            time.sleep(sleep_time)
            return True  # Retry recommended
        else:
            # No Retry-After header, use exponential backoff
            sleep_time = self.config.backoff_factor * (2 ** random.randint(0, 3))
            self.logger.warning(f"Rate limit exceeded, backing off {sleep_time} seconds")
            time.sleep(sleep_time)
            return True
    return False
```

**Authentication Errors (401 Unauthorized)**
```python
def handle_auth_error(self, response: requests.Response) -> None:
    """
    Handle authentication failures.
    
    Authentication errors are not recoverable and require
    manual intervention to fix API credentials.
    """
    if response.status_code == 401:
        error_msg = "Football API authentication failed. Check FOOTBALL_API_KEY environment variable."
        self.logger.error(error_msg)
        
        # Log additional context for debugging
        self.logger.error(f"API URL: {response.url}")
        self.logger.error(f"Request headers: {dict(response.request.headers)}")
        
        # Don't retry auth errors - fall back to mock data
        raise APIAuthenticationError(error_msg)
```

**Network Connectivity Issues**
```python
def handle_network_error(self, error: requests.exceptions.RequestException) -> bool:
    """
    Handle network-related errors with retry logic.
    
    Network errors are often transient and benefit from retry
    with exponential backoff.
    """
    if isinstance(error, (requests.exceptions.ConnectionError, 
                         requests.exceptions.Timeout)):
        
        self.logger.warning(f"Network error: {str(error)}")
        
        # Implement exponential backoff
        retry_count = getattr(self, '_retry_count', 0)
        if retry_count < self.config.max_retries:
            sleep_time = self.config.backoff_factor * (2 ** retry_count)
            self.logger.info(f"Retrying in {sleep_time} seconds (attempt {retry_count + 1})")
            time.sleep(sleep_time)
            self._retry_count = retry_count + 1
            return True  # Retry
        else:
            self.logger.error(f"Max retries exceeded for network error: {str(error)}")
            return False  # Fall back to mock data
    
    return False
```

#### Fallback to Mock Data
```python
def collect_football_data(self, start_date: datetime, end_date: datetime) -> List[FootballMatch]:
    """
    Collect football data with comprehensive error handling and fallback.
    
    Error handling priority:
    1. Try real API data collection
    2. On any error, log details and fall back to mock data
    3. Ensure system continues operation regardless of API status
    """
    try:
        # Check API credentials
        if not self.config.football_api_key:
            self.logger.warning("No Football API key provided, using mock data")
            return self._fallback_to_mock_matches(start_date, end_date)
        
        # Attempt real data collection
        matches = self._fetch_real_matches(start_date, end_date)
        
        if matches:
            self.logger.info(f"Successfully collected {len(matches)} real football matches")
            return matches
        else:
            self.logger.warning("No real matches retrieved, falling back to mock data")
            return self._fallback_to_mock_matches(start_date, end_date)
            
    except APIAuthenticationError as e:
        self.logger.error(f"Authentication failed: {e}")
        return self._fallback_to_mock_matches(start_date, end_date)
        
    except requests.exceptions.RequestException as e:
        self.logger.error(f"Network error collecting football data: {e}")
        return self._fallback_to_mock_matches(start_date, end_date)
        
    except Exception as e:
        self.logger.error(f"Unexpected error collecting football data: {e}")
        return self._fallback_to_mock_matches(start_date, end_date)
```

### 2. Domino's API Error Handling

Since real Domino's API access requires business partnerships, the system is designed to gracefully handle the absence of real pizza order data:

```python
def collect_dominos_data(self, start_date: datetime, end_date: datetime) -> List[DominosOrder]:
    """
    Collect Domino's data with intelligent fallback strategy.
    
    The system is designed to work primarily with mock pizza data
    since real Domino's APIs require business partnerships.
    """
    # Check for API credentials
    if not self.config.dominos_api_key or not self.config.dominos_store_id:
        self.logger.info("Domino's API credentials not configured, using realistic mock data")
        return self._fallback_to_mock_orders(start_date, end_date)
    
    try:
        # Attempt real data collection if credentials are available
        orders = self._fetch_real_orders(start_date, end_date)
        if orders:
            self.logger.info(f"Successfully collected {len(orders)} real Domino's orders")
            return orders
        else:
            self.logger.info("No real orders available, using mock data")
            return self._fallback_to_mock_orders(start_date, end_date)
            
    except Exception as e:
        self.logger.warning(f"Error collecting real Domino's data: {e}")
        return self._fallback_to_mock_orders(start_date, end_date)
```

## AWS Service Error Handling

### 1. S3 Storage Errors

#### Bucket Access Errors
```python
def _verify_bucket_access(self) -> None:
    """
    Verify S3 bucket access with detailed error reporting.
    
    This method provides specific error messages for different
    S3 access issues to aid in troubleshooting.
    """
    try:
        self.s3_client.head_bucket(Bucket=self.bucket_name)
        self.logger.info(f"Successfully connected to S3 bucket: {self.bucket_name}")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        if error_code == '404':
            error_msg = f"S3 bucket '{self.bucket_name}' not found. Please create the bucket first."
            self.logger.error(error_msg)
            raise S3StorageError(error_msg)
            
        elif error_code == '403':
            error_msg = f"Access denied to S3 bucket '{self.bucket_name}'. Check IAM permissions."
            self.logger.error(error_msg)
            self.logger.error("Required permissions: s3:GetObject, s3:PutObject, s3:ListBucket")
            raise S3StorageError(error_msg)
            
        else:
            error_msg = f"Error accessing S3 bucket '{self.bucket_name}': {str(e)}"
            self.logger.error(error_msg)
            raise S3StorageError(error_msg)
            
    except NoCredentialsError:
        error_msg = "AWS credentials not found. Configure AWS credentials or IAM role."
        self.logger.error(error_msg)
        raise S3StorageError(error_msg)
```

#### Upload/Download Error Handling
```python
def upload_json_data(self, data: Union[List[Dict], Dict], data_type: str, 
                    data_source: str, filename: str = None, 
                    timestamp: datetime = None, **metadata_kwargs) -> str:
    """
    Upload JSON data with comprehensive error handling and retry logic.
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Generate S3 key and prepare data
            s3_key = self._generate_file_key(data_type, data_source, filename, timestamp)
            json_data = json.dumps(data, indent=2, default=str)
            
            # Create metadata
            record_count = len(data) if isinstance(data, list) else 1
            metadata = self._create_metadata(data_source, data_type, record_count, **metadata_kwargs)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_data,
                ContentType='application/json',
                Metadata=metadata
            )
            
            self.logger.info(f"Successfully uploaded JSON data to s3://{self.bucket_name}/{s3_key}")
            return s3_key
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            retry_count += 1
            
            if error_code in ['ServiceUnavailable', 'SlowDown', 'RequestTimeout']:
                if retry_count < max_retries:
                    sleep_time = 2 ** retry_count  # Exponential backoff
                    self.logger.warning(f"S3 service error {error_code}, retrying in {sleep_time}s (attempt {retry_count})")
                    time.sleep(sleep_time)
                    continue
                else:
                    raise S3StorageError(f"S3 upload failed after {max_retries} retries: {str(e)}")
            else:
                raise S3StorageError(f"S3 upload failed: {str(e)}")
                
        except Exception as e:
            raise S3StorageError(f"Unexpected error uploading to S3: {str(e)}")
    
    raise S3StorageError(f"S3 upload failed after {max_retries} retries")
```

### 2. Lambda Function Errors

#### Memory and Timeout Handling
```python
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler with comprehensive error handling and monitoring.
    
    Handles memory limits, timeouts, and provides detailed error reporting
    for CloudWatch monitoring and alerting.
    """
    execution_id = context.aws_request_id if context else f'local-{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    start_time = time.time()
    
    try:
        # Check remaining execution time
        if context and context.get_remaining_time_in_millis() < 60000:  # Less than 1 minute
            raise LambdaTimeoutError("Insufficient time remaining for execution")
        
        # Initialize services with error handling
        try:
            s3_service = S3Service()
            api_config = create_api_config_from_env()
            data_collector = DataCollectionSystem(api_config)
        except Exception as e:
            return create_error_response(500, f"Service initialization failed: {str(e)}", execution_id)
        
        # Execute main pipeline with progress monitoring
        try:
            # Monitor memory usage
            import psutil
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 90:
                logger.warning(f"High memory usage: {memory_percent}%")
            
            # Execute data collection
            pizza_orders, football_matches = data_collector.collect_all_data(start_date, end_date)
            
            # Check execution time before processing
            if context and context.get_remaining_time_in_millis() < 300000:  # Less than 5 minutes
                logger.warning("Limited time remaining, skipping detailed analysis")
                # Perform basic processing only
            
            # Continue with processing...
            
        except MemoryError:
            return create_error_response(500, "Lambda function ran out of memory", execution_id)
        except Exception as e:
            return create_error_response(500, f"Pipeline execution failed: {str(e)}", execution_id)
        
        # Success response
        execution_time = time.time() - start_time
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Pipeline completed successfully',
                'execution_id': execution_id,
                'execution_time_seconds': round(execution_time, 2),
                'data_summary': {
                    'pizza_orders_collected': len(pizza_orders),
                    'football_matches_collected': len(football_matches)
                }
            })
        }
        
    except Exception as e:
        # Catch-all error handler
        execution_time = time.time() - start_time
        logger.error(f"Unhandled error in Lambda execution: {str(e)}")
        return create_error_response(500, f"Unhandled error: {str(e)}", execution_id, execution_time)

def create_error_response(status_code: int, error_message: str, 
                         execution_id: str, execution_time: float = None) -> Dict[str, Any]:
    """Create standardized error response for Lambda function."""
    response_body = {
        'error': error_message,
        'execution_id': execution_id,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if execution_time:
        response_body['execution_time_seconds'] = round(execution_time, 2)
    
    return {
        'statusCode': status_code,
        'body': json.dumps(response_body)
    }
```

## Data Processing Error Handling

### 1. ETL Pipeline Errors

#### Data Validation Errors
```python
def extract_pizza_orders(self, data_source: str = None, 
                        date_range: Tuple[datetime, datetime] = None) -> List[DominosOrder]:
    """
    Extract pizza orders with comprehensive validation and error recovery.
    """
    try:
        orders = []
        sources_to_check = [data_source] if data_source else ['real', 'mock']
        
        for source in sources_to_check:
            try:
                files = self.s3_service.list_files(data_type='dominos-orders', data_source=source)
                self.logger.info(f"Found {len(files)} files for {source} pizza orders")
                
                for file_info in files:
                    try:
                        # Validate file before processing
                        if not self._validate_file_info(file_info):
                            self.logger.warning(f"Skipping invalid file: {file_info['key']}")
                            continue
                        
                        # Process file based on type
                        if file_info['key'].endswith('.json'):
                            file_orders = self._process_json_order_file(file_info)
                        elif file_info['key'].endswith('.csv'):
                            file_orders = self._process_csv_order_file(file_info)
                        else:
                            self.logger.warning(f"Unsupported file format: {file_info['key']}")
                            continue
                        
                        # Validate extracted orders
                        valid_orders = self._validate_orders(file_orders, date_range)
                        orders.extend(valid_orders)
                        
                    except Exception as e:
                        self.logger.error(f"Failed to process file {file_info['key']}: {str(e)}")
                        # Continue processing other files
                        continue
                        
            except S3StorageError as e:
                self.logger.warning(f"No {source} pizza order data found: {str(e)}")
                continue
        
        if not orders:
            raise ETLPipelineError("No valid pizza orders found for processing")
        
        self.logger.info(f"Successfully extracted {len(orders)} pizza orders")
        return orders
        
    except Exception as e:
        raise ETLPipelineError(f"Failed to extract pizza orders: {str(e)}")

def _validate_orders(self, orders: List[DominosOrder], 
                    date_range: Tuple[datetime, datetime] = None) -> List[DominosOrder]:
    """
    Validate pizza orders and filter out invalid records.
    """
    valid_orders = []
    
    for order in orders:
        try:
            # Validate required fields
            if not order.order_id or not order.timestamp:
                self.logger.warning(f"Order missing required fields: {order.order_id}")
                continue
            
            # Validate data types
            if not isinstance(order.order_total, (int, float)) or order.order_total < 0:
                self.logger.warning(f"Invalid order total for order {order.order_id}: {order.order_total}")
                continue
            
            # Validate date range
            if date_range and not self._is_in_date_range(order.timestamp, date_range):
                continue
            
            # Validate business logic
            if order.quantity <= 0:
                self.logger.warning(f"Invalid quantity for order {order.order_id}: {order.quantity}")
                continue
            
            valid_orders.append(order)
            
        except Exception as e:
            self.logger.warning(f"Error validating order {getattr(order, 'order_id', 'unknown')}: {str(e)}")
            continue
    
    validation_rate = len(valid_orders) / len(orders) * 100 if orders else 0
    self.logger.info(f"Order validation rate: {validation_rate:.1f}% ({len(valid_orders)}/{len(orders)})")
    
    return valid_orders
```

#### Data Transformation Errors
```python
def normalize_data_formats(self, orders: List[DominosOrder], 
                          matches: List[FootballMatch]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Normalize data formats with error handling for data quality issues.
    """
    try:
        self.logger.info("Normalizing data formats for consistent processing")
        
        # Process orders with error handling
        orders_data = []
        failed_orders = 0
        
        for order in orders:
            try:
                normalized_order = {
                    'id': str(order.order_id),
                    'timestamp': pd.to_datetime(order.timestamp, utc=True),
                    'location': str(order.location).strip().lower(),
                    'total_amount': float(order.order_total),
                    'pizza_count': int(order.quantity),
                    'pizza_types': ';'.join(sorted([pt.strip().lower() for pt in order.pizza_types])),
                    'data_source': str(order.data_source),
                    'record_type': 'pizza_order'
                }
                
                # Validate normalized data
                if self._validate_normalized_order(normalized_order):
                    orders_data.append(normalized_order)
                else:
                    failed_orders += 1
                    
            except Exception as e:
                self.logger.warning(f"Failed to normalize order {order.order_id}: {str(e)}")
                failed_orders += 1
                continue
        
        # Process matches with error handling
        matches_data = []
        failed_matches = 0
        
        for match in matches:
            try:
                normalized_match = {
                    'id': str(match.match_id),
                    'timestamp': pd.to_datetime(match.timestamp, utc=True),
                    'home_team': str(match.home_team).strip().title(),
                    'away_team': str(match.away_team).strip().title(),
                    'home_score': int(match.home_score),
                    'away_score': int(match.away_score),
                    'total_goals': int(match.home_score + match.away_score),
                    'event_type': str(match.event_type).lower(),
                    'match_significance': str(match.match_significance).lower(),
                    'winner': match.get_winner() if hasattr(match, 'get_winner') else self._determine_winner(match),
                    'is_high_scoring': (match.home_score + match.away_score) >= 3,
                    'data_source': str(match.data_source),
                    'record_type': 'football_match'
                }
                
                # Validate normalized data
                if self._validate_normalized_match(normalized_match):
                    matches_data.append(normalized_match)
                else:
                    failed_matches += 1
                    
            except Exception as e:
                self.logger.warning(f"Failed to normalize match {match.match_id}: {str(e)}")
                failed_matches += 1
                continue
        
        # Create DataFrames
        orders_df = pd.DataFrame(orders_data)
        matches_df = pd.DataFrame(matches_data)
        
        # Log normalization results
        self.logger.info(f"Normalization complete:")
        self.logger.info(f"  Orders: {len(orders_df)} successful, {failed_orders} failed")
        self.logger.info(f"  Matches: {len(matches_df)} successful, {failed_matches} failed")
        
        # Ensure we have data to work with
        if orders_df.empty:
            raise ETLPipelineError("No valid orders after normalization")
        if matches_df.empty:
            raise ETLPipelineError("No valid matches after normalization")
        
        return orders_df, matches_df
        
    except Exception as e:
        raise ETLPipelineError(f"Failed to normalize data formats: {str(e)}")
```

### 2. Correlation Analysis Errors

#### Statistical Calculation Errors
```python
def _calculate_single_correlation(self, volume_data: pd.Series, outcome_data: pd.Series,
                                outcome_name: str, volume_name: str,
                                metrics_df: pd.DataFrame) -> Optional[CorrelationResult]:
    """
    Calculate correlation with comprehensive error handling for statistical edge cases.
    """
    try:
        # Data validation and cleaning
        if volume_data.empty or outcome_data.empty:
            self.logger.warning(f"Empty data for correlation: {outcome_name} vs {volume_name}")
            return None
        
        # Remove NaN values
        valid_mask = ~(pd.isna(volume_data) | pd.isna(outcome_data))
        clean_volume = volume_data[valid_mask]
        clean_outcome = outcome_data[valid_mask]
        
        # Check for sufficient data points
        if len(clean_volume) < 3:
            self.logger.warning(f"Insufficient data points for correlation: {len(clean_volume)} < 3")
            return None
        
        # Check for variance in data
        if clean_volume.var() == 0:
            self.logger.warning(f"No variance in volume data for {volume_name}")
            return None
        
        if hasattr(clean_outcome, 'var') and clean_outcome.var() == 0:
            self.logger.warning(f"No variance in outcome data for {outcome_name}")
            return None
        
        # Calculate correlation based on data type
        try:
            if clean_outcome.dtype == bool or clean_outcome.nunique() == 2:
                # Point-biserial correlation for binary outcomes
                correlation_coef, p_value = stats.pointbiserialr(clean_outcome, clean_volume)
            else:
                # Pearson correlation for continuous outcomes
                correlation_coef, p_value = stats.pearsonr(clean_volume, clean_outcome)
        
        except Exception as e:
            self.logger.error(f"Statistical calculation failed for {outcome_name} vs {volume_name}: {str(e)}")
            return None
        
        # Handle invalid correlation results
        if np.isnan(correlation_coef) or np.isnan(p_value):
            self.logger.warning(f"Invalid correlation result (NaN) for {outcome_name} vs {volume_name}")
            return None
        
        if np.isinf(correlation_coef) or np.isinf(p_value):
            self.logger.warning(f"Invalid correlation result (Inf) for {outcome_name} vs {volume_name}")
            return None
        
        # Create correlation result
        time_window = self._extract_time_window(volume_name)
        pattern_description = self._generate_pattern_description(
            correlation_coef, p_value, outcome_name, volume_name, time_window
        )
        data_quality = self._calculate_data_quality_score(metrics_df)
        
        return CorrelationResult(
            analysis_id=str(uuid.uuid4()),
            correlation_coefficient=float(correlation_coef),
            statistical_significance=float(p_value),
            time_window=time_window,
            pattern_description=pattern_description,
            data_quality=data_quality,
            analysis_timestamp=datetime.utcnow(),
            sample_size=len(clean_volume)
        )
        
    except Exception as e:
        self.logger.error(f"Unexpected error calculating correlation for {outcome_name} vs {volume_name}: {str(e)}")
        return None
```

## Troubleshooting Guide

### 1. Common Issues and Solutions

#### Issue: "No API key" warnings
**Symptoms**: Logs show warnings about missing API keys
**Cause**: Environment variables not set
**Solution**:
```bash
# For local development
export FOOTBALL_API_KEY=your_key_here

# For Lambda deployment
# Set environment variables in Lambda console or SAM template
```

#### Issue: Rate limit errors
**Symptoms**: HTTP 429 errors in logs
**Cause**: Exceeding API rate limits (10 requests/minute for football-data.org)
**Solution**: The system automatically handles this with exponential backoff. No action needed.

#### Issue: S3 access denied
**Symptoms**: HTTP 403 errors when accessing S3
**Cause**: Insufficient IAM permissions
**Solution**:
1. Check IAM role has required S3 permissions
2. Verify bucket name is correct
3. Ensure bucket exists in the correct region

#### Issue: Lambda timeout
**Symptoms**: Lambda function times out after 15 minutes
**Cause**: Large dataset processing or API delays
**Solution**:
1. Reduce date range for data collection
2. Optimize processing logic
3. Consider splitting into multiple Lambda functions

#### Issue: Memory errors in Lambda
**Symptoms**: Lambda function runs out of memory
**Cause**: Processing large datasets
**Solution**:
1. Increase Lambda memory allocation
2. Process data in smaller chunks
3. Optimize data structures

### 2. Diagnostic Commands

#### Check API Configuration
```python
from src.data_collection import create_api_config_from_env

config = create_api_config_from_env()
print(f"Football API Key: {'Set' if config.football_api_key else 'Not set'}")
print(f"Dominos API Key: {'Set' if config.dominos_api_key else 'Not set'}")
print(f"Rate Limits: {config.max_requests_per_minute}/min, {config.max_requests_per_hour}/hour")
```

#### Test S3 Connection
```python
from src.storage.s3_service import S3Service

try:
    s3_service = S3Service()
    files = s3_service.list_files()
    print(f"S3 connection successful. Found {len(files)} files.")
except Exception as e:
    print(f"S3 connection failed: {str(e)}")
```

#### Validate Data Processing
```python
from src.data_processing.etl_pipeline import ETLPipeline

try:
    pipeline = ETLPipeline()
    # Test with small date range
    start_date = datetime.now() - timedelta(days=1)
    end_date = datetime.now()
    
    orders = pipeline.extract_pizza_orders(date_range=(start_date, end_date))
    matches = pipeline.extract_football_matches(date_range=(start_date, end_date))
    
    print(f"Data extraction successful: {len(orders)} orders, {len(matches)} matches")
except Exception as e:
    print(f"Data processing failed: {str(e)}")
```

### 3. Monitoring and Alerting

#### CloudWatch Metrics to Monitor
- Lambda function duration and memory usage
- API error rates and response times
- S3 upload/download success rates
- Data processing completion rates

#### Recommended CloudWatch Alarms
```json
{
    "AlarmName": "PizzaDashboard-LambdaErrors",
    "MetricName": "Errors",
    "Namespace": "AWS/Lambda",
    "Statistic": "Sum",
    "Period": 300,
    "EvaluationPeriods": 1,
    "Threshold": 1,
    "ComparisonOperator": "GreaterThanOrEqualToThreshold"
}
```

#### Log Analysis Queries
```sql
-- Find API errors
fields @timestamp, @message
| filter @message like /API.*error/
| sort @timestamp desc

-- Monitor data collection success rates
fields @timestamp, @message
| filter @message like /Successfully collected/
| stats count() by bin(5m)

-- Track fallback to mock data usage
fields @timestamp, @message
| filter @message like /fallback.*mock/
| sort @timestamp desc
```

### 4. Recovery Procedures

#### Automatic Recovery
The system is designed for automatic recovery from most error conditions:
- API failures → Automatic fallback to mock data
- Rate limiting → Exponential backoff and retry
- Network issues → Retry with backoff
- Partial data failures → Continue with available data

#### Manual Recovery Steps

**For persistent API issues:**
1. Check API service status at provider websites
2. Verify API keys are still valid
3. Check rate limiting quotas
4. Review CloudWatch logs for specific error patterns

**For S3 access issues:**
1. Verify IAM role permissions
2. Check bucket exists and is accessible
3. Validate bucket policy and CORS settings
4. Test with AWS CLI: `aws s3 ls s3://your-bucket-name`

**For Lambda function issues:**
1. Check CloudWatch logs for error details
2. Verify environment variables are set correctly
3. Test function with smaller payload
4. Monitor memory and timeout settings

**For data quality issues:**
1. Review data validation logs
2. Check source data formats
3. Validate timestamp formats and timezones
4. Verify correlation analysis parameters

### 5. Performance Optimization

#### Reducing Execution Time
- Implement parallel processing for independent operations
- Cache frequently accessed data
- Optimize database queries and data transformations
- Use appropriate data structures for large datasets

#### Memory Optimization
- Process data in chunks rather than loading everything into memory
- Use generators for large data iterations
- Clean up unused objects explicitly
- Monitor memory usage throughout execution

#### Cost Optimization
- Right-size Lambda memory allocation
- Implement S3 lifecycle policies for data archival
- Use appropriate S3 storage classes
- Monitor and optimize API usage patterns