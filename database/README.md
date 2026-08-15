# Database Directory

This directory contains the SQL schema and seed data for the MaskGate application.

## Files

- `schema.sql` - Database schema definition including tables, indexes, and triggers
- `seed.sql` - Sample medical data for testing and demonstration purposes
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
- `masking_recommendations` - AI-generated masking recommendations pending review
- `query_history` - Log of executed queries
- `schema_analysis_cache` - Cached schema analysis results
- `audit_logs` - Security audit trail

### Medical Data Tables

- `patients` - Patient information with sensitive PII (name, DOB, blood group, contact info)
- `medical_records` - Medical records with diagnoses, medications, allergies, and clinical notes
- `appointments` - Appointment scheduling with doctor information and visit status

## Medical Data Sensitivity

The medical tables contain synthetic patient data designed to demonstrate realistic privacy concerns:

### High Sensitivity Fields
- `patients.email` - Patient contact information
- `patients.phone` - Patient phone numbers
- `patients.address` - Patient residential addresses
- `patients.date_of_birth` - Protected health information (PHI)
- `patients.blood_group` - Medical information
- `patients.emergency_contact` - Emergency contact details
- `medical_records.diagnosis` - Medical diagnoses
- `medical_records.medication` - Prescription information
- `medical_records.allergies` - Allergy information

### Medium Sensitivity Fields
- `appointments.doctor_name` - Healthcare provider information

### Low Sensitivity Fields
- `appointments.status` - Appointment status (scheduled, completed, etc.)

## Security Notes

- The seed data contains synthetic medical information for testing purposes only
- All patient data is fictional and designed to demonstrate privacy masking
- In production, ensure proper HIPAA compliance, access controls, and encryption
- Regular backups and security audits are recommended
- Consider using row-level security for multi-tenant deployments
- Medical data requires special handling under healthcare privacy regulations
