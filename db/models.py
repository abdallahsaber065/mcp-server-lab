import json
import os
from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

try:
    from pgvector.sqlalchemy import Vector as PgVectorType
except ImportError:
    PgVectorType = None


class SafeVector(TypeDecorator):
    """Bulletproof Vector type: uses native PostgreSQL VECTOR(768) when USE_PGVECTOR=1, otherwise JSON Text."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and PgVectorType is not None and os.getenv("USE_PGVECTOR", "0") == "1":
            return dialect.type_descriptor(PgVectorType(768))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql" and PgVectorType is not None and os.getenv("USE_PGVECTOR", "0") == "1":
            return value
        if isinstance(value, (list, tuple)):
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value


class Base(DeclarativeBase):
    pass


class Property(Base):
    __tablename__ = "properties"

    property_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    neighborhood: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    property_type: Mapped[str] = mapped_column(String(50), default="residential")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    amenities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    year_built: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    virtual_tour_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    total_units: Mapped[int] = mapped_column(Integer, default=1)
    occupancy_rate: Mapped[float] = mapped_column(Float, default=1.0)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    units: Mapped[List["Unit"]] = relationship("Unit", back_populates="property", cascade="all, delete-orphan")


class Unit(Base):
    __tablename__ = "units"

    unit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[int] = mapped_column(Integer, ForeignKey("properties.property_id"), nullable=False)
    unit_number: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    bedrooms: Mapped[int] = mapped_column(Integer, default=1)
    bathrooms: Mapped[float] = mapped_column(Float, default=1.0)
    square_feet: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    floor_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    features: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    pet_policy: Mapped[Optional[str]] = mapped_column(String(50), default="Allowed")
    virtual_tour_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    monthly_rent: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="available")  # available, occupied, maintenance, reserved
    is_high_value: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    property: Mapped["Property"] = relationship("Property", back_populates="units")
    leases: Mapped[List["Lease"]] = relationship("Lease", back_populates="unit")
    maintenance_requests: Mapped[List["MaintenanceRequest"]] = relationship("MaintenanceRequest", back_populates="unit")
    applications: Mapped[List["LeaseApplication"]] = relationship("LeaseApplication", back_populates="unit")


class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    role: Mapped[str] = mapped_column(String(30), default="tenant")  # tenant, prospect, landlord, property_manager, executive_admin
    assigned_unit_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    leases: Mapped[List["Lease"]] = relationship("Lease", back_populates="tenant")
    maintenance_requests: Mapped[List["MaintenanceRequest"]] = relationship("MaintenanceRequest", back_populates="tenant")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="tenant")
    applications: Mapped[List["LeaseApplication"]] = relationship("LeaseApplication", back_populates="applicant")


class Lease(Base):
    __tablename__ = "leases"

    lease_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("units.unit_id"), nullable=False)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.tenant_id"), nullable=False)
    start_date: Mapped[str] = mapped_column(String(20), nullable=False)
    end_date: Mapped[str] = mapped_column(String(20), nullable=False)
    monthly_rent: Mapped[float] = mapped_column(Float, nullable=False)
    deposit_amount: Mapped[float] = mapped_column(Float, default=0.0)
    lease_type: Mapped[str] = mapped_column(String(30), default="residential")  # residential, commercial, mixed
    status: Mapped[str] = mapped_column(String(30), default="active")  # active, pending_approval, renewed, expired, terminated
    payment_status: Mapped[str] = mapped_column(String(20), default="current")  # current, pending, arrears, disputed
    renewal_status: Mapped[str] = mapped_column(String(30), default="none")  # none, requested, approved, declined
    renewal_requested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_executive_signoff: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    unit: Mapped["Unit"] = relationship("Unit", back_populates="leases")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="leases")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="lease", cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"

    payment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lease_id: Mapped[int] = mapped_column(Integer, ForeignKey("leases.lease_id"), nullable=False)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.tenant_id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    due_date: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_method: Mapped[str] = mapped_column(String(30), default="fawry")  # fawry, credit_card, bank_transfer, cash
    transaction_reference: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # paid, pending, overdue, failed, refunded
    receipt_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    lease: Mapped["Lease"] = relationship("Lease", back_populates="payments")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="payments")


class LeaseApplication(Base):
    __tablename__ = "lease_applications"

    application_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("units.unit_id"), nullable=False)
    applicant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tenants.tenant_id"), nullable=True)
    applicant_name: Mapped[str] = mapped_column(String(100), nullable=False)
    applicant_email: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    applicant_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    proposed_monthly_rent: Mapped[float] = mapped_column(Float, nullable=False)
    lease_duration_months: Mapped[int] = mapped_column(Integer, default=12)
    move_in_date: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="submitted")  # submitted, under_review, approved, rejected, withdrawn
    employment_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    unit: Mapped["Unit"] = relationship("Unit", back_populates="applications")
    applicant: Mapped[Optional["Tenant"]] = relationship("Tenant", back_populates="applications")


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    request_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("units.unit_id"), nullable=False)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.tenant_id"), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False)  # plumbing, electrical, hvac, structural, general
    priority: Mapped[str] = mapped_column(String(20), default="medium")   # emergency, high, medium, low
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open")       # open, dispatched, in_progress, resolved, cancelled
    preferred_time_slot: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    contractor_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contractor_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tenant_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1 to 5
    tenant_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    unit: Mapped["Unit"] = relationship("Unit", back_populates="maintenance_requests")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="maintenance_requests")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), default="محادثة جديدة")
    user_role: Mapped[str] = mapped_column(String(50), default="property_manager")
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)  # FK to tenant_id; null = legacy/unowned
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("chat_sessions.session_id"), nullable=False)
    sender: Mapped[str] = mapped_column(String(50), default="assistant")  # user, assistant, system, tool
    msg_type: Mapped[str] = mapped_column(String(50), default="assistant")  # user, assistant, tool_trace, elicitation, planning_subtask
    message_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tool_args: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    elicitation_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sse_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")


class GraphCheckpoint(Base):
    __tablename__ = "graph_checkpoints"

    checkpoint_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    node_name: Mapped[str] = mapped_column(String(100), nullable=False)
    state_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)  # RUNNING, PAUSED_HITL, AWAITING_WEBHOOK, FAILED_TICKET, COMPLETED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class HITLTask(Base):
    __tablename__ = "hitl_tasks"

    task_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    graph_id: Mapped[str] = mapped_column(String(100), nullable=False)
    node_name: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    task_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, rejected, modified
    decision_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class GraphFailureTicket(Base):
    __tablename__ = "graph_failure_tickets"

    ticket_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    graph_id: Mapped[str] = mapped_column(String(100), nullable=False)
    node_name: Mapped[str] = mapped_column(String(100), nullable=False)
    error_type: Mapped[str] = mapped_column(String(100), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[str] = mapped_column(Text, nullable=False)
    persisted_state_json: Mapped[str] = mapped_column(Text, nullable=False)
    ticket_status: Mapped[str] = mapped_column(String(20), default="open")  # open, investigating, resolved
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentToolBinding(Base):
    __tablename__ = "agent_tool_bindings"

    agent_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tool_name: Mapped[str] = mapped_column(String(100), primary_key=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class RAGDocument(Base):
    __tablename__ = "rag_documents"

    doc_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="policy")  # policy, bylaw, standard, engineering
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RagDocumentEmbedding(Base):
    __tablename__ = "rag_document_embeddings"

    embedding_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), default="gemini-embedding-2")
    embedding: Mapped[Optional[Any]] = mapped_column(SafeVector, nullable=True)
    allowed_roles_json: Mapped[str] = mapped_column(Text, default='["all"]')  # JSON list e.g. ["all"], ["tenant"], ["property_manager"]
    target_property_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    target_tenant_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class EpisodicMemoryRecord(Base):
    __tablename__ = "episodic_memory"

    episode_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(100), default="default")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    event_summary: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    importance_score: Mapped[float] = mapped_column(Float, default=0.5)
    consolidated: Mapped[int] = mapped_column(Integer, default=0)


class SemanticFactRecord(Base):
    __tablename__ = "semantic_memory"

    fact_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    fact_key: Mapped[str] = mapped_column(String(100), nullable=False)
    fact_value: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="active")  # active, superseded, expired
    valid_from: Mapped[str] = mapped_column(String(50), nullable=False)
    valid_to: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.9)
    evidence_episode_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    superseded_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class TourBooking(Base):
    __tablename__ = "tour_bookings"

    booking_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[int] = mapped_column(Integer, ForeignKey("properties.property_id"), nullable=False)
    unit_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("units.unit_id"), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tenants.tenant_id"), nullable=True)
    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(120), nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tour_type: Mapped[str] = mapped_column(String(30), default="in_person")  # in_person, virtual_guided, 3d_self_guided
    requested_date: Mapped[str] = mapped_column(String(50), nullable=False)
    time_slot: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending, confirmed, rescheduled, completed, cancelled
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rescheduled_from_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    property: Mapped["Property"] = relationship("Property")
    unit: Mapped[Optional["Unit"]] = relationship("Unit")
    user: Mapped[Optional["Tenant"]] = relationship("Tenant")


