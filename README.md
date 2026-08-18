# 🛡️ MaskGate

**A Proxy-Based Dynamic Data Masking Framework for PostgreSQL**

MaskGate enables developers to query production-like databases securely by masking sensitive information in real time while maintaining data relationships and supporting GDPR-compliant access.

---

## 🎯 Problem

Developers often need access to realistic database data when debugging applications. However, production databases can contain sensitive information such as:

* Names
* Email addresses
* Phone numbers
* Addresses
* Dates of birth
* Medical information
* Diagnoses
* Allergies
* Other personally identifiable information (PII)

Giving developers unrestricted access to this information creates privacy and security risks.

Manually identifying every sensitive database field and creating masking rules can also be difficult and error-prone.

### The problem MaskGate explores

> **How can Generative AI assist developers and administrators in identifying and dynamically masking sensitive database information while preserving useful data for debugging?**

---

# 💡 Proposed Solution

MaskGate introduces an AI-assisted masking workflow.

```text
                    ┌─────────────────────┐
                    │       Admin         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Admin Dashboard   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      FastAPI        │
                    │   Python Backend    │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
                 ▼             ▼             ▼
          ┌────────────┐ ┌────────────┐ ┌────────────┐
          │ PostgreSQL │ │ LangChain  │ │  Masking   │
          │            │ │    + LLM   │ │   Engine   │
          └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
                │              │              │
                └──────────────┼──────────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Masking Policies    │
                    │ + Runtime Detection │
                    └──────────┬──────────┘
                               │
                               ▼
                       Masked Results
```

---

# 🚀 Current MVP

The current implementation is intentionally focused on the core masking problem.

### Current scope

1. Connect to PostgreSQL.
2. Discover database schemas.
3. Discover tables and columns.
4. Expose schema information through FastAPI.
5. Display schema information in the admin interface.
6. Send schema metadata to LangChain/LLM.
7. Generate masking recommendations.
8. Allow an administrator to review recommendations.
9. Store approved masking policies.
10. Process controlled database queries.
11. Apply deterministic masking to query results.
12. Perform an additional GenAI sensitive-data scan.
13. Mask sensitive information detected at runtime.
14. Test and document the system.

---

# 🔄 Core Workflow

## Phase 1 — Schema Discovery

```text
PostgreSQL
    │
    ▼
Python Database Layer
    │
    ▼
FastAPI
    │
    ▼
Schema / Tables / Columns
    │
    ▼
Admin Dashboard
```

---

## Phase 2 — AI Masking Recommendations

```text
PostgreSQL Schema
       │
       ▼
Schema Metadata
       │
       ▼
LangChain
       │
       ▼
LLM
       │
       ▼
Sensitive Field Detection
       │
       ▼
Masking Recommendations
```

Example:

| Table           | Column      | Sensitivity | Recommendation |
| --------------- | ----------- | ----------- | -------------- |
| patients        | full_name   | Medium      | Partial        |
| patients        | email       | High        | Email          |
| patients        | phone       | High        | Last 4         |
| patients        | address     | High        | Partial        |
| patients        | blood_group | High        | Redact         |
| medical_records | diagnosis   | High        | Redact         |
| medical_records | allergies   | High        | Redact         |

The LLM provides **recommendations**. It does not directly modify the database.

---

# 👨‍💻 Administrator Review

The administrator reviews the AI recommendations.

```text
AI Recommendation
        │
        ▼
Admin Review
        │
   ┌────┴────┐
   │         │
Approve    Reject
   │
   ▼
Masking Policy
```

This keeps the administrator in control of the final masking configuration.

---

# 🔐 Deterministic Dynamic Data Masking

MaskGate provides high-performance, deterministic query-result masking based on approved `ACTIVE` masking policies.

```text
Database
    ↓
Query
    ↓
Active Policy
    ↓
Masking Engine (Pure Python)
    ↓
Masked Result
    ↓
Client
```

### Core Security Guarantee: Zero Database Mutation

> **MaskGate does not modify the original database value. Masking is applied to query results before they are returned to the client.**

### Supported Deterministic Strategies

| Strategy | Description | Example Input | Example Output |
| :--- | :--- | :--- | :--- |
| `NONE` | Returns original value without modifications | `12345` | `12345` |
| `REDACT` | Replaces entire string/value with asterisks | `Confidential` | `************` |
| `PARTIAL` | Preserves outer characters while masking center | `sensitive_text` | `se**********xt` |
| `EMAIL` | Preserves first character and domain, masks local part | `john.smith@gmail.com` | `j***@gmail.com` |
| `PHONE_LAST4` | Preserves only the last 4 digits of phone numbers | `0771234567` | `******4567` |

### Deterministic Masking Examples

**Database value:**
```text
john.smith@gmail.com
```

**Policy:**
```text
EMAIL
```

**Returned value:**
```text
j***@gmail.com
```

---

**Database value:**
```text
0771234567
```

**Policy:**
```text
PHONE_LAST4
```

**Returned value:**
```text
******4567
```

---

# 🧠 Runtime GenAI Detection

MaskGate also introduces a second protection layer.

A sensitive field may not have been identified during the initial policy-generation stage.

Therefore, returned data can be checked again.

```text
Developer Query
      │
      ▼
PostgreSQL
      │
      ▼
Query Results
      │
      ▼
Approved Masking Rules
      │
      ▼
GenAI Sensitive Data Detection
      │
      ├───────────────┐
      │               │
      ▼               ▼
No Sensitive      Sensitive
Data Found        Data Found
      │               │
      │               ▼
      │          Additional Masking
      │               │
      └───────┬───────┘
              ▼
        Final Response
              │
              ▼
          Developer
```

The GenAI layer is an **additional detection mechanism**, not the only security control.

---

# 🏗️ Architecture

The current MVP uses a simplified architecture so development can focus on the core masking functionality.

```text
                    ┌──────────────────┐
                    │      Admin       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Admin Dashboard │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │     FastAPI      │
                    │  Python Backend  │
                    └────────┬─────────┘
                             │
             ┌───────────────┼────────────────┐
             │               │                │
             ▼               ▼                ▼
      ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
      │ PostgreSQL  │ │  LangChain  │ │   Masking   │
      │             │ │    + LLM    │ │   Engine    │
      └─────────────┘ └─────────────┘ └─────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Masking Policies │
                    └──────────────────┘
```

---

# 🧩 Technology Stack

| Component       | Technology                  |
| --------------- | --------------------------- |
| Language        | Python                      |
| Backend API     | FastAPI                     |
| Database        | PostgreSQL                  |
| GenAI Framework | LangChain                   |
| LLM             | Configurable LLM Provider   |
| Data Validation | Pydantic                    |
| Frontend        | Lightweight Admin Dashboard |
| Testing         | pytest                      |
| Environment     | Python Virtual Environment  |
| Version Control | Git / GitHub                |
| Development     | Cursor                      |

---

# 📁 Project Structure

The project is intentionally separated into clear components.

```text
MaskGate/
│
├── AGENTS.md
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── backend/
│   └── app/
│       ├── main.py
│       │
│       ├── api/
│       │   └── routes/
│       │       ├── health.py
│       │       ├── schema.py
│       │       ├── masking.py
│       │       └── query.py
│       │
│       ├── config/
│       │   └── settings.py
│       │
│       ├── database/
│       │   ├── base.py
│       │   ├── connection.py
│       │   └── postgresql.py
│       │
│       ├── schemas/
│       │   ├── database.py
│       │   ├── masking.py
│       │   └── query.py
│       │
│       ├── services/
│       │   ├── schema_service.py
│       │   ├── masking_service.py
│       │   └── query_service.py
│       │
│       ├── ai/
│       │   ├── llm.py
│       │   ├── schema_analyzer.py
│       │   └── sensitive_data_detector.py
│       │
│       └── masking/
│           ├── engine.py
│           ├── policies.py
│           └── strategies.py
│
├── frontend/
│
├── database/
│   ├── schema.sql
│   ├── seed.sql
│   └── README.md
│
├── tests/
│   ├── test_database.py
│   ├── test_schema.py
│   ├── test_masking.py
│   └── test_ai.py
│
├── docs/
│   ├── architecture.md
│   ├── masking.md
│   └── future-roadmap.md
│
└── scripts/
```

The structure can grow as features are implemented. Unnecessary empty modules should not be created prematurely.

---

# 🗄️ Database

## Current Database

MaskGate currently supports:

```text
PostgreSQL
    ✅ Current MVP
```

The database layer is designed so that additional database connectors can be added in the future without redesigning the entire application.

Conceptually:

```text
DatabaseConnector
       │
       └── PostgreSQLConnector   ← Current
       
Future:
       ├── MySQLConnector
       ├── MongoDBConnector
       └── SQLServerConnector
```

Only PostgreSQL is implemented in the current project.

---

# 🔌 API

The backend uses FastAPI.

Initial API endpoints include:

```text
GET  /health

GET  /api/v1/schema

GET  /api/v1/schema/tables

POST /api/v1/schema/analyze

GET  /api/v1/masking/policies

POST /api/v1/masking/policies

POST /api/v1/query
```

FastAPI's interactive API documentation can be used during development to test the endpoints.

---

# 🔒 Security Principles

## Original Data Preservation

MaskGate does not modify the original database records during masking.

## Least Data Exposure

Only information necessary for the task should be exposed to developers.

## Human Approval

AI-generated masking recommendations should be reviewed before becoming active policies.

## Defense in Depth

MaskGate combines:

```text
Approved Masking Policies
          +
Deterministic Masking
          +
Runtime GenAI Detection
```

## Secret Protection

Database credentials and LLM API keys must never be hard-coded.

Use environment variables instead.

---

# ⚠️ LLM Security

The LLM should not be treated as a trusted database administrator.

The LLM must NOT:

* Execute arbitrary SQL.
* Modify database records.
* Modify database schemas.
* Disable masking.
* Bypass application policies.

The application controls database access and validates LLM-generated outputs before using them.

Where possible, schema metadata should be sent to the LLM instead of unnecessary real database records.

---

# 🧪 Example Dataset

For demonstration and testing, MaskGate can use a synthetic healthcare-style dataset.

Example tables:

```text
patients
├── patient_id
├── full_name
├── date_of_birth
├── blood_group
├── phone
├── email
├── address
└── emergency_contact

medical_records
├── record_id
├── patient_id
├── diagnosis
├── medication
├── allergies
├── notes
└── visit_date

appointments
├── appointment_id
├── patient_id
├── doctor_name
├── appointment_date
└── status
```

**Only synthetic/fake data should be used for development and demonstrations.**

---

# 🛠️ Local Development

## Requirements

* Python 3.x
* PostgreSQL
* Git
* Cursor or another code editor

---

## 1. Clone the Repository

```bash
git clone https://github.com/faizamfairooz/MaskGate.git
cd MaskGate
```

---

## 2. Create Virtual Environment

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create `.env` locally using `.env.example` as the template.

Example:

```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=maskgate
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password

LLM_API_KEY=your_api_key
```

Never commit `.env` to GitHub.

---

## 5. Start the FastAPI Application

The exact development command depends on the project entry point.

Typical development command:

```bash
uvicorn backend.app.main:app --reload
```

---

## 6. Test the API

Open the FastAPI documentation:

```text
/docs
```

The first milestone is:

```text
PostgreSQL
    ↓
Python
    ↓
FastAPI
    ↓
API
    ↓
Schema JSON
```

---

# 🧪 Testing

Run:

```bash
pytest
```

Tests will cover areas such as:

* PostgreSQL connectivity
* Schema extraction
* API responses
* Masking strategies
* Masking policies
* LLM output validation
* Runtime sensitive-data detection

---

# 📅 Development Roadmap

## Phase 1 — Foundation

* [ ] Repository structure
* [ ] AGENTS.md
* [ ] Python environment
* [ ] PostgreSQL connection
* [ ] Configuration management

## Phase 2 — PostgreSQL + FastAPI

* [ ] Schema discovery
* [ ] Table discovery
* [ ] Column discovery
* [ ] FastAPI endpoints
* [ ] API testing

## Phase 3 — Admin Dashboard

* [ ] Connect frontend to API
* [ ] Display schemas
* [ ] Display tables
* [ ] Display columns
* [ ] Display database relationships

## Phase 4 — GenAI

* [ ] LangChain integration
* [ ] LLM configuration
* [ ] Schema analysis
* [ ] Sensitive-field recommendations
* [ ] Structured LLM output
* [ ] Recommendation validation

## Phase 5 — Masking Policies

* [ ] Admin review
* [ ] Policy creation
* [ ] Policy storage
* [ ] Masking strategies
* [ ] Deterministic masking

## Phase 6 — Runtime Protection

* [ ] Controlled query processing
* [ ] Apply approved masking policies
* [ ] Runtime sensitive-data detection
* [ ] Additional masking
* [ ] Final protected response

## Phase 7 — Testing & Demonstration

* [ ] Unit tests
* [ ] Integration tests
* [ ] API testing
* [ ] End-to-end demonstration
* [ ] Documentation
* [ ] Architecture diagrams

---

# 🔮 Future Work

The current MVP intentionally does **not** implement the following.

## Database Proxy

A future version could introduce:

```text
Developer
    │
    ▼
MaskGate Proxy
    │
    ▼
Masking / Policy Engine
    │
    ▼
PostgreSQL
```

This could provide a transparent database access layer without requiring developers to change their existing database workflow.

---

## TCP Database Communication

Future versions may investigate TCP/database-protocol-level communication for a transparent proxy architecture.

---

## JDBC Connectivity

JDBC-style connectivity may be investigated in future versions to support applications that connect through JDBC-compatible database interfaces.

---

## VS Code Integration

A future version could integrate MaskGate with developer tools such as VS Code.

---

## Role-Based Access Control

RBAC could later provide different capabilities for:

```text
Administrator
Developer
Auditor
Other Roles
```

---

## Additional Databases

Future connectors may support:

```text
PostgreSQL     ← Current
MySQL          ← Future
MongoDB        ← Future
SQL Server     ← Future
```

---

## Enterprise Features

Potential future work includes:

* Advanced auditing
* Authentication
* Authorization
* Enterprise deployment
* Centralized policy management
* Additional database integrations

These features are outside the current MVP.

---

# 📚 Research Focus

MaskGate investigates the combination of:

```text
Database Metadata
       +
Generative AI
       +
Human Policy Review
       +
Deterministic Masking
       +
Runtime Sensitive Data Detection
```

The central research direction is:

> **Using Generative AI as an intelligent assistance layer for identifying and protecting sensitive database information while preserving the usefulness of data for software development and debugging.**

---

# 📊 Project Status

```text
🚧 Research Prototype
```

MaskGate is currently under active development as an academic research project.

The current implementation prioritizes a working PostgreSQL + FastAPI + GenAI masking workflow over a complex production infrastructure.

---

# 👨‍💻 Author

**Faizam Fairooz**

GitHub:

https://github.com/faizamfairooz/MaskGate

---

# 📜 License

This project is currently being developed as an academic research prototype.

License terms will be determined before public release.
