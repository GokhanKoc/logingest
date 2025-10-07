# logingest/src/services/base_service.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseService(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch data from the API."""
        pass

    @abstractmethod
    def transform(self, data: Any) -> List[Dict[str, Any]]:
        """Transform API response to log entries."""
        pass