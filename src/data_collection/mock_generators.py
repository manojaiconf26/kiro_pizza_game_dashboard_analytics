"""
Mock data generators for pizza orders and football matches.

This module provides realistic mock data generation for both Domino's pizza orders
and football matches, with temporal alignment capabilities to create meaningful
correlations for analysis.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import math

from ..models.pizza_order import DominosOrder
from ..models.football_match import FootballMatch


@dataclass
class GeneratorConfig:
    """Configuration parameters for mock data generation."""
    
    # Time range parameters
    start_date: datetime
    end_date: datetime
    
    # Pizza order parameters
    base_orders_per_day: int = 150
    order_variance: float = 0.3  # 30% variance in daily orders
    match_day_multiplier: float = 1.8  # 80% increase on match days
    post_win_multiplier: float = 2.2  # 120% increase after wins
    
    # Football match parameters
    matches_per_week: int = 3
    tournament_probability: float = 0.15  # 15% chance of tournament matches
    final_probability: float = 0.05  # 5% chance of finals
    
    # Location parameters
    locations: List[str] = None
    
    def __post_init__(self):
        """Set default locations if not provided."""
        if self.locations is None:
            self.locations = [
                "Manchester City Centre",
                "Liverpool Downtown", 
                "London Bridge",
                "Birmingham Central",
                "Leeds City",
                "Newcastle Upon Tyne",
                "Sheffield Center",
                "Bristol Downtown",
                "Cardiff Bay",
                "Edinburgh Old Town"
            ]


class MockDataGenerator:
    """
    Generates realistic mock data for pizza orders and football matches
    with temporal alignment for correlation analysis.
    """
    
    # Common pizza types with realistic frequency weights
    PIZZA_TYPES = [
        ("Margherita", 0.25),
        ("Pepperoni", 0.20),
        ("Hawaiian", 0.15),
        ("Meat Feast", 0.12),
        ("Vegetarian Supreme", 0.10),
        ("BBQ Chicken", 0.08),
        ("Four Cheese", 0.05),
        ("Spicy Italian", 0.03),
        ("Seafood Special", 0.02)
    ]
    
    # Premier League teams for realistic match generation
    FOOTBALL_TEAMS = [
        "Manchester United", "Manchester City", "Liverpool", "Chelsea",
        "Arsenal", "Tottenham", "Newcastle", "Brighton", "Aston Villa",
        "West Ham", "Crystal Palace", "Fulham", "Wolves", "Everton",
        "Brentford", "Nottingham Forest", "Leeds United", "Leicester City",
        "Southampton", "Bournemouth"
    ]
    
    def __init__(self, config: GeneratorConfig):
        """
        Initialize the mock data generator with configuration.
        
        Args:
            config: Configuration parameters for data generation
        """
        self.config = config
        self.random = random.Random(42)  # Fixed seed for reproducible results
        
    def generate_pizza_orders(self, 
                            num_days: Optional[int] = None,
                            base_volume: Optional[int] = None) -> List[DominosOrder]:
        """
        Generate realistic Domino's pizza orders with statistical distributions.
        
        Args:
            num_days: Number of days to generate data for (overrides config date range)
            base_volume: Base orders per day (overrides config)
            
        Returns:
            List of DominosOrder objects with realistic patterns
        """
        if num_days is not None:
            end_date = self.config.start_date + timedelta(days=num_days)
        else:
            end_date = self.config.end_date
            
        if base_volume is not None:
            daily_base = base_volume
        else:
            daily_base = self.config.base_orders_per_day
            
        orders = []
        current_date = self.config.start_date
        
        while current_date < end_date:
            # Calculate daily order volume with realistic patterns
            daily_orders = self._calculate_daily_order_volume(current_date, daily_base)
            
            # Generate orders for this day
            day_orders = self._generate_orders_for_day(current_date, daily_orders)
            orders.extend(day_orders)
            
            current_date += timedelta(days=1)
            
        return orders
    
    def generate_football_matches(self, num_games: Optional[int] = None) -> List[FootballMatch]:
        """
        Generate realistic football matches with scores and timing.
        
        Args:
            num_games: Number of games to generate (overrides config calculation)
            
        Returns:
            List of FootballMatch objects with realistic patterns
        """
        if num_games is not None:
            total_matches = num_games
        else:
            # Calculate matches based on date range and weekly frequency
            days = (self.config.end_date - self.config.start_date).days
            weeks = days / 7
            total_matches = int(weeks * self.config.matches_per_week)
            
        matches = []
        current_date = self.config.start_date
        
        for i in range(total_matches):
            # Spread matches across the date range
            days_offset = (i / total_matches) * (self.config.end_date - self.config.start_date).days
            match_date = current_date + timedelta(days=days_offset)
            
            # Adjust to realistic match times (weekends, evenings)
            match_date = self._adjust_to_realistic_match_time(match_date)
            
            match = self._generate_single_match(match_date, f"MATCH_{i+1:04d}")
            matches.append(match)
            
        # Sort matches by timestamp
        matches.sort(key=lambda m: m.timestamp)
        return matches
    
    def correlate_data_timing(self, 
                            orders: List[DominosOrder], 
                            matches: List[FootballMatch]) -> Tuple[List[DominosOrder], List[FootballMatch]]:
        """
        Ensure temporal alignment between pizza orders and match events for meaningful correlation.
        
        Args:
            orders: List of pizza orders
            matches: List of football matches
            
        Returns:
            Tuple of (aligned_orders, aligned_matches) with temporal correlation
        """
        if not matches:
            return orders, matches
            
        # Create a map of match dates to match outcomes
        match_effects = {}
        for match in matches:
            match_date = match.timestamp.date()
            
            # Determine the effect this match should have on orders
            effect_multiplier = 1.0
            
            if match.event_type == 'win':
                effect_multiplier = self.config.post_win_multiplier
            elif match.event_type == 'draw':
                effect_multiplier = 1.3  # Moderate increase for draws
            else:  # loss
                effect_multiplier = 0.8  # Slight decrease for losses
                
            # Tournament and final matches have stronger effects
            if match.match_significance == 'final':
                effect_multiplier *= 1.5
            elif match.match_significance == 'tournament':
                effect_multiplier *= 1.2
                
            match_effects[match_date] = effect_multiplier
        
        # Adjust order volumes based on match effects
        aligned_orders = []
        for order in orders:
            order_date = order.timestamp.date()
            
            # Check for match effects on this date and the day after
            effect_multiplier = 1.0
            
            # Same day effect (during/after match)
            if order_date in match_effects:
                effect_multiplier = match_effects[order_date]
            
            # Next day effect (celebration/disappointment orders)
            prev_date = order_date - timedelta(days=1)
            if prev_date in match_effects:
                next_day_effect = match_effects[prev_date] * 0.6  # Reduced effect next day
                effect_multiplier = max(effect_multiplier, next_day_effect)
            
            # Randomly decide whether to include this order based on effect
            if self.random.random() < effect_multiplier:
                aligned_orders.append(order)
                
                # For high-effect periods, potentially add extra orders
                if effect_multiplier > 1.5 and self.random.random() < 0.3:
                    # Create additional order with slight time variation
                    extra_order = self._create_similar_order(order)
                    aligned_orders.append(extra_order)
        
        return aligned_orders, matches
    
    def _calculate_daily_order_volume(self, date: datetime, base_volume: int) -> int:
        """Calculate realistic daily order volume with patterns."""
        volume = base_volume
        
        # Weekend boost (Friday-Sunday)
        if date.weekday() >= 4:  # Friday = 4, Saturday = 5, Sunday = 6
            volume *= 1.4
        
        # Evening hours boost (simulated through daily variance)
        daily_variance = self.random.gauss(1.0, self.config.order_variance)
        volume = int(volume * max(0.3, daily_variance))  # Minimum 30% of base
        
        return volume
    
    def _generate_orders_for_day(self, date: datetime, num_orders: int) -> List[DominosOrder]:
        """Generate orders for a specific day with realistic timing patterns."""
        orders = []
        
        for i in range(num_orders):
            # Generate realistic order time (peak hours: 12-14, 18-22)
            hour = self._generate_realistic_order_hour()
            minute = self.random.randint(0, 59)
            second = self.random.randint(0, 59)
            
            order_time = date.replace(hour=hour, minute=minute, second=second)
            
            # Generate order details
            order = DominosOrder(
                order_id=f"DOM_{date.strftime('%Y%m%d')}_{i+1:04d}",
                timestamp=order_time,
                location=self.random.choice(self.config.locations),
                order_total=self._generate_realistic_order_total(),
                pizza_types=self._generate_pizza_selection(),
                quantity=self._generate_order_quantity(),
                data_source='mock'
            )
            
            orders.append(order)
        
        return orders
    
    def _generate_realistic_order_hour(self) -> int:
        """Generate realistic order hours with peak time distributions."""
        # Define peak hours with weights
        hour_weights = {
            11: 0.05, 12: 0.12, 13: 0.15, 14: 0.08,  # Lunch peak
            17: 0.08, 18: 0.15, 19: 0.20, 20: 0.12, 21: 0.05  # Dinner peak
        }
        
        # Fill in other hours with low weights
        for hour in range(24):
            if hour not in hour_weights:
                if 6 <= hour <= 10 or 15 <= hour <= 16 or 22 <= hour <= 23:
                    hour_weights[hour] = 0.02  # Low activity
                else:
                    hour_weights[hour] = 0.005  # Very low activity (night)
        
        # Weighted random selection
        hours = list(hour_weights.keys())
        weights = list(hour_weights.values())
        return self.random.choices(hours, weights=weights)[0]
    
    def _generate_realistic_order_total(self) -> float:
        """Generate realistic order totals with proper distribution."""
        # Log-normal distribution for order totals (realistic for food orders)
        base_price = self.random.lognormvariate(2.8, 0.4)  # Mean ~£16, std ~£7
        return round(max(8.99, min(45.99, base_price)), 2)  # Clamp to realistic range
    
    def _generate_pizza_selection(self) -> List[str]:
        """Generate realistic pizza type selection."""
        num_pizzas = self.random.choices([1, 2, 3, 4], weights=[0.6, 0.25, 0.12, 0.03])[0]
        
        selected_pizzas = []
        pizza_types = [pizza for pizza, _ in self.PIZZA_TYPES]
        weights = [weight for _, weight in self.PIZZA_TYPES]
        
        for _ in range(num_pizzas):
            pizza = self.random.choices(pizza_types, weights=weights)[0]
            if pizza not in selected_pizzas:  # Avoid duplicates
                selected_pizzas.append(pizza)
        
        return selected_pizzas if selected_pizzas else ["Margherita"]  # Fallback
    
    def _generate_order_quantity(self) -> int:
        """Generate realistic order quantities."""
        return self.random.choices([1, 2, 3, 4, 5], weights=[0.5, 0.25, 0.15, 0.07, 0.03])[0]
    
    def _adjust_to_realistic_match_time(self, date: datetime) -> datetime:
        """Adjust match date to realistic match times (weekends, evenings)."""
        # Move to weekend if it's a weekday (80% chance)
        if date.weekday() < 5 and self.random.random() < 0.8:  # Monday-Friday
            # Move to next Saturday or Sunday
            days_to_weekend = 5 - date.weekday()  # Days to Saturday
            if self.random.random() < 0.6:  # 60% Saturday, 40% Sunday
                date += timedelta(days=days_to_weekend)
            else:
                date += timedelta(days=days_to_weekend + 1)
        
        # Set realistic match times
        if date.weekday() == 5:  # Saturday
            hour = self.random.choice([12, 15, 17])  # 12:30, 15:00, 17:30
        elif date.weekday() == 6:  # Sunday
            hour = self.random.choice([14, 16])  # 14:00, 16:30
        else:  # Weekday evening matches
            hour = self.random.choice([19, 20])  # 19:45, 20:00
        
        minute = self.random.choice([0, 15, 30, 45])
        return date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    def _generate_single_match(self, match_date: datetime, match_id: str) -> FootballMatch:
        """Generate a single realistic football match."""
        # Select teams (ensure they're different)
        teams = self.random.sample(self.FOOTBALL_TEAMS, 2)
        home_team, away_team = teams[0], teams[1]
        
        # Generate realistic scores
        home_score, away_score = self._generate_realistic_scores()
        
        # Determine event type based on scores
        if home_score > away_score:
            event_type = 'win'
        elif away_score > home_score:
            event_type = 'loss'
        else:
            event_type = 'draw'
        
        # Determine match significance
        significance_rand = self.random.random()
        if significance_rand < self.config.final_probability:
            match_significance = 'final'
        elif significance_rand < self.config.tournament_probability:
            match_significance = 'tournament'
        else:
            match_significance = 'regular'
        
        return FootballMatch(
            match_id=match_id,
            timestamp=match_date,
            home_team=home_team,
            away_team=away_team,
            home_score=home_score,
            away_score=away_score,
            event_type=event_type,
            match_significance=match_significance,
            data_source='mock'
        )
    
    def _generate_realistic_scores(self) -> Tuple[int, int]:
        """Generate realistic football scores based on real-world distributions."""
        # Common football score patterns
        score_patterns = [
            (0, 0, 0.08), (1, 0, 0.12), (0, 1, 0.12), (1, 1, 0.15),
            (2, 0, 0.10), (0, 2, 0.10), (2, 1, 0.12), (1, 2, 0.12),
            (3, 0, 0.05), (0, 3, 0.05), (2, 2, 0.06), (3, 1, 0.04),
            (1, 3, 0.04), (3, 2, 0.02), (2, 3, 0.02), (4, 0, 0.01)
        ]
        
        # Weighted random selection
        scores = [(home, away) for home, away, _ in score_patterns]
        weights = [weight for _, _, weight in score_patterns]
        
        return self.random.choices(scores, weights=weights)[0]
    
    def _create_similar_order(self, original_order: DominosOrder) -> DominosOrder:
        """Create a similar order for high-activity periods."""
        # Slight time variation (within 30 minutes)
        time_offset = timedelta(minutes=self.random.randint(-30, 30))
        new_time = original_order.timestamp + time_offset
        
        return DominosOrder(
            order_id=f"{original_order.order_id}_EXTRA_{self.random.randint(1000, 9999)}",
            timestamp=new_time,
            location=original_order.location,  # Same location for correlation
            order_total=self._generate_realistic_order_total(),
            pizza_types=self._generate_pizza_selection(),
            quantity=self._generate_order_quantity(),
            data_source='mock'
        )


def create_default_config(start_date: datetime, 
                         end_date: datetime,
                         **kwargs) -> GeneratorConfig:
    """
    Create a default generator configuration with sensible defaults.
    
    Args:
        start_date: Start date for data generation
        end_date: End date for data generation
        **kwargs: Additional configuration parameters to override defaults
        
    Returns:
        GeneratorConfig with specified parameters
    """
    config_params = {
        'start_date': start_date,
        'end_date': end_date
    }
    config_params.update(kwargs)
    
    return GeneratorConfig(**config_params)


def generate_correlated_dataset(start_date: datetime,
                              end_date: datetime,
                              **config_kwargs) -> Tuple[List[DominosOrder], List[FootballMatch]]:
    """
    Generate a complete correlated dataset of pizza orders and football matches.
    
    Args:
        start_date: Start date for data generation
        end_date: End date for data generation
        **config_kwargs: Additional configuration parameters
        
    Returns:
        Tuple of (pizza_orders, football_matches) with temporal correlation
    """
    config = create_default_config(start_date, end_date, **config_kwargs)
    generator = MockDataGenerator(config)
    
    # Generate base data
    matches = generator.generate_football_matches()
    orders = generator.generate_pizza_orders()
    
    # Apply temporal correlation
    correlated_orders, correlated_matches = generator.correlate_data_timing(orders, matches)
    
    return correlated_orders, correlated_matches