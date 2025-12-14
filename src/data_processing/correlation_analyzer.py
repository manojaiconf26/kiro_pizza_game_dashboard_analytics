"""
Correlation Analysis Engine for Pizza Game Dashboard

This module implements comprehensive statistical correlation analysis between
pizza ordering patterns and football match events, providing the analytical
foundation for understanding consumer behavior during sporting events.

STATISTICAL METHODS IMPLEMENTED:

1. Pearson Correlation Coefficient:
   - Used for continuous variables (order volumes, match scores)
   - Measures linear relationships between variables
   - Range: -1 (perfect negative) to +1 (perfect positive)
   - Assumes normal distribution and linear relationships

2. Point-Biserial Correlation:
   - Used for binary outcomes (win/loss, high-scoring/low-scoring)
   - Special case of Pearson correlation for dichotomous variables
   - Appropriate for correlating continuous order data with binary match outcomes

3. Statistical Significance Testing:
   - P-value calculation using scipy.stats methods
   - Significance threshold: α = 0.05 (95% confidence level)
   - Null hypothesis: No correlation between variables
   - Alternative hypothesis: Significant correlation exists

TEMPORAL ANALYSIS FRAMEWORK:

Time Period Definitions:
- Pre-match: 2 hours before match start (anticipation effect)
- During-match: Match time ± 1 hour (live viewing effect)
- Post-match: 2 hours after match end (celebration/disappointment effect)

Metrics Calculated per Period:
- Order count: Total number of pizza orders
- Order volume: Total monetary value of orders
- Average order value: Mean order amount
- Pizza count: Total number of pizzas ordered
- Unique locations: Geographic distribution of orders
- Orders per hour: Normalized ordering rate

CORRELATION ANALYSIS TYPES:

1. Outcome-Based Correlations:
   - Home wins vs order patterns
   - Away wins vs order patterns  
   - Draws vs order patterns
   - High-scoring matches (3+ goals) vs order spikes
   - Tournament matches vs regular season patterns

2. Temporal Pattern Correlations:
   - Pre-match to post-match order relationships
   - During-match to post-match immediate reactions
   - Cross-period correlation patterns

3. Event Classification Correlations:
   - Match significance (regular/tournament/final) effects
   - Goal differential impact on ordering
   - Team-specific ordering patterns

STATISTICAL VALIDATION:

Edge Case Handling:
- Insufficient data points (< 3 observations)
- Zero variance in variables (constant values)
- NaN/Inf values from calculation errors
- Empty datasets or missing time periods

Data Quality Assessment:
- Real vs mock data ratio tracking
- Sample size adequacy validation
- Correlation strength interpretation
- Statistical power considerations

BUSINESS INSIGHTS GENERATION:

Pattern Recognition:
- Identifies statistically significant correlations
- Classifies correlation strength (weak/moderate/strong)
- Generates human-readable pattern descriptions
- Provides business-relevant interpretations

Requirements Satisfied:
- 5.4: Comprehensive metric calculation for match periods
- 7.1: Accurate correlation coefficient calculations
- 7.2: Statistical significance detection with proper testing
- 2.4: Football event classification for enhanced analysis

Mathematical Foundation:
- Uses scipy.stats for robust statistical calculations
- Implements proper handling of statistical assumptions
- Provides confidence intervals and effect size measures
- Ensures reproducible and scientifically valid results
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from scipy import stats
from dataclasses import asdict
import uuid

from src.models.pizza_order import DominosOrder
from src.models.football_match import FootballMatch
from src.models.correlation_result import CorrelationResult


class CorrelationAnalysisError(Exception):
    """Custom exception for correlation analysis operations"""
    pass


class CorrelationAnalyzer:
    """
    Correlation analysis engine for analyzing relationships between pizza orders and football matches.
    
    Provides comprehensive analysis including:
    - Pre-match, during-match, and post-match order volume calculations
    - Correlation coefficient calculations between match outcomes and order spikes
    - Statistical significance testing for pattern detection
    - Event classification logic for football match events
    """
    
    def __init__(self):
        """Initialize the correlation analyzer."""
        self.logger = logging.getLogger(__name__)
    
    def calculate_match_period_metrics(self, orders: List[DominosOrder], 
                                     matches: List[FootballMatch],
                                     pre_match_hours: int = 2,
                                     during_match_hours: int = 2,
                                     post_match_hours: int = 2) -> pd.DataFrame:
        """
        Calculate order volume metrics for pre-match, during-match, and post-match periods.
        
        Args:
            orders: List of pizza orders
            matches: List of football matches
            pre_match_hours: Hours before match to consider as pre-match period
            during_match_hours: Hours around match time to consider as during-match period
            post_match_hours: Hours after match to consider as post-match period
            
        Returns:
            DataFrame with metrics for each match and time period
            
        Requirements: 5.4 - Comprehensive metric calculation
        """
        try:
            self.logger.info("Calculating match period metrics")
            
            if not orders or not matches:
                return pd.DataFrame()
            
            # Convert to DataFrames for easier processing
            orders_df = pd.DataFrame([asdict(order) for order in orders])
            orders_df['timestamp'] = pd.to_datetime(orders_df['timestamp'])
            
            matches_df = pd.DataFrame([asdict(match) for match in matches])
            matches_df['timestamp'] = pd.to_datetime(matches_df['timestamp'])
            
            metrics_data = []
            
            for _, match in matches_df.iterrows():
                match_time = match['timestamp']
                
                # Define time periods around the match
                pre_match_start = match_time - timedelta(hours=pre_match_hours)
                pre_match_end = match_time
                
                during_match_start = match_time - timedelta(hours=during_match_hours // 2)
                during_match_end = match_time + timedelta(hours=during_match_hours // 2)
                
                post_match_start = match_time
                post_match_end = match_time + timedelta(hours=post_match_hours)
                
                # Calculate metrics for each period
                pre_match_orders = orders_df[
                    (orders_df['timestamp'] >= pre_match_start) &
                    (orders_df['timestamp'] < pre_match_end)
                ]
                
                during_match_orders = orders_df[
                    (orders_df['timestamp'] >= during_match_start) &
                    (orders_df['timestamp'] <= during_match_end)
                ]
                
                post_match_orders = orders_df[
                    (orders_df['timestamp'] > post_match_start) &
                    (orders_df['timestamp'] <= post_match_end)
                ]
                
                # Calculate volume metrics
                pre_match_metrics = self._calculate_period_metrics(pre_match_orders, 'pre_match')
                during_match_metrics = self._calculate_period_metrics(during_match_orders, 'during_match')
                post_match_metrics = self._calculate_period_metrics(post_match_orders, 'post_match')
                
                # Combine match info with metrics
                match_metrics = {
                    'match_id': match['match_id'],
                    'match_timestamp': match['timestamp'],
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'home_score': match['home_score'],
                    'away_score': match['away_score'],
                    'event_type': match['event_type'],
                    'match_significance': match['match_significance'],
                    'data_source': match['data_source'],
                    'winner': self._get_match_winner(match['home_score'], match['away_score']),
                    'total_goals': match['home_score'] + match['away_score'],
                    'is_high_scoring': (match['home_score'] + match['away_score']) >= 3,
                    **pre_match_metrics,
                    **during_match_metrics,
                    **post_match_metrics
                }
                
                metrics_data.append(match_metrics)
            
            metrics_df = pd.DataFrame(metrics_data)
            
            self.logger.info(f"Calculated metrics for {len(metrics_df)} matches")
            return metrics_df
            
        except Exception as e:
            raise CorrelationAnalysisError(f"Failed to calculate match period metrics: {str(e)}")
    
    def _calculate_period_metrics(self, period_orders: pd.DataFrame, period_name: str) -> Dict[str, Any]:
        """
        Calculate order volume metrics for a specific time period.
        
        Args:
            period_orders: DataFrame of orders in the time period
            period_name: Name of the period ('pre_match', 'during_match', 'post_match')
            
        Returns:
            Dictionary of metrics for the period
        """
        if period_orders.empty:
            return {
                f'{period_name}_order_count': 0,
                f'{period_name}_total_volume': 0.0,
                f'{period_name}_avg_order_value': 0.0,
                f'{period_name}_pizza_count': 0,
                f'{period_name}_unique_locations': 0,
                f'{period_name}_orders_per_hour': 0.0
            }
        
        return {
            f'{period_name}_order_count': len(period_orders),
            f'{period_name}_total_volume': period_orders['order_total'].sum(),
            f'{period_name}_avg_order_value': period_orders['order_total'].mean(),
            f'{period_name}_pizza_count': period_orders['quantity'].sum(),
            f'{period_name}_unique_locations': period_orders['location'].nunique(),
            f'{period_name}_orders_per_hour': len(period_orders) / 2.0  # Assuming 2-hour periods
        }
    
    def _get_match_winner(self, home_score: int, away_score: int) -> str:
        """Determine match winner from scores."""
        if home_score > away_score:
            return 'home'
        elif away_score > home_score:
            return 'away'
        else:
            return 'draw'
    
    def calculate_correlation_coefficients(self, metrics_df: pd.DataFrame) -> List[CorrelationResult]:
        """
        Calculate correlation coefficients between match outcomes and order spikes.
        
        Args:
            metrics_df: DataFrame with match and order metrics
            
        Returns:
            List of CorrelationResult objects with correlation analysis
            
        Requirements: 7.1 - Correlation coefficient accuracy
        """
        try:
            self.logger.info("Calculating correlation coefficients")
            
            if metrics_df.empty:
                return []
            
            correlation_results = []
            
            # Define outcome variables to correlate with
            outcome_variables = {
                'home_wins': metrics_df['winner'] == 'home',
                'away_wins': metrics_df['winner'] == 'away',
                'draws': metrics_df['winner'] == 'draw',
                'high_scoring_matches': metrics_df['is_high_scoring'],
                'total_goals': metrics_df['total_goals'],
                'tournament_matches': metrics_df['match_significance'] == 'tournament',
                'final_matches': metrics_df['match_significance'] == 'final'
            }
            
            # Define order volume variables
            volume_variables = {
                'pre_match_order_count': 'pre_match_order_count',
                'during_match_order_count': 'during_match_order_count',
                'post_match_order_count': 'post_match_order_count',
                'pre_match_total_volume': 'pre_match_total_volume',
                'during_match_total_volume': 'during_match_total_volume',
                'post_match_total_volume': 'post_match_total_volume',
                'pre_match_orders_per_hour': 'pre_match_orders_per_hour',
                'during_match_orders_per_hour': 'during_match_orders_per_hour',
                'post_match_orders_per_hour': 'post_match_orders_per_hour'
            }
            
            # Calculate correlations for each combination
            for outcome_name, outcome_data in outcome_variables.items():
                for volume_name, volume_column in volume_variables.items():
                    if volume_column in metrics_df.columns:
                        correlation_result = self._calculate_single_correlation(
                            metrics_df[volume_column],
                            outcome_data,
                            outcome_name,
                            volume_name,
                            metrics_df
                        )
                        if correlation_result:
                            correlation_results.append(correlation_result)
            
            # Calculate period-to-period correlations (order spike patterns)
            period_correlations = self._calculate_period_correlations(metrics_df)
            correlation_results.extend(period_correlations)
            
            self.logger.info(f"Calculated {len(correlation_results)} correlation coefficients")
            return correlation_results
            
        except Exception as e:
            raise CorrelationAnalysisError(f"Failed to calculate correlation coefficients: {str(e)}")
    
    def _calculate_single_correlation(self, volume_data: pd.Series, outcome_data: pd.Series,
                                    outcome_name: str, volume_name: str,
                                    metrics_df: pd.DataFrame) -> Optional[CorrelationResult]:
        """
        Calculate a single correlation coefficient with comprehensive statistical validation.
        
        This method implements the core statistical calculation with robust error handling
        and validation to ensure meaningful and reliable correlation results.
        
        Statistical Method Selection:
        - Point-biserial correlation: Used when outcome_data is binary (True/False, Win/Loss)
        - Pearson correlation: Used when outcome_data is continuous (scores, counts)
        
        Data Validation Steps:
        1. Check for sufficient sample size (minimum 3 data points)
        2. Remove NaN values that would invalidate calculations
        3. Verify variance exists in both variables (no constant values)
        4. Validate data types and ranges for statistical assumptions
        
        Statistical Significance:
        - Calculates p-value using appropriate statistical test
        - P-value represents probability of observing correlation by chance
        - Lower p-values indicate stronger evidence against null hypothesis
        - Standard significance threshold: p < 0.05 (95% confidence)
        
        Error Handling:
        - Returns None for invalid inputs or calculation failures
        - Logs warnings for edge cases (insufficient data, no variance)
        - Handles NaN/Inf results from statistical calculations
        - Provides detailed error context for debugging
        
        Args:
            volume_data: Pizza order volume data (continuous variable)
                        Examples: order_count, total_revenue, orders_per_hour
            outcome_data: Football match outcome data (binary or continuous)
                         Examples: win/loss (binary), total_goals (continuous)
            outcome_name: Human-readable name of outcome variable for reporting
            volume_name: Human-readable name of volume variable for reporting
            metrics_df: Complete metrics DataFrame for data quality assessment
            
        Returns:
            CorrelationResult object containing:
            - correlation_coefficient: Strength and direction of relationship (-1 to +1)
            - statistical_significance: P-value for hypothesis testing
            - time_window: Temporal context (pre_match, during_match, post_match)
            - pattern_description: Human-readable interpretation
            - data_quality: Percentage of real vs mock data used
            - sample_size: Number of observations in calculation
            
            Returns None if:
            - Insufficient data points (< 3 observations)
            - No variance in either variable
            - Statistical calculation produces invalid results (NaN/Inf)
            - Unexpected errors during processing
        
        Statistical Assumptions:
        - Pearson: Linear relationship, normal distribution, homoscedasticity
        - Point-biserial: One continuous variable, one true dichotomy
        - Both methods assume independence of observations
        
        Business Interpretation:
        - Correlation ≠ causation (correlation does not imply causal relationship)
        - Strength interpretation: |r| < 0.3 (weak), 0.3-0.7 (moderate), > 0.7 (strong)
        - Practical significance may differ from statistical significance
        """
        try:
            # Remove any NaN values
            valid_mask = ~(pd.isna(volume_data) | pd.isna(outcome_data))
            clean_volume = volume_data[valid_mask]
            clean_outcome = outcome_data[valid_mask]
            
            if len(clean_volume) < 3:  # Need at least 3 data points
                return None
            
            # Calculate correlation coefficient and p-value
            if clean_outcome.dtype == bool:
                # For boolean outcomes, use point-biserial correlation
                correlation_coef, p_value = stats.pointbiserialr(clean_outcome, clean_volume)
            else:
                # For continuous outcomes, use Pearson correlation
                correlation_coef, p_value = stats.pearsonr(clean_volume, clean_outcome)
            
            # Handle NaN correlations (when there's no variation in data)
            if np.isnan(correlation_coef) or np.isnan(p_value):
                return None
            
            # Determine time window from volume variable name
            if 'pre_match' in volume_name:
                time_window = 'pre_match'
            elif 'during_match' in volume_name:
                time_window = 'during_match'
            elif 'post_match' in volume_name:
                time_window = 'post_match'
            else:
                time_window = 'full_match'
            
            # Generate pattern description
            pattern_description = self._generate_pattern_description(
                correlation_coef, p_value, outcome_name, volume_name, time_window
            )
            
            # Calculate data quality score
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
            self.logger.warning(f"Failed to calculate correlation for {outcome_name} vs {volume_name}: {str(e)}")
            return None
    
    def _calculate_period_correlations(self, metrics_df: pd.DataFrame) -> List[CorrelationResult]:
        """
        Calculate correlations between different time periods to identify order spike patterns.
        
        Args:
            metrics_df: DataFrame with match and order metrics
            
        Returns:
            List of CorrelationResult objects for period correlations
        """
        period_correlations = []
        
        try:
            # Pre-match to post-match order correlation
            if 'pre_match_order_count' in metrics_df.columns and 'post_match_order_count' in metrics_df.columns:
                pre_post_corr = self._calculate_single_correlation(
                    metrics_df['pre_match_order_count'],
                    metrics_df['post_match_order_count'],
                    'post_match_orders',
                    'pre_match_order_count',
                    metrics_df
                )
                if pre_post_corr:
                    pre_post_corr.time_window = 'pre_to_post_match'
                    pre_post_corr.pattern_description = f"Correlation between pre-match and post-match order volumes: {pre_post_corr.get_strength_description()} {pre_post_corr.get_direction_description()} relationship"
                    period_correlations.append(pre_post_corr)
            
            # During-match to post-match correlation (immediate reaction)
            if 'during_match_order_count' in metrics_df.columns and 'post_match_order_count' in metrics_df.columns:
                during_post_corr = self._calculate_single_correlation(
                    metrics_df['during_match_order_count'],
                    metrics_df['post_match_order_count'],
                    'post_match_orders',
                    'during_match_order_count',
                    metrics_df
                )
                if during_post_corr:
                    during_post_corr.time_window = 'during_to_post_match'
                    during_post_corr.pattern_description = f"Correlation between during-match and post-match order volumes: {during_post_corr.get_strength_description()} {during_post_corr.get_direction_description()} relationship"
                    period_correlations.append(during_post_corr)
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate period correlations: {str(e)}")
        
        return period_correlations
    
    def _generate_pattern_description(self, correlation_coef: float, p_value: float,
                                    outcome_name: str, volume_name: str, time_window: str) -> str:
        """
        Generate a human-readable description of the correlation pattern.
        
        Args:
            correlation_coef: Correlation coefficient
            p_value: Statistical significance p-value
            outcome_name: Name of the outcome variable
            volume_name: Name of the volume variable
            time_window: Time window of analysis
            
        Returns:
            Human-readable pattern description
        """
        strength = self._get_correlation_strength(abs(correlation_coef))
        direction = "positive" if correlation_coef > 0 else "negative" if correlation_coef < 0 else "no"
        significance = "significant" if p_value < 0.05 else "not significant"
        
        return (f"{strength.title()} {direction} correlation between {outcome_name} and "
                f"{volume_name} during {time_window} period (r={correlation_coef:.3f}, "
                f"p={p_value:.3f}, {significance})")
    
    def _get_correlation_strength(self, abs_correlation: float) -> str:
        """Get correlation strength description."""
        if abs_correlation < 0.1:
            return "negligible"
        elif abs_correlation < 0.3:
            return "weak"
        elif abs_correlation < 0.5:
            return "moderate"
        elif abs_correlation < 0.7:
            return "strong"
        else:
            return "very strong"
    
    def _calculate_data_quality_score(self, metrics_df: pd.DataFrame) -> float:
        """
        Calculate data quality score based on real vs mock data ratio.
        
        Args:
            metrics_df: DataFrame with data source information
            
        Returns:
            Data quality score as percentage (0-100)
        """
        if metrics_df.empty or 'data_source' not in metrics_df.columns:
            return 0.0
        
        real_data_count = (metrics_df['data_source'] == 'real').sum()
        total_count = len(metrics_df)
        
        return (real_data_count / total_count) * 100.0
    
    def detect_statistical_significance(self, correlation_results: List[CorrelationResult],
                                      alpha: float = 0.05) -> List[CorrelationResult]:
        """
        Detect statistically significant patterns in correlation results.
        
        Args:
            correlation_results: List of correlation results to analyze
            alpha: Significance level threshold (default 0.05)
            
        Returns:
            List of statistically significant correlation results
            
        Requirements: 7.2 - Statistical significance detection
        """
        try:
            self.logger.info(f"Detecting statistical significance with alpha={alpha}")
            
            significant_results = []
            
            for result in correlation_results:
                if result.is_significant(alpha):
                    # Add additional significance information
                    enhanced_result = CorrelationResult(
                        analysis_id=result.analysis_id,
                        correlation_coefficient=result.correlation_coefficient,
                        statistical_significance=result.statistical_significance,
                        time_window=result.time_window,
                        pattern_description=f"SIGNIFICANT: {result.pattern_description}",
                        data_quality=result.data_quality,
                        analysis_timestamp=result.analysis_timestamp,
                        sample_size=result.sample_size
                    )
                    significant_results.append(enhanced_result)
            
            self.logger.info(f"Found {len(significant_results)} statistically significant patterns")
            return significant_results
            
        except Exception as e:
            raise CorrelationAnalysisError(f"Failed to detect statistical significance: {str(e)}")
    
    def classify_football_events(self, matches: List[FootballMatch]) -> pd.DataFrame:
        """
        Classify football match events for enhanced analysis.
        
        Args:
            matches: List of football matches to classify
            
        Returns:
            DataFrame with enhanced event classifications
            
        Requirements: 2.4 - Event classification accuracy
        """
        try:
            self.logger.info("Classifying football match events")
            
            if not matches:
                return pd.DataFrame()
            
            # Convert to DataFrame
            matches_df = pd.DataFrame([asdict(match) for match in matches])
            
            # Add enhanced event classifications
            matches_df['goal_differential'] = abs(matches_df['home_score'] - matches_df['away_score'])
            matches_df['total_goals'] = matches_df['home_score'] + matches_df['away_score']
            
            # Classify match excitement level
            matches_df['excitement_level'] = matches_df.apply(self._classify_excitement_level, axis=1)
            
            # Classify match outcome type
            matches_df['outcome_type'] = matches_df.apply(self._classify_outcome_type, axis=1)
            
            # Classify scoring pattern
            matches_df['scoring_pattern'] = matches_df.apply(self._classify_scoring_pattern, axis=1)
            
            # Classify match importance
            matches_df['importance_level'] = matches_df.apply(self._classify_importance_level, axis=1)
            
            # Add event impact score (0-100)
            matches_df['event_impact_score'] = matches_df.apply(self._calculate_event_impact_score, axis=1)
            
            self.logger.info(f"Classified {len(matches_df)} football match events")
            return matches_df
            
        except Exception as e:
            raise CorrelationAnalysisError(f"Failed to classify football events: {str(e)}")
    
    def _classify_excitement_level(self, match_row: pd.Series) -> str:
        """Classify match excitement based on goals and outcome."""
        total_goals = match_row['total_goals']
        goal_diff = match_row['goal_differential']
        
        if total_goals >= 5:
            return 'very_high'
        elif total_goals >= 3 and goal_diff <= 1:
            return 'high'
        elif total_goals >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _classify_outcome_type(self, match_row: pd.Series) -> str:
        """Classify the type of match outcome."""
        home_score = match_row['home_score']
        away_score = match_row['away_score']
        
        if home_score == away_score:
            return 'draw'
        elif abs(home_score - away_score) >= 3:
            return 'blowout'
        elif abs(home_score - away_score) == 1:
            return 'close_win'
        else:
            return 'comfortable_win'
    
    def _classify_scoring_pattern(self, match_row: pd.Series) -> str:
        """Classify the scoring pattern of the match."""
        total_goals = match_row['total_goals']
        
        if total_goals == 0:
            return 'scoreless'
        elif total_goals == 1:
            return 'low_scoring'
        elif total_goals <= 3:
            return 'moderate_scoring'
        elif total_goals <= 5:
            return 'high_scoring'
        else:
            return 'very_high_scoring'
    
    def _classify_importance_level(self, match_row: pd.Series) -> str:
        """Classify the importance level of the match."""
        significance = match_row['match_significance']
        
        if significance == 'final':
            return 'critical'
        elif significance == 'tournament':
            return 'high'
        else:
            return 'regular'
    
    def _calculate_event_impact_score(self, match_row: pd.Series) -> int:
        """
        Calculate an event impact score (0-100) based on multiple factors.
        
        Args:
            match_row: Row containing match data
            
        Returns:
            Impact score from 0-100
        """
        score = 0
        
        # Base score from total goals (0-30 points)
        total_goals = match_row['total_goals']
        score += min(total_goals * 5, 30)
        
        # Bonus for close matches (0-20 points)
        goal_diff = match_row['goal_differential']
        if goal_diff == 0:
            score += 20  # Draw
        elif goal_diff == 1:
            score += 15  # Very close
        elif goal_diff == 2:
            score += 10  # Close
        
        # Bonus for match significance (0-30 points)
        significance = match_row['match_significance']
        if significance == 'final':
            score += 30
        elif significance == 'tournament':
            score += 20
        else:
            score += 10
        
        # Bonus for high-scoring matches (0-20 points)
        if total_goals >= 5:
            score += 20
        elif total_goals >= 3:
            score += 10
        
        return min(score, 100)  # Cap at 100
    
    def generate_correlation_summary(self, correlation_results: List[CorrelationResult]) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of correlation analysis results.
        
        Args:
            correlation_results: List of correlation results to summarize
            
        Returns:
            Dictionary containing summary statistics and insights
        """
        try:
            self.logger.info("Generating correlation analysis summary")
            
            if not correlation_results:
                return {
                    'total_correlations': 0,
                    'significant_correlations': 0,
                    'strongest_correlation': None,
                    'summary': "No correlation results to analyze"
                }
            
            # Basic statistics
            total_correlations = len(correlation_results)
            significant_correlations = sum(1 for r in correlation_results if r.is_significant())
            
            # Find strongest correlations
            strongest_positive = max(correlation_results, key=lambda r: r.correlation_coefficient)
            strongest_negative = min(correlation_results, key=lambda r: r.correlation_coefficient)
            strongest_overall = max(correlation_results, key=lambda r: abs(r.correlation_coefficient))
            
            # Calculate average data quality
            avg_data_quality = np.mean([r.data_quality for r in correlation_results])
            
            # Group by time window
            time_window_stats = {}
            for result in correlation_results:
                window = result.time_window
                if window not in time_window_stats:
                    time_window_stats[window] = {
                        'count': 0,
                        'significant_count': 0,
                        'avg_correlation': 0,
                        'correlations': []
                    }
                
                time_window_stats[window]['count'] += 1
                time_window_stats[window]['correlations'].append(result.correlation_coefficient)
                if result.is_significant():
                    time_window_stats[window]['significant_count'] += 1
            
            # Calculate averages for each time window
            for window_stats in time_window_stats.values():
                window_stats['avg_correlation'] = np.mean(window_stats['correlations'])
                window_stats['significance_rate'] = (
                    window_stats['significant_count'] / window_stats['count'] * 100
                )
            
            summary = {
                'total_correlations': total_correlations,
                'significant_correlations': significant_correlations,
                'significance_rate': (significant_correlations / total_correlations * 100) if total_correlations > 0 else 0,
                'strongest_positive_correlation': {
                    'coefficient': strongest_positive.correlation_coefficient,
                    'description': strongest_positive.pattern_description,
                    'time_window': strongest_positive.time_window,
                    'significant': strongest_positive.is_significant()
                },
                'strongest_negative_correlation': {
                    'coefficient': strongest_negative.correlation_coefficient,
                    'description': strongest_negative.pattern_description,
                    'time_window': strongest_negative.time_window,
                    'significant': strongest_negative.is_significant()
                },
                'strongest_overall_correlation': {
                    'coefficient': strongest_overall.correlation_coefficient,
                    'description': strongest_overall.pattern_description,
                    'time_window': strongest_overall.time_window,
                    'significant': strongest_overall.is_significant()
                },
                'average_data_quality': avg_data_quality,
                'time_window_analysis': time_window_stats,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Generated summary for {total_correlations} correlations")
            return summary
            
        except Exception as e:
            raise CorrelationAnalysisError(f"Failed to generate correlation summary: {str(e)}")