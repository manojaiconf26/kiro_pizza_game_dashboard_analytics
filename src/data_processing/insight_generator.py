"""
Insight Generation System for Pizza Game Dashboard

This module implements comprehensive insight generation including temporal pattern analysis,
summary statistics generation, anomaly detection with source distinction capabilities,
and comprehensive analysis reports with data quality indicators.

Requirements: 7.3, 7.4, 7.5
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from scipy import stats
from dataclasses import dataclass, asdict
import uuid

from src.models.pizza_order import DominosOrder
from src.models.football_match import FootballMatch
from src.models.correlation_result import CorrelationResult


class InsightGenerationError(Exception):
    """Custom exception for insight generation operations"""
    pass


@dataclass
class TemporalPattern:
    """Data model for temporal pattern analysis results."""
    pattern_id: str
    time_period: str  # 'pre_match', 'during_match', 'post_match'
    pattern_type: str  # 'spike', 'dip', 'stable', 'trend'
    magnitude: float  # Strength of the pattern (0-100)
    confidence: float  # Statistical confidence (0-1)
    description: str
    data_source_breakdown: Dict[str, float]  # Percentage by source
    sample_size: int


@dataclass
class AnomalyDetection:
    """Data model for anomaly detection results."""
    anomaly_id: str
    timestamp: datetime
    anomaly_type: str  # 'order_spike', 'order_dip', 'unusual_pattern'
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    data_source: str  # 'real', 'mock', 'mixed'
    confidence_score: float  # 0-1
    context: Dict[str, Any]  # Additional context information


@dataclass
class InsightReport:
    """Comprehensive analysis report with data quality indicators."""
    report_id: str
    generation_timestamp: datetime
    analysis_period: Tuple[datetime, datetime]
    data_quality_score: float  # Overall quality (0-100)
    total_matches: int
    total_orders: int
    real_data_percentage: float
    temporal_patterns: List[TemporalPattern]
    anomalies: List[AnomalyDetection]
    summary_statistics: Dict[str, Any]
    key_insights: List[str]
    recommendations: List[str]


class InsightGenerator:
    """
    Comprehensive insight generation system for pizza orders and football match analysis.
    
    Provides:
    - Temporal pattern analysis across match periods
    - Summary statistics generation for all available data
    - Anomaly detection with source distinction capabilities
    - Comprehensive analysis reports with data quality indicators
    """
    
    def __init__(self):
        """Initialize the insight generator."""
        self.logger = logging.getLogger(__name__)
    
    def analyze_temporal_patterns(self, orders: List[DominosOrder], 
                                matches: List[FootballMatch],
                                metrics_df: pd.DataFrame) -> List[TemporalPattern]:
        """
        Implement temporal pattern analysis across match periods.
        
        Args:
            orders: List of pizza orders
            matches: List of football matches
            metrics_df: DataFrame with calculated match period metrics
            
        Returns:
            List of TemporalPattern objects describing patterns found
            
        Requirements: 7.3 - Temporal pattern analysis
        """
        try:
            self.logger.info("Analyzing temporal patterns across match periods")
            
            if metrics_df.empty:
                return []
            
            patterns = []
            
            # Analyze patterns for each time period
            time_periods = ['pre_match', 'during_match', 'post_match']
            
            for period in time_periods:
                order_count_col = f'{period}_order_count'
                volume_col = f'{period}_total_volume'
                
                if order_count_col in metrics_df.columns and volume_col in metrics_df.columns:
                    # Analyze order count patterns
                    count_patterns = self._analyze_period_patterns(
                        metrics_df[order_count_col], 
                        period, 
                        'order_count',
                        metrics_df
                    )
                    patterns.extend(count_patterns)
                    
                    # Analyze volume patterns
                    volume_patterns = self._analyze_period_patterns(
                        metrics_df[volume_col], 
                        period, 
                        'order_volume',
                        metrics_df
                    )
                    patterns.extend(volume_patterns)
            
            # Analyze cross-period patterns (e.g., pre-match to post-match trends)
            cross_period_patterns = self._analyze_cross_period_patterns(metrics_df)
            patterns.extend(cross_period_patterns)
            
            # Analyze match outcome impact patterns
            outcome_patterns = self._analyze_outcome_impact_patterns(metrics_df)
            patterns.extend(outcome_patterns)
            
            self.logger.info(f"Identified {len(patterns)} temporal patterns")
            return patterns
            
        except Exception as e:
            self.logger.error(f"Failed to analyze temporal patterns: {str(e)}")
            return []
    
    def _analyze_period_patterns(self, data_series: pd.Series, period: str, 
                               metric_type: str, metrics_df: pd.DataFrame) -> List[TemporalPattern]:
        """
        Analyze patterns within a specific time period.
        
        Args:
            data_series: Data to analyze
            period: Time period name
            metric_type: Type of metric being analyzed
            metrics_df: Full metrics DataFrame for context
            
        Returns:
            List of TemporalPattern objects
        """
        patterns = []
        
        try:
            if len(data_series) < 3:
                return patterns
            
            # Calculate statistical measures
            mean_value = data_series.mean()
            std_value = data_series.std()
            median_value = data_series.median()
            
            # Identify spikes (values > mean + 2*std)
            spike_threshold = mean_value + 2 * std_value
            spikes = data_series > spike_threshold
            
            if spikes.any():
                spike_magnitude = ((data_series[spikes].mean() - mean_value) / mean_value * 100) if mean_value > 0 else 0
                data_source_breakdown = self._calculate_source_breakdown(metrics_df[spikes], 'data_source')
                
                pattern = TemporalPattern(
                    pattern_id=str(uuid.uuid4()),
                    time_period=period,
                    pattern_type='spike',
                    magnitude=min(spike_magnitude, 100),
                    confidence=self._calculate_pattern_confidence(spikes.sum(), len(data_series)),
                    description=f"Significant {metric_type} spikes detected in {period} period ({spikes.sum()} instances)",
                    data_source_breakdown=data_source_breakdown,
                    sample_size=len(data_series)
                )
                patterns.append(pattern)
            
            # Identify dips (values < mean - 2*std)
            dip_threshold = max(0, mean_value - 2 * std_value)
            dips = data_series < dip_threshold
            
            if dips.any():
                dip_magnitude = ((mean_value - data_series[dips].mean()) / mean_value * 100) if mean_value > 0 else 0
                data_source_breakdown = self._calculate_source_breakdown(metrics_df[dips], 'data_source')
                
                pattern = TemporalPattern(
                    pattern_id=str(uuid.uuid4()),
                    time_period=period,
                    pattern_type='dip',
                    magnitude=min(dip_magnitude, 100),
                    confidence=self._calculate_pattern_confidence(dips.sum(), len(data_series)),
                    description=f"Significant {metric_type} dips detected in {period} period ({dips.sum()} instances)",
                    data_source_breakdown=data_source_breakdown,
                    sample_size=len(data_series)
                )
                patterns.append(pattern)
            
            # Check for trends using linear regression
            if len(data_series) >= 5:
                x_values = np.arange(len(data_series))
                slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, data_series)
                
                if abs(r_value) > 0.3 and p_value < 0.05:  # Significant trend
                    trend_type = 'increasing' if slope > 0 else 'decreasing'
                    trend_magnitude = abs(r_value) * 100
                    
                    pattern = TemporalPattern(
                        pattern_id=str(uuid.uuid4()),
                        time_period=period,
                        pattern_type='trend',
                        magnitude=trend_magnitude,
                        confidence=1 - p_value,
                        description=f"{trend_type.title()} trend in {metric_type} during {period} period (r={r_value:.3f})",
                        data_source_breakdown=self._calculate_source_breakdown(metrics_df, 'data_source'),
                        sample_size=len(data_series)
                    )
                    patterns.append(pattern)
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze patterns for {period} {metric_type}: {str(e)}")
        
        return patterns
    
    def _analyze_cross_period_patterns(self, metrics_df: pd.DataFrame) -> List[TemporalPattern]:
        """
        Analyze patterns across different time periods.
        
        Args:
            metrics_df: DataFrame with match period metrics
            
        Returns:
            List of cross-period TemporalPattern objects
        """
        patterns = []
        
        try:
            # Pre-match to post-match pattern analysis
            if 'pre_match_order_count' in metrics_df.columns and 'post_match_order_count' in metrics_df.columns:
                pre_orders = metrics_df['pre_match_order_count']
                post_orders = metrics_df['post_match_order_count']
                
                # Calculate order increase/decrease from pre to post
                order_changes = post_orders - pre_orders
                significant_increases = order_changes > order_changes.quantile(0.75)
                
                if significant_increases.any():
                    avg_increase = order_changes[significant_increases].mean()
                    pattern = TemporalPattern(
                        pattern_id=str(uuid.uuid4()),
                        time_period='pre_to_post_match',
                        pattern_type='spike',
                        magnitude=min(avg_increase / pre_orders.mean() * 100 if pre_orders.mean() > 0 else 0, 100),
                        confidence=self._calculate_pattern_confidence(significant_increases.sum(), len(metrics_df)),
                        description=f"Significant order increases from pre-match to post-match periods ({significant_increases.sum()} matches)",
                        data_source_breakdown=self._calculate_source_breakdown(metrics_df[significant_increases], 'data_source'),
                        sample_size=len(metrics_df)
                    )
                    patterns.append(pattern)
            
            # During-match to post-match reaction patterns
            if 'during_match_order_count' in metrics_df.columns and 'post_match_order_count' in metrics_df.columns:
                during_orders = metrics_df['during_match_order_count']
                post_orders = metrics_df['post_match_order_count']
                
                # Look for immediate reactions (high correlation)
                correlation, p_value = stats.pearsonr(during_orders, post_orders)
                
                if abs(correlation) > 0.4 and p_value < 0.05:
                    pattern = TemporalPattern(
                        pattern_id=str(uuid.uuid4()),
                        time_period='during_to_post_match',
                        pattern_type='trend',
                        magnitude=abs(correlation) * 100,
                        confidence=1 - p_value,
                        description=f"Strong correlation between during-match and post-match orders (r={correlation:.3f})",
                        data_source_breakdown=self._calculate_source_breakdown(metrics_df, 'data_source'),
                        sample_size=len(metrics_df)
                    )
                    patterns.append(pattern)
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze cross-period patterns: {str(e)}")
        
        return patterns
    
    def _analyze_outcome_impact_patterns(self, metrics_df: pd.DataFrame) -> List[TemporalPattern]:
        """
        Analyze how match outcomes impact ordering patterns.
        
        Args:
            metrics_df: DataFrame with match period metrics
            
        Returns:
            List of outcome-related TemporalPattern objects
        """
        patterns = []
        
        try:
            if 'winner' not in metrics_df.columns:
                return patterns
            
            # Analyze post-match ordering by outcome
            if 'post_match_order_count' in metrics_df.columns:
                for outcome in ['home', 'away', 'draw']:
                    outcome_matches = metrics_df[metrics_df['winner'] == outcome]
                    
                    if len(outcome_matches) >= 3:
                        outcome_orders = outcome_matches['post_match_order_count']
                        all_orders = metrics_df['post_match_order_count']
                        
                        # Compare outcome-specific orders to overall average
                        outcome_mean = outcome_orders.mean()
                        overall_mean = all_orders.mean()
                        
                        if outcome_mean > overall_mean * 1.2:  # 20% higher than average
                            magnitude = ((outcome_mean - overall_mean) / overall_mean * 100)
                            
                            pattern = TemporalPattern(
                                pattern_id=str(uuid.uuid4()),
                                time_period='post_match',
                                pattern_type='spike',
                                magnitude=min(magnitude, 100),
                                confidence=self._calculate_pattern_confidence(len(outcome_matches), len(metrics_df)),
                                description=f"Higher post-match orders following {outcome} wins ({outcome_mean:.1f} vs {overall_mean:.1f} average)",
                                data_source_breakdown=self._calculate_source_breakdown(outcome_matches, 'data_source'),
                                sample_size=len(outcome_matches)
                            )
                            patterns.append(pattern)
            
            # Analyze high-scoring match impact
            if 'is_high_scoring' in metrics_df.columns and 'post_match_order_count' in metrics_df.columns:
                high_scoring = metrics_df[metrics_df['is_high_scoring'] == True]
                regular_scoring = metrics_df[metrics_df['is_high_scoring'] == False]
                
                if len(high_scoring) >= 3 and len(regular_scoring) >= 3:
                    high_scoring_orders = high_scoring['post_match_order_count'].mean()
                    regular_orders = regular_scoring['post_match_order_count'].mean()
                    
                    if high_scoring_orders > regular_orders * 1.15:  # 15% higher
                        magnitude = ((high_scoring_orders - regular_orders) / regular_orders * 100)
                        
                        pattern = TemporalPattern(
                            pattern_id=str(uuid.uuid4()),
                            time_period='post_match',
                            pattern_type='spike',
                            magnitude=min(magnitude, 100),
                            confidence=self._calculate_pattern_confidence(len(high_scoring), len(metrics_df)),
                            description=f"Higher orders after high-scoring matches ({high_scoring_orders:.1f} vs {regular_orders:.1f})",
                            data_source_breakdown=self._calculate_source_breakdown(high_scoring, 'data_source'),
                            sample_size=len(high_scoring)
                        )
                        patterns.append(pattern)
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze outcome impact patterns: {str(e)}")
        
        return patterns
    
    def _calculate_pattern_confidence(self, pattern_instances: int, total_instances: int) -> float:
        """Calculate confidence score for a pattern based on sample size."""
        if total_instances == 0:
            return 0.0
        
        # Base confidence on proportion and minimum sample size
        proportion = pattern_instances / total_instances
        sample_factor = min(pattern_instances / 10, 1.0)  # Confidence increases with sample size up to 10
        
        return min(proportion * sample_factor, 1.0)
    
    def _calculate_source_breakdown(self, data_subset: pd.DataFrame, source_column: str) -> Dict[str, float]:
        """Calculate percentage breakdown by data source."""
        if data_subset.empty or source_column not in data_subset.columns:
            return {'real': 0.0, 'mock': 0.0}
        
        source_counts = data_subset[source_column].value_counts()
        total = len(data_subset)
        
        return {
            'real': (source_counts.get('real', 0) / total * 100) if total > 0 else 0.0,
            'mock': (source_counts.get('mock', 0) / total * 100) if total > 0 else 0.0
        }
    
    def generate_summary_statistics(self, orders: List[DominosOrder], 
                                  matches: List[FootballMatch],
                                  metrics_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Create summary statistics generation for all available data.
        
        Args:
            orders: List of pizza orders
            matches: List of football matches
            metrics_df: DataFrame with calculated match period metrics
            
        Returns:
            Dictionary containing comprehensive summary statistics
            
        Requirements: 7.4 - Insight generation completeness
        """
        try:
            self.logger.info("Generating comprehensive summary statistics")
            
            summary = {
                'generation_timestamp': datetime.utcnow().isoformat(),
                'data_overview': {},
                'order_statistics': {},
                'match_statistics': {},
                'correlation_statistics': {},
                'temporal_statistics': {},
                'data_quality_metrics': {}
            }
            
            # Data overview
            summary['data_overview'] = {
                'total_orders': len(orders),
                'total_matches': len(matches),
                'analysis_period': self._get_analysis_period(orders, matches),
                'data_sources': self._get_data_source_summary(orders, matches)
            }
            
            # Order statistics
            if orders:
                order_df = pd.DataFrame([asdict(order) for order in orders])
                order_df['timestamp'] = pd.to_datetime(order_df['timestamp'])
                
                summary['order_statistics'] = {
                    'total_revenue': order_df['order_total'].sum(),
                    'average_order_value': order_df['order_total'].mean(),
                    'median_order_value': order_df['order_total'].median(),
                    'total_pizzas': order_df['quantity'].sum(),
                    'average_pizzas_per_order': order_df['quantity'].mean(),
                    'unique_locations': order_df['location'].nunique(),
                    'most_popular_location': order_df['location'].mode().iloc[0] if not order_df['location'].mode().empty else None,
                    'orders_per_day': len(orders) / max(1, (order_df['timestamp'].max() - order_df['timestamp'].min()).days),
                    'peak_order_hour': order_df['timestamp'].dt.hour.mode().iloc[0] if not order_df['timestamp'].dt.hour.mode().empty else None,
                    'pizza_type_distribution': self._get_pizza_type_distribution(orders)
                }
            
            # Match statistics
            if matches:
                match_df = pd.DataFrame([asdict(match) for match in matches])
                match_df['timestamp'] = pd.to_datetime(match_df['timestamp'])
                
                summary['match_statistics'] = {
                    'total_goals': match_df['home_score'].sum() + match_df['away_score'].sum(),
                    'average_goals_per_match': (match_df['home_score'] + match_df['away_score']).mean(),
                    'high_scoring_matches': ((match_df['home_score'] + match_df['away_score']) >= 3).sum(),
                    'home_win_rate': (match_df['home_score'] > match_df['away_score']).mean() * 100,
                    'draw_rate': (match_df['home_score'] == match_df['away_score']).mean() * 100,
                    'tournament_matches': (match_df['match_significance'] == 'tournament').sum(),
                    'final_matches': (match_df['match_significance'] == 'final').sum(),
                    'most_common_score': self._get_most_common_score(matches),
                    'team_performance': self._get_team_performance_summary(matches)
                }
            
            # Temporal statistics from metrics
            if not metrics_df.empty:
                summary['temporal_statistics'] = {
                    'pre_match_avg_orders': metrics_df.get('pre_match_order_count', pd.Series()).mean(),
                    'during_match_avg_orders': metrics_df.get('during_match_order_count', pd.Series()).mean(),
                    'post_match_avg_orders': metrics_df.get('post_match_order_count', pd.Series()).mean(),
                    'pre_match_avg_volume': metrics_df.get('pre_match_total_volume', pd.Series()).mean(),
                    'during_match_avg_volume': metrics_df.get('during_match_total_volume', pd.Series()).mean(),
                    'post_match_avg_volume': metrics_df.get('post_match_total_volume', pd.Series()).mean(),
                    'highest_order_period': self._identify_peak_order_period(metrics_df),
                    'order_volatility': self._calculate_order_volatility(metrics_df)
                }
            
            # Data quality metrics
            summary['data_quality_metrics'] = {
                'real_data_percentage': self._calculate_real_data_percentage(orders, matches),
                'data_completeness': self._assess_data_completeness(orders, matches, metrics_df),
                'temporal_coverage': self._assess_temporal_coverage(orders, matches),
                'data_consistency_score': self._assess_data_consistency(orders, matches)
            }
            
            self.logger.info("Generated comprehensive summary statistics")
            return summary
            
        except Exception as e:
            raise InsightGenerationError(f"Failed to generate summary statistics: {str(e)}")
    
    def detect_anomalies_with_source_distinction(self, orders: List[DominosOrder], 
                                               matches: List[FootballMatch],
                                               metrics_df: pd.DataFrame) -> List[AnomalyDetection]:
        """
        Add anomaly detection with source distinction capabilities.
        
        Args:
            orders: List of pizza orders
            matches: List of football matches
            metrics_df: DataFrame with calculated match period metrics
            
        Returns:
            List of AnomalyDetection objects
            
        Requirements: 7.5 - Anomaly detection with source distinction
        """
        try:
            self.logger.info("Detecting anomalies with source distinction")
            
            anomalies = []
            
            # Detect order volume anomalies
            order_anomalies = self._detect_order_volume_anomalies(orders, metrics_df)
            anomalies.extend(order_anomalies)
            
            # Detect temporal anomalies
            temporal_anomalies = self._detect_temporal_anomalies(metrics_df)
            anomalies.extend(temporal_anomalies)
            
            # Detect correlation anomalies
            correlation_anomalies = self._detect_correlation_anomalies(metrics_df)
            anomalies.extend(correlation_anomalies)
            
            # Detect data source inconsistencies
            source_anomalies = self._detect_source_inconsistencies(orders, matches)
            anomalies.extend(source_anomalies)
            
            self.logger.info(f"Detected {len(anomalies)} anomalies")
            return anomalies
            
        except Exception as e:
            raise InsightGenerationError(f"Failed to detect anomalies: {str(e)}")
    
    def generate_comprehensive_report(self, orders: List[DominosOrder], 
                                   matches: List[FootballMatch],
                                   metrics_df: pd.DataFrame,
                                   correlation_results: List[CorrelationResult]) -> InsightReport:
        """
        Generate comprehensive analysis reports with data quality indicators.
        
        Args:
            orders: List of pizza orders
            matches: List of football matches
            metrics_df: DataFrame with calculated match period metrics
            correlation_results: List of correlation analysis results
            
        Returns:
            InsightReport object containing comprehensive analysis
            
        Requirements: 7.3, 7.4, 7.5 - Comprehensive reporting
        """
        try:
            self.logger.info("Generating comprehensive insight report")
            
            # Generate all components
            temporal_patterns = self.analyze_temporal_patterns(orders, matches, metrics_df)
            summary_statistics = self.generate_summary_statistics(orders, matches, metrics_df)
            anomalies = self.detect_anomalies_with_source_distinction(orders, matches, metrics_df)
            
            # Calculate overall data quality score
            data_quality_score = self._calculate_overall_data_quality(orders, matches, metrics_df)
            
            # Generate key insights
            key_insights = self._generate_key_insights(temporal_patterns, summary_statistics, anomalies, correlation_results)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(temporal_patterns, anomalies, data_quality_score)
            
            # Determine analysis period
            analysis_period = self._get_analysis_period_tuple(orders, matches)
            
            # Calculate real data percentage
            real_data_percentage = self._calculate_real_data_percentage(orders, matches)
            
            report = InsightReport(
                report_id=str(uuid.uuid4()),
                generation_timestamp=datetime.utcnow(),
                analysis_period=analysis_period,
                data_quality_score=data_quality_score,
                total_matches=len(matches),
                total_orders=len(orders),
                real_data_percentage=real_data_percentage,
                temporal_patterns=temporal_patterns,
                anomalies=anomalies,
                summary_statistics=summary_statistics,
                key_insights=key_insights,
                recommendations=recommendations
            )
            
            self.logger.info(f"Generated comprehensive report with {len(temporal_patterns)} patterns, {len(anomalies)} anomalies")
            return report
            
        except Exception as e:
            raise InsightGenerationError(f"Failed to generate comprehensive report: {str(e)}")
    
    # Helper methods for summary statistics
    def _get_analysis_period(self, orders: List[DominosOrder], matches: List[FootballMatch]) -> Dict[str, str]:
        """Get the analysis period from orders and matches."""
        timestamps = []
        
        if orders:
            timestamps.extend([order.timestamp for order in orders])
        if matches:
            timestamps.extend([match.timestamp for match in matches])
        
        if not timestamps:
            return {'start': None, 'end': None, 'duration_days': 0}
        
        start_time = min(timestamps)
        end_time = max(timestamps)
        duration = (end_time - start_time).days
        
        return {
            'start': start_time.isoformat(),
            'end': end_time.isoformat(),
            'duration_days': duration
        }
    
    def _get_analysis_period_tuple(self, orders: List[DominosOrder], matches: List[FootballMatch]) -> Tuple[datetime, datetime]:
        """Get analysis period as tuple for InsightReport."""
        timestamps = []
        
        if orders:
            timestamps.extend([order.timestamp for order in orders])
        if matches:
            timestamps.extend([match.timestamp for match in matches])
        
        if not timestamps:
            now = datetime.utcnow()
            return (now, now)
        
        return (min(timestamps), max(timestamps))
    
    def _get_data_source_summary(self, orders: List[DominosOrder], matches: List[FootballMatch]) -> Dict[str, Any]:
        """Get summary of data sources."""
        order_sources = {'real': 0, 'mock': 0}
        match_sources = {'real': 0, 'mock': 0}
        
        for order in orders:
            order_sources[order.data_source] += 1
        
        for match in matches:
            match_sources[match.data_source] += 1
        
        total_orders = len(orders)
        total_matches = len(matches)
        
        return {
            'orders': {
                'real_count': order_sources['real'],
                'mock_count': order_sources['mock'],
                'real_percentage': (order_sources['real'] / total_orders * 100) if total_orders > 0 else 0
            },
            'matches': {
                'real_count': match_sources['real'],
                'mock_count': match_sources['mock'],
                'real_percentage': (match_sources['real'] / total_matches * 100) if total_matches > 0 else 0
            }
        }
    
    def _get_pizza_type_distribution(self, orders: List[DominosOrder]) -> Dict[str, int]:
        """Get distribution of pizza types across all orders."""
        pizza_counts = {}
        
        for order in orders:
            for pizza_type in order.pizza_types:
                pizza_counts[pizza_type] = pizza_counts.get(pizza_type, 0) + 1
        
        # Return top 10 most popular pizza types
        sorted_pizzas = sorted(pizza_counts.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_pizzas[:10])
    
    def _get_most_common_score(self, matches: List[FootballMatch]) -> str:
        """Get the most common match score."""
        score_counts = {}
        
        for match in matches:
            score = f"{match.home_score}-{match.away_score}"
            score_counts[score] = score_counts.get(score, 0) + 1
        
        if not score_counts:
            return "N/A"
        
        return max(score_counts.items(), key=lambda x: x[1])[0]
    
    def _get_team_performance_summary(self, matches: List[FootballMatch]) -> Dict[str, Any]:
        """Get summary of team performance."""
        team_stats = {}
        
        for match in matches:
            # Home team stats
            if match.home_team not in team_stats:
                team_stats[match.home_team] = {'wins': 0, 'losses': 0, 'draws': 0, 'goals_for': 0, 'goals_against': 0}
            
            team_stats[match.home_team]['goals_for'] += match.home_score
            team_stats[match.home_team]['goals_against'] += match.away_score
            
            if match.home_score > match.away_score:
                team_stats[match.home_team]['wins'] += 1
            elif match.home_score < match.away_score:
                team_stats[match.home_team]['losses'] += 1
            else:
                team_stats[match.home_team]['draws'] += 1
            
            # Away team stats
            if match.away_team not in team_stats:
                team_stats[match.away_team] = {'wins': 0, 'losses': 0, 'draws': 0, 'goals_for': 0, 'goals_against': 0}
            
            team_stats[match.away_team]['goals_for'] += match.away_score
            team_stats[match.away_team]['goals_against'] += match.home_score
            
            if match.away_score > match.home_score:
                team_stats[match.away_team]['wins'] += 1
            elif match.away_score < match.home_score:
                team_stats[match.away_team]['losses'] += 1
            else:
                team_stats[match.away_team]['draws'] += 1
        
        # Find best performing team (by win rate)
        best_team = None
        best_win_rate = 0
        
        for team, stats in team_stats.items():
            total_games = stats['wins'] + stats['losses'] + stats['draws']
            if total_games > 0:
                win_rate = stats['wins'] / total_games
                if win_rate > best_win_rate:
                    best_win_rate = win_rate
                    best_team = team
        
        return {
            'total_teams': len(team_stats),
            'best_performing_team': best_team,
            'best_win_rate': best_win_rate * 100 if best_win_rate > 0 else 0,
            'average_goals_per_team': sum(stats['goals_for'] for stats in team_stats.values()) / len(team_stats) if team_stats else 0
        }
    
    def _identify_peak_order_period(self, metrics_df: pd.DataFrame) -> str:
        """Identify which period has the highest average orders."""
        if metrics_df.empty:
            return "unknown"
        
        period_averages = {}
        
        for period in ['pre_match', 'during_match', 'post_match']:
            col = f'{period}_order_count'
            if col in metrics_df.columns:
                period_averages[period] = metrics_df[col].mean()
        
        if not period_averages:
            return "unknown"
        
        return max(period_averages.items(), key=lambda x: x[1])[0]
    
    def _calculate_order_volatility(self, metrics_df: pd.DataFrame) -> float:
        """Calculate order volatility across all periods."""
        if metrics_df.empty:
            return 0.0
        
        volatilities = []
        
        for period in ['pre_match', 'during_match', 'post_match']:
            col = f'{period}_order_count'
            if col in metrics_df.columns and len(metrics_df[col]) > 1:
                volatility = metrics_df[col].std() / metrics_df[col].mean() if metrics_df[col].mean() > 0 else 0
                volatilities.append(volatility)
        
        return np.mean(volatilities) if volatilities else 0.0    
 
   # Helper methods for data quality assessment
    def _calculate_real_data_percentage(self, orders: List[DominosOrder], matches: List[FootballMatch]) -> float:
        """Calculate percentage of real vs mock data."""
        total_items = len(orders) + len(matches)
        if total_items == 0:
            return 0.0
        
        real_items = sum(1 for order in orders if order.data_source == 'real')
        real_items += sum(1 for match in matches if match.data_source == 'real')
        
        return (real_items / total_items) * 100
    
    def _assess_data_completeness(self, orders: List[DominosOrder], matches: List[FootballMatch], metrics_df: pd.DataFrame) -> float:
        """Assess completeness of data (0-100 score)."""
        completeness_score = 0
        
        # Check if we have orders (25 points)
        if orders:
            completeness_score += 25
        
        # Check if we have matches (25 points)
        if matches:
            completeness_score += 25
        
        # Check if we have metrics (25 points)
        if not metrics_df.empty:
            completeness_score += 25
        
        # Check temporal alignment (25 points)
        if orders and matches:
            order_times = [order.timestamp for order in orders]
            match_times = [match.timestamp for match in matches]
            
            # Check if there's temporal overlap
            order_range = (min(order_times), max(order_times))
            match_range = (min(match_times), max(match_times))
            
            # Check for overlap
            if (order_range[0] <= match_range[1] and match_range[0] <= order_range[1]):
                completeness_score += 25
        
        return completeness_score
    
    def _assess_temporal_coverage(self, orders: List[DominosOrder], matches: List[FootballMatch]) -> Dict[str, Any]:
        """Assess temporal coverage of the data."""
        if not orders and not matches:
            return {'coverage_days': 0, 'data_density': 0, 'gaps': []}
        
        all_timestamps = []
        if orders:
            all_timestamps.extend([order.timestamp for order in orders])
        if matches:
            all_timestamps.extend([match.timestamp for match in matches])
        
        if not all_timestamps:
            return {'coverage_days': 0, 'data_density': 0, 'gaps': []}
        
        start_time = min(all_timestamps)
        end_time = max(all_timestamps)
        coverage_days = (end_time - start_time).days + 1
        
        # Calculate data density (events per day)
        data_density = len(all_timestamps) / coverage_days if coverage_days > 0 else 0
        
        # Identify gaps (days with no data)
        dates_with_data = set(ts.date() for ts in all_timestamps)
        all_dates = set()
        current_date = start_time.date()
        while current_date <= end_time.date():
            all_dates.add(current_date)
            current_date += timedelta(days=1)
        
        gaps = sorted(list(all_dates - dates_with_data))
        
        return {
            'coverage_days': coverage_days,
            'data_density': data_density,
            'gaps': [gap.isoformat() for gap in gaps[:10]]  # Limit to first 10 gaps
        }
    
    def _assess_data_consistency(self, orders: List[DominosOrder], matches: List[FootballMatch]) -> float:
        """Assess consistency of data (0-100 score)."""
        consistency_score = 100  # Start with perfect score and deduct for issues
        
        # Check for data validation issues
        try:
            for order in orders:
                order.validate()
        except ValueError:
            consistency_score -= 10  # Deduct for validation failures
        
        try:
            for match in matches:
                match.validate()
        except ValueError:
            consistency_score -= 10
        
        # Check for reasonable data ranges
        if orders:
            order_totals = [order.order_total for order in orders]
            if any(total > 1000 for total in order_totals):  # Unreasonably high orders
                consistency_score -= 5
            if any(total < 5 for total in order_totals):  # Unreasonably low orders
                consistency_score -= 5
        
        if matches:
            scores = [match.home_score + match.away_score for match in matches]
            if any(score > 10 for score in scores):  # Unreasonably high scores
                consistency_score -= 5
        
        return max(consistency_score, 0)
    
    def _calculate_overall_data_quality(self, orders: List[DominosOrder], matches: List[FootballMatch], metrics_df: pd.DataFrame) -> float:
        """Calculate overall data quality score."""
        real_data_pct = self._calculate_real_data_percentage(orders, matches)
        completeness = self._assess_data_completeness(orders, matches, metrics_df)
        consistency = self._assess_data_consistency(orders, matches)
        
        # Weighted average: real data 40%, completeness 30%, consistency 30%
        overall_quality = (real_data_pct * 0.4) + (completeness * 0.3) + (consistency * 0.3)
        return min(overall_quality, 100)
    
    # Helper methods for anomaly detection
    def _detect_order_volume_anomalies(self, orders: List[DominosOrder], metrics_df: pd.DataFrame) -> List[AnomalyDetection]:
        """Detect anomalies in order volumes."""
        anomalies = []
        
        try:
            if not orders:
                return anomalies
            
            # Convert orders to DataFrame for analysis
            order_df = pd.DataFrame([asdict(order) for order in orders])
            order_df['timestamp'] = pd.to_datetime(order_df['timestamp'])
            
            # Detect extreme order values
            order_totals = order_df['order_total']
            q1 = order_totals.quantile(0.25)
            q3 = order_totals.quantile(0.75)
            iqr = q3 - q1
            
            # Outliers are beyond 3*IQR from quartiles
            lower_bound = q1 - 3 * iqr
            upper_bound = q3 + 3 * iqr
            
            outliers = order_df[(order_df['order_total'] < lower_bound) | (order_df['order_total'] > upper_bound)]
            
            for _, outlier in outliers.iterrows():
                severity = 'high' if outlier['order_total'] > upper_bound else 'medium'
                anomaly_type = 'order_spike' if outlier['order_total'] > upper_bound else 'order_dip'
                
                anomaly = AnomalyDetection(
                    anomaly_id=str(uuid.uuid4()),
                    timestamp=outlier['timestamp'],
                    anomaly_type=anomaly_type,
                    severity=severity,
                    description=f"Unusual order value: ${outlier['order_total']:.2f} (normal range: ${lower_bound:.2f}-${upper_bound:.2f})",
                    data_source=outlier['data_source'],
                    confidence_score=0.8,
                    context={
                        'order_id': outlier['order_id'],
                        'location': outlier['location'],
                        'expected_range': f"${lower_bound:.2f}-${upper_bound:.2f}"
                    }
                )
                anomalies.append(anomaly)
            
        except Exception as e:
            self.logger.warning(f"Failed to detect order volume anomalies: {str(e)}")
        
        return anomalies
    
    def _detect_temporal_anomalies(self, metrics_df: pd.DataFrame) -> List[AnomalyDetection]:
        """Detect temporal anomalies in ordering patterns."""
        anomalies = []
        
        try:
            if metrics_df.empty:
                return anomalies
            
            # Check for unusual patterns in each time period
            for period in ['pre_match', 'during_match', 'post_match']:
                order_col = f'{period}_order_count'
                
                if order_col in metrics_df.columns:
                    orders = metrics_df[order_col]
                    
                    # Detect zero-order periods (unusual)
                    zero_orders = metrics_df[orders == 0]
                    
                    if len(zero_orders) > len(metrics_df) * 0.1:  # More than 10% zero-order periods
                        anomaly = AnomalyDetection(
                            anomaly_id=str(uuid.uuid4()),
                            timestamp=datetime.utcnow(),
                            anomaly_type='unusual_pattern',
                            severity='medium',
                            description=f"Unusually high number of zero-order {period} periods ({len(zero_orders)} out of {len(metrics_df)})",
                            data_source='mixed',
                            confidence_score=0.7,
                            context={
                                'period': period,
                                'zero_count': len(zero_orders),
                                'total_periods': len(metrics_df),
                                'percentage': len(zero_orders) / len(metrics_df) * 100
                            }
                        )
                        anomalies.append(anomaly)
            
        except Exception as e:
            self.logger.warning(f"Failed to detect temporal anomalies: {str(e)}")
        
        return anomalies
    
    def _detect_correlation_anomalies(self, metrics_df: pd.DataFrame) -> List[AnomalyDetection]:
        """Detect anomalies in correlation patterns."""
        anomalies = []
        
        try:
            if metrics_df.empty or len(metrics_df) < 5:
                return anomalies
            
            # Check for negative correlation between match excitement and orders (unusual)
            if 'total_goals' in metrics_df.columns and 'post_match_order_count' in metrics_df.columns:
                correlation, p_value = stats.pearsonr(metrics_df['total_goals'], metrics_df['post_match_order_count'])
                
                if correlation < -0.3 and p_value < 0.05:  # Significant negative correlation
                    anomaly = AnomalyDetection(
                        anomaly_id=str(uuid.uuid4()),
                        timestamp=datetime.utcnow(),
                        anomaly_type='unusual_pattern',
                        severity='high',
                        description=f"Unusual negative correlation between match excitement and post-match orders (r={correlation:.3f})",
                        data_source='mixed',
                        confidence_score=1 - p_value,
                        context={
                            'correlation_coefficient': correlation,
                            'p_value': p_value,
                            'sample_size': len(metrics_df)
                        }
                    )
                    anomalies.append(anomaly)
            
        except Exception as e:
            self.logger.warning(f"Failed to detect correlation anomalies: {str(e)}")
        
        return anomalies
    
    def _detect_source_inconsistencies(self, orders: List[DominosOrder], matches: List[FootballMatch]) -> List[AnomalyDetection]:
        """Detect inconsistencies between real and mock data sources."""
        anomalies = []
        
        try:
            # Check for extreme differences between real and mock data patterns
            if orders:
                real_orders = [order for order in orders if order.data_source == 'real']
                mock_orders = [order for order in orders if order.data_source == 'mock']
                
                if real_orders and mock_orders:
                    real_avg = np.mean([order.order_total for order in real_orders])
                    mock_avg = np.mean([order.order_total for order in mock_orders])
                    
                    # Check if averages differ by more than 50%
                    if abs(real_avg - mock_avg) / max(real_avg, mock_avg) > 0.5:
                        anomaly = AnomalyDetection(
                            anomaly_id=str(uuid.uuid4()),
                            timestamp=datetime.utcnow(),
                            anomaly_type='unusual_pattern',
                            severity='medium',
                            description=f"Significant difference between real and mock order averages (${real_avg:.2f} vs ${mock_avg:.2f})",
                            data_source='mixed',
                            confidence_score=0.8,
                            context={
                                'real_average': real_avg,
                                'mock_average': mock_avg,
                                'real_count': len(real_orders),
                                'mock_count': len(mock_orders)
                            }
                        )
                        anomalies.append(anomaly)
            
        except Exception as e:
            self.logger.warning(f"Failed to detect source inconsistencies: {str(e)}")
        
        return anomalies
    
    # Helper methods for insight generation
    def _generate_key_insights(self, temporal_patterns: List[TemporalPattern], 
                             summary_statistics: Dict[str, Any],
                             anomalies: List[AnomalyDetection],
                             correlation_results: List[CorrelationResult]) -> List[str]:
        """Generate key insights from analysis results."""
        insights = []
        
        try:
            # Insights from temporal patterns
            spike_patterns = [p for p in temporal_patterns if p.pattern_type == 'spike']
            if spike_patterns:
                strongest_spike = max(spike_patterns, key=lambda p: p.magnitude)
                insights.append(f"Strongest ordering spike detected in {strongest_spike.time_period} period with {strongest_spike.magnitude:.1f}% increase")
            
            # Insights from correlations
            if correlation_results:
                significant_correlations = [r for r in correlation_results if r.is_significant()]
                if significant_correlations:
                    strongest_corr = max(significant_correlations, key=lambda r: abs(r.correlation_coefficient))
                    insights.append(f"Strongest significant correlation: {strongest_corr.pattern_description}")
            
            # Insights from data quality
            if 'data_quality_metrics' in summary_statistics:
                real_pct = summary_statistics['data_quality_metrics'].get('real_data_percentage', 0)
                if real_pct > 70:
                    insights.append(f"High data quality with {real_pct:.1f}% real data")
                elif real_pct < 30:
                    insights.append(f"Analysis primarily based on mock data ({real_pct:.1f}% real data)")
            
            # Insights from anomalies
            high_severity_anomalies = [a for a in anomalies if a.severity in ['high', 'critical']]
            if high_severity_anomalies:
                insights.append(f"Detected {len(high_severity_anomalies)} high-severity anomalies requiring attention")
            
            # Insights from order patterns
            if 'temporal_statistics' in summary_statistics:
                peak_period = summary_statistics['temporal_statistics'].get('highest_order_period')
                if peak_period and peak_period != 'unknown':
                    insights.append(f"Peak ordering occurs during {peak_period.replace('_', '-')} period")
            
        except Exception as e:
            self.logger.warning(f"Failed to generate key insights: {str(e)}")
            insights.append("Analysis completed with limited insight generation due to data processing issues")
        
        return insights[:10]  # Limit to top 10 insights
    
    def _generate_recommendations(self, temporal_patterns: List[TemporalPattern], 
                                anomalies: List[AnomalyDetection],
                                data_quality_score: float) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        try:
            # Data quality recommendations
            if data_quality_score < 50:
                recommendations.append("Improve data collection to increase real data percentage for more reliable insights")
            
            # Pattern-based recommendations
            post_match_spikes = [p for p in temporal_patterns if p.time_period == 'post_match' and p.pattern_type == 'spike']
            if post_match_spikes:
                recommendations.append("Consider targeted marketing campaigns immediately after football matches to capitalize on ordering spikes")
            
            # Anomaly-based recommendations
            high_anomalies = [a for a in anomalies if a.severity in ['high', 'critical']]
            if high_anomalies:
                recommendations.append("Investigate high-severity anomalies to identify potential data quality issues or unusual business patterns")
            
            # General recommendations
            recommendations.append("Continue monitoring correlation patterns to identify optimal timing for promotional activities")
            
            if len(temporal_patterns) > 5:
                recommendations.append("Rich pattern data suggests implementing automated alert system for significant ordering changes")
            
        except Exception as e:
            self.logger.warning(f"Failed to generate recommendations: {str(e)}")
            recommendations.append("Review analysis results manually to identify actionable insights")
        
        return recommendations[:8]  # Limit to top 8 recommendations