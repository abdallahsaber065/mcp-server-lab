"""
Lease Service (services/lease_service.py)
Encapsulates tenant and lease domain operations and discount policy evaluation.
"""

from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.repositories.tenant_repo import AsyncTenantRepository, TenantRepository

MAX_MANAGER_DISCOUNT_PERCENT = 15.0
EXECUTIVE_APPROVAL_RENT_THRESHOLD = 40000.0


class LeaseService:
    @staticmethod
    def get_tenant_lease_details(session: Session, email: str) -> Dict[str, Any]:
        repo = TenantRepository(session)
        return repo.get_lease_details(email)

    @staticmethod
    async def aget_tenant_lease_details(session: AsyncSession, email: str) -> Dict[str, Any]:
        repo = AsyncTenantRepository(session)
        return await repo.get_lease_details(email)

    @staticmethod
    def evaluate_discount_policy(base_rent: float, proposed_rent: float) -> Dict[str, Any]:
        """Evaluates whether proposed rent requires executive approval under company policy."""
        if base_rent <= 0:
            return {"discount_pct": 0.0, "requires_executive_signoff": False}

        discount_pct = ((base_rent - proposed_rent) / base_rent) * 100.0
        requires_signoff = (
            discount_pct > MAX_MANAGER_DISCOUNT_PERCENT or proposed_rent > EXECUTIVE_APPROVAL_RENT_THRESHOLD
        )
        return {
            "discount_pct": discount_pct,
            "requires_executive_signoff": requires_signoff,
            "max_allowed_standard_discount": MAX_MANAGER_DISCOUNT_PERCENT,
            "threshold_rent": EXECUTIVE_APPROVAL_RENT_THRESHOLD
        }
