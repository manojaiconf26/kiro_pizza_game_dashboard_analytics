# Design Document

## Overview

The Pizza Orders vs Game Scores Dashboard is an AWS-based analytics system that correlates pizza ordering patterns with football/soccer events. The system focuses on Domino's pizza orders and football match data, integrating real-time data collection with intelligent fallback to mock data generation when external sources are unavailable. All data is processed through Python-based ETL pipelines, stored in Amazon S3, and visualized through Amazon QuickSight dashboards to reveal insights about customer behavior during football matches.

## Architecture

The system follows a modular, cloud-native architecture with the following key components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   External APIs │    │  Mock Data Gen  │    │  Data Collection│
│                 │    │                 │    │     System      │
│ • Domino's API  │───▶│ • Pizza Orders  │───▶│                 │
│ • Football API  │    │ • Match Scores  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   QuickSight    │    │ Data Processing │    │   Amazon S3     │
│   Dashboard     │◀───│     Engine      │◀───│   Storage       │
│                 │    │                 │    │                 │
│ • Visualizations│    │ • ETL Pipeline  │    │ • Raw Data      │
│ • Analytics     │    │ • Correlations  │    │ • Processed     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components and Interfaces

### 1. Data Collection System

**External Data Collector**
- **Purpose**: Interfaces with Domino's API and football data sources
- **Key Methods**:
  - `collect_dominos_data(date_range)`: Retrieves order data from Domino's API
  - `collect_football_data(date_range)`: Fetches match scores and events
  - `handle_api_errors(response)`: Manages rate limits and authentication failures
- **Fallback Strategy**: Automatically switches to mock data generation on API failures

**Mock Data Generator**
- **Purpose**: Creates realistic synthetic data when real sources are unavailable
- **Key Methods**:
  - `generate_pizza_orders(num_days, base_volume)`: Creates Domino's order datasets with realistic patterns
  - `generate_football_matches(num_games)`: Produces football scores and event timelines
  - `correlate_data_timing(orders, matches)`: Ensures temporal alignment between datasets

### 2. Data Processing Engine

**ETL Pipeline**
- **Extract**: Retrieves data from S3 storage (both real and mock sources)
- **Transform**: Normalizes data formats, handles time zones, calculates derived metrics
- **Load**: Stores processed datasets back to S3 in QuickSight-compatible formats

**Correlation Analyzer**
- **Statistical Analysis**: Calculates correlation coefficients between football match events and Domino's order volumes
- **Pattern Detection**: Identifies significant spikes in orders following wins, goals, or major match events
- **Temporal Analysis**: Analyzes order patterns before, during, and after football matches

### 3. Storage Layer (Amazon S3)

**Bucket Structure**:
```
pizza-game-analytics/
├── raw-data/
│   ├── dominos-orders/
│   │   ├── real/
│   │   └── mock/
│   └── football-data/
│       ├── real/
│       └── mock/
├── processed-data/
│   ├── merged-datasets/
│   └── correlation-analysis/
└── quicksight-ready/
    ├── dashboard-data/
    └── metadata/
```

### 4. Visualization Layer (Amazon QuickSight)

**Dashboard Components**:
- **Time Series Charts**: Domino's order volumes over time with football match event overlays
- **Correlation Analysis**: Statistical relationships between match outcomes and order patterns
- **Interactive Filters**: Team, match type, data source (real vs mock)
- **Drill-Down Capabilities**: From high-level trends to specific match-day patterns

## Data Models

### Pizza Order Model
```python
@dataclass
class DominosOrder:
    order_id: str
    timestamp: datetime
    location: str
    order_total: float
    pizza_types: List[str]
    quantity: int
    data_source: str  # 'real' or 'mock'
```

### Football Match Model
```python
@dataclass
class FootballMatch:
    match_id: str
    timestamp: datetime
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    event_type: str  # 'goal', 'win', 'loss', 'draw'
    match_significance: str  # 'regular', 'tournament', 'final'
    data_source: str  # 'real' or 'mock'
```

### Correlation Analysis Model
```python
@dataclass
class CorrelationResult:
    analysis_id: str
    correlation_coefficient: float
    statistical_significance: float
    time_window: str  # 'pre_match', 'during_match', 'post_match'
    pattern_description: str
    data_quality: str  # percentage of real vs mock data used
```
## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

**Property 1: API Fallback Consistency**
*For any* external API (Domino's or football), when the API is unavailable or returns errors, the system should automatically fall back to mock data generation without failing
**Validates: Requirements 1.1, 1.3, 2.1, 2.3**

**Property 2: Complete Data Extraction**
*For any* successful API response (Domino's orders or football matches), all required fields (timestamps, quantities, scores, team names) should be extracted and present in the resulting dataset
**Validates: Requirements 1.4, 2.2**

**Property 3: Robust Error Handling**
*For any* API operation or S3 interaction, authentication failures, rate limits, and network errors should be handled gracefully without system crashes
**Validates: Requirements 1.2, 4.3**

**Property 4: Rate Limiting Compliance**
*For any* external API with usage restrictions, the system should never exceed the specified request rate limits during data collection
**Validates: Requirements 1.5**

**Property 5: Event Classification Accuracy**
*For any* football data collected, major events (goals, wins, tournament matches) should be correctly identified and categorized
**Validates: Requirements 2.4**

**Property 6: Data Format Consistency**
*For any* data collected (Domino's orders or football matches), the final dataset should have consistent field formats and structures
**Validates: Requirements 2.5**

**Property 7: Mock Data Realism**
*For any* mock data generation, the statistical distributions and patterns should mirror realistic Domino's ordering and football match behaviors
**Validates: Requirements 3.1, 3.2, 3.3**

**Property 8: Temporal Alignment**
*For any* generated or collected dataset, Domino's orders and football matches should occur within overlapping time windows to enable meaningful correlation analysis
**Validates: Requirements 3.4**

**Property 9: Data Source Labeling**
*For any* data record throughout the pipeline, the source (real vs mock) should be clearly labeled and maintained from collection through final visualization
**Validates: Requirements 3.5, 4.2, 5.5**

**Property 10: S3 Storage Organization**
*For any* data file stored in S3, it should be placed in the correct bucket structure with proper naming conventions indicating source and timestamp
**Validates: Requirements 4.1, 4.4**

**Property 11: Data Retrieval Reliability**
*For any* processing operation, the system should successfully retrieve both pizza order and game score datasets from S3 storage
**Validates: Requirements 5.1**

**Property 12: Timestamp-Based Alignment**
*For any* data merging operation, Domino's orders should be correctly aligned with nearby football match events based on temporal proximity
**Validates: Requirements 5.2**

**Property 13: Source-Agnostic Processing**
*For any* dataset (real or mock), the processing logic should handle both data sources consistently and produce equivalent output formats
**Validates: Requirements 5.3**

**Property 14: Comprehensive Metric Calculation**
*For any* football match event, the system should calculate Domino's order volumes for pre-match, during-match, and post-match time windows
**Validates: Requirements 5.4**

**Property 15: Correlation Coefficient Accuracy**
*For any* football match outcome, correlation coefficients between match results and Domino's order spikes should be calculated correctly
**Validates: Requirements 7.1**

**Property 16: Statistical Significance Detection**
*For any* order pattern analysis, statistically significant increases in Domino's orders following victories or major football events should be correctly identified
**Validates: Requirements 7.2**

**Property 17: Temporal Pattern Analysis**
*For any* football match, Domino's ordering patterns should be analyzed consistently across pre-match, during-match, and post-match time periods
**Validates: Requirements 7.3**

**Property 18: Insight Generation Completeness**
*For any* analysis run, summary statistics should be generated for all available football match and Domino's order data
**Validates: Requirements 7.4**

**Property 19: Anomaly Detection with Source Distinction**
*For any* anomalous ordering pattern detected, the system should correctly distinguish whether the anomaly appears in real data, mock data, or both
**Validates: Requirements 7.5**

## Error Handling

The system implements comprehensive error handling across all components:

**API Integration Errors**:
- Network timeouts and connection failures
- Authentication and authorization errors
- Rate limiting and quota exceeded responses
- Invalid or malformed API responses
- Service unavailability and maintenance windows

**Data Processing Errors**:
- Missing or corrupted data files in S3
- Schema mismatches between expected and actual data formats
- Timestamp parsing and timezone conversion errors
- Statistical calculation errors (division by zero, insufficient data)
- Memory and performance issues with large datasets

**AWS Service Errors**:
- S3 access permission errors
- Bucket not found or misconfigured
- QuickSight connection and authentication failures
- Data source refresh and synchronization errors

**Fallback Strategies**:
- Automatic switching to mock data when real APIs fail
- Graceful degradation with partial data when some sources are unavailable
- Retry mechanisms with exponential backoff for transient failures
- Clear error logging and alerting for monitoring and debugging

## Testing Strategy

The system employs a dual testing approach combining unit tests and property-based tests to ensure comprehensive coverage and correctness validation.

**Property-Based Testing Framework**: The system uses **Hypothesis** for Python property-based testing, configured to run a minimum of 100 iterations per property test to ensure statistical confidence in the results.

**Property-Based Tests**:
- Each correctness property will be implemented as a separate property-based test
- Tests will generate random inputs across the valid input space to verify universal properties
- Property tests will focus on behavioral correctness across all possible inputs
- Each property test will be tagged with comments explicitly referencing the design document property: **Feature: pizza-game-dashboard, Property {number}: {property_text}**

**Unit Tests**:
- Specific examples demonstrating correct behavior for known inputs
- Edge cases such as empty datasets, single data points, and boundary conditions
- Integration points between components (API to storage, storage to processing)
- Error conditions and exception handling scenarios

**Test Coverage Requirements**:
- All API integration points must have both unit and property tests
- Data transformation logic must be validated with property tests for correctness
- Mock data generators must be tested to ensure realistic output distributions
- S3 operations must be tested for proper error handling and data organization
- Statistical calculations must be verified for mathematical accuracy

**Testing Infrastructure**:
- Automated test execution in CI/CD pipeline
- Mock AWS services for testing S3 and QuickSight integration
- Test data fixtures for consistent unit test scenarios
- Performance benchmarks for large dataset processing
- Integration tests with real API endpoints (when available and appropriate)