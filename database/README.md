# Database Directory

This directory contains the SQL schema and seed data for the MaskGate application.

## Files

- `schema.sql` - Database schema definition including tables, indexes, and triggers
- `seed.sql` - Sample data for testing and demonstration purposes
- `README.md` - This file

## Setup Instructions

1. Create the database:
   ```bash
   createdb maskgate
   ```

2. Run the schema script:
   ```bash
   psql -U postgres -d maskgate -f schema.sql
   ```

3. Run the seed script (optional, for testing):
   ```bash
   psql -U postgres -d maskgate -f seed.sql
   ```

## Database Schema

### Core Tables

- `users` - Application users and authentication
- `masking_policies` - Data masking policies and rules
- `query_history` - Log of executed queries
- `schema_analysis_cache` - Cached schema analysis results
- `audit_logs` - Security audit trail

### Sample Data Tables

- `customers` - Customer information with PII
- `orders` - Order information with payment data
- `employees` - Employee information with sensitive data

## Security Notes

- The seed data contains realistic PII for testing purposes
- In production, ensure proper access controls and encryption
- Regular backups and security audits are recommended
- Consider using row-level security for multi-tenant deployments
