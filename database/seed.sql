-- MaskGate Database Seed Data
-- This file contains sample data for testing and demonstration

-- Insert sample users
INSERT INTO users (username, email, password_hash, full_name) VALUES
('admin', 'admin@maskgate.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYlWnJMq.3a', 'System Administrator'),
('analyst', 'analyst@maskgate.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYlWnJMq.3a', 'Data Analyst'),
('auditor', 'auditor@maskgate.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYlWnJMq.3a', 'Security Auditor')
ON CONFLICT (username) DO NOTHING;

-- Insert sample masking policies
INSERT INTO masking_policies (name, description, table_name, column_name, strategy, parameters, is_active, created_by) VALUES
('Email Redaction', 'Masks email addresses in customer data', 'customers', 'email', 'email_mask', '{}', true, 1),
('SSN Masking', 'Masks social security numbers', 'customers', 'ssn', 'ssn_mask', '{}', true, 1),
('Phone Masking', 'Masks phone numbers', 'customers', 'phone', 'phone_mask', '{}', true, 1),
('Credit Card Protection', 'Masks credit card numbers', 'orders', 'credit_card_number', 'credit_card_mask', '{}', true, 1),
('Employee SSN Masking', 'Masks employee SSNs', 'employees', 'ssn', 'ssn_mask', '{}', true, 1),
('Employee Email Masking', 'Masks employee emails', 'employees', 'email', 'email_mask', '{}', true, 1)
ON CONFLICT (table_name, column_name, strategy) DO NOTHING;

-- Insert sample customers
INSERT INTO customers (first_name, last_name, email, phone, ssn, address, city, state, zip_code, date_of_birth) VALUES
('John', 'Smith', 'john.smith@email.com', '555-123-4567', '123-45-6789', '123 Main St', 'New York', 'NY', '10001', '1985-05-15'),
('Jane', 'Doe', 'jane.doe@email.com', '555-234-5678', '234-56-7890', '456 Oak Ave', 'Los Angeles', 'CA', '90001', '1990-08-22'),
('Robert', 'Johnson', 'robert.johnson@email.com', '555-345-6789', '345-67-8901', '789 Pine Rd', 'Chicago', 'IL', '60601', '1978-12-10'),
('Emily', 'Williams', 'emily.williams@email.com', '555-456-7890', '456-78-9012', '321 Elm St', 'Houston', 'TX', '77001', '1992-03-28'),
('Michael', 'Brown', 'michael.brown@email.com', '555-567-8901', '567-89-0123', '654 Maple Dr', 'Phoenix', 'AZ', '85001', '1988-07-14'),
('Sarah', 'Davis', 'sarah.davis@email.com', '555-678-9012', '678-90-1234', '987 Cedar Ln', 'Philadelphia', 'PA', '19101', '1995-11-03'),
('David', 'Miller', 'david.miller@email.com', '555-789-0123', '789-01-2345', '147 Birch Blvd', 'San Antonio', 'TX', '78201', '1982-09-19'),
('Lisa', 'Wilson', 'lisa.wilson@email.com', '555-890-1234', '890-12-3456', '258 Spruce Way', 'San Diego', 'CA', '92101', '1991-04-25'),
('James', 'Taylor', 'james.taylor@email.com', '555-901-2345', '901-23-4567', '369 Ash Ct', 'Dallas', 'TX', '75201', '1986-01-30'),
('Jennifer', 'Anderson', 'jennifer.anderson@email.com', '555-012-3456', '012-34-5678', '741 Willow Pl', 'San Jose', 'CA', '95101', '1993-06-12')
ON CONFLICT (email) DO NOTHING;

-- Insert sample orders
INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_address, credit_card_number, credit_card_expiry) VALUES
(1, '2024-01-15 10:30:00', 125.50, 'completed', '123 Main St, New York, NY 10001', '4111111111111111', '12/25'),
(1, '2024-02-20 14:45:00', 89.99, 'completed', '123 Main St, New York, NY 10001', '4111111111111111', '12/25'),
(2, '2024-01-22 09:15:00', 250.00, 'completed', '456 Oak Ave, Los Angeles, CA 90001', '5555555555554444', '08/26'),
(3, '2024-03-10 16:20:00', 175.25, 'shipped', '789 Pine Rd, Chicago, IL 60601', '378282246310005', '03/27'),
(4, '2024-02-05 11:00:00', 99.99, 'completed', '321 Elm St, Houston, TX 77001', '6011111111111117', '11/25'),
(5, '2024-03-18 13:30:00', 310.75, 'processing', '654 Maple Dr, Phoenix, AZ 85001', '3530111333300000', '07/26'),
(6, '2024-01-28 15:45:00', 145.00, 'completed', '987 Cedar Ln, Philadelphia, PA 19101', '5555555555554444', '09/28'),
(7, '2024-02-12 10:00:00', 225.50, 'shipped', '147 Birch Blvd, San Antonio, TX 78201', '4111111111111111', '01/27'),
(8, '2024-03-22 14:15:00', 180.25, 'processing', '258 Spruce Way, San Diego, CA 92101', '6011111111111117', '06/26'),
(9, '2024-01-08 09:30:00', 295.00, 'completed', '369 Ash Ct, Dallas, TX 75201', '371449635398431', '10/25')
ON CONFLICT DO NOTHING;

-- Insert sample employees
INSERT INTO employees (first_name, last_name, email, phone, ssn, hire_date, salary, department, address) VALUES
('Alex', 'Thompson', 'alex.thompson@company.com', '555-111-2222', '111-22-3333', '2020-03-15', 75000.00, 'Engineering', '100 Tech Park, Building A'),
('Maria', 'Garcia', 'maria.garcia@company.com', '555-222-3333', '222-33-4444', '2019-07-22', 68000.00, 'Marketing', '100 Tech Park, Building B'),
('Steven', 'Martinez', 'steven.martinez@company.com', '555-333-4444', '333-44-5555', '2021-01-10', 82000.00, 'Engineering', '100 Tech Park, Building A'),
('Laura', 'Hernandez', 'laura.hernandez@company.com', '555-444-5555', '444-55-6666', '2020-09-05', 72000.00, 'Sales', '100 Tech Park, Building C'),
('Kevin', 'Lopez', 'kevin.lopez@company.com', '555-555-6666', '555-66-7777', '2022-02-28', 65000.00, 'Support', '100 Tech Park, Building D'),
('Amanda', 'Gonzalez', 'amanda.gonzalez@company.com', '555-666-7777', '666-77-8888', '2019-11-18', 78000.00, 'Engineering', '100 Tech Park, Building A'),
('Brian', 'Wilson', 'brian.wilson@company.com', '555-777-8888', '777-88-9999', '2021-06-30', 70000.00, 'Marketing', '100 Tech Park, Building B'),
('Nicole', 'Anderson', 'nicole.anderson@company.com', '555-888-9999', '888-99-0000', '2020-04-12', 74000.00, 'HR', '100 Tech Park, Building E'),
('Carlos', 'Thomas', 'carlos.thomas@company.com', '555-999-0000', '999-00-1111', '2022-08-15', 62000.00, 'Support', '100 Tech Park, Building D'),
('Stephanie', 'Moore', 'stephanie.moore@company.com', '555-000-1111', '000-11-2222', '2019-12-01', 85000.00, 'Engineering', '100 Tech Park, Building A')
ON CONFLICT (email) DO NOTHING;

-- Insert sample query history
INSERT INTO query_history (user_id, query_text, query_hash, execution_time, row_count, was_masked, executed_at) VALUES
(2, 'SELECT * FROM customers LIMIT 10', 'abc123def456', 0.125, 10, true, '2024-03-01 10:00:00'),
(2, 'SELECT COUNT(*) FROM orders', 'def456ghi789', 0.045, 1, false, '2024-03-01 10:05:00'),
(3, 'SELECT first_name, last_name, email FROM employees', 'ghi789jkl012', 0.089, 10, true, '2024-03-01 11:00:00'),
(2, 'SELECT * FROM orders WHERE status = completed', 'jkl012mno345', 0.156, 6, true, '2024-03-01 11:30:00'),
(3, 'SELECT COUNT(*) FROM customers WHERE state = CA', 'mno345pqr678', 0.034, 1, false, '2024-03-01 12:00:00')
ON CONFLICT DO NOTHING;

-- Insert sample audit logs
INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, ip_address, created_at) VALUES
(1, 'CREATE', 'masking_policy', 1, '{"name": "Email Redaction"}', '192.168.1.100', '2024-02-01 09:00:00'),
(1, 'CREATE', 'masking_policy', 2, '{"name": "SSN Masking"}', '192.168.1.100', '2024-02-01 09:05:00'),
(2, 'READ', 'customers', null, '{"query": "SELECT * FROM customers LIMIT 10"}', '192.168.1.101', '2024-03-01 10:00:00'),
(3, 'READ', 'employees', null, '{"query": "SELECT first_name, last_name, email FROM employees"}', '192.168.1.102', '2024-03-01 11:00:00'),
(1, 'UPDATE', 'masking_policy', 1, '{"is_active": false}', '192.168.1.100', '2024-03-05 14:00:00')
ON CONFLICT DO NOTHING;
