# logingest/src/models/log_entry.py
import json
from datetime import datetime
from typing import Optional, Dict, Any, Union
from .base_model import BaseModel

class LogEntry(BaseModel):
    def __init__(
        self,
        source: str,
        product: str,
        event_type: str,
        raw_data: Union[str, Dict[str, Any]],
        severity: str = "info",
        timestamp: Optional[datetime] = None,
        **kwargs
    ):
        self.source = source
        self.product = product
        self.event_type = event_type
        self.severity = severity
        # Convert raw_data to JSON string if it's a dict
        if isinstance(raw_data, dict):
            self.raw_data = json.dumps(raw_data)
        elif isinstance(raw_data, str):
            self.raw_data = raw_data
        else:
            self.raw_data = json.dumps(raw_data)
        self.timestamp = timestamp or datetime.utcnow()
        self.additional_fields = kwargs

    def to_dict(self) -> dict:
        """Convert log entry to dictionary."""
        base_dict = {
            "source": self.source,
            "product": self.product,
            "event_type": self.event_type,
            "severity": self.severity,
            "raw_data": self.raw_data,
            "timestamp": self.timestamp.isoformat() + 'Z',
            **self.additional_fields
        }
        return base_dict