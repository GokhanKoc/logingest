# tests/test_json_placeholder_service.py
import pytest
from src.services.api_services.json_placeholder_service import JsonPlaceholderService

@pytest.fixture
def sample_config():
    return {
        'name': 'test_service',
        'endpoint': 'https://jsonplaceholder.typicode.com/posts/1',
        'product': 'test',
        'event_type': 'test',
        'severity': 'info'
    }

@pytest.mark.asyncio
async def test_fetch_data(sample_config):
    service = JsonPlaceholderService(sample_config)
    data = await service.fetch_data()
    assert isinstance(data, list)
    assert len(data) > 0
    assert 'id' in data[0]

@pytest.mark.asyncio
async def test_transform(sample_config):
    service = JsonPlaceholderService(sample_config)
    test_data = [{'id': 1, 'title': 'Test', 'body': 'Test body', 'userId': 1}]
    result = service.transform(test_data)
    
    assert len(result) == 1
    assert result[0]['source'] == 'test_service'
    assert result[0]['event_type'] == 'test'
    assert 'Test' in result[0]['raw_data']