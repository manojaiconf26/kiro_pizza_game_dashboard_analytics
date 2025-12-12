"""
Football match data model with validation methods.
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, List
import json
import csv
from io import StringIO


@dataclass
class FootballMatch:
    """
    Data model for football matches with validation methods.
    
    Attributes:
        match_id: Unique identifier for the match
        timestamp: When the match occurred
        home_team: Name of the home team
        away_team: Name of the away team
        home_score: Final score for home team
        away_score: Final score for away team
        event_type: Type of event ('goal', 'win', 'loss', 'draw')
        match_significance: Significance level ('regular', 'tournament', 'final')
        data_source: Source of data ('real' or 'mock')
    """
    match_id: str
    timestamp: datetime
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    event_type: str
    match_significance: str
    data_source: str

    def __post_init__(self):
        """Validate the match data after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate all fields of the football match.
        
        Raises:
            ValueError: If any field contains invalid data
        """
        if not self.match_id or not isinstance(self.match_id, str):
            raise ValueError("match_id must be a non-empty string")
        
        if not isinstance(self.timestamp, datetime):
            raise ValueError("timestamp must be a datetime object")
        
        if not self.home_team or not isinstance(self.home_team, str):
            raise ValueError("home_team must be a non-empty string")
        
        if not self.away_team or not isinstance(self.away_team, str):
            raise ValueError("away_team must be a non-empty string")
        
        if self.home_team == self.away_team:
            raise ValueError("home_team and away_team must be different")
        
        if not isinstance(self.home_score, int) or self.home_score < 0:
            raise ValueError("home_score must be a non-negative integer")
        
        if not isinstance(self.away_score, int) or self.away_score < 0:
            raise ValueError("away_score must be a non-negative integer")
        
        valid_event_types = ['goal', 'win', 'loss', 'draw']
        if self.event_type not in valid_event_types:
            raise ValueError(f"event_type must be one of {valid_event_types}")
        
        valid_significance = ['regular', 'tournament', 'final']
        if self.match_significance not in valid_significance:
            raise ValueError(f"match_significance must be one of {valid_significance}")
        
        if self.data_source not in ['real', 'mock']:
            raise ValueError("data_source must be either 'real' or 'mock'")
        
        # Validate event_type consistency with scores
        if self.event_type == 'draw' and self.home_score != self.away_score:
            raise ValueError("event_type 'draw' requires equal home and away scores")
        
        if self.event_type == 'win' and self.home_score <= self.away_score:
            raise ValueError("event_type 'win' requires home_score > away_score")
        
        if self.event_type == 'loss' and self.home_score >= self.away_score:
            raise ValueError("event_type 'loss' requires home_score < away_score")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the match to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the match
        """
        data = asdict(self)
        # Convert datetime to ISO format string for JSON serialization
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FootballMatch':
        """
        Create a FootballMatch from a dictionary.
        
        Args:
            data: Dictionary containing match data
            
        Returns:
            FootballMatch instance
        """
        # Convert timestamp string back to datetime
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return cls(**data)

    def to_json(self) -> str:
        """
        Serialize the match to JSON format.
        
        Returns:
            JSON string representation of the match
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'FootballMatch':
        """
        Create a FootballMatch from a JSON string.
        
        Args:
            json_str: JSON string containing match data
            
        Returns:
            FootballMatch instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_csv_row(self) -> List[str]:
        """
        Convert the match to a CSV row format.
        
        Returns:
            List of strings representing CSV row values
        """
        return [
            self.match_id,
            self.timestamp.isoformat(),
            self.home_team,
            self.away_team,
            str(self.home_score),
            str(self.away_score),
            self.event_type,
            self.match_significance,
            self.data_source
        ]

    @classmethod
    def csv_headers(cls) -> List[str]:
        """
        Get the CSV headers for FootballMatch.
        
        Returns:
            List of CSV header names
        """
        return [
            'match_id',
            'timestamp',
            'home_team',
            'away_team',
            'home_score',
            'away_score',
            'event_type',
            'match_significance',
            'data_source'
        ]

    @classmethod
    def from_csv_row(cls, row: List[str]) -> 'FootballMatch':
        """
        Create a FootballMatch from a CSV row.
        
        Args:
            row: List of strings representing CSV row values
            
        Returns:
            FootballMatch instance
        """
        if len(row) != 9:
            raise ValueError(f"Expected 9 CSV columns, got {len(row)}")
        
        return cls(
            match_id=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            home_team=row[2],
            away_team=row[3],
            home_score=int(row[4]),
            away_score=int(row[5]),
            event_type=row[6],
            match_significance=row[7],
            data_source=row[8]
        )

    def get_winner(self) -> str:
        """
        Determine the winner of the match.
        
        Returns:
            'home', 'away', or 'draw'
        """
        if self.home_score > self.away_score:
            return 'home'
        elif self.away_score > self.home_score:
            return 'away'
        else:
            return 'draw'

    def is_high_scoring(self, threshold: int = 3) -> bool:
        """
        Check if the match is high-scoring based on total goals.
        
        Args:
            threshold: Minimum total goals to be considered high-scoring
            
        Returns:
            True if total goals >= threshold
        """
        return (self.home_score + self.away_score) >= threshold


def matches_to_csv(matches: List[FootballMatch]) -> str:
    """
    Convert a list of FootballMatch objects to CSV format.
    
    Args:
        matches: List of FootballMatch objects
        
    Returns:
        CSV string representation
    """
    if not matches:
        return ""
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(FootballMatch.csv_headers())
    
    # Write data rows
    for match in matches:
        writer.writerow(match.to_csv_row())
    
    return output.getvalue()


def matches_from_csv(csv_str: str) -> List[FootballMatch]:
    """
    Create a list of FootballMatch objects from CSV format.
    
    Args:
        csv_str: CSV string containing match data
        
    Returns:
        List of FootballMatch objects
    """
    if not csv_str.strip():
        return []
    
    input_stream = StringIO(csv_str)
    reader = csv.reader(input_stream)
    
    # Skip headers
    next(reader, None)
    
    matches = []
    for row in reader:
        if row:  # Skip empty rows
            matches.append(FootballMatch.from_csv_row(row))
    
    return matches