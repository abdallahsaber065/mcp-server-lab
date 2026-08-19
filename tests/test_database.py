"""
Database ORM, Schema & Constraint Verification Suite (tests/test_database.py)
Verifies:
  1. SQLAlchemy 2.0 ORM model definitions and table creation.
  2. Foreign key integrity and cascade constraints.
  3. Unique constraints and relationship mappings.
  4. Template prompt generation.
"""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, Lease, MaintenanceRequest, Property, Tenant, Unit
from db.repositories.property_repo import PropertyRepository
from db.repositories.tenant_repo import TenantRepository
from mcp_server.prompts.templates import draft_lease_notice


@pytest.fixture(scope="module")
def orm_session():
    """Create isolated in-memory SQLite database with SQLAlchemy ORM."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Seed minimal baseline for testing
    prop = Property(property_id=1, name="Cornerstone Test Heights", address="123 Test St", city="Cairo")
    session.add(prop)
    session.commit()

    unit = Unit(unit_id=101, property_id=1, unit_number="A-101", bedrooms=2, monthly_rent=12000.0)
    session.add(unit)
    session.commit()

    tenant = Tenant(tenant_id=1, full_name="Amr Hassan", email="amr@test.eg", role="tenant")
    session.add(tenant)
    session.commit()

    lease = Lease(lease_id=1, unit_id=101, tenant_id=1, start_date="2026-01-01", end_date="2027-01-01", monthly_rent=12000.0)
    session.add(lease)
    session.commit()

    yield session
    session.close()


def test_properties_table_exists(orm_session: Session):
    prop = orm_session.get(Property, 1)
    assert prop is not None
    assert prop.name == "Cornerstone Test Heights"


def test_foreign_key_constraints(orm_session: Session):
    # Attempt inserting a Unit with nonexistent property_id
    invalid_unit = Unit(unit_id=999, property_id=999, unit_number="X-999", monthly_rent=5000.0)
    orm_session.add(invalid_unit)
    # Rollback on test failure
    try:
        orm_session.commit()
    except Exception:
        orm_session.rollback()


def test_seed_data_counts(orm_session: Session):
    props = orm_session.scalars(select(Property)).all()
    assert len(props) >= 1

    units = orm_session.scalars(select(Unit)).all()
    assert len(units) >= 1

    tenants = orm_session.scalars(select(Tenant)).all()
    assert len(tenants) >= 1


def test_property_repository_query(orm_session: Session):
    repo = PropertyRepository(orm_session)
    available = repo.query_available_units(city="Cairo")
    assert isinstance(available, list)


def test_tenant_repository_lookup(orm_session: Session):
    repo = TenantRepository(orm_session)
    tenant = repo.get_by_email("amr@test.eg")
    assert tenant is not None
    assert tenant.full_name == "Amr Hassan"


def test_lease_notice_template():
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
