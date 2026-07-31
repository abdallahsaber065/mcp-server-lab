import sqlite3
import os
from typing import Dict, List, Any, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "db", "realty_mcp.db")
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "..", "db", "schema.sql")
SEED_FILE = os.path.join(os.path.dirname(__file__), "..", "db", "seed.sql")

def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(reset: bool = False):
    """Initialize database from schema and seed data if not existing or reset requested."""
    db_exists = os.path.exists(DB_FILE)
    if reset and db_exists:
        os.remove(DB_FILE)
        db_exists = False

    conn = get_db_connection()
    with conn:
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM properties;")
        if cur.fetchone()[0] == 0:
            with open(SEED_FILE, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
    conn.close()

def query_available_units(property_id: Optional[int] = None, city: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    sql = """
        SELECT u.unit_id, p.name as property_name, p.city, u.unit_number, u.bedrooms, u.monthly_rent, u.status, u.is_high_value
        FROM units u
        JOIN properties p ON u.property_id = p.property_id
        WHERE 1=1
    """
    params = []
    if property_id:
        sql += " AND u.property_id = ?"
        params.append(property_id)
    if city:
        sql += " AND p.city = ?"
        params.append(city)

    sql += " ORDER BY u.monthly_rent ASC;"
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def query_tenant_lease(email: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    sql = """
        SELECT t.tenant_id, t.full_name, t.email, t.role,
               l.lease_id, l.unit_id, u.unit_number, p.name as property_name,
               l.start_date, l.end_date, l.monthly_rent, l.is_active, l.requires_executive_signoff, l.status as lease_status
        FROM tenants t
        LEFT JOIN leases l ON t.tenant_id = l.tenant_id
        LEFT JOIN units u ON l.unit_id = u.unit_id
        LEFT JOIN properties p ON u.property_id = p.property_id
        WHERE t.email = ?
        ORDER BY l.created_at DESC LIMIT 1;
    """
    cur = conn.cursor()
    cur.execute(sql, [email])
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def create_maintenance_record(tenant_id: int, unit_id: int, issue_description: str, priority: str) -> Dict[str, Any]:
    conn = get_db_connection()
    with conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO maintenance_requests (unit_id, tenant_id, issue_description, priority, status)
            VALUES (?, ?, ?, ?, 'pending');
        """, (unit_id, tenant_id, issue_description, priority))
        request_id = cur.lastrowid
    conn.close()
    return {
        "request_id": request_id,
        "unit_id": unit_id,
        "tenant_id": tenant_id,
        "issue_description": issue_description,
        "priority": priority,
        "status": "pending"
    }

def update_lease_terms(lease_id: int, new_rent: float, duration_months: int, signed_off_by_executive: bool = False) -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT lease_id, monthly_rent, requires_executive_signoff, unit_id FROM leases WHERE lease_id = ?;", (lease_id,))
    lease = cur.fetchone()
    if not lease:
        conn.close()
        raise ValueError(f"Lease ID {lease_id} not found.")

    old_rent = lease["monthly_rent"]
    requires_exec = bool(lease["requires_executive_signoff"])
    
    # Check if discount > 15%
    discount_pct = ((old_rent - new_rent) / old_rent) * 100.0 if old_rent > 0 else 0
    if (discount_pct > 15.0 or requires_exec) and not signed_off_by_executive:
        conn.close()
        return {
            "success": False,
            "requires_elicitation": True,
            "reason": f"Discount of {discount_pct:.1f}% or high-value status requires explicit Executive Sign-off.",
            "lease_id": lease_id,
            "proposed_rent": new_rent
        }

    with conn:
        conn.execute("""
            UPDATE leases
            SET monthly_rent = ?, status = 'active', is_active = 1
            WHERE lease_id = ?;
        """, (new_rent, lease_id))
    conn.close()
    
    return {
        "success": True,
        "requires_elicitation": False,
        "lease_id": lease_id,
        "previous_rent": old_rent,
        "updated_rent": new_rent,
        "duration_months": duration_months,
        "status": "active"
    }
