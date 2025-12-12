"""
ETL Pipeline for Pizza Game Dashboard

This module implements the Extract, Transform, Load pipeline that:
- Extracts data from S3 storage (both real and mock sources)
- Transforms and normalizes data formats across sources
- Loads processed datasets back to S3 for analysis

Requirements: 5.1, 5.2, 5.3, 2.5
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional, Union
import pandas as pd
from dataclasses import asdict
from io import StringIO

from src.storage.s3_service import S3Service, S3StorageError
from src.models.pizza_order import DominosOrder, orders_from_csv
from src.models.football_match import FootballMatch, matches_from_csv
from src.models.correlation_result import CorrelationResult, results_to_csv
from src.data_processing.correlation_analyzer import CorrelationAnalyzer
from config.settings import S3_BUCKET_NAME


class ETLPipelineError(Exception):
    """Custom exception for ETL pipeline operations"""
    pass


class ETLPipeline:
    """
    ETL Pipeline for processing pizza orders and football match data.
    
    Handles extraction from S3, transformation/normalization of data formats,
    and loading of processed datasets back to S3 for analysis.
    """
    
    def __init__(self, s3_service: S3Service = None):
        """
        Initialize ETL pipeline with S3 service.
        
        Args:
            s3_service: Optional S3Service instance (creates new if None)
        """
        self.s3_service = s3_service or S3Service()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.logger = logging.getLogger(__name__)
    
    def extract_pizza_orders(self, data_source: str = None, 
                           date_range: Tuple[datetime, datetime] = None) -> List[DominosOrder]:
        """
        Extract pizza order data from S3 storage.
        
        Args:
            data_source: Filter by data source ('real', 'mock', or None for both)
            date_range: Optional tuple of (start_date, end_date) for filtering
            
        Returns:
            List of DominosOrder objects
            
        Raises:
            ETLPipelineError: If extraction fails
        """
        try:
            self.logger.info(f"Extracting pizza orders (source: {data_source})")
            
            orders = []
            sources_to_check = [data_source] if data_source else ['real', 'mock']
            
            for source in sources_to_check:
                try:
                    # List files for this data source
                    files = self.s3_service.list_files(
                        data_type='dominos-orders',
                        data_source=source
                    )
                    
                    self.logger.info(f"Found {len(files)} files for {source} pizza orders")
                    
                    for file_info in files:
                        try:
                            # Download and parse data based on file type
                            if file_info['key'].endswith('.json'):
                                data = self.s3_service.download_json_data(file_info['key'])
                                # Convert JSON data to DominosOrder objects
                                for item in data if isinstance(data, list) else [data]:
                                    order = DominosOrder.from_dict(item)
                                    if self._is_in_date_range(order.timestamp, date_range):
                                        orders.append(order)
                            
                            elif file_info['key'].endswith('.csv'):
                                csv_data = self.s3_service.download_csv_data(file_info['key'])
                                # Convert CSV to string and parse
                                csv_string = csv_data.to_csv(index=False)
                                csv_orders = orders_from_csv(csv_string)
                                for order in csv_orders:
                                    if self._is_in_date_range(order.timestamp, date_range):
                                        orders.append(order)
                        
                        except Exception as e:
                            self.logger.warning(f"Failed to process file {file_info['key']}: {str(e)}")
                            continue
                
                except S3StorageError as e:
                    self.logger.warning(f"No {source} pizza order data found: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully extracted {len(orders)} pizza orders")
            return orders
            
        except Exception as e:
            raise ETLPipelineError(f"Failed to extract pizza orders: {str(e)}")
    
    def extract_football_matches(self, data_source: str = None,
                               date_range: Tuple[datetime, datetime] = None) -> List[FootballMatch]:
        """
        Extract football match data from S3 storage.
        
        Args:
            data_source: Filter by data source ('real', 'mock', or None for both)
            date_range: Optional tuple of (start_date, end_date) for filtering
            
        Returns:
            List of FootballMatch objects
            
        Raises:
            ETLPipelineError: If extraction fails
        """
        try:
            self.logger.info(f"Extracting football matches (source: {data_source})")
            
            matches = []
            sources_to_check = [data_source] if data_source else ['real', 'mock']
            
            for source in sources_to_check:
                try:
                    # List files for this data source
                    files = self.s3_service.list_files(
                        data_type='football-data',
                        data_source=source
                    )
                    
                    self.logger.info(f"Found {len(files)} files for {source} football matches")
                    
                    for file_info in files:
                        try:
                            # Download and parse data based on file type
                            if file_info['key'].endswith('.json'):
                                data = self.s3_service.download_json_data(file_info['key'])
                                # Convert JSON data to FootballMatch objects
                                for item in data if isinstance(data, list) else [data]:
                                    match = FootballMatch.from_dict(item)
                                    if self._is_in_date_range(match.timestamp, date_range):
                                        matches.append(match)
                            
                            elif file_info['key'].endswith('.csv'):
                                csv_data = self.s3_service.download_csv_data(file_info['key'])
                                # Convert CSV to string and parse
                                csv_string = csv_data.to_csv(index=False)
                                csv_matches = matches_from_csv(csv_string)
                                for match in csv_matches:
                                    if self._is_in_date_range(match.timestamp, date_range):
                                        matches.append(match)
                        
                        except Exception as e:
                            self.logger.warning(f"Failed to process file {file_info['key']}: {str(e)}")
                            continue
                
                except S3StorageError as e:
                    self.logger.warning(f"No {source} football match data found: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully extracted {len(matches)} football matches")
            return matches
            
        except Exception as e:
            raise ETLPipelineError(f"Failed to extract football matches: {str(e)}")
    
    def _is_in_date_range(self, timestamp: datetime, 
                         date_range: Tuple[datetime, datetime] = None) -> bool:
        """
        Check if timestamp falls within the specified date range.
        
        Args:
            timestamp: Timestamp to check
            date_range: Optional tuple of (start_date, end_date)
            
        Returns:
            True if timestamp is in range (or no range specified)
        """
        if date_range is None:
            return True
        
        start_date, end_date = date_range
        return start_date <= timestamp <= end_date
    
    def normalize_data_formats(self, orders: List[DominosOrder], 
                             matches: List[FootballMatch]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Normalize data formats for consistent processing across sources.
        
        Args:
            orders: List of DominosOrder objects
            matches: List of FootballMatch objects
            
        Returns:
            Tuple of (normalized_orders_df, normalized_matches_df)
            
        Requirements: 2.5 - Data format consistency
        """
        try:
            self.logger.info("Normalizing data formats for consistent processing")
            
            # Convert orders to normalized DataFrame
            orders_data = []
            for order in orders:
                orders_data.append({
                    'id': order.order_id,
                    'timestamp': order.timestamp,
                    'location': order.location.strip().lower(),  # Normalize location
                    'total_amount': float(order.order_total),
                    'pizza_count': int(order.quantity),
                    'pizza_types': ';'.join(sorted([pt.strip().lower() for pt in order.pizza_types])),
                    'data_source': order.data_source,
                    'record_type': 'pizza_order'
                })
            
            orders_df = pd.DataFrame(orders_data)
            
            # Convert matches to normalized DataFrame
            matches_data = []
            for match in matches:
                matches_data.append({
                    'id': match.match_id,
                    'timestamp': match.timestamp,
                    'home_team': match.home_team.strip().title(),  # Normalize team names
                    'away_team': match.away_team.strip().title(),
                    'home_score': int(match.home_score),
                    'away_score': int(match.away_score),
                    'total_goals': int(match.home_score + match.away_score),
                    'event_type': match.event_type.lower(),
                    'match_significance': match.match_significance.lower(),
                    'winner': match.get_winner(),
                    'is_high_scoring': match.is_high_scoring(),
                    'data_source': match.data_source,
                    'record_type': 'football_match'
                })
            
            matches_df = pd.DataFrame(matches_data)
            
            # Ensure consistent timestamp format and timezone handling
            if not orders_df.empty:
                orders_df['timestamp'] = pd.to_datetime(orders_df['timestamp'], utc=True)
                orders_df = orders_df.sort_values('timestamp').reset_index(drop=True)
            
            if not matches_df.empty:
                matches_df['timestamp'] = pd.to_datetime(matches_df['timestamp'], utc=True)
                matches_df = matches_df.sort_values('timestamp').reset_index(drop=True)
            
            self.logger.info(f"Normalized {len(orders_df)} orders and {len(matches_df)} matches")
            return orders_df, matches_df
            
        except Exception as e:
            raise ETLPipelineError(f"Failed to normalize data formats: {str(e)}")
    
    def align_datasets_by_timestamp(self, orders_df: pd.DataFrame, 
                                  matches_df: pd.DataFrame,
                                  time_window_hours: int = 6) -> pd.DataFrame:
        """
        Align pizza orders with football matches based on timestamps.
        
        Creates time windows around each match to capture related pizza orders:
        - Pre-match: 2 hours before match
        - During-match: match time ± 2 hours
        - Post-match: 2 hours after match
        
        Args:
            orders_df: Normalized pizza orders DataFrame
            matches_df: Normalized football matches DataFrame
            time_window_hours: Total time window around matches (default 6 hours)
            
        Returns:
            DataFrame with aligned orders and matches
            
        Requirements: 5.2 - Timestamp-based alignment
        """
        try:
            self.logger.info("Aligning datasets by timestamp")
            
            if orders_df.empty or matches_df.empty:
                self.logger.warning("One or both datasets are empty, returning empty alignment")
                return pd.DataFrame()
            
            aligned_data = []
            window_delta = timedelta(hours=time_window_hours // 2)
            
            for _, match in matches_df.iterrows():
                match_time = match['timestamp']
                
                # Define time windows around the match
                pre_match_start = match_time - timedelta(hours=2)
                match_start = match_time - timedelta(hours=1)
                match_end = match_time + timedelta(hours=1)
                post_match_end = match_time + timedelta(hours=2)
                
                # Find orders within the extended time window
                window_start = match_time - window_delta
                window_end = match_time + window_delta
                
                relevant_orders = orders_df[
                    (orders_df['timestamp'] >= window_start) &
                    (orders_df['timestamp'] <= window_end)
                ].copy()
                
                if not relevant_orders.empty:
                    # Categorize orders by time period
                    relevant_orders['time_period'] = 'other'
                    relevant_orders.loc[
                        (relevant_orders['timestamp'] >= pre_match_start) &
                        (relevant_orders['timestamp'] < match_start), 'time_period'
                    ] = 'pre_match'
                    relevant_orders.loc[
                        (relevant_orders['timestamp'] >= match_start) &
                        (relevant_orders['timestamp'] <= match_end), 'time_period'
                    ] = 'during_match'
                    relevant_orders.loc[
                        (relevant_orders['timestamp'] > match_end) &
                        (relevant_orders['timestamp'] <= post_match_end), 'time_period'
                    ] = 'post_match'
                    
                    # Calculate time difference from match start
                    relevant_orders['time_diff_minutes'] = (
                        relevant_orders['timestamp'] - match_time
                    ).dt.total_seconds() / 60
                    
                    # Add match information to each relevant order
                    for _, order in relevant_orders.iterrows():
                        aligned_record = {
                            # Order information
                            'order_id': order['id'],
                            'order_timestamp': order['timestamp'],
                            'order_location': order['location'],
                            'order_amount': order['total_amount'],
                            'pizza_count': order['pizza_count'],
                            'pizza_types': order['pizza_types'],
                            'order_data_source': order['data_source'],
                            
                            # Match information
                            'match_id': match['id'],
                            'match_timestamp': match['timestamp'],
                            'home_team': match['home_team'],
                            'away_team': match['away_team'],
                            'home_score': match['home_score'],
                            'away_score': match['away_score'],
                            'total_goals': match['total_goals'],
                            'event_type': match['event_type'],
                            'match_significance': match['match_significance'],
                            'winner': match['winner'],
                            'is_high_scoring': match['is_high_scoring'],
                            'match_data_source': match['data_source'],
                            
                            # Alignment information
                            'time_period': order['time_period'],
                            'time_diff_minutes': order['time_diff_minutes'],
                            'alignment_window_hours': time_window_hours,
                            
                            # Data quality indicators
                            'mixed_data_sources': order['data_source'] != match['data_source'],
                            'alignment_timestamp': datetime.utcnow()
                        }
                        aligned_data.append(aligned_record)
            
            aligned_df = pd.DataFrame(aligned_data)
            
            if not aligned_df.empty:
                # Sort by match timestamp, then by order timestamp
                aligned_df = aligned_df.sort_values(
                    ['match_timestamp', 'order_timestamp']
                ).reset_index(drop=True)
            
            self.logger.info(f"Successfully aligned {len(aligned_df)} order-match pairs")
            return aligned_df
            
        except Exception as e:
            raise ETLPipelineError(f"Failed to align datasets by timestamp: {str(e)}")
    
    def process_source_agnostic(self, aligned_df: pd.DataFrame) -> pd.DataFrame:
        """
        Process aligned data in a source-agnostic manner.
        
        Ensures consistent processing logic regardless of whether data comes
        from real or mock sources, while preserving source attribution.
        
        Args:
            aligned_df: DataFrame with aligned orders and matches
            
        Returns:
            DataFrame with source-agnostic processing applied
            
        Requirements: 5.3 - Source-agnostic processing
        """
        try:
            self.logger.info("Applying source-agnostic processing")
            
            if aligned_df.empty:
                return aligned_df
            
            processed_df = aligned_df.copy()
            
            # Add derived metrics that work regardless of data source
            processed_df['order_volume_category'] = pd.cut(
                processed_df['order_amount'],
                bins=[0, 20, 50, 100, float('inf')],
                labels=['low', 'medium', 'high', 'premium']
            )
            
            processed_df['pizza_per_dollar'] = (
                processed_df['pizza_count'] / processed_df['order_amount']
            ).round(3)
            
            # Normalize team names for consistent analysis across sources
            processed_df['match_teams_normalized'] = (
                processed_df['home_team'] + ' vs ' + processed_df['away_team']
            ).str.lower()
            
            # Create consistent event categories
            processed_df['match_outcome_category'] = processed_df.apply(
                lambda row: self._categorize_match_outcome(row), axis=1
            )
            
            # Add data quality score (higher score = more real data)
            processed_df['data_quality_score'] = processed_df.apply(
                lambda row: self._calculate_data_quality_score(row), axis=1
            )
            
            # Group by match and calculate aggregated metrics
            match_groups = processed_df.groupby('match_id').agg({
                'order_amount': ['sum', 'mean', 'count'],
                'pizza_count': ['sum', 'mean'],
                'data_quality_score': 'mean',
                'mixed_data_sources': 'any'
            }).round(2)
            
            # Flatten column names
            match_groups.columns = [
                f"{col[0]}_{col[1]}" if col[1] else col[0] 
                for col in match_groups.columns
            ]
            
            # Add aggregated metrics back to main DataFrame
            processed_df = processed_df.merge(
                match_groups,
                left_on='match_id',
                right_index=True,
                suffixes=('', '_match_agg')
            )
            
            # Calculate order density (orders per hour in time window)
            processed_df['order_density'] = (
                processed_df['order_amount_count'] / 
                processed_df['alignment_window_hours']
            ).round(2)
            
            self.logger.info(f"Applied source-agnostic processing to {len(processed_df)} records")
            return processed_df
            
        except Exception as e:
            raise ETLPipelineError(f"Failed to apply source-agnostic processing: {str(e)}")
    
    def _categorize_match_outcome(self, row: pd.Series) -> str:
        """Categorize match outcome for consistent analysis."""
        if row['winner'] == 'draw':
            return 'draw'
        elif row['is_high_scoring']:
            return f"{row['winner']}_win_high_scoring"
        else:
            return f"{row['winner']}_win_regular"
    
    def _calculate_data_quality_score(self, row: pd.Series) -> float:
        """
        Calculate data quality score based on source mix.
        
        Returns:
            Float between 0-1 (1 = all real data, 0 = all mock data)
        """
        order_real = 1.0 if row['order_data_source'] == 'real' else 0.0
        match_real = 1.0 if row['match_data_source'] == 'real' else 0.0
        return (order_real + match_real) / 2.0
    
    def load_processed_data(self, processed_df: pd.DataFrame, 
                          dataset_name: str = None) -> str:
        """
        Load processed data back to S3 for analysis.
        
        Args:
            processed_df: Processed DataFrame to upload
            dataset_name: Optional custom dataset name
            
        Returns:
            S3 key of uploaded processed dataset
            
        Requirements: 5.1 - ETL pipeline data loading
        """
        try:
            if dataset_name is None:
                timestamp = datetime.utcnow()
                dataset_name = f"merged_pizza_football_data_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            self.logger.info(f"Loading processed data: {dataset_name}")
            
            # Upload as both CSV and JSON for different use cases
            csv_key = self.s3_service.upload_csv_data(
                processed_df,
                data_type='merged-datasets',
                data_source='processed',
                filename=f"{dataset_name}.csv",
                record_count=len(processed_df),
                processing_timestamp=datetime.utcnow().isoformat()
            )
            
            # Also upload as JSON for programmatic access
            json_data = processed_df.to_dict('records')
            json_key = self.s3_service.upload_json_data(
                json_data,
                data_type='merged-datasets',
                data_source='processed',
                filename=f"{dataset_name}.json",
                record_count=len(processed_df),
                processing_timestamp=datetime.utcnow().isoformat()
            )
            
            self.logger.info(f"Successfully loaded processed data to S3: {csv_key}")
            return csv_key
            
        except Exception as e:
            raise ETLPipelineError(f"Failed to load processed data: {str(e)}")
    
    def run_full_pipeline(self, data_source: str = None,
                         date_range: Tuple[datetime, datetime] = None,
                         time_window_hours: int = 6) -> str:
        """
        Run the complete ETL pipeline from extraction to loading.
        
        Args:
            data_source: Filter by data source ('real', 'mock', or None for both)
            date_range: Optional date range for filtering
            time_window_hours: Time window for alignment (default 6 hours)
            
        Returns:
            S3 key of the final processed dataset
            
        Requirements: 5.1, 5.2, 5.3, 2.5
        """
        try:
            self.logger.info("Starting full ETL pipeline execution")
            
            # Extract data from S3
            orders = self.extract_pizza_orders(data_source, date_range)
            matches = self.extract_football_matches(data_source, date_range)
            
            if not orders:
                raise ETLPipelineError("No pizza orders found for processing")
            if not matches:
                raise ETLPipelineError("No football matches found for processing")
            
            # Transform and normalize data
            orders_df, matches_df = self.normalize_data_formats(orders, matches)
            
            # Align datasets by timestamp
            aligned_df = self.align_datasets_by_timestamp(
                orders_df, matches_df, time_window_hours
            )
            
            if aligned_df.empty:
                raise ETLPipelineError("No aligned data found - check time windows and data availability")
            
            # Apply source-agnostic processing
            processed_df = self.process_source_agnostic(aligned_df)
            
            # Load processed data back to S3
            s3_key = self.load_processed_data(processed_df)
            
            self.logger.info(f"ETL pipeline completed successfully. Output: {s3_key}")
            return s3_key
            
        except Exception as e:
            raise ETLPipelineError(f"ETL pipeline failed: {str(e)}")
    
    def run_correlation_analysis(self, data_source: str = None,
                               date_range: Tuple[datetime, datetime] = None) -> str:
        """
        Run correlation analysis on pizza orders and football matches.
        
        Args:
            data_source: Filter by data source ('real', 'mock', or None for both)
            date_range: Optional date range for filtering
            
        Returns:
            S3 key of the correlation analysis results
            
        Requirements: 5.4, 7.1, 7.2, 2.4
        """
        try:
            self.logger.info("Starting correlation analysis")
            
            # Extract data from S3
            orders = self.extract_pizza_orders(data_source, date_range)
            matches = self.extract_football_matches(data_source, date_range)
            
            if not orders:
                raise ETLPipelineError("No pizza orders found for correlation analysis")
            if not matches:
                raise ETLPipelineError("No football matches found for correlation analysis")
            
            # Calculate match period metrics
            metrics_df = self.correlation_analyzer.calculate_match_period_metrics(orders, matches)
            
            if metrics_df.empty:
                raise ETLPipelineError("No aligned data found for correlation analysis")
            
            # Calculate correlation coefficients
            correlation_results = self.correlation_analyzer.calculate_correlation_coefficients(metrics_df)
            
            # Detect statistically significant patterns
            significant_results = self.correlation_analyzer.detect_statistical_significance(correlation_results)
            
            # Classify football events
            classified_matches_df = self.correlation_analyzer.classify_football_events(matches)
            
            # Generate correlation summary
            correlation_summary = self.correlation_analyzer.generate_correlation_summary(correlation_results)
            
            # Upload correlation results to S3
            timestamp = datetime.utcnow()
            
            # Upload detailed correlation results
            correlation_csv = results_to_csv(correlation_results)
            correlation_key = self.s3_service.upload_csv_data(
                pd.read_csv(StringIO(correlation_csv)),
                data_type='correlation-analysis',
                data_source='processed',
                filename=f"correlation_results_{timestamp.strftime('%Y%m%d_%H%M%S')}.csv",
                record_count=len(correlation_results),
                processing_timestamp=timestamp.isoformat()
            )
            
            # Upload significant results
            if significant_results:
                significant_csv = results_to_csv(significant_results)
                self.s3_service.upload_csv_data(
                    pd.read_csv(StringIO(significant_csv)),
                    data_type='correlation-analysis',
                    data_source='processed',
                    filename=f"significant_correlations_{timestamp.strftime('%Y%m%d_%H%M%S')}.csv",
                    record_count=len(significant_results),
                    processing_timestamp=timestamp.isoformat()
                )
            
            # Upload match metrics
            metrics_key = self.s3_service.upload_csv_data(
                metrics_df,
                data_type='correlation-analysis',
                data_source='processed',
                filename=f"match_metrics_{timestamp.strftime('%Y%m%d_%H%M%S')}.csv",
                record_count=len(metrics_df),
                processing_timestamp=timestamp.isoformat()
            )
            
            # Upload classified matches
            classified_key = self.s3_service.upload_csv_data(
                classified_matches_df,
                data_type='correlation-analysis',
                data_source='processed',
                filename=f"classified_matches_{timestamp.strftime('%Y%m%d_%H%M%S')}.csv",
                record_count=len(classified_matches_df),
                processing_timestamp=timestamp.isoformat()
            )
            
            # Upload correlation summary as JSON
            summary_key = self.s3_service.upload_json_data(
                correlation_summary,
                data_type='correlation-analysis',
                data_source='processed',
                filename=f"correlation_summary_{timestamp.strftime('%Y%m%d_%H%M%S')}.json",
                record_count=len(correlation_results),
                processing_timestamp=timestamp.isoformat()
            )
            
            self.logger.info(f"Correlation analysis completed successfully. Results: {correlation_key}")
            return correlation_key
            
        except Exception as e:
            raise ETLPipelineError(f"Correlation analysis failed: {str(e)}")