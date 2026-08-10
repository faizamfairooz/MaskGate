# 🛡️ MaskGate

> **GenAI-Assisted Dynamic Data Masking for Secure Database Access**

MaskGate is a privacy-preserving database access system designed to help developers work with database data without unnecessarily exposing sensitive information.

The current prototype focuses on **PostgreSQL** and uses a **Python service, LangChain, and a Large Language Model (LLM)** to analyze database schemas, identify potentially sensitive fields, recommend masking policies, and dynamically mask sensitive information returned from database queries.

---

## 🚨 Problem

Developers often need realistic database data to debug and investigate application issues. However, providing direct access to production or sensitive databases can expose Personally Identifiable Information (PII) and other confidential data.

Traditional approaches may require manually identifying sensitive columns and configuring masking rules in advance. This creates two major problems:

1. Sensitive fields may be overlooked during manual configuration.
2. Developers may still receive sensitive information that was not included in the initial masking rules.

MaskGate explores how **Generative AI can assist with both policy creation and runtime sensitive-data detection** while keeping the original PostgreSQL data unchanged.

---

## 💡 Solution

MaskGate introduces an AI-assisted masking workflow:

```text
                 ┌─────────────────────┐
                 │       Admin         │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    MaskGate UI      │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Python Service    │
                 │      (Flask)        │
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │     PostgreSQL      │
                 │  Schema / Tables /  │
                 │  Columns / Types    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     LangChain       │
                 │         +           │
                 │        LLM          │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Masking Suggestions │
                 └──────────┬──────────┘
                            │
                       Admin Review
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Masking Policies  │
                 └──────────┬──────────┘
                            │
                            ▼
Developer ──► Query ──► PostgreSQL
                            │
                            ▼
                    Query Result
                            │
                            ▼
                 ┌─────────────────────┐
                 │  Masking Engine     │
                 │                     │
                 │ Rule-based Masking  │
                 │         +           │
                 │ GenAI Safety Scan   │
                 └──────────┬──────────┘
                            │
                            ▼
                    Masked Response
                            │
                            ▼
                       Developer
```

---

# 🎯 Objectives

MaskGate aims to:

- Protect sensitive information during database access.
- Reduce manual effort when creating masking policies.
- Use GenAI to identify potentially sensitive database fields.
- Allow administrators to review and approve AI-generated masking suggestions.
- Apply masking rules dynamically without modifying the original database.
- Detect sensitive information that may have been missed by predefined rules.
- Provide developers with useful data for debugging while reducing privacy risks.
- Establish an architecture that can later support additional databases and access methods.

---

# ✨ Core Features

## 1. PostgreSQL Schema Discovery

MaskGate connects to a PostgreSQL database and retrieves metadata such as:

- Databases
- Schemas
- Tables
- Columns
- Data types
- Primary keys
- Foreign keys
- Indexes
- Relationships

Example:

```text
PostgreSQL
│
└── public
    │
    ├── users
    │   ├── id
    │   ├── name
    │   ├── email
    │   ├── phone
    │   └── address
    │
    └── orders
        ├── id
        ├── user_id
        └── amount
```

---

## 2. AI-Assisted Sensitive Data Identification

The database schema is provided to an LLM through LangChain.

The LLM analyzes the schema and recommends potentially sensitive fields.

Example:

| Table | Column | Risk | Recommendation |
|---|---|---|---|
| users | email | High | Email masking |
| users | phone | High | Last 4 digits |
| users | address | High | Partial masking |
| users | name | Medium | Partial masking |
| users | id | Low | No masking |

The AI provides **recommendations rather than directly modifying the database**.

---

## 3. Administrator Review

AI-generated recommendations are presented to the administrator.

```text
AI Recommendation
       │
       ▼
Admin Review
       │
   ┌───┴────┐
   ▼        ▼
Approve   Reject
   │
   ▼
Masking Policy
```

This keeps the administrator in control of the final masking policy.

---

## 4. Dynamic Data Masking

Approved policies are applied when query results are returned.

Example:

### Original database value

```text
john.doe@gmail.com
```

### Developer receives

```text
j***@gmail.com
```

The original database value remains unchanged.

---

## 5. Runtime Sensitive Data Detection

MaskGate includes an additional protection layer for information that may have been missed during initial policy creation.

```text
Database Result
       │
       ▼
Rule-Based Masking
       │
       ▼
GenAI Sensitive Data Scan
       │
       ├── No sensitive data
       │        ↓
       │     Return
       │
       └── Sensitive data detected
                ↓
             Mask
                ↓
          Return Result
```

This provides a second layer of protection against sensitive information that may have slipped through the predefined rules.

---

# 🏗️ Current Architecture

The current prototype intentionally uses a simplified architecture to keep development focused on the core masking problem.

```text
┌──────────────────────────────────────┐
│              Admin / User            │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│             Flask API                │
│          Python Application          │
└──────────────────┬───────────────────┘
                   │
          ┌────────┴─────────┐
          │                  │
          ▼                  ▼
┌─────────────────┐   ┌─────────────────┐
│   PostgreSQL    │   │    LangChain    │
│                 │   │       +         │
│ Schema / Query  │   │      LLM        │
└────────┬────────┘   └────────┬────────┘
         │                     │
         └──────────┬──────────┘
                    ▼
          ┌───────────────────┐
          │   Masking Engine  │
          └─────────┬─────────┘
                    │
                    ▼
            Masked Response
```

---

# 🔄 Core Workflow

## Phase 1 — Schema Analysis

```text
Connect PostgreSQL
       ↓
Retrieve Database Metadata
       ↓
Extract Schema Information
       ↓
Send Structured Schema to LLM
       ↓
Generate Masking Recommendations
```

## Phase 2 — Policy Creation

```text
AI Recommendations
       ↓
Administrator Review
       ↓
Approve / Modify / Reject
       ↓
Save Masking Policies
```

## Phase 3 — Query Processing

```text
User Query
    ↓
Query Analysis
    ↓
Validate Against Policies
    ↓
Execute Query
    ↓
Retrieve Results
```

## Phase 4 — Result Protection

```text
Query Results
     ↓
Rule-Based Masking
     ↓
GenAI Sensitive Data Detection
     ↓
Additional Masking if Required
     ↓
Return Safe Results
```

---

# 🧠 Role of Generative AI

Generative AI is used in two primary areas.

### 1. AI-Assisted Policy Generation

The LLM analyzes database metadata and recommends:

- Potentially sensitive columns
- Sensitivity levels
- Suitable masking strategies
- Additional fields that may require protection

### 2. Runtime Sensitive Data Detection

The LLM can inspect query results for potentially sensitive information that was not covered by the predefined masking policies.

The AI acts as an **additional detection layer**, not as the sole security mechanism.

---

# 🔐 Example

Suppose PostgreSQL contains:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(150),
    phone VARCHAR(20),
    address TEXT
);
```

The database contains:

```text
John Smith
john.smith@gmail.com
0771234567
Colombo, Sri Lanka
```

MaskGate may generate:

```text
name     → PARTIAL
email    → EMAIL
phone    → LAST4
address  → PARTIAL
```

The developer receives:

```text
J*** S****
j***@gmail.com
*******4567
C******, Sri Lanka
```

while the original PostgreSQL records remain unchanged.

---

# 🧩 Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Database | PostgreSQL |
| API Framework | Flask |
| GenAI Orchestration | LangChain |
| LLM | Configurable |
| Database Driver | PostgreSQL Python Driver |
| Frontend | Web UI |
| Environment | Python Virtual Environment |
| Dependency Management | `requirements.txt` |
| Version Control | Git / GitHub |

---

# 📁 Project Structure

```text
MaskGate/
│
├── app/
│   ├── __init__.py
│   │
│   ├── config.py
│   │
│   ├── database/
│   │   ├── base.py
│   │   └── postgresql.py
│   │
│   ├── ai/
│   │   ├── schema_analyzer.py
│   │   ├── masking_recommender.py
│   │   └── runtime_detector.py
│   │
│   ├── masking/
│   │   ├── engine.py
│   │   ├── policies.py
│   │   └── strategies.py
│   │
│   └── routes/
│       ├── schema.py
│       ├── masking.py
│       └── query.py
│
├── tests/
│   ├── test_database.py
│   ├── test_masking.py
│   └── test_ai.py
│
├── docs/
│   ├── architecture/
│   ├── research/
│   └── diagrams/
│
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── run.py
```

---

# 🗄️ Database Support

## Current

MaskGate currently focuses on:

```text
PostgreSQL
    ✅ Implemented
```

The database layer is designed around an abstraction so additional database connectors can be introduced later.

```text
DatabaseConnector
       │
       ├── PostgreSQLConnector  ✅
       │
       ├── MySQLConnector       🔮
       │
       ├── MongoDBConnector     🔮
       │
       └── SQLServerConnector   🔮
```

Only PostgreSQL is within the scope of the current prototype.

---

# 🔮 Future Architecture

The current Python service is intentionally simplified for rapid development.

A future version could introduce a database proxy layer:

```text
                    Developer
                        │
                        ▼
                ┌───────────────┐
                │ MaskGate Proxy│
                └───────┬───────┘
                        │
                        ▼
                ┌───────────────┐
                │ Policy / AI   │
                │ Masking Engine│
                └───────┬───────┘
                        │
                        ▼
                   PostgreSQL
```

Potential future extensions include:

- Database proxy
- TCP-based database communication
- JDBC-style connectivity
- VS Code integration
- Role-Based Access Control
- Additional database connectors
- Enterprise deployment
- Advanced audit logging

These components are **outside the current MVP scope**.

---

# 📊 Current Development Scope

### MVP

- [x] PostgreSQL connection
- [ ] Schema discovery
- [ ] Table and column analysis
- [ ] AI masking recommendations
- [ ] Administrator review
- [ ] Masking policy storage
- [ ] Rule-based dynamic masking
- [ ] Runtime sensitive-data detection
- [ ] Flask API
- [ ] Basic web UI
- [ ] Testing
- [ ] Documentation

### Future

- [ ] Database Proxy
- [ ] TCP Socket Communication
- [ ] JDBC Connectivity
- [ ] VS Code Integration
- [ ] Role-Based Access Control
- [ ] MySQL Support
- [ ] MongoDB Support
- [ ] SQL Server Support
- [ ] Advanced Audit Logging

---

# 🛠️ Local Development

## Requirements

- macOS / Linux / Windows
- Python 3.x
- PostgreSQL
- Git
- VS Code

---

## 1. Clone the Repository

```bash
git clone https://github.com/faizamfairooz/MaskGate.git
cd MaskGate
```

---

## 2. Create a Python Virtual Environment

```bash
python3 -m venv .venv
```

Activate it:

### macOS / Linux

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

Create a `.env` file:

```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=maskgate
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password

LLM_API_KEY=your_api_key
```

**Never commit `.env` or API keys to GitHub.**

---

## 5. Run the Application

```bash
python run.py
```

The API will be available locally.

---

# 🧪 Testing

Run the test suite using:

```bash
pytest
```

Testing will cover:

- PostgreSQL connectivity
- Schema extraction
- Masking strategies
- Masking policies
- AI recommendations
- Runtime sensitive-data detection
- API endpoints

---

# 🔒 Security Principles

MaskGate follows several important principles:

### Original Data Preservation

Masking does not modify the original database records.

### Least Exposure

Developers should receive only the information necessary for debugging.

### Human Approval

AI-generated masking policies should be reviewed by an administrator before becoming active.

### Defense in Depth

MaskGate combines:

```text
Manual / Approved Policies
          +
Rule-Based Masking
          +
GenAI Detection
```

### API Key Protection

Secrets and API keys must be stored outside source code and excluded from Git.

---

# ⚠️ Limitations

The current prototype has several limitations:

- PostgreSQL is the only supported database.
- LLM-based detection is not guaranteed to identify every sensitive value.
- AI recommendations require human review.
- The prototype is not intended to replace a complete enterprise GDPR compliance system.
- Production deployment requires additional security controls.
- The current implementation does not provide a database proxy.

---

# 📅 Development Timeline

**Project Deadline: 29 August 2026**

### Phase 1 — Foundation

- PostgreSQL integration
- Schema discovery
- Python application
- LangChain + LLM integration

### Phase 2 — Masking

- AI masking recommendations
- Policy creation
- Dynamic masking
- Runtime sensitive-data detection

### Phase 3 — Application

- Flask API
- Basic UI
- Testing
- Documentation
- Demonstration

---

# 🎓 Research Direction

MaskGate investigates the following question:

> **How can Generative AI assist in identifying and dynamically masking sensitive information in database systems while preserving the usefulness of data for software development and debugging?**

The project explores the balance between:

```text
Developer Debugging Utility
            ↕
       Data Privacy
            ↕
     Security Controls
            ↕
       GenAI Assistance
```

---

# 🤝 Contributors

- **Faizam Fairooz** — Project Developer
- **Supervisor:** *Arnaldo Pasangha*
- **Co-Supervisor:** *Venura Pesanjith*
---

# 📄 Project Status

> 🚧 **Research / Prototype — In Development**

MaskGate is currently being developed as a research prototype focused on GenAI-assisted dynamic data masking for PostgreSQL.

---

# 📜 License

This project is currently under academic development.

License terms will be determined before public release.
