"""
Comprehensive Database Seeding Engine (scripts/seed_db.py)
Reads structured JSON seed files from db/seeds/ and populates the database using SQLAlchemy 2.0 ORM.
Supports sync and async seeding modes with --reset flag.
"""

import os
import sys
import json
import argparse
import asyncio
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from db.models import (
    Base, Property, Unit, Tenant, Lease, MaintenanceRequest,
    AgentToolBinding, RAGDocument
)
from db.session import (
    SyncSessionLocal, AsyncSessionLocal, init_sync_db, init_async_db,
    sync_engine, async_engine
)

SEEDS_DIR = Path(__file__).resolve().parent.parent / "db" / "seeds"


def load_json(filename: str):
    file_path = SEEDS_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Seed file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_sync(reset: bool = False):
    """Synchronous seeding pipeline using SQLAlchemy ORM Session."""
    print("Initializing sync database tables...")
    if reset:
        Base.metadata.drop_all(bind=sync_engine)
    init_sync_db()

    with SyncSessionLocal() as session:
        # 1. Properties
        props_data = load_json("properties.json")
        for item in props_data:
            existing = session.get(Property, item["property_id"])
            if not existing:
                session.add(Property(**item))
            else:
                for k, v in item.items():
                    setattr(existing, k, v)
        session.commit()
        print(f"✅ Seeded {len(props_data)} Properties.")

        # 2. Units
        units_data = load_json("units.json")
        for item in units_data:
            existing = session.get(Unit, item["unit_id"])
            if not existing:
                session.add(Unit(**item))
            else:
                for k, v in item.items():
                    setattr(existing, k, v)
        session.commit()
        print(f"✅ Seeded {len(units_data)} Units.")
        # 3. Tenants with Hashed Passwords
        from services.auth_service import AuthService
        tenants_data = load_json("tenants.json")
        for item in tenants_data:
            d = dict(item)
            default_pass = "AdminPass123!" if d.get("role") == "executive_admin" else ("ManagerPass123!" if d.get("role") == "property_manager" else "TenantPass123!")
            d["hashed_password"] = AuthService.hash_password(default_pass)
            d["is_active"] = True
            existing = session.get(Tenant, d["tenant_id"])
            if not existing:
                session.add(Tenant(**d))
            else:
                for k, v in d.items():
                    setattr(existing, k, v)
        session.commit()
        print(f"✅ Seeded {len(tenants_data)} Tenants with Secure Hashed Passwords.")

        # 4. Leases
        leases_data = load_json("leases.json")
        for item in leases_data:
            existing = session.get(Lease, item["lease_id"])
            if not existing:
                session.add(Lease(**item))
            else:
                for k, v in item.items():
                    setattr(existing, k, v)
        session.commit()
        print(f"✅ Seeded {len(leases_data)} Leases.")

        # 5. Maintenance Requests
        maint_data = load_json("maintenance_requests.json")
        for item in maint_data:
            existing = session.get(MaintenanceRequest, item["request_id"])
            if not existing:
                # convert submitted_at to datetime if string
                from datetime import datetime
                d = dict(item)
                if "submitted_at" in d and isinstance(d["submitted_at"], str):
                    d["submitted_at"] = datetime.fromisoformat(d["submitted_at"])
                session.add(MaintenanceRequest(**d))
        session.commit()
        print(f"✅ Seeded {len(maint_data)} Maintenance Requests.")

        # 6. Agent Tool Bindings
        tool_data = load_json("agent_tool_bindings.json")
        for item in tool_data:
            existing = session.get(AgentToolBinding, (item["agent_id"], item["tool_name"]))
            if not existing:
                session.add(AgentToolBinding(**item))
            else:
                existing.is_enabled = item["is_enabled"]
        session.commit()
        print(f"✅ Seeded {len(tool_data)} Agent Tool Bindings.")

        # 7. RAG Documents
        rag_data = load_json("rag_documents.json")
        for item in rag_data:
            existing = session.get(RAGDocument, item["doc_id"])
            if not existing:
                session.add(RAGDocument(**item))
            else:
                for k, v in item.items():
                    setattr(existing, k, v)
        session.commit()
        print(f"✅ Seeded {len(rag_data)} RAG Documents.")

    print("\n🎉 Database sync seeding completed successfully!\n")


async def seed_async(reset: bool = False):
    """Asynchronous seeding pipeline using SQLAlchemy AsyncSession."""
    print("Initializing async database tables...")
    if reset:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    await init_async_db()

    async with AsyncSessionLocal() as session:
        # Properties
        props_data = load_json("properties.json")
        for item in props_data:
            existing = await session.get(Property, item["property_id"])
            if not existing:
                session.add(Property(**item))
            else:
                for k, v in item.items():
                    setattr(existing, k, v)
        await session.commit()
        print(f"✅ [Async] Seeded {len(props_data)} Properties.")

        # Units
        units_data = load_json("units.json")
        for item in units_data:
            existing = await session.get(Unit, item["unit_id"])
            if not existing:
                session.add(Unit(**item))
            else:
                for k, v in item.items():
                    setattr(existing, k, v)
        await session.commit()
        print(f"✅ [Async] Seeded {len(units_data)} Units.")

        # Tenants with Hashed Passwords
        tenants_data = load_json("tenants.json")
        for item in tenants_data:
            d = dict(item)
            default_pass = "AdminPass123!" if d.get("role") == "executive_admin" else ("ManagerPass123!" if d.get("role") == "property_manager" else "TenantPass123!")
            d["hashed_password"] = AuthService.hash_password(default_pass)
            d["is_active"] = True
            existing = await session.get(Tenant, d["tenant_id"])
            if not existing:
                session.add(Tenant(**d))
            else:
                for k, v in d.items():
                    setattr(existing, k, v)
        await session.commit()
        print(f"✅ [Async] Seeded {len(tenants_data)} Tenants with Secure Hashed Passwords.")

        # Leases
        leases_data = load_json("leases.json")
        for item in leases_data:
            existing = await session.get(Lease, item["lease_id"])
            if not existing:
                session.add(Lease(**item))
            else:
                for k, v in item.items():
                    setattr(existing, k, v)
        await session.commit()
        print(f"✅ [Async] Seeded {len(leases_data)} Leases.")

        # Maintenance Requests
        maint_data = load_json("maintenance_requests.json")
        for item in maint_data:
            existing = await session.get(MaintenanceRequest, item["request_id"])
            if not existing:
                from datetime import datetime
                d = dict(item)
                if "submitted_at" in d and isinstance(d["submitted_at"], str):
                    d["submitted_at"] = datetime.fromisoformat(d["submitted_at"])
                session.add(MaintenanceRequest(**d))
        await session.commit()
        print(f"✅ [Async] Seeded {len(maint_data)} Maintenance Requests.")

        # Agent Tool Bindings
        tool_data = load_json("agent_tool_bindings.json")
        for item in tool_data:
            existing = await session.get(AgentToolBinding, (item["agent_id"], item["tool_name"]))
            if not existing:
                session.add(AgentToolBinding(**item))
            else:
                existing.is_enabled = item["is_enabled"]
        await session.commit()
        print(f"✅ [Async] Seeded {len(tool_data)} Agent Tool Bindings.")

        # RAG Documents
        rag_data = load_json("rag_documents.json")
        for item in rag_data:
            existing = await session.get(RAGDocument, item["doc_id"])
            if not existing:
                session.add(RAGDocument(**item))
            else:
                for k, v in item.items():
                    setattr(existing, k, v)
        await session.commit()
        print(f"✅ [Async] Seeded {len(rag_data)} RAG Documents.")

    print("\n🎉 Database async seeding completed successfully!\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Cornerstone Realty Database")
    parser.add_argument("--reset", action="store_true", help="Reset all tables before seeding")
    parser.add_argument("--async", dest="use_async", action="store_true", help="Run async seeding pipeline")
    args = parser.parse_args()

    if args.use_async:
        asyncio.run(seed_async(reset=args.reset))
    else:
        seed_sync(reset=args.reset)
