import os
import sqlite3

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(BASE_DIR, "db", "schema.sql")
SEED_PATH = os.path.join(BASE_DIR, "db", "seed.sql")


def load_sql(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


@pytest.fixture(scope="module")
def in_memory_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(load_sql(SCHEMA_PATH))
    conn.executescript(load_sql(SEED_PATH))
    yield conn
    conn.close()


def test_properties_table_exists(in_memory_db):
    cursor = in_memory_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='properties'"
    )
    assert cursor.fetchone() is not None


def test_foreign_key_constraints(in_memory_db):
    conn = in_memory_db
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO units (property_id, unit_number, bedrooms, monthly_rent) VALUES (?, ?, ?, ?)",
            (999, "X-999", 1, 5000.0),
        )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO leases (unit_id, tenant_id, start_date, end_date, monthly_rent) VALUES (?, ?, ?, ?, ?)",
            (999, 1, "2026-01-01", "2027-01-01", 10000.0),
        )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO leases (unit_id, tenant_id, start_date, end_date, monthly_rent) VALUES (?, ?, ?, ?, ?)",
            (101, 999, "2026-01-01", "2027-01-01", 10000.0),
        )


def test_seed_data_counts(in_memory_db):
    cursor = in_memory_db.execute("SELECT COUNT(*) FROM properties")
    assert cursor.fetchone()[0] == 3

    cursor = in_memory_db.execute("SELECT COUNT(*) FROM units")
    assert cursor.fetchone()[0] == 6

    cursor = in_memory_db.execute("SELECT COUNT(*) FROM tenants")
    assert cursor.fetchone()[0] == 4

    cursor = in_memory_db.execute("SELECT COUNT(*) FROM leases")
    assert cursor.fetchone()[0] == 3

    cursor = in_memory_db.execute("SELECT COUNT(*) FROM maintenance_requests")
    assert cursor.fetchone()[0] == 2


def test_lease_date_check(in_memory_db):
    with pytest.raises(sqlite3.IntegrityError):
        in_memory_db.execute(
            "INSERT INTO leases (unit_id, tenant_id, start_date, end_date, monthly_rent) VALUES (?, ?, ?, ?, ?)",
            (101, 1, "2026-01-01", "2025-01-01", 12000.0),
        )


def test_unique_unit_per_property(in_memory_db):
    with pytest.raises(sqlite3.IntegrityError):
        in_memory_db.execute(
            "INSERT INTO units (property_id, unit_number, bedrooms, monthly_rent) VALUES (?, ?, ?, ?)",
            (1, "A-101", 2, 12000.0),
        )


def test_lease_notice_template():
    from mcp_server.prompts.templates import draft_lease_notice

    prompt = draft_lease_notice(
        tenant_name="Amr Hassan",
        property_name="Cornerstone Heights",
        unit_number="A-101",
        start_date="2025-01-01",
        end_date="2026-01-01",
        monthly_rent=12000.0,
        additional_terms="Tenant is responsible for utilities.",
    )

    assert "Draft a professional lease notice for Amr Hassan." in prompt
    assert "Property: Cornerstone Heights" in prompt
    assert "Unit: A-101" in prompt
    assert "Monthly rent: 12000.00 EGP" in prompt
    assert "Tenant is responsible for utilities." in prompt
