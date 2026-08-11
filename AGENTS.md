# MaskGate — Coding Agent Instructions

## 1. Project Overview

MaskGate is an academic research prototype for GenAI-assisted dynamic data masking during database access.

The current implementation focuses ONLY on:

* PostgreSQL
* Python
* FastAPI
* LangChain
* LLM-assisted schema analysis
* Masking policy recommendations
* Administrator review
* Dynamic data masking
* Runtime sensitive-data detection
* Basic admin dashboard

The goal is to demonstrate that sensitive database information can be identified and masked while preserving useful data for development and debugging.

---

## 2. Current MVP Scope

The current development priority is:

1. Connect Python to PostgreSQL.
2. Retrieve database/schema/table/column metadata.
3. Expose PostgreSQL information through FastAPI.
4. Display schema/table information in the admin dashboard.
5. Integrate LangChain with an LLM.
6. Analyze database schema using the LLM.
7. Generate masking recommendations.
8. Allow an administrator to review and approve recommendations.
9. Store approved masking policies.
10. Execute developer queries through the controlled application.
11. Apply rule-based masking to query results.
12. Add a secondary GenAI sensitive-data detection layer.
13. Return masked results to the user.
14. Add tests and documentation.

Always implement the smallest working feature first.

---

## 3. Explicitly OUT OF SCOPE

Do NOT implement the following during the current MVP unless explicitly requested by the user:

* TCP database proxy
* Database protocol proxy
* JDBC connectivity
* VS Code extension
* VS Code database integration
* Role-Based Access Control
* Kafka
* Redis
* Kubernetes
* MongoDB
* MySQL
* SQL Server
* Enterprise deployment infrastructure
* Complex authentication systems
* Production GDPR compliance claims

These are future extensions.

Do not create implementation code for these features merely because they appear in README.md or architecture documentation.

---

## 4. Current Technology Stack

Backend:

* Python
* FastAPI
* PostgreSQL
* LangChain
* Configurable LLM provider
* Pydantic
* pytest

Frontend:

* Simple admin dashboard
* Keep frontend implementation lightweight.
* Do not introduce unnecessary frontend complexity.

Database:

* PostgreSQL ONLY for the current MVP.

---

## 5. Architecture

Use this logical architecture:

Admin Dashboard
|
v
FastAPI
|
+---- PostgreSQL Connector
|
+---- LangChain / LLM
|
+---- Masking Engine
|
v
Masked Results

Keep responsibilities separated.

The API layer should not contain database implementation details.

The database layer should not contain LLM logic.

The LLM layer should not directly execute arbitrary SQL.

The masking engine should be deterministic wherever possible.

---

## 6. Database Abstraction

Create a small database abstraction so future database support is possible.

The current implementation must contain only:

PostgreSQLConnector

Do not implement MySQL, MongoDB, or other connectors now.

Future connectors may eventually implement the same abstraction.

---

## 7. Security Rules

NEVER hard-code:

* database passwords
* API keys
* LLM credentials
* secrets

Use environment variables.

Use:

.env

for local development.

Use:

.env.example

as a safe template.

Never commit .env.

Never expose secrets in API responses.

Never send unnecessary sensitive database values to the LLM.

Prefer schema metadata over real records when generating masking recommendations.

---

## 8. LLM Safety Rules

The LLM is an analysis and recommendation component.

Do not allow the LLM to:

* execute arbitrary SQL directly
* modify database records
* modify database schema
* disable masking
* bypass application policy checks

The application must control database execution.

LLM output must be validated before being converted into application policies.

Prefer structured LLM output.

---

## 9. Masking Principles

Masking must not modify the original PostgreSQL data.

Example:

Original:

[john.smith@gmail.com](mailto:john.smith@gmail.com)

Masked:

j***@gmail.com

Masking should occur before returning data to the developer.

The system should support deterministic masking strategies such as:

* email masking
* phone masking
* partial text masking
* full redaction
* configurable generic masking

Do not rely exclusively on the LLM for masking.

Use deterministic application logic for approved masking policies.

---

## 10. GenAI Responsibilities

GenAI has two main responsibilities.

### Schema Analysis

Analyze PostgreSQL metadata and recommend potentially sensitive columns.

Example:

users.email -> HIGH -> EMAIL
users.phone -> HIGH -> LAST4
users.address -> HIGH -> PARTIAL

### Runtime Detection

Inspect query results for sensitive information that may not have been covered by existing rules.

GenAI detection is a secondary safety layer, not the only protection mechanism.

---

## 11. API Design

Use FastAPI.

Initial endpoints should include:

GET /health

GET /api/v1/schema

GET /api/v1/schema/tables

POST /api/v1/schema/analyze

GET /api/v1/masking/policies

POST /api/v1/masking/policies

POST /api/v1/query

Keep endpoint responsibilities small and clear.

FastAPI automatic OpenAPI documentation should remain enabled for development.

---

## 12. Project Structure

Prefer:

backend/
frontend/
database/
docs/
scripts/

Inside backend:

app/
api/
config/
database/
schemas/
services/
ai/
masking/

Do not create unnecessary files.

Only create a new module when it has a clear responsibility.

---

## 13. Configuration

Use a typed configuration object.

Environment variables should be loaded centrally.

Do not read environment variables randomly throughout the codebase.

Database connection configuration belongs in the configuration/database layer.

---

## 14. Dependencies

Use a Python virtual environment.

Maintain:

requirements.txt

When dependencies change, update requirements.txt.

Do not introduce alternative package managers such as uv unless explicitly requested.

The project should remain easy for mentors to reproduce.

---

## 15. Testing

Every meaningful feature should have tests.

At minimum test:

* database connection
* schema extraction
* API responses
* masking strategies
* masking policies
* LLM output validation
* query processing
* sensitive-data detection

Never claim a feature works without testing it.

---

## 16. Coding Style

Prefer:

* clear Python
* type hints
* small functions
* small classes
* descriptive names
* explicit error handling
* separation of concerns

Avoid:

* unnecessary abstractions
* premature optimization
* huge files
* duplicated database logic
* hard-coded credentials
* hidden fallback credentials
* unnecessary dependencies

---

## 17. Development Method

Work incrementally.

For each task:

1. Inspect the existing code.
2. Explain the proposed change.
3. Make the smallest implementation.
4. Run relevant tests.
5. Fix failures.
6. Report what changed.
7. Do not silently expand scope.

Do not implement multiple major features in one step.

---

## 18. Priority Order

Priority 1:
PostgreSQL connection

Priority 2:
Schema extraction

Priority 3:
FastAPI schema endpoint

Priority 4:
Admin dashboard schema display

Priority 5:
LangChain + LLM integration

Priority 6:
AI masking recommendations

Priority 7:
Masking policy approval/storage

Priority 8:
Query processing

Priority 9:
Deterministic result masking

Priority 10:
Runtime GenAI sensitive-data detection

Priority 11:
Testing

Priority 12:
Documentation and demo

---

## 19. Future Architecture

The following may be documented but must not be implemented during the MVP:

Developer
|
v
MaskGate Database Proxy
|
v
Policy / Masking Engine
|
v
PostgreSQL

Future technologies may include:

* TCP proxy
* JDBC-style connectivity
* VS Code integration
* RBAC
* multiple database connectors
* enterprise audit functionality

These are future roadmap items.

---

## 20. Agent Behavior

Before modifying code:

* Read AGENTS.md.
* Read the relevant README/documentation.
* Inspect the existing implementation.
* Do not assume missing code exists.
* Do not recreate working components.
* Do not overwrite unrelated work.
* Do not implement future-scope features.

If requirements are ambiguous, explain the ambiguity before making a large architectural change.

Always keep the MVP deadline and scope in mind.

The goal is a working, understandable academic prototype rather than an over-engineered production platform.
