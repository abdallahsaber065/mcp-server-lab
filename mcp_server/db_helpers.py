import sqlite3
import os
import time
import json
from typing import Dict, List, Any, Optional

def get_db_file_path() -> str:
    return os.getenv("MCP_DB_FILE", os.path.join(os.path.dirname(__file__), "..", "db", "realty_mcp.db"))

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "..", "db", "schema.sql")
SEED_FILE = os.path.join(os.path.dirname(__file__), "..", "db", "seed.sql")

def get_db_connection() -> sqlite3.Connection:
    db_file = get_db_file_path()
    os.makedirs(os.path.dirname(db_file), exist_ok=True)
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(reset: bool = False):
    """Initialize database from schema, seed data, and chat history tables."""
    db_file = get_db_file_path()
    db_exists = os.path.exists(db_file)
    if reset and db_exists:
        try:
            os.remove(db_file)
            db_exists = False
        except Exception:
            pass

    conn = get_db_connection()
    with conn:
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM properties;")
        if cur.fetchone()[0] == 0:
            with open(SEED_FILE, "r", encoding="utf-8") as f:
                conn.executescript(f.read())

        # Initialize Chat Sessions & Messages Tables
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                role TEXT DEFAULT 'property_manager',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                msg_type TEXT NOT NULL, -- 'user', 'assistant', 'tool_trace', 'elicitation'
                content TEXT,
                tool_name TEXT,
                tool_args TEXT,
                tool_result TEXT,
                elicitation_payload TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
            );
        """)
    conn.close()

# --- CHAT PERSISTENCE HELPERS ---

def create_chat_session(session_id: str, title: str = "محادثة جديدة", role: str = "property_manager") -> Dict[str, Any]:
    init_db(reset=False)
    conn = get_db_connection()
    with conn:
        conn.execute("""
            INSERT INTO chat_sessions (session_id, title, role, created_at, updated_at)
            VALUES (?, ?, ?, datetime('now'), datetime('now'));
        """, (session_id, title, role))
    conn.close()
    return {"session_id": session_id, "title": title, "role": role}

def get_all_chat_sessions() -> List[Dict[str, Any]]:
    init_db(reset=False)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT session_id, title, role, created_at, updated_at
        FROM chat_sessions
        ORDER BY updated_at DESC;
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_chat_messages(session_id: str) -> List[Dict[str, Any]]:
    init_db(reset=False)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT message_id, session_id, msg_type, content, tool_name, tool_args, tool_result, elicitation_payload, created_at
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY message_id ASC;
    """, (session_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    
    # Format JSON strings back into objects
    formatted = []
    for r in rows:
        item = {
            "id": r["message_id"],
            "type": r["msg_type"],
            "content": r["content"],
            "created_at": r["created_at"]
        }
        if r["tool_name"]:
            item["tool"] = r["tool_name"]
            item["args"] = json.loads(r["tool_args"]) if r["tool_args"] else {}
            item["result"] = json.loads(r["tool_result"]) if r["tool_result"] else {}
        if r["elicitation_payload"]:
            item["payload"] = json.loads(r["elicitation_payload"])
        formatted.append(item)
    return formatted

def save_chat_message(
    session_id: str,
    msg_type: str,
    content: Optional[str] = None,
    tool_name: Optional[str] = None,
    tool_args: Optional[Dict[str, Any]] = None,
    tool_result: Optional[Dict[str, Any]] = None,
    elicitation_payload: Optional[Dict[str, Any]] = None
) -> int:
    init_db(reset=False)
    conn = get_db_connection()
    with conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO chat_messages (session_id, msg_type, content, tool_name, tool_args, tool_result, elicitation_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            session_id,
            msg_type,
            content,
            tool_name,
            json.dumps(tool_args, ensure_ascii=False) if tool_args else None,
            json.dumps(tool_result, ensure_ascii=False) if tool_result else None,
            json.dumps(elicitation_payload, ensure_ascii=False) if elicitation_payload else None
        ))
        msg_id = cur.lastrowid
        
        # Update session title on first user message in session
        if msg_type == 'user' and content:
            clean_content = content.strip()
            if clean_content:
                snippet = clean_content[:35] + ("..." if len(clean_content) > 35 else "")
                cur.execute("SELECT title FROM chat_sessions WHERE session_id = ?;", (session_id,))
                t_row = cur.fetchone()
                current_title = t_row[0] if t_row else ""
                
                cur.execute("SELECT COUNT(*) FROM chat_messages WHERE session_id = ? AND msg_type = 'user';", (session_id,))
                user_msg_count = cur.fetchone()[0]
                
                if user_msg_count <= 1 or any(k in current_title.strip().lower() for k in ['new conversation', 'new chat', 'محادثة جديدة', '']):
                    conn.execute("UPDATE chat_sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?;", (snippet, session_id))

                else:
                    conn.execute("UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?;", (session_id,))
            else:
                conn.execute("UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?;", (session_id,))
        else:
            conn.execute("UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?;", (session_id,))

    conn.close()
    return msg_id




def delete_chat_session(session_id: str) -> bool:
    init_db(reset=False)
    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM chat_sessions WHERE session_id = ?;", (session_id,))
    conn.close()
    return True

def update_chat_session_role(session_id: str, role: str) -> bool:
    init_db(reset=False)
    conn = get_db_connection()
    with conn:
        conn.execute("UPDATE chat_sessions SET role = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?;", (role, session_id))
    conn.close()
    return True

def get_chat_session_role(session_id: str) -> str:
    init_db(reset=False)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT role FROM chat_sessions WHERE session_id = ?;", (session_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else "property_manager"

# --- REPOSITORY DB OPERATIONAL HELPERS ---

def query_available_units(city: Optional[str] = None, min_beds: Optional[int] = None, max_rent: Optional[float] = None, property_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    sql = """
        SELECT u.unit_id, p.name as property_name, p.city, p.address, u.unit_number, u.bedrooms, u.monthly_rent, u.status, u.is_high_value
        FROM units u
        JOIN properties p ON u.property_id = p.property_id
        WHERE u.status = 'available'
    """
    params = []
    if property_id is not None:
        sql += " AND p.property_id = ?"
        params.append(property_id)
    if city:
        sql += " AND p.city = ?"
        params.append(city)
    if min_beds is not None:
        sql += " AND u.bedrooms >= ?"
        params.append(min_beds)
    if max_rent is not None:
        sql += " AND u.monthly_rent <= ?"
        params.append(max_rent)
    
    sql += " ORDER BY u.monthly_rent ASC;"
    
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def query_tenant_lease(email: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    sql = """
        SELECT l.lease_id, t.full_name as tenant_name, t.email, p.name as property_name, u.unit_number,
               l.monthly_rent, l.start_date, l.end_date, l.status, l.requires_executive_signoff
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

get_available_units = query_available_units
get_active_lease_by_email = query_tenant_lease

def create_maintenance_record(tenant_id: int, unit_id: int, issue_description: str, priority: str) -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT unit_id FROM units WHERE unit_id = ?;", (unit_id,))
    if not cur.fetchone():
        conn.close()
        raise ValueError(f"Unit ID {unit_id} not found in property database. Please verify the unit number.")
        
    cur.execute("SELECT tenant_id FROM tenants WHERE tenant_id = ?;", (tenant_id,))
    if not cur.fetchone():
        conn.close()
        raise ValueError(f"Tenant ID {tenant_id} not found in property database.")
        
    with conn:
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
