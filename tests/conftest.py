"""
conftest.py — Pytest configuration for local test environments.

Automatically sets DATABASE_URL to SQLite if no DATABASE_URL env var points
to a reachable PostgreSQL instance.  This lets any contributor run
`uv run pytest` without a local Postgres setup.
"""
import os
import socket


def _is_postgres_reachable(host: str, port: int, timeout: float = 1.0) -> bool:
    """Quick TCP probe to check if Postgres is actually reachable."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def pytest_configure(config):
    """Before collection: fall back to SQLite if local Postgres is unreachable."""
    db_url = os.getenv("DATABASE_URL", "")
    if "postgresql" in db_url or "postgres" in db_url:
        # Extract host/port from the URL for a quick reachability probe
        try:
            import re
            m = re.search(r"@([^:/]+):(\d+)", db_url)
            if m:
                host, port = m.group(1), int(m.group(2))
                if not _is_postgres_reachable(host, port):
                    os.environ["DATABASE_URL"] = "sqlite:///./test_run.db"
        except Exception:
            os.environ["DATABASE_URL"] = "sqlite:///./test_run.db"
    elif not db_url:
        # No DATABASE_URL set at all — use SQLite
        os.environ["DATABASE_URL"] = "sqlite:///./test_run.db"
