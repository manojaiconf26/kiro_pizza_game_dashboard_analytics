"""
Tests for data model serialization functionality.
"""
import pytest
from datetime import datetime
from src.models import (
    DominosOrder, FootballMatch, CorrelationResult,
    orders_to_csv, orders_from_csv,
    matches_to_csv, matches_from_csv,
    results_to_csv, results_from_csv
)


class TestSerializationRoundTrip:
    """Test serialization round-trip functionality."""
    
    def test_dominos_order_csv_round_trip(self):
        """Test CSV serialization round-trip for DominosOrder."""
        orders = [
            DominosOrder(
                order_id="ORD001",
                timestamp=datetime(2024, 1, 15, 18, 30),
                location="123 Main St",
                order_total=25.99,
                pizza_types=["Pepperoni", "Margherita"],
                quantity=2,
                data_source="real"
            ),
            DominosOrder(
                order_id="ORD002",
                timestamp=datetime(2024, 1, 15, 19, 0),
                location="456 Oak Ave",
                order_total=18.50,
                pizza_types=["Hawaiian"],
                quantity=1,
                data_source="mock"
            )
        ]
        
        # Convert to CSV and back
        csv_str = orders_to_csv(orders)
        restored_orders = orders_from_csv(csv_str)
        
        assert len(restored_orders) == 2
        assert restored_orders[0].order_id == "ORD001"
        assert restored_orders[0].pizza_types == ["Pepperoni", "Margherita"]
        assert restored_orders[1].data_source == "mock"
    
    def test_football_match_csv_round_trip(self):
        """Test CSV serialization round-trip for FootballMatch."""
        matches = [
            FootballMatch(
                match_id="MATCH001",
                timestamp=datetime(2024, 1, 15, 15, 0),
                home_team="Arsenal",
                away_team="Chelsea",
                home_score=2,
                away_score=1,
                event_type="win",
                match_significance="regular",
                data_source="real"
            )
        ]
        
        # Convert to CSV and back
        csv_str = matches_to_csv(matches)
        restored_matches = matches_from_csv(csv_str)
        
        assert len(restored_matches) == 1
        assert restored_matches[0].match_id == "MATCH001"
        assert restored_matches[0].home_team == "Arsenal"
        assert restored_matches[0].event_type == "win"
    
    def test_correlation_result_json_round_trip(self):
        """Test JSON serialization round-trip for CorrelationResult."""
        result = CorrelationResult(
            analysis_id="ANALYSIS001",
            correlation_coefficient=0.65,
            statistical_significance=0.03,
            time_window="post_match",
            pattern_description="Moderate positive correlation",
            data_quality=92.5,
            sample_size=150
        )
        
        # Convert to JSON and back
        json_str = result.to_json()
        restored_result = CorrelationResult.from_json(json_str)
        
        assert restored_result.analysis_id == "ANALYSIS001"
        assert restored_result.correlation_coefficient == 0.65
        assert restored_result.sample_size == 150
    
    def test_empty_csv_handling(self):
        """Test handling of empty CSV strings."""
        assert orders_from_csv("") == []
        assert matches_from_csv("") == []
        assert results_from_csv("") == []
        
        assert orders_to_csv([]) == ""
        assert matches_to_csv([]) == ""
        assert results_to_csv([]) == ""
    
    def test_csv_with_special_characters(self):
        """Test CSV handling with special characters in data."""
        order = DominosOrder(
            order_id="ORD,123",  # Comma in ID
            timestamp=datetime(2024, 1, 15, 18, 30),
            location="123 Main St, Apt 2",  # Comma in location
            order_total=25.99,
            pizza_types=["Pepperoni", "Meat Lovers"],
            quantity=2,
            data_source="real"
        )
        
        csv_str = orders_to_csv([order])
        restored_orders = orders_from_csv(csv_str)
        
        assert len(restored_orders) == 1
        assert restored_orders[0].order_id == "ORD,123"
        assert restored_orders[0].location == "123 Main St, Apt 2"