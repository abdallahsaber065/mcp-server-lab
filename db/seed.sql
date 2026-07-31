INSERT INTO properties (property_id, name, address, city, total_units) VALUES
(1, 'Cornerstone Heights', '12 El-Tahrir Square', 'Cairo', 10),
(2, 'Alexandria Beachfront Towers', '45 Corniche El-Nile', 'Alexandria', 8),
(3, 'Giza Commercial Center', '88 Pyramids Road', 'Giza', 5);

INSERT INTO units (unit_id, property_id, unit_number, bedrooms, monthly_rent, status, is_high_value) VALUES
(101, 1, 'A-101', 2, 12000.0, 'occupied', 0),
(102, 1, 'A-102', 3, 18000.0, 'available', 0),
(103, 1, 'Penthouse-1', 4, 45000.0, 'available', 1),
(201, 2, 'B-201', 2, 15000.0, 'occupied', 0),
(202, 2, 'B-202', 1, 9500.0, 'under_maintenance', 0),
(301, 3, 'Suite-301', 5, 60000.0, 'occupied', 1);

INSERT INTO tenants (tenant_id, full_name, email, phone, role) VALUES
(1, 'Amr Hassan', 'amr.hassan@example.com', '+201001234567', 'tenant'),
(2, 'Noha El-Sayed', 'noha.elsayed@example.com', '+201119876543', 'tenant'),
(3, 'Tarek Mahmoud', 'tarek.m@cornerstonerealty.eg', '+201223334444', 'property_manager'),
(4, 'Laila Fouad', 'laila.fouad@cornerstonerealty.eg', '+201000000001', 'executive_admin');

INSERT INTO leases (lease_id, unit_id, tenant_id, start_date, end_date, monthly_rent, is_active, requires_executive_signoff, status) VALUES
(1, 101, 1, '2025-01-01', '2026-01-01', 12000.0, 1, 0, 'active'),
(2, 201, 2, '2024-06-01', '2025-06-01', 15000.0, 0, 0, 'expired'),
(3, 301, 2, '2026-01-01', '2027-01-01', 60000.0, 1, 1, 'pending_approval');

INSERT INTO maintenance_requests (request_id, unit_id, tenant_id, issue_description, priority, status) VALUES
(1, 101, 1, 'Air conditioner leaking water in main bedroom', 'high', 'in_progress'),
(2, 202, 2, 'Water pipe burst flooding kitchen area', 'urgent', 'pending');
