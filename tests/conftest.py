import pytest
from unittest.mock import AsyncMock, MagicMock
from talon.config import TalonConfig

def pytest_addoption(parser):
    parser.addoption("--run-live", action="store_true", help="run live network tests")

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-live"):
        skip = pytest.mark.skip(reason="pass --run-live to run")
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip)

@pytest.fixture
def mock_config():
    return TalonConfig(
        rate_limiting={"base_delay": 0, "jitter": 0},  # no sleeps in tests
    )

@pytest.fixture
def mock_client():
    client = MagicMock()
    client.get = AsyncMock()
    return client

@pytest.fixture
def domain():
    return "example.com"
