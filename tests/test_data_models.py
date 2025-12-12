"""
Tests for data models and validation.
"""
import pytest
from datetime import datetime
from src.models import DominosOrder, FootballMatch, CorrelationResult


class TestDominosOrder:
    """Test cases for DominosOrder data model."""
    
    def test_valid_order_creation(self):
        """Test creating a valid Domino's order."""
        order = DominosOrder(
            order_id="ORD123",
            timestamp=datetime(2024, 1, 15, 18, 30),
            location="123 Main St",
            order_total=25.99,
            pizza_types=["Pepperoni", "Margherita"],
            quantity=2,
            data_source="real"
        )
        
        assert order.order_id == "ORD123"
        assert order.quantity == 2
        assert order.data_source == "real"
    
    def test_order_validation_empty_id(self):
        """Test validation fails for empty order_id."""
        with pytest.raises(ValueError, match="order_id must be a non-empty string"):
            DominosOrder(
                order_id="",
                timestamp=datetime.now(),
                location="123 Main St",
                order_total=25.99,
                pizza_types=["Pepperoni"],
                quantity=1,
                data_source="real"
            )
    
    def test_order_validation_negative_total(self):
        """Test validation fails for negative order total."""
        with pytest.raises(ValueError, match="order_total must be a non-negative number"):
            DominosOrder(
                order_id="ORD123",
                timestamp=datetime.now(),
                location="123 Main St",
                order_total=-5.99,
                pizza_types=["Pepperoni"],
                quantity=1,
                data_source="real"
            )
    
    def test_order_json_serialization(self):
        """Test JSON serialization and deserialization."""
        order = DominosOrder(
            order_id="ORD123",
            timestamp=datetime(2024, 1, 15, 18, 30),
            location="123 Main St",
            order_total=25.99,
            pizza_types=["Pepperoni"],
            quantity=1,
            data_source="mock"
        )
        
        json_str = order.to_json()
        restored_order = DominosOrder.from_json(json_str)
        
        assert restored_order.order_id == order.order_id
        assert restored_order.timestamp == order.timestamp
        assert restored_order.data_source == order.data_source


class TestFootballMatch:
    """Test cases for FootballMatch data model."""
    
    def test_valid_match_creation(self):
        """Test creating a valid football match."""
        match = FootballMatch(
            match_id="MATCH123",
            timestamp=datetime(2024, 1, 15, 15, 0),
            home_team="Arsenal",
            away_team="Chelsea",
            home_score=2,
            away_score=1,
            event_type="win",
            match_significance="regular",
            data_source="real"
        )
        
        assert match.match_id == "MATCH123"
        assert match.home_team == "Arsenal"
        assert match.get_winner() == "home"
    
    def test_match_validation_same_teams(self):
        """Test validation fails when home and away teams are the same."""
        with pytest.raises(ValueError, match="home_team and away_team must be different"):
            FootballMatch(
                match_id="MATCH123",
                timestamp=datetime.now(),
                home_team="Arsenal",
                away_team="Arsenal",
                home_score=2,
                away_score=1,
                event_type="win",
                match_significance="regular",
                data_source="real"
            )
    
    def test_match_validation_inconsistent_event_type(self):
        """Test validation fails for inconsistent event_type and scores."""
        with pytest.raises(ValueError, match="event_type 'draw' requires equal home and away scores"):
            FootballMatch(
                match_id="MATCH123",
                timestamp=datetime.now(),
                home_team="Arsenal",
                away_team="Chelsea",
                home_score=2,
                away_score=1,
                event_type="draw",
                match_significance="regular",
                data_source="real"
            )
    
    def test_match_csv_serialization(self):
        """Test CSV serialization and deserialization."""
        match = FootballMatch(
            match_id="MATCH123",
            timestamp=datetime(2024, 1, 15, 15, 0),
            home_team="Arsenal",
            away_team="Chelsea",
            home_score=1,
            away_score=1,
            event_type="draw",
            match_significance="tournament",
            data_source="mock"
        )
        
        csv_row = match.to_csv_row()
        restored_match = FootballMatch.from_csv_row(csv_row)
        
        assert restored_match.match_id == match.match_id
        assert restored_match.home_team == match.home_team
        assert restored_match.event_type == match.event_type


class TestCorrelationResult:
    """Test cases for CorrelationResult data model."""
    
    def test_valid_result_creation(self):
        """Test creating a valid correlation result."""
        result = CorrelationResult(
            analysis_id="ANALYSIS123",
            correlation_coefficient=0.75,
            statistical_significance=0.02,
            time_window="post_match",
            pattern_description="Strong positive correlation between wins and order spikes",
            data_quality=85.5
        )
        
        assert result.analysis_id == "ANALYSIS123"
        assert result.is_significant()
        assert result.get_strength_description() == "very strong"
        assert result.get_direction_description() == "positive"
    
    def test_result_validation_invalid_correlation(self):
        """Test validation fails for correlation coefficient outside [-1, 1]."""
        with pytest.raises(ValueError, match="correlation_coefficient must be between -1 and 1"):
            CorrelationResult(
                analysis_id="ANALYSIS123",
                correlation_coefficient=1.5,
                statistical_significance=0.02,
                time_window="post_match",
                pattern_description="Invalid correlation",
                data_quality=85.5
            )
    
    def test_result_validation_invalid_significance(self):
        """Test validation fails for statistical significance outside [0, 1]."""
        with pytest.raises(ValueError, match="statistical_significance must be between 0 and 1"):
            CorrelationResult(
                analysis_id="ANALYSIS123",
                correlation_coefficient=0.75,
                statistical_significance=1.5,
                time_window="post_match",
                pattern_description="Invalid significance",
                data_quality=85.5
            )
    
    def test_result_strength_descriptions(self):
        """Test correlation strength descriptions."""
        # Test negligible correlation
        result = CorrelationResult(
            analysis_id="TEST1",
            correlation_coefficient=0.05,
            statistical_significance=0.5,
            time_window="pre_match",
            pattern_description="Test",
            data_quality=100.0
        )
        assert result.get_strength_description() == "negligible"
        
        # Test very strong correlation
        result.correlation_coefficient = -0.85
        assert result.get_strength_description() == "very strong"
        assert result.get_direction_description() == "negative"