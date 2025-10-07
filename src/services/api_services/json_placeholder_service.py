# logingest/src/services/api_services/json_placeholder_service.py
import httpx
import logging
from typing import List, Dict, Any
from ...models.log_entry import LogEntry
from ..base_service import BaseService

logger = logging.getLogger(__name__)

class JsonPlaceholderService(BaseService):
    async def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch data from JSONPlaceholder API."""
        url = self.config.get('endpoint')
        params = self.config.get('params', {})
        
        try:
            logger.info(f"Fetching data from {url} with params: {params}")
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Received data: {data}")
                return data if isinstance(data, list) else [data]
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform API response to log entries."""
        log_entries = []
        
        for item in data:
            try:
                log_entry = LogEntry(
                    source=self.config['name'],
                    product=self.config.get('product', 'unknown'),
                    event_type=self.config.get('event_type', 'api_request'),
                    severity=self.config.get('severity', 'info'),
                    raw_data=item
                )
                log_entries.append(log_entry.to_dict())
            except Exception as e:
                logger.error(f"Error transforming data: {str(e)}", exc_info=True)
                continue
                
        return log_entries