"""
Tour Booking Repository (db/repositories/tour_repo.py)
Manages property viewing schedules, in-person tours, and 3D guided walkthrough requests.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from db.models import Property, Tenant, TourBooking, Unit


class TourRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_booking(
        self,
        property_id: int,
        contact_name: str,
        contact_email: str,
        requested_date: str,
        time_slot: str,
        unit_id: Optional[int] = None,
        user_id: Optional[int] = None,
        contact_phone: Optional[str] = None,
        tour_type: str = "in_person",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        booking = TourBooking(
            property_id=property_id,
            unit_id=unit_id,
            user_id=user_id,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            tour_type=tour_type,
            requested_date=requested_date,
            time_slot=time_slot,
            status="pending",
            notes=notes
        )
        self.session.add(booking)
        self.session.commit()
        self.session.refresh(booking)

        return self._to_dict(booking)

    def get_booking_by_id(self, booking_id: int) -> Optional[Dict[str, Any]]:
        stmt = (
            select(TourBooking)
            .options(joinedload(TourBooking.property), joinedload(TourBooking.unit))
            .where(TourBooking.booking_id == booking_id)
        )
        booking = self.session.scalars(stmt).first()
        return self._to_dict(booking) if booking else None

    def list_bookings(
        self,
        user_id: Optional[int] = None,
        property_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(TourBooking)
            .options(joinedload(TourBooking.property), joinedload(TourBooking.unit))
        )
        if user_id:
            stmt = stmt.where(TourBooking.user_id == user_id)
        if property_id:
            stmt = stmt.where(TourBooking.property_id == property_id)
        if status:
            stmt = stmt.where(TourBooking.status == status)

        stmt = stmt.order_by(TourBooking.created_at.desc()).limit(limit)
        bookings = self.session.scalars(stmt).all()
        return [self._to_dict(b) for b in bookings]

    def update_status(
        self,
        booking_id: int,
        status: str,
        manager_notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        booking = self.session.get(TourBooking, booking_id)
        if not booking:
            return None

        booking.status = status
        if manager_notes:
            booking.manager_notes = manager_notes

        self.session.commit()
        self.session.refresh(booking)
        return self._to_dict(booking)

    def _to_dict(self, b: Optional[TourBooking]) -> Dict[str, Any]:
        if not b:
            return {}
        return {
            "booking_id": b.booking_id,
            "property_id": b.property_id,
            "property_name": b.property.name if b.property else f"Property #{b.property_id}",
            "property_city": b.property.city if b.property else "",
            "unit_id": b.unit_id,
            "unit_number": b.unit.unit_number if b.unit else None,
            "user_id": b.user_id,
            "contact_name": b.contact_name,
            "contact_email": b.contact_email,
            "contact_phone": b.contact_phone,
            "tour_type": b.tour_type,
            "requested_date": b.requested_date,
            "time_slot": b.time_slot,
            "status": b.status,
            "notes": b.notes,
            "manager_notes": b.manager_notes,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
