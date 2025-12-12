"""
Correlation analysis result data model with validation methods.
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import csv
from io import StringIO


@dataclass
class CorrelationResult:
    """
    Data model for correlation analysis results with validation methods.
    
    Attributes:
        analysis_id: Unique identifier for the analysis
        correlation_coefficient: Correlation coefficient between -1 and 1
        statistical_significance: P-value or significance level (0-1)
        time_window: Analysis time window ('pre_match', 'during_match', 'post_match')
        pattern_description: Human-readable description of the pattern
        data_quality: Percentage of real vs mock data used (0-100)
        analysis_timestamp: When the analysis was performed
        sample_size: Number of data points used in analysis
    """
    analysis_id: str
    correlation_coefficient: float
    statistical_significance: float
    time_window: str
    pattern_description: str
    data_quality: float
    analysis_timestamp: Optional[datetime] = None
    sample_size: Optional[int] = None

    def __post_init__(self):
        """Set default values and validate the analysis result after initialization."""
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.now()
        self.validate()

    def validate(self) -> None:
        """
        Validate all fields of the correlation result.
        
        Raises:
            ValueError: If any field contains invalid data
        """
        if not self.analysis_id or not isinstance(self.analysis_id, str):
            raise ValueError("analysis_id must be a non-empty string")
        
        if not isinstance(self.correlation_coefficient, (int, float)):
            raise ValueError("correlation_coefficient must be a number")
        
        if not (-1.0 <= self.correlation_coefficient <= 1.0):
            raise ValueError("correlation_coefficient must be between -1 and 1")
        
        if not isinstance(self.statistical_significance, (int, float)):
            raise ValueError("statistical_significance must be a number")
        
        if not (0.0 <= self.statistical_significance <= 1.0):
            raise ValueError("statistical_significance must be between 0 and 1")
        
        valid_time_windows = ['pre_match', 'during_match', 'post_match', 'full_match', 'pre_to_post_match', 'during_to_post_match']
        if self.time_window not in valid_time_windows:
            raise ValueError(f"time_window must be one of {valid_time_windows}")
        
        if not self.pattern_description or not isinstance(self.pattern_description, str):
            raise ValueError("pattern_description must be a non-empty string")
        
        if not isinstance(self.data_quality, (int, float)):
            raise ValueError("data_quality must be a number")
        
        if not (0.0 <= self.data_quality <= 100.0):
            raise ValueError("data_quality must be between 0 and 100")
        
        if self.analysis_timestamp is not None and not isinstance(self.analysis_timestamp, datetime):
            raise ValueError("analysis_timestamp must be a datetime object or None")
        
        if self.sample_size is not None and (not isinstance(self.sample_size, int) or self.sample_size < 0):
            raise ValueError("sample_size must be a non-negative integer or None")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the correlation result to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the correlation result
        """
        data = asdict(self)
        # Convert datetime to ISO format string for JSON serialization
        if self.analysis_timestamp:
            data['analysis_timestamp'] = self.analysis_timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CorrelationResult':
        """
        Create a CorrelationResult from a dictionary.
        
        Args:
            data: Dictionary containing correlation result data
            
        Returns:
            CorrelationResult instance
        """
        # Convert timestamp string back to datetime
        if data.get('analysis_timestamp') and isinstance(data['analysis_timestamp'], str):
            data['analysis_timestamp'] = datetime.fromisoformat(data['analysis_timestamp'])
        
        return cls(**data)

    def to_json(self) -> str:
        """
        Serialize the correlation result to JSON format.
        
        Returns:
            JSON string representation of the correlation result
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'CorrelationResult':
        """
        Create a CorrelationResult from a JSON string.
        
        Args:
            json_str: JSON string containing correlation result data
            
        Returns:
            CorrelationResult instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_csv_row(self) -> List[str]:
        """
        Convert the correlation result to a CSV row format.
        
        Returns:
            List of strings representing CSV row values
        """
        return [
            self.analysis_id,
            str(self.correlation_coefficient),
            str(self.statistical_significance),
            self.time_window,
            self.pattern_description,
            str(self.data_quality),
            self.analysis_timestamp.isoformat() if self.analysis_timestamp else '',
            str(self.sample_size) if self.sample_size is not None else ''
        ]

    @classmethod
    def csv_headers(cls) -> List[str]:
        """
        Get the CSV headers for CorrelationResult.
        
        Returns:
            List of CSV header names
        """
        return [
            'analysis_id',
            'correlation_coefficient',
            'statistical_significance',
            'time_window',
            'pattern_description',
            'data_quality',
            'analysis_timestamp',
            'sample_size'
        ]

    @classmethod
    def from_csv_row(cls, row: List[str]) -> 'CorrelationResult':
        """
        Create a CorrelationResult from a CSV row.
        
        Args:
            row: List of strings representing CSV row values
            
        Returns:
            CorrelationResult instance
        """
        if len(row) != 8:
            raise ValueError(f"Expected 8 CSV columns, got {len(row)}")
        
        # Handle optional fields
        analysis_timestamp = datetime.fromisoformat(row[6]) if row[6] else None
        sample_size = int(row[7]) if row[7] else None
        
        return cls(
            analysis_id=row[0],
            correlation_coefficient=float(row[1]),
            statistical_significance=float(row[2]),
            time_window=row[3],
            pattern_description=row[4],
            data_quality=float(row[5]),
            analysis_timestamp=analysis_timestamp,
            sample_size=sample_size
        )

    def is_significant(self, alpha: float = 0.05) -> bool:
        """
        Check if the correlation is statistically significant.
        
        Args:
            alpha: Significance level threshold (default 0.05)
            
        Returns:
            True if p-value < alpha
        """
        return self.statistical_significance < alpha

    def get_strength_description(self) -> str:
        """
        Get a human-readable description of correlation strength.
        
        Returns:
            String describing correlation strength
        """
        abs_corr = abs(self.correlation_coefficient)
        
        if abs_corr < 0.1:
            return "negligible"
        elif abs_corr < 0.3:
            return "weak"
        elif abs_corr < 0.5:
            return "moderate"
        elif abs_corr < 0.7:
            return "strong"
        else:
            return "very strong"

    def get_direction_description(self) -> str:
        """
        Get a human-readable description of correlation direction.
        
        Returns:
            String describing correlation direction
        """
        if self.correlation_coefficient > 0:
            return "positive"
        elif self.correlation_coefficient < 0:
            return "negative"
        else:
            return "no correlation"


def results_to_csv(results: List[CorrelationResult]) -> str:
    """
    Convert a list of CorrelationResult objects to CSV format.
    
    Args:
        results: List of CorrelationResult objects
        
    Returns:
        CSV string representation
    """
    if not results:
        return ""
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(CorrelationResult.csv_headers())
    
    # Write data rows
    for result in results:
        writer.writerow(result.to_csv_row())
    
    return output.getvalue()


def results_from_csv(csv_str: str) -> List[CorrelationResult]:
    """
    Create a list of CorrelationResult objects from CSV format.
    
    Args:
        csv_str: CSV string containing correlation result data
        
    Returns:
        List of CorrelationResult objects
    """
    if not csv_str.strip():
        return []
    
    input_stream = StringIO(csv_str)
    reader = csv.reader(input_stream)
    
    # Skip headers
    next(reader, None)
    
    results = []
    for row in reader:
        if row:  # Skip empty rows
            results.append(CorrelationResult.from_csv_row(row))
    
    return results