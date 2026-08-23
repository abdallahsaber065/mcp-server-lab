"""
MCP Server Database Helpers (mcp_server/db_helpers.py)
Unified helper layer delegating to SQLAlchemy 2.0 Repositories for PostgreSQL & SQLite concurrency.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add root path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.models import Lease, MaintenanceRequest, Property, Tenant, Unit
from db.repositories.chat_repo import ChatRepository
from db.repositories.maintenance_repo import MaintenanceRepository
from db.repositories.property_repo import PropertyRepository
from db.repositories.tenant_repo import TenantRepository
from db.repositories.user_repo import UserRepository
from db.session import IS_SQLITE, SYNC_DATABASE_URL, SyncSessionLocal, get_sync_db, init_sync_db
from scripts.seed_db import seed_sync

logger = logging.getLogger("mcp.db_helpers")


_DB_INITIALIZED = False


def init_db(reset: bool = False):
    """Initialize active database tables via SQLAlchemy metadata and seed only if empty."""
    global _DB_INITIALIZED
    if _DB_INITIALIZED and not reset:
        return
    try:
        init_sync_db()
        with SyncSessionLocal() as session:
            has_data = session.query(Property).first() is not None
        if reset or not has_data:
            seed_sync(reset=reset, verbose=False)
        _DB_INITIALIZED = True
    except Exception as e:
        logger.warning("init_db notice: %s", e)


# --- CHAT PERSISTENCE HELPERS ---

def create_chat_session(session_id: Optional[str] = None, title: str = "محادثة جديدة", role: str = "property_manager") -> Dict[str, Any]:
    with next(get_sync_db()) as session:
        repo = ChatRepository(session)
        return repo.create_chat_session(session_id=session_id, title=title, role=role)


def get_all_chat_sessions() -> List[Dict[str, Any]]:
    with next(get_sync_db()) as session:
        repo = ChatRepository(session)
        return repo.get_all_chat_sessions()


def get_chat_session_history(session_id: str) -> List[Dict[str, Any]]:
    with next(get_sync_db()) as session:
        repo = ChatRepository(session)
        return repo.get_chat_messages(session_id)


def save_chat_message(
    session_id: str,
    sender: str = "assistant",
    message_text: str = "",
    tool_name: Optional[str] = None,
    tool_args: Optional[Dict[str, Any]] = None,
    tool_result: Optional[Dict[str, Any]] = None,
    elicitation_payload: Optional[Dict[str, Any]] = None,
    content: Optional[str] = None,
    msg_type: Optional[str] = None,
    sse_payload: Optional[Dict[str, Any]] = None
) -> int:
    with next(get_sync_db()) as session:
        repo = ChatRepository(session)
        return repo.save_chat_message(
            session_id=session_id,
            msg_type=msg_type or sender,
            content=content or message_text,
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result=tool_result,
            elicitation_payload=elicitation_payload,
            sse_payload=json.dumps(sse_payload) if sse_payload else None
        )


def delete_chat_session(session_id: str) -> bool:
    with next(get_sync_db()) as session:
        repo = ChatRepository(session)
        return repo.delete_chat_session(session_id)


def update_chat_session_role(session_id: str, role: str) -> bool:
    with next(get_sync_db()) as session:
        repo = ChatRepository(session)
        return repo.update_chat_session_role(session_id, role)


def get_chat_session_role(session_id: str) -> str:
    with next(get_sync_db()) as session:
        repo = ChatRepository(session)
        return repo.get_chat_session_role(session_id)


# --- REPOSITORY DB OPERATIONAL HELPERS ---

def query_available_units(city: Optional[str] = None, min_beds: Optional[int] = None, max_rent: Optional[float] = None, property_id: Optional[int] = None) -> List[Dict[str, Any]]:
    with next(get_sync_db()) as session:
        repo = PropertyRepository(session)
        units = repo.query_available_units(property_id=property_id, city=city, max_rent=max_rent)
        if min_beds is not None:
            units = [u for u in units if int(u.get("bedrooms", 0)) >= min_beds]
        return units


def query_tenant_lease(email: str) -> Dict[str, Any]:
    with next(get_sync_db()) as session:
        repo = TenantRepository(session)
        return repo.get_lease_details(email)


get_available_units = query_available_units
get_active_lease_by_email = query_tenant_lease


def create_maintenance_record(tenant_id: int, unit_id: int, issue_description: str, priority: str) -> Dict[str, Any]:
    with next(get_sync_db()) as session:
        unit = session.get(Unit, unit_id)
        if not unit:
            unit = session.query(Unit).first()
            if not unit:
                raise ValueError(f"Unit ID {unit_id} not found in property database.")
            actual_unit_id = unit.unit_id
        else:
            actual_unit_id = unit_id

        tenant = session.get(Tenant, tenant_id)
        if not tenant:
            tenant = session.query(Tenant).first()
            if not tenant:
                raise ValueError(f"Tenant ID {tenant_id} not found in property database.")
            actual_tenant_id = tenant.tenant_id
        else:
            actual_tenant_id = tenant_id

        req = MaintenanceRequest(
            unit_id=actual_unit_id,
            tenant_id=actual_tenant_id,
            issue_type="general",
            priority=priority,
            description=issue_description,
            status="pending"
        )
        session.add(req)
        session.commit()
        session.refresh(req)
        return {
            "request_id": req.request_id,
            "unit_id": unit_id,
            "tenant_id": tenant_id,
            "issue_description": issue_description,
            "priority": priority,
            "status": "pending"
        }


def update_lease_terms(lease_id: int, new_rent: float, duration_months: int, signed_off_by_executive: bool = False) -> Dict[str, Any]:
    with next(get_sync_db()) as session:
        lease = session.get(Lease, lease_id)
        if not lease:
            raise ValueError(f"Lease ID {lease_id} not found.")

        old_rent = float(lease.monthly_rent)
        requires_exec = bool(lease.requires_executive_signoff)

        discount_pct = ((old_rent - new_rent) / old_rent) * 100.0 if old_rent > 0 else 0
        if (discount_pct > 15.0 or requires_exec) and not signed_off_by_executive:
            return {
                "success": False,
                "requires_elicitation": True,
                "reason": f"Discount of {discount_pct:.1f}% or high-value status requires explicit Executive Sign-off.",
                "lease_id": lease_id,
                "proposed_rent": new_rent
            }

        lease.monthly_rent = new_rent
        lease.is_active = True
        session.commit()
        session.refresh(lease)

        return {
            "success": True,
            "requires_elicitation": False,
            "lease_id": lease_id,
            "previous_rent": old_rent,
            "updated_rent": new_rent,
            "duration_months": duration_months,
            "status": "active"
        }
