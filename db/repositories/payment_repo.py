"""
Payment Repository (db/repositories/payment_repo.py)
Handles payment ledger queries, payment recording, and tenant billing history.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.models import Lease, Payment, Property, Tenant, Unit
from db.repositories.base import AsyncBaseRepository, BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, session: Session):
        super().__init__(Payment, session)

    def get_by_tenant(self, tenant_id: int) -> List[Dict[str, Any]]:
        stmt = (
            select(Payment, Lease, Unit, Property)
            .join(Lease, Payment.lease_id == Lease.lease_id)
            .join(Unit, Lease.unit_id == Unit.unit_id)
            .join(Property, Unit.property_id == Property.property_id)
            .where(Payment.tenant_id == tenant_id)
            .order_by(Payment.due_date.desc())
        )
        rows = self.session.execute(stmt).all()
        results = []
        for payment, lease, unit, prop in rows:
            results.append({
                "payment_id": payment.payment_id,
                "lease_id": payment.lease_id,
                "tenant_id": payment.tenant_id,
                "property_name": prop.name,
                "unit_number": unit.unit_number,
                "amount": payment.amount,
                "due_date": payment.due_date,
                "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
                "payment_method": payment.payment_method,
                "transaction_reference": payment.transaction_reference,
                "status": payment.status,
                "receipt_url": payment.receipt_url,
                "notes": payment.notes
            })
        return results

    def get_by_lease(self, lease_id: int) -> List[Dict[str, Any]]:
        stmt = (
            select(Payment)
            .where(Payment.lease_id == lease_id)
            .order_by(Payment.due_date.desc())
        )
        payments = self.session.scalars(stmt).all()
        return [
            {
                "payment_id": p.payment_id,
                "lease_id": p.lease_id,
                "tenant_id": p.tenant_id,
                "amount": p.amount,
                "due_date": p.due_date,
                "payment_date": p.payment_date.isoformat() if p.payment_date else None,
                "payment_method": p.payment_method,
                "transaction_reference": p.transaction_reference,
                "status": p.status,
                "receipt_url": p.receipt_url,
                "notes": p.notes
            }
            for p in payments
        ]

    def record_payment(
        self,
        lease_id: int,
        tenant_id: int,
        amount: float,
        payment_method: str = "credit_card",
        due_date: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        ref = f"TXN-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        due = due_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        payment = Payment(
            lease_id=lease_id,
            tenant_id=tenant_id,
            amount=amount,
            due_date=due,
            payment_date=datetime.now(timezone.utc),
            payment_method=payment_method,
            transaction_reference=ref,
            status="paid",
            receipt_url=f"/receipts/{ref}.pdf",
            notes=notes or f"Rent installment processed via {payment_method}."
        )
        self.session.add(payment)
        self.session.commit()
        self.session.refresh(payment)
        return {
            "payment_id": payment.payment_id,
            "lease_id": payment.lease_id,
            "tenant_id": payment.tenant_id,
            "amount": payment.amount,
            "transaction_reference": payment.transaction_reference,
            "status": payment.status,
            "receipt_url": payment.receipt_url,
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None
        }


class AsyncPaymentRepository(AsyncBaseRepository[Payment]):
    def __init__(self, session: AsyncSession):
        super().__init__(Payment, session)

    async def get_by_tenant(self, tenant_id: int) -> List[Dict[str, Any]]:
        stmt = (
            select(Payment, Lease, Unit, Property)
            .join(Lease, Payment.lease_id == Lease.lease_id)
            .join(Unit, Lease.unit_id == Unit.unit_id)
            .join(Property, Unit.property_id == Property.property_id)
            .where(Payment.tenant_id == tenant_id)
            .order_by(Payment.due_date.desc())
        )
        rows = (await self.session.execute(stmt)).all()
        results = []
        for payment, lease, unit, prop in rows:
            results.append({
                "payment_id": payment.payment_id,
                "lease_id": payment.lease_id,
                "tenant_id": payment.tenant_id,
                "property_name": prop.name,
                "unit_number": unit.unit_number,
                "amount": payment.amount,
                "due_date": payment.due_date,
                "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
                "payment_method": payment.payment_method,
                "transaction_reference": payment.transaction_reference,
                "status": payment.status,
                "receipt_url": payment.receipt_url,
                "notes": payment.notes
            })
        return results

    async def record_payment(
        self,
        lease_id: int,
        tenant_id: int,
        amount: float,
        payment_method: str = "credit_card",
        due_date: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        ref = f"TXN-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        due = due_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        payment = Payment(
            lease_id=lease_id,
            tenant_id=tenant_id,
            amount=amount,
            due_date=due,
            payment_date=datetime.now(timezone.utc),
            payment_method=payment_method,
            transaction_reference=ref,
            status="paid",
            receipt_url=f"/receipts/{ref}.pdf",
            notes=notes or f"Rent installment processed via {payment_method}."
        )
        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)
        return {
            "payment_id": payment.payment_id,
            "lease_id": payment.lease_id,
            "tenant_id": payment.tenant_id,
            "amount": payment.amount,
            "transaction_reference": payment.transaction_reference,
            "status": payment.status,
            "receipt_url": payment.receipt_url,
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None
        }
