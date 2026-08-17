"""
SQLAlchemy 2.0 Declarative ORM Models (db/models.py)
Cornerstone Realty Group B Master Schema
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Property(Base):
    __tablename__ = "properties"

    property_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    address = Column(String(200), nullable=False)
    city = Column(String(50), nullable=False)
    property_type = Column(String(50), default="residential")
    total_units = Column(Integer, default=1)
    occupancy_rate = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    units = relationship("Unit", back_populates="property", cascade="all, delete-orphan")


class Unit(Base):
    __tablename__ = "units"

    unit_id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Integer, ForeignKey("properties.property_id"), nullable=False)
    unit_number = Column(String(20), nullable=False)
    bedrooms = Column(Integer, default=1)
    bathrooms = Column(Float, default=1.0)
    square_feet = Column(Float, nullable=True)
    monthly_rent = Column(Float, nullable=False)
    status = Column(String(20), default="available")  # available, occupied, maintenance, reserved
    is_high_value = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="units")
    leases = relationship("Lease", back_populates="unit")
    maintenance_requests = relationship("MaintenanceRequest", back_populates="unit")


class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(30), nullable=True)
    role = Column(String(30), default="tenant")  # tenant, property_manager, executive_admin
    assigned_unit_id = Column(Integer, ForeignKey("units.unit_id"), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    leases = relationship("Lease", back_populates="tenant")
    maintenance_requests = relationship("MaintenanceRequest", back_populates="tenant")


class Lease(Base):
    __tablename__ = "leases"

    lease_id = Column(Integer, primary_key=True, autoincrement=True)
    unit_id = Column(Integer, ForeignKey("units.unit_id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id"), nullable=False)
    start_date = Column(String(20), nullable=False)
    end_date = Column(String(20), nullable=False)
    monthly_rent = Column(Float, nullable=False)
    deposit_amount = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    requires_executive_signoff = Column(Boolean, default=False)
    payment_status = Column(String(20), default="current")  # current, pending, arrears, disputed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    unit = relationship("Unit", back_populates="leases")
    tenant = relationship("Tenant", back_populates="leases")


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    request_id = Column(Integer, primary_key=True, autoincrement=True)
    unit_id = Column(Integer, ForeignKey("units.unit_id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id"), nullable=False)
    issue_type = Column(String(50), nullable=False)  # plumbing, electrical, hvac, structural, general
    priority = Column(String(20), default="medium")   # emergency, high, medium, low
    description = Column(Text, nullable=False)
    status = Column(String(20), default="open")       # open, dispatched, in_progress, resolved, cancelled
    estimated_cost = Column(Float, default=0.0)
    contractor_name = Column(String(100), nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    unit = relationship("Unit", back_populates="maintenance_requests")
    tenant = relationship("Tenant", back_populates="maintenance_requests")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String(64), primary_key=True)
    title = Column(String(200), default="محادثة جديدة")
    user_role = Column(String(50), default="property_manager")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("chat_sessions.session_id"), nullable=False)
    sender = Column(String(20), nullable=False)  # user, assistant, system, tool
    message_text = Column(Text, nullable=False)
    sse_payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")


class GraphCheckpoint(Base):
    __tablename__ = "graph_checkpoints"

    checkpoint_id = Column(String(64), primary_key=True)
    run_id = Column(String(64), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    node_name = Column(String(100), nullable=False)
    state_json = Column(Text, nullable=False)
    status = Column(String(30), nullable=False)  # RUNNING, PAUSED_HITL, AWAITING_WEBHOOK, FAILED_TICKET, COMPLETED
    created_at = Column(DateTime, default=datetime.utcnow)


class HITLTask(Base):
    __tablename__ = "hitl_tasks"

    task_id = Column(String(64), primary_key=True)
    run_id = Column(String(64), nullable=False, index=True)
    graph_id = Column(String(100), nullable=False)
    node_name = Column(String(100), nullable=False)
    reason = Column(Text, nullable=False)
    payload_json = Column(Text, nullable=False)
    task_status = Column(String(20), default="pending")  # pending, approved, rejected, modified
    decision_notes = Column(Text, nullable=True)
    decided_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class GraphFailureTicket(Base):
    __tablename__ = "graph_failure_tickets"

    ticket_id = Column(String(64), primary_key=True)
    run_id = Column(String(64), nullable=False, index=True)
    graph_id = Column(String(100), nullable=False)
    node_name = Column(String(100), nullable=False)
    error_type = Column(String(100), nullable=False)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=False)
    persisted_state_json = Column(Text, nullable=False)
    ticket_status = Column(String(20), default="open")  # open, investigating, resolved
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class AgentToolBinding(Base):
    __tablename__ = "agent_tool_bindings"

    agent_id = Column(String(64), primary_key=True)
    tool_name = Column(String(100), primary_key=True)
    is_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RAGDocument(Base):
    __tablename__ = "rag_documents"

    doc_id = Column(String(64), primary_key=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), default="policy")  # policy, bylaw, standard, engineering
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)
