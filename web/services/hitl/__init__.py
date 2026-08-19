"""
HITL Service Package (web/services/hitl/__init__.py)

Exports a pre-built, fully configured HITLRegistry singleton.
Import this in llm_engine.py — zero further setup needed.
"""

from web.services.hitl.base_handler import BaseHITLHandler
from web.services.hitl.handlers import (
    LeaseModificationHandler,
    MaintenanceRequestHandler,
    RentPaymentHandler,
    TourBookingHandler,
    TourCancellationHandler,
)
from web.services.hitl.registry import HITLRegistry


def build_hitl_registry() -> HITLRegistry:
    """Factory — returns a fully wired registry with all production handlers."""
    registry = HITLRegistry()
    registry.register(TourBookingHandler())
    registry.register(MaintenanceRequestHandler())
    registry.register(LeaseModificationHandler())
    registry.register(RentPaymentHandler())
    registry.register(TourCancellationHandler())
    return registry


# Module-level singleton — import and use directly
hitl_registry: HITLRegistry = build_hitl_registry()

__all__ = [
    "BaseHITLHandler",
    "HITLRegistry",
    "hitl_registry",
    "build_hitl_registry",
    "TourBookingHandler",
    "MaintenanceRequestHandler",
    "LeaseModificationHandler",
    "RentPaymentHandler",
    "TourCancellationHandler",
]
