"""
Tests for the insight generation system.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import numpy as np

from src.data_processing.insight_generator import (
    InsightGenerator, 
    InsightGenerationError,
    TemporalPattern,
    AnomalyDetection,
    InsightReport
)
from src.models.pizza_order import DominosOrder
from src.models.football_match import FootballMatch
from src.models.correlation_result import CorrelationResult


class TestInsightGenerator:
    """Test cases for InsightGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = InsightGenerator()
        
        # Create sample data
        base_time = datetime(2024, 1, 1, 18, 0)
        
        self.sample_orders = [
            DominosOrder(
                order_id=f"order_{i}",
                timestamp=base_time + timedelta(hours=i),
                location=f"Location_{i % 3}",
                order_total=15.0 + (i % 10) * 2,
                pizza_types=["Pepperoni", "Margherita"],
                quantity=2,
                data_source="real" if i % 2 == 0 else "mock"
            )
            for i in range(10)
        ]
        
        self.sample_matches = [
            FootballMatch(
                match_id=f"match_{i}",
                timestamp=base_time + timedelta(hours=i * 2),
                home_team=f"Team_A_{i}",
                away_team=f"Team_B_{i}",
                home_score=i % 4,
                away_score=(i + 1) % 3,
                event_type="win" if i % 4 > (i + 1) % 3 else "loss" if i % 4 < (i + 1) % 3 else "draw",
                match_significance="tournament" if i % 3 == 0 else "regular",
                data_source="real" if i % 2 == 0 else "mock"
            )
            for i in range(5)
        ]
        
        # Create sample metrics DataFrame
        self.sample_metrics_df = pd.DataFrame({
            'match_id': [f"match_{i}" for i in range(5)],
            'pre_match_order_count': [5, 8, 3, 12, 6],
            'during_match_order_count': [7, 10, 4, 15, 8],
            'post_match_order_count': [10, 15, 6, 20, 12],
            'pre_match_total_volume': [75.0, 120.0, 45.0, 180.0, 90.0],
            'during_match_total_volume': [105.0, 150.0, 60.0, 225.0, 120.0],
            'post_match_total_volume': [150.0, 225.0, 90.0, 300.0, 180.0],
            'winner': ['home', 'away', 'draw', 'home', 'away'],
            'is_high_scoring': [False, True, False, True, False],
            'data_source': ['real', 'mock', 'real', 'mock', 'real']
        })
    
    def test_analyze_temporal_patterns_basic(self):
        """Test basic temporal pattern analysis."""
        patterns = self.generator.analyze_temporal_patterns(
            self.sample_orders, 
            self.sample_matches, 
            self.sample_metrics_df
        )
        
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        
        # Check that patterns have required attributes
        for pattern in patterns:
            assert isinstance(pattern, TemporalPattern)
            assert pattern.pattern_id
            assert pattern.time_period in ['pre_match', 'during_match', 'post_match', 'pre_to_post_match', 'during_to_post_match']
            assert pattern.pattern_type in ['spike', 'dip', 'stable', 'trend']
            assert 0 <= pattern.magnitude <= 100
            assert 0 <= pattern.confidence <= 1
            assert isinstance(pattern.data_source_breakdown, dict)
    
    def test_analyze_temporal_patterns_empty_data(self):
        """Test temporal pattern analysis with empty data."""
        patterns = self.generator.analyze_temporal_patterns([], [], pd.DataFrame())
        assert patterns == []
    
    def test_generate_summary_statistics_comprehensive(self):
        """Test comprehensive summary statistics generation."""
        summary = self.generator.generate_summary_statistics(
            self.sample_orders,
            self.sample_matches,
            self.sample_metrics_df
        )
        
        assert isinstance(summary, dict)
        
        # Check required sections
        required_sections = [
            'generation_timestamp',
            'data_overview',
            'order_statistics',
            'match_statistics',
            'temporal_statistics',
            'data_quality_metrics'
        ]
        
        for section in required_sections:
            assert section in summary
        
        # Check data overview
        data_overview = summary['data_overview']
        assert data_overview['total_orders'] == len(self.sample_orders)
        assert data_overview['total_matches'] == len(self.sample_matches)
        assert 'analysis_period' in data_overview
        assert 'data_sources' in data_overview
        
        # Check order statistics
        order_stats = summary['order_statistics']
        assert 'total_revenue' in order_stats
        assert 'average_order_value' in order_stats
        assert 'total_pizzas' in order_stats
        assert order_stats['total_revenue'] > 0
        
        # Check match statistics
        match_stats = summary['match_statistics']
        assert 'total_goals' in match_stats
        assert 'average_goals_per_match' in match_stats
        assert 'home_win_rate' in match_stats
        
        # Check data quality metrics
        quality_metrics = summary['data_quality_metrics']
        assert 'real_data_percentage' in quality_metrics
        assert 'data_completeness' in quality_metrics
        assert 0 <= quality_metrics['real_data_percentage'] <= 100
    
    def test_detect_anomalies_with_source_distinction(self):
        """Test anomaly detection with source distinction."""
        # Add some extreme values to trigger anomalies
        extreme_orders = self.sample_orders + [
            DominosOrder(
                order_id="extreme_order",
                timestamp=datetime(2024, 1, 1, 20, 0),
                location="Location_X",
                order_total=500.0,  # Extreme value
                pizza_types=["Pepperoni"],
                quantity=1,
                data_source="real"
            )
        ]
        
        anomalies = self.generator.detect_anomalies_with_source_distinction(
            extreme_orders,
            self.sample_matches,
            self.sample_metrics_df
        )
        
        assert isinstance(anomalies, list)
        
        # Check anomaly structure
        for anomaly in anomalies:
            assert isinstance(anomaly, AnomalyDetection)
            assert anomaly.anomaly_id
            assert anomaly.anomaly_type in ['order_spike', 'order_dip', 'unusual_pattern']
            assert anomaly.severity in ['low', 'medium', 'high', 'critical']
            assert anomaly.data_source in ['real', 'mock', 'mixed']
            assert 0 <= anomaly.confidence_score <= 1
            assert isinstance(anomaly.context, dict)
    
    def test_generate_comprehensive_report(self):
        """Test comprehensive report generation."""
        # Create sample correlation results
        correlation_results = [
            CorrelationResult(
                analysis_id="corr_1",
                correlation_coefficient=0.75,
                statistical_significance=0.02,
                time_window="post_match",
                pattern_description="Strong positive correlation",
                data_quality=85.0
            )
        ]
        
        report = self.generator.generate_comprehensive_report(
            self.sample_orders,
            self.sample_matches,
            self.sample_metrics_df,
            correlation_results
        )
        
        assert isinstance(report, InsightReport)
        assert report.report_id
        assert isinstance(report.generation_timestamp, datetime)
        assert isinstance(report.analysis_period, tuple)
        assert len(report.analysis_period) == 2
        assert 0 <= report.data_quality_score <= 100
        assert report.total_matches == len(self.sample_matches)
        assert report.total_orders == len(self.sample_orders)
        assert 0 <= report.real_data_percentage <= 100
        assert isinstance(report.temporal_patterns, list)
        assert isinstance(report.anomalies, list)
        assert isinstance(report.summary_statistics, dict)
        assert isinstance(report.key_insights, list)
        assert isinstance(report.recommendations, list)
    
    def test_calculate_pattern_confidence(self):
        """Test pattern confidence calculation."""
        # Test with different sample sizes
        confidence_1 = self.generator._calculate_pattern_confidence(5, 10)
        confidence_2 = self.generator._calculate_pattern_confidence(10, 10)
        confidence_3 = self.generator._calculate_pattern_confidence(0, 10)
        
        assert 0 <= confidence_1 <= 1
        assert 0 <= confidence_2 <= 1
        assert confidence_3 == 0
        assert confidence_2 > confidence_1  # Higher proportion should give higher confidence
    
    def test_calculate_source_breakdown(self):
        """Test data source breakdown calculation."""
        # Create test DataFrame
        test_df = pd.DataFrame({
            'data_source': ['real', 'real', 'mock', 'real'],
            'other_col': [1, 2, 3, 4]
        })
        
        breakdown = self.generator._calculate_source_breakdown(test_df, 'data_source')
        
        assert isinstance(breakdown, dict)
        assert 'real' in breakdown
        assert 'mock' in breakdown
        assert breakdown['real'] == 75.0  # 3 out of 4
        assert breakdown['mock'] == 25.0  # 1 out of 4
        assert breakdown['real'] + breakdown['mock'] == 100.0
    
    def test_calculate_real_data_percentage(self):
        """Test real data percentage calculation."""
        percentage = self.generator._calculate_real_data_percentage(
            self.sample_orders, 
            self.sample_matches
        )
        
        assert 0 <= percentage <= 100
        
        # With our test data (5 real orders out of 10, 3 real matches out of 5), should be 53.33%
        # Total: 8 real items out of 15 total items = 53.33%
        expected_percentage = 8 / 15 * 100  # 53.33%
        assert abs(percentage - expected_percentage) < 1.0  # Allow small floating point differences
    
    def test_assess_data_completeness(self):
        """Test data completeness assessment."""
        completeness = self.generator._assess_data_completeness(
            self.sample_orders,
            self.sample_matches,
            self.sample_metrics_df
        )
        
        assert 0 <= completeness <= 100
        # Should be high since we have orders, matches, and metrics
        assert completeness >= 75
    
    def test_assess_temporal_coverage(self):
        """Test temporal coverage assessment."""
        coverage = self.generator._assess_temporal_coverage(
            self.sample_orders,
            self.sample_matches
        )
        
        assert isinstance(coverage, dict)
        assert 'coverage_days' in coverage
        assert 'data_density' in coverage
        assert 'gaps' in coverage
        assert coverage['coverage_days'] >= 0
        assert coverage['data_density'] >= 0
    
    def test_error_handling(self):
        """Test error handling in insight generation."""
        # Test with invalid data that should trigger errors
        with patch.object(self.generator, '_analyze_period_patterns', side_effect=Exception("Test error")):
            # Should not raise exception, but return empty list
            patterns = self.generator.analyze_temporal_patterns(
                self.sample_orders,
                self.sample_matches,
                self.sample_metrics_df
            )
            assert isinstance(patterns, list)
    
    def test_empty_data_handling(self):
        """Test handling of empty datasets."""
        # Test with empty data
        empty_patterns = self.generator.analyze_temporal_patterns([], [], pd.DataFrame())
        assert empty_patterns == []
        
        empty_summary = self.generator.generate_summary_statistics([], [], pd.DataFrame())
        assert isinstance(empty_summary, dict)
        assert empty_summary['data_overview']['total_orders'] == 0
        assert empty_summary['data_overview']['total_matches'] == 0
        
        empty_anomalies = self.generator.detect_anomalies_with_source_distinction([], [], pd.DataFrame())
        assert empty_anomalies == []
    
    def test_pizza_type_distribution(self):
        """Test pizza type distribution calculation."""
        distribution = self.generator._get_pizza_type_distribution(self.sample_orders)
        
        assert isinstance(distribution, dict)
        assert 'Pepperoni' in distribution
        assert 'Margherita' in distribution
        assert all(isinstance(count, int) for count in distribution.values())
        assert all(count > 0 for count in distribution.values())
    
    def test_team_performance_summary(self):
        """Test team performance summary calculation."""
        performance = self.generator._get_team_performance_summary(self.sample_matches)
        
        assert isinstance(performance, dict)
        assert 'total_teams' in performance
        assert 'best_performing_team' in performance
        assert 'best_win_rate' in performance
        assert 'average_goals_per_team' in performance
        
        assert performance['total_teams'] > 0
        assert 0 <= performance['best_win_rate'] <= 100


class TestTemporalPattern:
    """Test cases for TemporalPattern dataclass."""
    
    def test_temporal_pattern_creation(self):
        """Test TemporalPattern creation and attributes."""
        pattern = TemporalPattern(
            pattern_id="test_pattern",
            time_period="post_match",
            pattern_type="spike",
            magnitude=75.5,
            confidence=0.85,
            description="Test pattern description",
            data_source_breakdown={'real': 60.0, 'mock': 40.0},
            sample_size=100
        )
        
        assert pattern.pattern_id == "test_pattern"
        assert pattern.time_period == "post_match"
        assert pattern.pattern_type == "spike"
        assert pattern.magnitude == 75.5
        assert pattern.confidence == 0.85
        assert pattern.description == "Test pattern description"
        assert pattern.data_source_breakdown == {'real': 60.0, 'mock': 40.0}
        assert pattern.sample_size == 100


class TestAnomalyDetection:
    """Test cases for AnomalyDetection dataclass."""
    
    def test_anomaly_detection_creation(self):
        """Test AnomalyDetection creation and attributes."""
        anomaly = AnomalyDetection(
            anomaly_id="test_anomaly",
            timestamp=datetime(2024, 1, 1, 12, 0),
            anomaly_type="order_spike",
            severity="high",
            description="Test anomaly description",
            data_source="real",
            confidence_score=0.9,
            context={'order_id': 'test_order', 'value': 500.0}
        )
        
        assert anomaly.anomaly_id == "test_anomaly"
        assert anomaly.timestamp == datetime(2024, 1, 1, 12, 0)
        assert anomaly.anomaly_type == "order_spike"
        assert anomaly.severity == "high"
        assert anomaly.description == "Test anomaly description"
        assert anomaly.data_source == "real"
        assert anomaly.confidence_score == 0.9
        assert anomaly.context == {'order_id': 'test_order', 'value': 500.0}


class TestInsightReport:
    """Test cases for InsightReport dataclass."""
    
    def test_insight_report_creation(self):
        """Test InsightReport creation and attributes."""
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 31)
        
        report = InsightReport(
            report_id="test_report",
            generation_timestamp=datetime(2024, 2, 1),
            analysis_period=(start_time, end_time),
            data_quality_score=85.5,
            total_matches=10,
            total_orders=100,
            real_data_percentage=75.0,
            temporal_patterns=[],
            anomalies=[],
            summary_statistics={},
            key_insights=["Insight 1", "Insight 2"],
            recommendations=["Recommendation 1", "Recommendation 2"]
        )
        
        assert report.report_id == "test_report"
        assert report.generation_timestamp == datetime(2024, 2, 1)
        assert report.analysis_period == (start_time, end_time)
        assert report.data_quality_score == 85.5
        assert report.total_matches == 10
        assert report.total_orders == 100
        assert report.real_data_percentage == 75.0
        assert report.temporal_patterns == []
        assert report.anomalies == []
        assert report.summary_statistics == {}
        assert report.key_insights == ["Insight 1", "Insight 2"]
        assert report.recommendations == ["Recommendation 1", "Recommendation 2"]


if __name__ == "__main__":
    pytest.main([__file__])