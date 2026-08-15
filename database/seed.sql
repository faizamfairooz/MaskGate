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
('Patient Email Masking', 'Masks patient email addresses', 'patients', 'email', 'email_mask', '{}', true, 1),
('Patient Phone Masking', 'Masks patient phone numbers', 'patients', 'phone', 'phone_mask', '{}', true, 1),
('Patient Address Masking', 'Masks patient addresses', 'patients', 'address', 'partial_mask', '{}', true, 1),
('Patient DOB Masking', 'Masks patient dates of birth', 'patients', 'date_of_birth', 'date_mask', '{}', true, 1),
('Blood Group Masking', 'Masks patient blood group information', 'patients', 'blood_group', 'redact', '{}', true, 1),
('Emergency Contact Masking', 'Masks emergency contact information', 'patients', 'emergency_contact', 'partial_mask', '{}', true, 1),
('Diagnosis Masking', 'Masks medical diagnosis information', 'medical_records', 'diagnosis', 'partial_mask', '{}', true, 1),
('Medication Masking', 'Masks medication information', 'medical_records', 'medication', 'partial_mask', '{}', true, 1),
('Allergies Masking', 'Masks allergy information', 'medical_records', 'allergies', 'partial_mask', '{}', true, 1),
('Doctor Name Masking', 'Masks doctor names in appointments', 'appointments', 'doctor_name', 'partial_mask', '{}', true, 1)
ON CONFLICT (table_name, column_name) DO NOTHING;

-- Insert sample patients
INSERT INTO patients (full_name, date_of_birth, blood_group, phone, email, address, emergency_contact) VALUES
('Sarah Johnson', '1985-03-15', 'A+', '555-123-4567', 'sarah.johnson@email.com', '123 Medical Center Dr, Boston, MA 02101', 'Michael Johnson - 555-999-8888'),
('James Williams', '1990-08-22', 'O-', '555-234-5678', 'james.williams@email.com', '456 Health Way, Los Angeles, CA 90001', 'Patricia Williams - 555-888-7777'),
('Emily Davis', '1978-12-10', 'B+', '555-345-6789', 'emily.davis@email.com', '789 Wellness Blvd, Chicago, IL 60601', 'Robert Davis - 555-777-6666'),
('Michael Brown', '1992-04-28', 'AB+', '555-456-7890', 'michael.brown@email.com', '321 Care Ave, Houston, TX 77001', 'Linda Brown - 555-666-5555'),
('Jessica Miller', '1988-07-14', 'A-', '555-567-8901', 'jessica.miller@email.com', '654 Hospital Ln, Phoenix, AZ 85001', 'David Miller - 555-555-4444'),
('David Wilson', '1995-11-03', 'O+', '555-678-9012', 'david.wilson@email.com', '987 Clinic Rd, Philadelphia, PA 19101', 'Susan Wilson - 555-444-3333'),
('Amanda Moore', '1982-09-19', 'B-', '555-789-0123', 'amanda.moore@email.com', '147 Health Center Ct, San Antonio, TX 78201', 'Thomas Moore - 555-333-2222'),
('Christopher Taylor', '1991-05-25', 'AB-', '555-890-1234', 'christopher.taylor@email.com', '258 Medical Plaza, San Diego, CA 92101', 'Elizabeth Taylor - 555-222-1111'),
('Matthew Anderson', '1986-02-28', 'A+', '555-901-2345', 'matthew.anderson@email.com', '369 Wellness Center, Dallas, TX 75201', 'Jennifer Anderson - 555-111-0000'),
('Ashley Thomas', '1993-06-12', 'O-', '555-012-3456', 'ashley.thomas@email.com', '741 Care Complex, San Jose, CA 95101', 'John Thomas - 555-000-9999')
ON CONFLICT (email) DO NOTHING;

-- Insert sample medical records
INSERT INTO medical_records (patient_id, diagnosis, medication, allergies, notes, visit_date) VALUES
(1, 'Hypertension Stage 1', 'Lisinopril 10mg daily', 'Penicillin', 'Patient reports occasional headaches', '2024-01-15'),
(1, 'Annual Physical', 'Multivitamin daily', 'None', 'Overall health good, blood pressure controlled', '2024-06-20'),
(2, 'Type 2 Diabetes', 'Metformin 500mg twice daily', 'Sulfa drugs', 'Blood sugar levels improving with diet changes', '2024-02-10'),
(2, 'Diabetic Follow-up', 'Metformin 500mg twice daily', 'Sulfa drugs', 'A1C reduced from 8.5 to 7.2', '2024-05-15'),
(3, 'Migraine with Aura', 'Sumatriptan as needed', 'None', 'Stress appears to be a trigger', '2024-03-22'),
(4, 'Generalized Anxiety Disorder', 'Sertraline 50mg daily', 'None', 'Therapy recommended in addition to medication', '2024-01-28'),
(5, 'Asthma (Mild)', 'Albuterol inhaler as needed', 'None', 'Symptoms worsen during allergy season', '2024-04-12'),
(6, 'Osteoarthritis (Knee)', 'Ibuprofen 400mg as needed', 'Aspirin', 'Physical therapy recommended', '2024-02-05'),
(7, 'Hypothyroidism', 'Levothyroxine 75mcg daily', 'None', 'TSH levels now within normal range', '2024-03-18'),
(8, 'Gastroesophageal Reflux Disease', 'Omeprazole 20mg daily', 'None', 'Symptoms improve with dietary modifications', '2024-01-08'),
(9, 'Seasonal Allergic Rhinitis', 'Cetirizine 10mg daily', 'None', 'Symptoms worse in spring months', '2024-04-25'),
(10, 'Depression (Mild)', 'Escitalopram 10mg daily', 'None', 'Patient reports improved mood and energy', '2024-02-28')
ON CONFLICT DO NOTHING;

-- Insert sample appointments
INSERT INTO appointments (patient_id, doctor_name, appointment_date, status) VALUES
(1, 'Dr. Sarah Chen', '2024-07-15 09:00:00', 'completed'),
(1, 'Dr. Michael Roberts', '2024-08-20 14:30:00', 'scheduled'),
(2, 'Dr. Emily Watson', '2024-07-22 10:15:00', 'completed'),
(2, 'Dr. David Kim', '2024-09-10 11:00:00', 'scheduled'),
(3, 'Dr. Lisa Park', '2024-08-05 15:45:00', 'completed'),
(4, 'Dr. James Miller', '2024-07-28 09:30:00', 'completed'),
(4, 'Dr. Amanda Foster', '2024-09-18 16:00:00', 'scheduled'),
(5, 'Dr. Robert Garcia', '2024-08-12 11:20:00', 'completed'),
(6, 'Dr. Jennifer Lee', '2024-07-10 14:00:00', 'completed'),
(7, 'Dr. Christopher Davis', '2024-08-25 10:30:00', 'scheduled'),
(8, 'Dr. Michelle Brown', '2024-07-18 13:15:00', 'completed'),
(9, 'Dr. Andrew Wilson', '2024-09-05 09:45:00', 'scheduled'),
(10, 'Dr. Stephanie Taylor', '2024-08-08 15:30:00', 'completed'),
(1, 'Dr. Sarah Chen', '2024-10-15 09:00:00', 'scheduled'),
(3, 'Dr. Lisa Park', '2024-10-22 15:45:00', 'scheduled')
ON CONFLICT DO NOTHING;

-- Insert sample query history
INSERT INTO query_history (user_id, query_text, query_hash, execution_time, row_count, was_masked, executed_at) VALUES
(2, 'SELECT * FROM patients LIMIT 10', 'abc123def456', 0.125, 10, true, '2024-03-01 10:00:00'),
(2, 'SELECT COUNT(*) FROM medical_records', 'def456ghi789', 0.045, 1, false, '2024-03-01 10:05:00'),
(3, 'SELECT full_name, email, phone FROM patients', 'ghi789jkl012', 0.089, 10, true, '2024-03-01 11:00:00'),
(2, 'SELECT * FROM medical_records WHERE patient_id = 1', 'jkl012mno345', 0.156, 2, true, '2024-03-01 11:30:00'),
(3, 'SELECT COUNT(*) FROM appointments WHERE status = scheduled', 'mno345pqr678', 0.034, 1, false, '2024-03-01 12:00:00')
ON CONFLICT DO NOTHING;

-- Insert sample audit logs
INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, ip_address, created_at) VALUES
(1, 'CREATE', 'masking_policy', 1, '{"name": "Patient Email Masking"}', '192.168.1.100', '2024-02-01 09:00:00'),
(1, 'CREATE', 'masking_policy', 2, '{"name": "Patient Phone Masking"}', '192.168.1.100', '2024-02-01 09:05:00'),
(2, 'READ', 'patients', null, '{"query": "SELECT * FROM patients LIMIT 10"}', '192.168.1.101', '2024-03-01 10:00:00'),
(3, 'READ', 'medical_records', null, '{"query": "SELECT * FROM medical_records WHERE patient_id = 1"}', '192.168.1.102', '2024-03-01 11:00:00'),
(1, 'UPDATE', 'masking_policy', 1, '{"is_active": false}', '192.168.1.100', '2024-03-05 14:00:00')
ON CONFLICT DO NOTHING;
