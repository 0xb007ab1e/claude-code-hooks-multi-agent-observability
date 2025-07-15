"""
Pytest configuration file for setting up a test environment.
"""
import pytest
from run_e2e_tests import read_orchestrator_config

@pytest.fixture(scope="session")
def orchestrator_config():
    """Fixture to provide orchestrator configuration throughout tests."""
    return read_orchestrator_config()
