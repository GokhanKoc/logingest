# logingest/src/models/base_model.py
from datetime import datetime
from typing import Any, Dict

class BaseModel:
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}