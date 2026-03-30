"""
Pytest Configuration and Fixtures

Provides test fixtures and mock configurations for SynapticBridge tests.
"""

import os
import sys
from unittest.mock import MagicMock

os.environ["TESTING"] = "1"
os.environ["JWT_SECRET"] = "test-jwt-secret-for-testing-only-minimum-length"


class MockDuckDBConnection:
    """Mock DuckDB connection for testing without duckdb installed."""

    def __init__(self, *args, **kwargs):
        self._tables = {}
        self._committed = True

    def execute(self, query: str, params: list = None):
        query_upper = query.upper().strip()

        if "CREATE SEQUENCE" in query_upper:
            return MagicMock()

        if "CREATE TABLE" in query_upper:
            match = (
                query_upper.split("IF NOT EXISTS")[1].split("(")[0].strip()
                if "IF NOT EXISTS" in query_upper
                else query_upper.split("CREATE TABLE")[1].split("(")[0].strip()
            )
            table_name = match.strip()
            self._tables[table_name] = []
            return MagicMock()

        if "CREATE INDEX" in query_upper:
            return MagicMock()

        if "INSERT INTO" in query_upper:
            return MagicMock()

        if "SELECT" in query_upper and "FROM corrections" in query_upper:
            if "WHERE correction_id" in query_upper and params:
                return MagicMock(fetchone=MagicMock(return_value=None))
            return MagicMock(fetchone=MagicMock(return_value=0))

        if "SELECT COUNT" in query_upper:
            return MagicMock(fetchone=MagicMock(return_value=(0,)))

        if "SELECT * FROM correction_patterns" in query_upper:
            return MagicMock(fetchall=MagicMock(return_value=[]))

        if "FROM correction_patterns" in query_upper:
            return MagicMock(fetchall=MagicMock(return_value=[]))

        return MagicMock()

    def commit(self):
        self._committed = True

    def close(self):
        pass


class MockDuckDB:
    """Mock DuckDB module for testing."""

    @staticmethod
    def connect(*args, **kwargs):
        return MockDuckDBConnection(*args, **kwargs)


def pytest_configure(config):
    """Configure pytest with mock duckdb if not available."""
    import importlib.util

    if importlib.util.find_spec("duckdb") is None:
        sys.modules["duckdb"] = MockDuckDB()
