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
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    parameters JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'approved',
    source VARCHAR(30) DEFAULT 'manual',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    UNIQUE(table_name, column_name)
);

-- AI masking recommendations (pending admin review)
CREATE TABLE IF NOT EXISTS masking_recommendations (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    sensitivity VARCHAR(20) NOT NULL,
    recommended_strategy VARCHAR(50) NOT NULL,
    rationale TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_masking_recommendations_status ON masking_recommendations(status);
CREATE INDEX IF NOT EXISTS idx_masking_recommendations_table ON masking_recommendations(table_name);

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

-- Sample data tables for testing and demonstration
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    ssn VARCHAR(11),
    address TEXT,
    city VARCHAR(50),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2),
    status VARCHAR(20),
    shipping_address TEXT,
    credit_card_number VARCHAR(20),
    credit_card_expiry VARCHAR(5)
);

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    ssn VARCHAR(11),
    hire_date DATE,
    salary DECIMAL(10, 2),
    department VARCHAR(50),
    address TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_masking_policies_table ON masking_policies(table_name);
CREATE INDEX IF NOT EXISTS idx_masking_policies_column ON masking_policies(column_name);
CREATE INDEX IF NOT EXISTS idx_query_history_user ON query_history(user_id);
CREATE INDEX IF NOT EXISTS idx_query_history_date ON query_history(executed_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_date ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email);

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
