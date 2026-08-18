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

        # 8. Memory Subsystem (Episodic & Semantic Stores)
        try:
            from memory.episodic_store import EpisodicStore
            from memory.consolidation import SemanticMemoryStore, SemanticConsolidationEngine
            ep_store = EpisodicStore(db_path="db/episodic_memory.db")
            sem_store = SemanticMemoryStore(db_path="db/semantic_memory.db")
            engine = SemanticConsolidationEngine(ep_store, sem_store)

            episodes = [
                ("tenant_1", "Tenant Dr. Tarek El-Mahdy reported severe asthma/fume allergy triggered by oil-based paints; requested mandatory low-VOC non-toxic paint for all unit maintenance.", "2026-02-15T09:00:00Z"),
                ("tenant_1", "Tenant submitted formal preferred contractor window (9:00 AM - 12:00 PM weekdays) to avoid patient clinic consultation hours.", "2026-03-01T11:30:00Z"),
                ("tenant_2", "Ambassador Jean-Luc Picard requested diplomatic security protocol addendum: 24/7 keycard access for French Embassy security liaisons.", "2026-01-20T10:00:00Z"),
                ("tenant_3", "Tenant Laila Soliman submitted medical registration for certified therapy dog (Golden Retriever); granted Section 6.1b pet fee exemption.", "2026-02-05T14:15:00Z"),
                ("tenant_4", "Apex Financial Holding requested emergency backup power circuit prioritization for server room HVAC chilling units.", "2026-02-28T16:00:00Z"),
                ("tenant_5", "Cinnabon Nile Delta requested 3-phase 380V electrical upgrade and 5% annual rent escalation cap under Cairo commercial tenancy law.", "2026-03-12T13:20:00Z"),
                ("tenant_6", "Eng. Karim Mostafa requested smart biometric lock installation authorization for Unit 501 for elderly parent accessibility.", "2026-02-18T10:30:00Z"),
                ("property_manager", "Issued quarterly building compliance audit for Cairo and Alexandria properties; enforcing Egyptian Tenancy Law 4/1996 4-hour emergency water shutoff SLA.", "2026-02-01T09:00:00Z"),
            ]

            for entity_id, summary, ts in episodes:
                ep_store.insert_episode(entity_id=entity_id, event_summary=summary, timestamp=ts)

            engine.run_periodic_consolidation()
            print(f"✅ Seeded {len(episodes)} Episodic Records & Consolidated Semantic Facts.")
        except Exception as mem_err:
            print(f"⚠️ Memory seeding notice: {mem_err}")

        # Synchronize PostgreSQL auto-increment sequences after explicit PK insertions
        from db.session import IS_SQLITE
        if not IS_SQLITE:
            from sqlalchemy import text
            seq_tables = [
                ("properties", "property_id"),
                ("units", "unit_id"),
                ("tenants", "tenant_id"),
                ("leases", "lease_id"),
                ("maintenance_requests", "request_id"),
                ("chat_messages", "message_id")
            ]
            for table, col in seq_tables:
                try:
                    session.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', '{col}'), coalesce(max({col}), 1) + 1, false) FROM {table};"))
                    session.commit()
                except Exception as seq_err:
                    session.rollback()

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
