"""
Properties & Units Router (web/routers/properties.py)
Provides public luxury catalog endpoints, unit search, and admin listing management.
"""

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Property, Tenant, TourBooking, Unit
from db.repositories.property_repo import AsyncPropertyRepository, _parse_json_field
from db.session import get_async_db
from services.cache_service import cache_service
from web.deps import get_current_user

router = APIRouter(prefix="/api/properties", tags=["Properties"])


class PropertyCreateRequest(BaseModel):
    name: str
    address: str
    city: str
    neighborhood: Optional[str] = None
    property_type: str = "residential"
    description: Optional[str] = None
    image_url: Optional[str] = None
    images: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    year_built: Optional[int] = 2024
    is_featured: bool = False
    virtual_tour_url: Optional[str] = None


class UnitCreateRequest(BaseModel):
    property_id: int
    unit_number: str
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    images: Optional[List[str]] = None
    bedrooms: int = 1
    bathrooms: float = 1.0
    square_feet: Optional[float] = 120.0
    floor_number: Optional[int] = 1
    features: Optional[List[str]] = None
    pet_policy: str = "Allowed"
    virtual_tour_url: Optional[str] = None
    monthly_rent: float
    status: str = "available"
    is_high_value: bool = False


class TourBookingCreateRequest(BaseModel):
    property_id: int
    unit_id: Optional[int] = None
    contact_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    tour_type: str = "in_person"  # in_person, virtual_guided, 3d_self_guided
    requested_date: str
    time_slot: str
    notes: Optional[str] = None


class TourStatusUpdateRequest(BaseModel):
    status: str  # confirmed, rescheduled, completed, cancelled
    manager_notes: Optional[str] = None


@router.get("")
async def list_properties(db: AsyncSession = Depends(get_async_db)):
    """List all properties with rich metadata, images, and unit counts."""
    cached = await cache_service.get_json("catalog:properties:all")
    if cached:
        return {"status": "success", "properties": cached, "cached": True}

    stmt = select(Property).options(selectinload(Property.units))
    rows = (await db.scalars(stmt)).all()
    properties = []
    for p in rows:
        properties.append({
            "property_id": p.property_id,
            "name": p.name,
            "address": p.address,
            "city": p.city,
            "neighborhood": p.neighborhood or p.city,
            "property_type": p.property_type,
            "description": p.description or "",
            "image_url": p.image_url or "/images/properties/nile_tower_ext.jpg",
            "images": _parse_json_field(p.images),
            "amenities": _parse_json_field(p.amenities),
            "year_built": p.year_built or 2024,
            "is_featured": p.is_featured,
            "virtual_tour_url": p.virtual_tour_url or "",
            "total_units": len(p.units) if p.units else p.total_units,
            "available_units": sum(1 for u in p.units if u.status == "available"),
            "starting_rent": min((float(u.monthly_rent) for u in p.units), default=15000.0)
        })

    await cache_service.set_json("catalog:properties:all", properties, expire_seconds=60)
    return {"status": "success", "properties": properties, "cached": False}


@router.get("/featured")
async def get_featured_properties(db: AsyncSession = Depends(get_async_db)):
    """List featured luxury residences for marketing landing page."""
    cached = await cache_service.get_json("catalog:properties:featured")
    if cached:
        return {"status": "success", "featured": cached, "cached": True}

    repo = AsyncPropertyRepository(db)
    featured = await repo.get_featured_properties()

    await cache_service.set_json("catalog:properties:featured", featured, expire_seconds=60)
    return {"status": "success", "featured": featured, "cached": False}


@router.get("/units/available")
async def list_available_units(
    property_id: Optional[int] = Query(None),
    city: Optional[str] = Query(None),
    max_rent: Optional[float] = Query(None),
    db: AsyncSession = Depends(get_async_db)
):
    """Query available units matching search criteria with Redis caching."""
    cache_key = f"catalog:units:available:{property_id}:{city}:{max_rent}"
    cached = await cache_service.get_json(cache_key)
    if cached:
        return {"status": "success", "units": cached, "count": len(cached), "cached": True}

    repo = AsyncPropertyRepository(db)
    units = await repo.query_available_units(property_id=property_id, city=city, max_rent=max_rent)

    await cache_service.set_json(cache_key, units, expire_seconds=60)
    return {"status": "success", "units": units, "count": len(units), "cached": False}


@router.get("/{property_id}")
async def get_property_detail(property_id: int, db: AsyncSession = Depends(get_async_db)):
    """Get full property details including units, amenities, and photos."""
    stmt = select(Property).options(selectinload(Property.units)).where(Property.property_id == property_id)
    prop = (await db.scalars(stmt)).first()
    if not prop:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not found")

    units_data = []
    for u in prop.units:
        units_data.append({
            "unit_id": u.unit_id,
            "unit_number": u.unit_number,
            "title": u.title or f"Unit {u.unit_number}",
            "description": u.description or "",
            "image_url": u.image_url or prop.image_url or "/images/properties/nile_tower_penthouse.jpg",
            "images": _parse_json_field(u.images),
            "bedrooms": u.bedrooms,
            "bathrooms": float(u.bathrooms),
            "square_feet": float(u.square_feet or 0.0),
            "floor_number": u.floor_number or 1,
            "features": _parse_json_field(u.features),
            "pet_policy": u.pet_policy or "Allowed",
            "virtual_tour_url": u.virtual_tour_url or "",
            "monthly_rent": float(u.monthly_rent),
            "status": u.status,
            "is_high_value": u.is_high_value
        })

    return {
        "status": "success",
        "property": {
            "property_id": prop.property_id,
            "name": prop.name,
            "address": prop.address,
            "city": prop.city,
            "neighborhood": prop.neighborhood or prop.city,
            "property_type": prop.property_type,
            "description": prop.description or "",
            "image_url": prop.image_url or "/images/properties/nile_tower_ext.jpg",
            "images": _parse_json_field(prop.images),
            "amenities": _parse_json_field(prop.amenities),
            "year_built": prop.year_built or 2024,
            "is_featured": prop.is_featured,
            "virtual_tour_url": prop.virtual_tour_url or "",
            "total_units": len(prop.units),
            "available_units": sum(1 for u in prop.units if u.status == "available"),
            "units": units_data
        }
    }


@router.post("")
async def create_property(req: PropertyCreateRequest, db: AsyncSession = Depends(get_async_db)):
    """Create a new property listing."""
    prop = Property(
        name=req.name,
        address=req.address,
        city=req.city,
        neighborhood=req.neighborhood or req.city,
        property_type=req.property_type,
        description=req.description,
        image_url=req.image_url or "/images/properties/nile_tower_ext.jpg",
        images=json.dumps(req.images or []),
        amenities=json.dumps(req.amenities or ["Pool", "Gym", "Concierge", "24/7 Security"]),
        year_built=req.year_built,
        is_featured=req.is_featured,
        virtual_tour_url=req.virtual_tour_url
    )
    db.add(prop)
    await db.commit()
    await db.refresh(prop)

    # Invalidate cache
    await cache_service.delete("catalog:properties:all")
    await cache_service.delete("catalog:properties:featured")

    return {"status": "success", "message": f"Property '{prop.name}' created successfully", "property_id": prop.property_id}


@router.post("/units")
async def create_unit(req: UnitCreateRequest, db: AsyncSession = Depends(get_async_db)):
    """Add a new unit to an existing property."""
    unit = Unit(
        property_id=req.property_id,
        unit_number=req.unit_number,
        title=req.title or f"Unit {req.unit_number}",
        description=req.description,
        image_url=req.image_url or "/images/properties/nile_tower_penthouse.jpg",
        images=json.dumps(req.images or []),
        bedrooms=req.bedrooms,
        bathrooms=req.bathrooms,
        square_feet=req.square_feet,
        floor_number=req.floor_number,
        features=json.dumps(req.features or ["Balcony", "Central AC"]),
        pet_policy=req.pet_policy,
        virtual_tour_url=req.virtual_tour_url,
        monthly_rent=req.monthly_rent,
        status=req.status,
        is_high_value=req.is_high_value or req.monthly_rent >= 25000.0
    )
    db.add(unit)
    await db.commit()
    await db.refresh(unit)

    # Invalidate cache
    await cache_service.delete("catalog:properties:all")
    await cache_service.delete("catalog:properties:featured")

    return {"status": "success", "message": f"Unit {unit.unit_number} added successfully", "unit_id": unit.unit_id}


# --- TOUR BOOKINGS & INQUIRIES ---

@router.post("/tours")
async def book_tour(req: TourBookingCreateRequest, db: AsyncSession = Depends(get_async_db)):
    """Book an accompanied in-person or 3D Matterport guided viewing experience."""
    booking = TourBooking(
        property_id=req.property_id,
        unit_id=req.unit_id,
        contact_name=req.contact_name,
        contact_email=req.contact_email,
        contact_phone=req.contact_phone,
        tour_type=req.tour_type,
        requested_date=req.requested_date,
        time_slot=req.time_slot,
        status="pending",
        notes=req.notes
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    stmt = select(Property).where(Property.property_id == req.property_id)
    prop = (await db.scalars(stmt)).first()

    return {
        "status": "success",
        "booking_id": booking.booking_id,
        "message": f"Tour confirmed for {booking.contact_name} at {prop.name if prop else 'the property'} on {booking.requested_date} at {booking.time_slot}.",
        "booking": {
            "booking_id": booking.booking_id,
            "property_id": booking.property_id,
            "property_name": prop.name if prop else "",
            "tour_type": booking.tour_type,
            "requested_date": booking.requested_date,
            "time_slot": booking.time_slot,
            "status": booking.status,
            "contact_email": booking.contact_email,
            "contact_name": booking.contact_name
        }
    }


@router.get("/tours/list")
async def list_tour_bookings(
    property_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db)
):
    """List scheduled tour bookings with status and date filtering for managers and users."""
    stmt = (
        select(TourBooking)
        .options(selectinload(TourBooking.property), selectinload(TourBooking.unit))
    )
    if property_id:
        stmt = stmt.where(TourBooking.property_id == property_id)
    if status:
        stmt = stmt.where(TourBooking.status == status)

    stmt = stmt.order_by(TourBooking.created_at.desc()).limit(100)
    rows = (await db.scalars(stmt)).all()

    bookings = []
    for b in rows:
        bookings.append({
            "booking_id": b.booking_id,
            "property_id": b.property_id,
            "property_name": b.property.name if b.property else f"Property #{b.property_id}",
            "property_city": b.property.city if b.property else "",
            "unit_id": b.unit_id,
            "unit_number": b.unit.unit_number if b.unit else None,
            "contact_name": b.contact_name,
            "contact_email": b.contact_email,
            "contact_phone": b.contact_phone,
            "tour_type": b.tour_type,
            "requested_date": b.requested_date,
            "time_slot": b.time_slot,
            "status": b.status,
            "notes": b.notes,
            "manager_notes": b.manager_notes,
            "created_at": b.created_at.isoformat() if b.created_at else None
        })

    return {"status": "success", "bookings": bookings, "count": len(bookings)}


@router.patch("/tours/{booking_id}")
async def update_tour_status(
    booking_id: int,
    req: TourStatusUpdateRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Approve, reschedule, complete, or cancel a tour booking (Property Manager & Admin)."""
    booking = await db.get(TourBooking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail=f"Tour booking #{booking_id} not found")

    booking.status = req.status
    if req.manager_notes:
        booking.manager_notes = req.manager_notes

    await db.commit()
    await db.refresh(booking)

    return {
        "status": "success",
        "message": f"Tour booking #{booking_id} updated to '{req.status}'",
        "booking_id": booking.booking_id,
        "new_status": booking.status
    }


@router.post("/inquire")
async def submit_inquiry(req: TourBookingCreateRequest, db: AsyncSession = Depends(get_async_db)):
    """Legacy alias for tour and VIP inquiry creation."""
    return await book_tour(req, db)
