PRAGMA foreign_keys = ON;

-- ============================================================================
-- Properties (5 Properties across Cairo, Alexandria, Giza)
-- ============================================================================
INSERT INTO properties (property_id, name, address, city, total_units) VALUES
(1, 'Cornerstone Heights', '12 El-Tahrir Square', 'Cairo', 10),
(2, 'Alexandria Beachfront Towers', '45 Corniche El-Nile', 'Alexandria', 8),
(3, 'Giza Commercial & Residential Center', '88 Pyramids Road', 'Giza', 6),
(4, 'Zamalek Royal Suites', '24 26th of July Street', 'Cairo', 5),
(5, 'Gleem Bay Residence', '102 El-Geish Road, Gleem', 'Alexandria', 4);

-- ============================================================================
-- Units (18 Apartments with varying statuses, prices, and high-value tags)
-- ============================================================================
INSERT INTO units (unit_id, property_id, unit_number, bedrooms, monthly_rent, status, is_high_value) VALUES
-- Cornerstone Heights (Cairo)
(101, 1, 'A-101', 2, 12000.0, 'occupied', 0),
(102, 1, 'A-102', 3, 18000.0, 'available', 0),
(103, 1, 'Penthouse-1', 4, 45000.0, 'available', 1),
(104, 1, 'A-104', 1, 9000.0, 'available', 0),
(105, 1, 'A-201', 3, 22000.0, 'occupied', 0),

-- Alexandria Beachfront Towers (Alexandria)
(201, 2, 'B-201', 2, 15000.0, 'occupied', 0),
(202, 2, 'B-202', 1, 9500.0, 'under_maintenance', 0),
(203, 2, 'B-301', 3, 28000.0, 'available', 0),
(204, 2, 'Sky-Penthouse-B', 5, 55000.0, 'reserved', 1),

-- Giza Commercial & Residential Center (Giza)
(301, 3, 'Suite-301', 5, 60000.0, 'occupied', 1),
(302, 3, 'Suite-302', 2, 14000.0, 'available', 0),
(303, 3, 'Suite-401', 3, 20000.0, 'occupied', 0),

-- Zamalek Royal Suites (Cairo)
(401, 4, 'Royal-101', 3, 35000.0, 'occupied', 0),
(402, 4, 'Royal-Penthouse', 4, 75000.0, 'available', 1),
(403, 4, 'Royal-201', 2, 28000.0, 'under_maintenance', 0),

-- Gleem Bay Residence (Alexandria)
(501, 5, 'G-101', 2, 16500.0, 'available', 0),
(502, 5, 'G-201', 3, 24000.0, 'occupied', 0),
(503, 5, 'G-301', 4, 48000.0, 'available', 1);

-- ============================================================================
-- Tenants & Staff
-- ============================================================================
INSERT INTO tenants (tenant_id, full_name, email, phone, role) VALUES
(1, 'Amr Hassan', 'amr.hassan@example.com', '+201001234567', 'tenant'),
(2, 'Noha El-Sayed', 'noha.elsayed@example.com', '+201119876543', 'tenant'),
(3, 'Tarek Mahmoud', 'tarek.m@cornerstonerealty.eg', '+201223334444', 'property_manager'),
(4, 'Laila Fouad', 'laila.fouad@cornerstonerealty.eg', '+201000000001', 'executive_admin'),
(5, 'Omar Farouk', 'omar.farouk@example.com', '+201005556677', 'tenant'),
(6, 'Yasmine Ibrahim', 'yasmine.ibrahim@example.com', '+201124445555', 'tenant'),
(7, 'Khaled Abdelrahman', 'khaled.abdel@example.com', '+201207778899', 'tenant'),
(8, 'Mariam Soliman', 'mariam.soliman@example.com', '+201091112233', 'tenant');

-- ============================================================================
-- Leases / Contracts
-- ============================================================================
INSERT INTO leases (lease_id, unit_id, tenant_id, start_date, end_date, monthly_rent, is_active, requires_executive_signoff, status) VALUES
(1, 101, 1, '2025-01-01', '2026-01-01', 12000.0, 1, 0, 'active'),
(2, 201, 2, '2024-06-01', '2025-06-01', 15000.0, 0, 0, 'expired'),
(3, 301, 2, '2026-01-01', '2027-01-01', 60000.0, 1, 1, 'pending_approval'),
(4, 105, 5, '2025-03-01', '2026-03-01', 22000.0, 1, 0, 'active'),
(5, 401, 6, '2025-02-15', '2026-02-15', 35000.0, 1, 0, 'active'),
(6, 402, 7, '2026-05-01', '2027-05-01', 75000.0, 0, 1, 'pending_approval'),
(7, 502, 8, '2024-11-01', '2025-11-01', 24000.0, 1, 0, 'active'),
(8, 303, 1, '2025-04-01', '2026-04-01', 20000.0, 1, 0, 'active');

-- ============================================================================
-- Maintenance Requests
-- ============================================================================
INSERT INTO maintenance_requests (request_id, unit_id, tenant_id, issue_description, priority, status) VALUES
(1, 101, 1, 'Air conditioner leaking water in main bedroom', 'high', 'in_progress'),
(2, 202, 2, 'Water pipe burst flooding kitchen area', 'urgent', 'pending'),
(3, 403, 6, 'Electrical circuit breaker keeps tripping', 'urgent', 'assigned'),
(4, 105, 5, 'Balcony door lock is jammed and hard to turn', 'medium', 'completed'),
(5, 502, 8, 'Water heater temperature control not working properly', 'medium', 'pending'),
(6, 301, 2, 'Elevator access keycard failing intermittently', 'low', 'in_progress');
