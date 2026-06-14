"""Pytest configuration: sets up sys.path so src/ modules are importable."""
import sys
import os
from unittest.mock import MagicMock, patch

import pytest

# Add src/ to path so imports work without the src. prefix
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def mock_dynamodb(monkeypatch):
    """Mock DynamoDB table operations for unit tests."""
    mock_table = MagicMock()
    mock_table.get_item.return_value = {"Item": None}
    mock_table.put_item.return_value = {}
    mock_table.delete_item.return_value = {}
    mock_table.query.return_value = {"Items": []}
    mock_table.update_item.return_value = {}
    return mock_table
