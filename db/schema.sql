PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS properties (
    property_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    address TEXT NOT NULL,
    city TEXT NOT NULL CHECK(city IN ('Cairo', 'Alexandria', 'Giza')),
    total_units INTEGER NOT NULL CHECK(total_units > 0),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS units (
    unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    unit_number TEXT NOT NULL,
    bedrooms INTEGER NOT NULL CHECK(bedrooms >= 0),
    monthly_rent REAL NOT NULL CHECK(monthly_rent > 0),
    status TEXT NOT NULL DEFAULT 'available' CHECK(status IN ('available', 'occupied', 'under_maintenance', 'reserved')),
    is_high_value INTEGER NOT NULL DEFAULT 0 CHECK(is_high_value IN (0, 1)),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE,
    UNIQUE(property_id, unit_number)
);

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'tenant' CHECK(role IN ('tenant', 'property_manager', 'executive_admin')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS leases (
    lease_id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER NOT NULL,
    tenant_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    monthly_rent REAL NOT NULL CHECK(monthly_rent > 0),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    requires_executive_signoff INTEGER NOT NULL DEFAULT 0 CHECK(requires_executive_signoff IN (0, 1)),
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'pending_approval', 'expired', 'terminated')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (unit_id) REFERENCES units(unit_id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE RESTRICT,
    CHECK(end_date > start_date)
);

CREATE TABLE IF NOT EXISTS maintenance_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER NOT NULL,
    tenant_id INTEGER NOT NULL,
    issue_description TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'urgent')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'assigned', 'in_progress', 'completed', 'rejected')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (unit_id) REFERENCES units(unit_id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_units_status ON units(status);
CREATE INDEX IF NOT EXISTS idx_leases_tenant ON leases(tenant_id);
