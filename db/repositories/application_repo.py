"""
Lease Application Repository (db/repositories/application_repo.py)
Manages prospect digital lease applications, reviewer status updates, and applicant lookups.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.models import LeaseApplication, Property, Tenant, Unit
from db.repositories.base import AsyncBaseRepository, BaseRepository


class ApplicationRepository(BaseRepository[LeaseApplication]):
    def __init__(self, session: Session):
        super().__init__(LeaseApplication, session)

    def create_application(
        self,
        unit_id: int,
        applicant_name: str,
        applicant_email: str,
        proposed_monthly_rent: float,
        lease_duration_months: int = 12,
        move_in_date: str = "2026-09-01",
        applicant_phone: Optional[str] = None,
        applicant_id: Optional[int] = None,
        employment_details: Optional[str] = None
    ) -> Dict[str, Any]:
        app = LeaseApplication(
            unit_id=unit_id,
            applicant_id=applicant_id,
            applicant_name=applicant_name,
            applicant_email=applicant_email,
            applicant_phone=applicant_phone,
            proposed_monthly_rent=proposed_monthly_rent,
            lease_duration_months=lease_duration_months,
            move_in_date=move_in_date,
            status="submitted",
            employment_details=employment_details
        )
        self.session.add(app)
        self.session.commit()
        self.session.refresh(app)
        return self._format(app)

    def list_applications(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        stmt = (
            select(LeaseApplication, Unit, Property)
            .join(Unit, LeaseApplication.unit_id == Unit.unit_id)
            .join(Property, Unit.property_id == Property.property_id)
        )
        if status:
            stmt = stmt.where(LeaseApplication.status == status)
        stmt = stmt.order_by(LeaseApplication.created_at.desc())

        rows = self.session.execute(stmt).all()
        results = []
        for app, unit, prop in rows:
            formatted = self._format(app)
            formatted["property_name"] = prop.name
            formatted["unit_number"] = unit.unit_number
            results.append(formatted)
        return results

    def get_by_id(self, application_id: int) -> Optional[Dict[str, Any]]:
        app = self.session.get(LeaseApplication, application_id)
        return self._format(app) if app else None

    def update_status(
        self,
        application_id: int,
        status: str,
        review_notes: Optional[str] = None,
        reviewed_by: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        app = self.session.get(LeaseApplication, application_id)
        if not app:
            return None
        app.status = status
        if review_notes:
            app.review_notes = review_notes
        if reviewed_by:
            app.reviewed_by = reviewed_by
        self.session.commit()
        self.session.refresh(app)
        return self._format(app)

    def _format(self, app: LeaseApplication) -> Dict[str, Any]:
        return {
            "application_id": app.application_id,
            "unit_id": app.unit_id,
            "applicant_id": app.applicant_id,
            "applicant_name": app.applicant_name,
            "applicant_email": app.applicant_email,
            "applicant_phone": app.applicant_phone,
            "proposed_monthly_rent": app.proposed_monthly_rent,
            "lease_duration_months": app.lease_duration_months,
            "move_in_date": app.move_in_date,
            "status": app.status,
            "employment_details": app.employment_details,
            "review_notes": app.review_notes,
            "reviewed_by": app.reviewed_by,
            "created_at": app.created_at.isoformat() if app.created_at else None
        }


class AsyncApplicationRepository(AsyncBaseRepository[LeaseApplication]):
    def __init__(self, session: AsyncSession):
        super().__init__(LeaseApplication, session)

    async def list_applications(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        stmt = (
            select(LeaseApplication, Unit, Property)
            .join(Unit, LeaseApplication.unit_id == Unit.unit_id)
            .join(Property, Unit.property_id == Property.property_id)
        )
        if status:
            stmt = stmt.where(LeaseApplication.status == status)
        stmt = stmt.order_by(LeaseApplication.created_at.desc())

        rows = (await self.session.execute(stmt)).all()
        results = []
        for app, unit, prop in rows:
            results.append({
                "application_id": app.application_id,
                "unit_id": app.unit_id,
                "property_name": prop.name,
                "unit_number": unit.unit_number,
                "applicant_id": app.applicant_id,
                "applicant_name": app.applicant_name,
                "applicant_email": app.applicant_email,
                "applicant_phone": app.applicant_phone,
                "proposed_monthly_rent": app.proposed_monthly_rent,
                "lease_duration_months": app.lease_duration_months,
                "move_in_date": app.move_in_date,
                "status": app.status,
                "employment_details": app.employment_details,
                "review_notes": app.review_notes,
                "reviewed_by": app.reviewed_by,
                "created_at": app.created_at.isoformat() if app.created_at else None
            })
        return results
