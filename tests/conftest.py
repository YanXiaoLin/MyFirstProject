"""
Pytest configuration and fixtures
"""
import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment
os.environ['APP_ENV'] = 'testing'
os.environ['LOG_LEVEL'] = 'DEBUG'

@pytest.fixture(scope='session')
def test_data_dir(tmp_path_factory):
    """Create temporary test data directory"""
    return tmp_path_factory.mktemp('test_data')

@pytest.fixture
def mock_config(monkeypatch):
    """Mock configuration for testing"""
    monkeypatch.setenv('APP_ENV', 'testing')
    monkeypatch.setenv('DEBUG', 'True')
    monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
    monkeypatch.setenv('API_KEY_REQUIRED', 'False')