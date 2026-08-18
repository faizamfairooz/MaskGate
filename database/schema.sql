-- MaskGate Database Schema
-- This schema supports the database security and masking platform

-- Create database if it doesn't exist
-- CREATE DATABASE maskgate;

-- Users table for application authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Masking policies table
CREATE TABLE IF NOT EXISTS masking_policies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    schema_name VARCHAR(100) DEFAULT 'public',
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    sensitivity VARCHAR(20) DEFAULT 'MEDIUM',
    parameters JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'ACTIVE',
    source VARCHAR(30) DEFAULT 'ai_recommendation',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    UNIQUE(table_name, column_name)
);

ALTER TABLE masking_policies ADD COLUMN IF NOT EXISTS schema_name VARCHAR(100) DEFAULT 'public';
ALTER TABLE masking_policies ADD COLUMN IF NOT EXISTS sensitivity VARCHAR(20) DEFAULT 'MEDIUM';
ALTER TABLE masking_policies ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE masking_policies ADD COLUMN IF NOT EXISTS source VARCHAR(30) DEFAULT 'ai_recommendation';

-- AI masking recommendations (pending admin review)
CREATE TABLE IF NOT EXISTS masking_recommendations (
    id SERIAL PRIMARY KEY,
    schema_name VARCHAR(100) DEFAULT 'public',
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    data_type VARCHAR(100) DEFAULT 'text',
    sensitivity VARCHAR(20) NOT NULL,
    recommended_strategy VARCHAR(50) NOT NULL,
    rationale TEXT,
    source VARCHAR(50) DEFAULT 'llm',
    status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_masking_recommendations_status ON masking_recommendations(status);
CREATE INDEX IF NOT EXISTS idx_masking_recommendations_table ON masking_recommendations(table_name);
ALTER TABLE masking_recommendations ADD COLUMN IF NOT EXISTS schema_name VARCHAR(100) DEFAULT 'public';
ALTER TABLE masking_recommendations ADD COLUMN IF NOT EXISTS data_type VARCHAR(100) DEFAULT 'text';
ALTER TABLE masking_recommendations ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'llm';
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_masking_policy ON masking_policies (schema_name, table_name, column_name) WHERE is_active = TRUE AND status = 'ACTIVE';

-- Query history table
CREATE TABLE IF NOT EXISTS query_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64),
    execution_time FLOAT,
    row_count INTEGER,
    was_masked BOOLEAN DEFAULT FALSE,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET
);

-- Schema analysis cache table
CREATE TABLE IF NOT EXISTS schema_analysis_cache (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    analysis_result JSONB NOT NULL,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(table_name)
);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medical data tables for testing and demonstration
CREATE TABLE IF NOT EXISTS patients (
    patient_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    blood_group VARCHAR(5),
    phone VARCHAR(20),
    email VARCHAR(255) UNIQUE,
    address TEXT,
    emergency_contact VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS medical_records (
    record_id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(patient_id),
    diagnosis TEXT NOT NULL,
    medication TEXT,
    allergies TEXT,
    notes TEXT,
    visit_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(patient_id),
    doctor_name VARCHAR(100) NOT NULL,
    appointment_date TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_masking_policies_table ON masking_policies(table_name);
CREATE INDEX IF NOT EXISTS idx_masking_policies_column ON masking_policies(column_name);
CREATE INDEX IF NOT EXISTS idx_query_history_user ON query_history(user_id);
CREATE INDEX IF NOT EXISTS idx_query_history_date ON query_history(executed_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_date ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_patients_email ON patients(email);
CREATE INDEX IF NOT EXISTS idx_medical_records_patient ON medical_records(patient_id);
CREATE INDEX IF NOT EXISTS idx_medical_records_date ON medical_records(visit_date);
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_masking_policies_updated_at BEFORE UPDATE ON masking_policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_masking_recommendations_updated_at BEFORE UPDATE ON masking_recommendations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
