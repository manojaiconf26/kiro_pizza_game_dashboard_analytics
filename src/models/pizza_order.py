"""
Pizza order data model with validation methods.
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any
import json
import csv
from io import StringIO


@dataclass
class DominosOrder:
    """
    Data model for Domino's pizza orders with validation methods.
    
    Attributes:
        order_id: Unique identifier for the order
        timestamp: When the order was placed
        location: Store location or delivery address
        order_total: Total cost of the order
        pizza_types: List of pizza types ordered
        quantity: Total number of pizzas ordered
        data_source: Source of data ('real' or 'mock')
    """
    order_id: str
    timestamp: datetime
    location: str
    order_total: float
    pizza_types: List[str]
    quantity: int
    data_source: str

    def __post_init__(self):
        """Validate the order data after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate all fields of the Domino's order.
        
        Raises:
            ValueError: If any field contains invalid data
        """
        if not self.order_id or not isinstance(self.order_id, str):
            raise ValueError("order_id must be a non-empty string")
        
        if not isinstance(self.timestamp, datetime):
            raise ValueError("timestamp must be a datetime object")
        
        if not self.location or not isinstance(self.location, str):
            raise ValueError("location must be a non-empty string")
        
        if not isinstance(self.order_total, (int, float)) or self.order_total < 0:
            raise ValueError("order_total must be a non-negative number")
        
        if not isinstance(self.pizza_types, list) or len(self.pizza_types) == 0:
            raise ValueError("pizza_types must be a non-empty list")
        
        for pizza_type in self.pizza_types:
            if not isinstance(pizza_type, str) or not pizza_type.strip():
                raise ValueError("All pizza types must be non-empty strings")
        
        if not isinstance(self.quantity, int) or self.quantity <= 0:
            raise ValueError("quantity must be a positive integer")
        
        if self.data_source not in ['real', 'mock']:
            raise ValueError("data_source must be either 'real' or 'mock'")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the order to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the order
        """
        data = asdict(self)
        # Convert datetime to ISO format string for JSON serialization
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DominosOrder':
        """
        Create a DominosOrder from a dictionary.
        
        Args:
            data: Dictionary containing order data
            
        Returns:
            DominosOrder instance
        """
        # Convert timestamp string back to datetime
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return cls(**data)

    def to_json(self) -> str:
        """
        Serialize the order to JSON format.
        
        Returns:
            JSON string representation of the order
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'DominosOrder':
        """
        Create a DominosOrder from a JSON string.
        
        Args:
            json_str: JSON string containing order data
            
        Returns:
            DominosOrder instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_csv_row(self) -> List[str]:
        """
        Convert the order to a CSV row format.
        
        Returns:
            List of strings representing CSV row values
        """
        return [
            self.order_id,
            self.timestamp.isoformat(),
            self.location,
            str(self.order_total),
            ';'.join(self.pizza_types),  # Join pizza types with semicolon
            str(self.quantity),
            self.data_source
        ]

    @classmethod
    def csv_headers(cls) -> List[str]:
        """
        Get the CSV headers for DominosOrder.
        
        Returns:
            List of CSV header names
        """
        return [
            'order_id',
            'timestamp',
            'location',
            'order_total',
            'pizza_types',
            'quantity',
            'data_source'
        ]

    @classmethod
    def from_csv_row(cls, row: List[str]) -> 'DominosOrder':
        """
        Create a DominosOrder from a CSV row.
        
        Args:
            row: List of strings representing CSV row values
            
        Returns:
            DominosOrder instance
        """
        if len(row) != 7:
            raise ValueError(f"Expected 7 CSV columns, got {len(row)}")
        
        return cls(
            order_id=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            location=row[2],
            order_total=float(row[3]),
            pizza_types=row[4].split(';') if row[4] else [],
            quantity=int(row[5]),
            data_source=row[6]
        )


def orders_to_csv(orders: List[DominosOrder]) -> str:
    """
    Convert a list of DominosOrder objects to CSV format.
    
    Args:
        orders: List of DominosOrder objects
        
    Returns:
        CSV string representation
    """
    if not orders:
        return ""
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(DominosOrder.csv_headers())
    
    # Write data rows
    for order in orders:
        writer.writerow(order.to_csv_row())
    
    return output.getvalue()


def orders_from_csv(csv_str: str) -> List[DominosOrder]:
    """
    Create a list of DominosOrder objects from CSV format.
    
    Args:
        csv_str: CSV string containing order data
        
    Returns:
        List of DominosOrder objects
    """
    if not csv_str.strip():
        return []
    
    input_stream = StringIO(csv_str)
    reader = csv.reader(input_stream)
    
    # Skip headers
    next(reader, None)
    
    orders = []
    for row in reader:
        if row:  # Skip empty rows
            orders.append(DominosOrder.from_csv_row(row))
    
    return orders