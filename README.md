# MaskGate

**GenAI-Assisted Dynamic Data Masking System for PostgreSQL**  
*Developed as part of the **Ascentic AI Launch Pad** Program*

> MaskGate is an AI-assisted database security platform and research project developed under the **Ascentic AI Launch Pad** initiative. It identifies sensitive database columns using GenAI, recommends masking policies for human administrator review, and enforces database-level and deterministic runtime masking on query results without modifying original data.

---

## 1. Project Overview

Modern software development and quality assurance workflows frequently require access to production-like databases for testing, debugging, and performance optimization. However, realistic databases often store sensitive personally identifiable information (PII), confidential medical history, and financial records. Providing developers with raw database access creates severe data privacy and compliance risks under regulations such as GDPR, HIPAA, and CCPA.

Developed under the **Ascentic AI Launch Pad** program, **MaskGate** provides an intelligent, controlled database security layer for PostgreSQL. It analyzes database schema metadata using Generative AI (LLMs) to automatically detect sensitive attributes, suggests contextual masking strategies, and presents them to an administrator for review. Once approved, policies are compiled into PostgreSQL stored functions and enforced dynamically during SQL query execution through AST query rewriting and secondary runtime detection—guaranteeing that protected data is masked before reaching the user while leaving original database records completely intact.

---

## 2. Problem Statement

Organizations face a fundamental conflict between developer productivity and data confidentiality:

- **Sensitive Data in Non-Production Workflows:** Development, staging, and analytics databases often mirror production schemas containing names, emails, phone numbers, addresses, national identification numbers, and medical notes.
- **Utility vs. Privacy:** Developers need realistic data formats, cardinalities, and relational integrity to replicate software bugs and test complex SQL queries effectively.
- **Manual Policy Definition at Scale:** Enterprise schemas contain hundreds of tables and thousands of columns. Manually inspecting every column to define and maintain masking rules is labor-intensive, error-prone, and slow.
- **Risk of Application-Layer Masking:** If data masking is implemented solely at the user interface or presentation layer, unmasked plaintext data must still traverse the network and application backends, leaving it vulnerable to intermediary exposure or query bypass.
- **Need for Database-Level Enforcement:** Enforcing masking inside the database engine projection and at query evaluation ensures zero-mutation safety and strict compliance before records leave the database boundary.

---

## 3. Solution

MaskGate introduces a closed-loop, human-in-the-loop dynamic data masking workflow:

1. **Schema Discovery:** Automatically inspects PostgreSQL system catalogs to map schemas, tables, columns, and data types.
2. **Metadata-Only AI Analysis:** LangChain passes schema metadata (never raw database records) to an LLM to identify sensitive columns.
3. **Structured Policy Recommendations:** The system generates structured recommendations with sensitivity levels, suggested algorithms, confidence scores, and rationales.
4. **Administrator Review:** A human administrator reviews, approves, rejects, or customizes recommendations.
5. **Database-Level Function Deployment:** Approved policies automatically generate immutable PL/pgSQL stored masking functions inside PostgreSQL.
6. **SQL AST Rewriting (Stage 1):** User SQL queries are parsed, expanding wildcards (`SELECT *`), resolving table aliases and JOINs, and injecting policy masking functions directly into projections.
7. **Runtime Detection (Stage 2):** Unmasked query result cells are scanned via local regex patterns and bounded LLM sampling to catch unclassified PII before response delivery.
8. **Safe Result Delivery:** Developers receive sanitized query results preserving relational structures without exposing plaintext sensitive values.

```mermaid
flowchart TD
    A["PostgreSQL Schema"] --> B["Metadata Extraction"]
    B --> C["AI / LLM Analysis (Metadata Only)"]
    C --> D["Structured Recommendations (PENDING)"]
    D --> E["Administrator Review"]
    E -->|Reject| F["Rejected (No Policy Created)"]
    E -->|Approve| G["Active Masking Policy"]
    G --> H["Deploy Stored DB Function"]
    H --> I["SQL Query Execution & AST Rewrite"]
    I --> J["Stage 1: Database-Level Masking"]
    J --> K["Stage 2: Runtime Sensitive-Data Detection"]
    K --> L["Safe Masked Query Results"]
```

---

## 4. Key Features

| Category | Feature | Description |
| :--- | :--- | :--- |
| **Schema Discovery** | PostgreSQL Catalog Extraction | Discovers user-visible schemas, tables, column types, and relationships using `SchemaService`. |
| **AI Classification** | Metadata-Only Schema Analysis | Analyzes column names and SQL data types via LangChain LLM prompts; cross-validates outputs against PostgreSQL catalogs to discard hallucinated columns. |
| **Heuristic Fallback** | Deterministic Pattern Matching | Automatically falls back to deterministic regex pattern matching when LLM services are offline or unconfigured. |
| **Approval Workflow** | Human-in-the-Loop Review | Holds AI recommendations in a `PENDING` state until explicitly approved or rejected by an administrator. |
| **Policy Management** | Full Policy Lifecycle | Supports creating, editing, parameter tuning, deactivating, reactivating, and deleting masking policies with conflict prevention. |
| **Database Masking** | PL/pgSQL Stored Functions | Generates and executes immutable PostgreSQL stored functions (`maskgate_policy_<id>`) for active policies directly inside the database engine. |
| **SQL AST Parsing** | Intelligent Query Rewriter | Parses `SELECT` statements, expands `SELECT *` and table aliases, binds active policies, replaces protected columns with stored functions, and applies default `LIMIT` clauses. |
| **Zero Mutation** | Read-Only Data Preservation | Guarantees that underlying PostgreSQL tables and stored records are never altered; masking occurs only dynamically during query projections. |
| **Runtime Detection** | Two-Stage Defense in Depth | Scans unmasked result cells using local regex patterns (Email, Phone, SSN, Credit Cards, IP) and optional bounded LLM analysis. |
| **Security Guardrails** | SQL Query Validation | Enforces read-only `SELECT` queries, blocks multi-statement execution (`;`), and rejects DDL/DML keywords (`DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, `TRUNCATE`, `GRANT`). |
| **Admin Dashboard** | Modern React Interface | Interactive single-page application featuring system metric cards, schema browser, policy manager, and live SQL query editor with masked data previews. |

---

## 5. System Architecture

MaskGate is built with a clear separation of concerns across its frontend, backend API, AI integration layer, and PostgreSQL database engine:

```mermaid
flowchart TB
    USER["Developer / Database User"]

    subgraph FRONTEND["Frontend (React 18 + Vite + Tailwind CSS)"]
        DASH["Dashboard\n- System metrics & health\n- Recent query activity"]
        SCHEMA_UI["Schema Browser\n- Table/column catalog\n- AI analysis trigger"]
        POLICY_UI["Masking Policies\n- Pending AI review\n- Active policy editor"]
        QUERY_UI["Query Editor\n- SQL execution\n- Two-stage result inspector"]
    end

    subgraph BACKEND["Backend API (FastAPI)"]
        API["REST API Router (/api/v1)"]
        
        subgraph SERVICES["Application Core Services"]
            SCHEMA_SVC["Schema Service\n(Catalog extraction)"]
            AI_ANALYZER["AI Schema Analyzer\n(LangChain + Heuristics)"]
            MASKING_SVC["Masking Service\n(Policy & Engine Facade)"]
            QUERY_SVC["Query Service\n(Validation & Execution)"]
            PARSER["SQL Query Parser\n(AST & rewrite engine)"]
            DETECTOR["Runtime Detector\n(Regex & bounded LLM)"]
        end
    end

    subgraph DATABASE["PostgreSQL Database"]
        APP_TABLES["Application Tables\n(patients, medical_records, etc.)"]
        POLICY_TABLES["Metadata Tables\n(masking_policies, masking_recommendations)"]
        DB_FUNCS["Stored Masking Functions\n(maskgate_policy_<id>, maskgate_fn_*)"]
    end

    subgraph LLM_PROVIDERS["Configurable LLM Provider"]
        LLM_GW["LangChain Gateway\n(OpenAI GPT-4 / Google Gemini)"]
    end

    USER --> FRONTEND
    FRONTEND -->|HTTP / JSON| API
    API --> SCHEMA_SVC
    API --> AI_ANALYZER
    API --> MASKING_SVC
    API --> QUERY_SVC

    AI_ANALYZER -->|Metadata Prompts| LLM_GW
    AI_ANALYZER -->|Persist Recommendations| POLICY_TABLES
    MASKING_SVC -->|Manage Policies| POLICY_TABLES
    MASKING_SVC -->|Deploy PL/pgSQL Functions| DB_FUNCS

    QUERY_SVC --> PARSER
    PARSER -->|Fetch Table Schema & Active Policies| POLICY_TABLES
    QUERY_SVC -->|Execute Rewritten SQL| APP_TABLES
    APP_TABLES -->|Executes Stored Functions| DB_FUNCS
    QUERY_SVC -->|Unmasked Cells Scan| DETECTOR
    DETECTOR -.->|Bounded LLM Sample Scan| LLM_GW
```

*Stand-alone diagram source: [`docs/diagrams/architecture.mmd`](docs/diagrams/architecture.mmd)*

---

## 6. AI Recommendation Workflow

MaskGate strictly implements the principle: **"AI recommends; the administrator makes the final policy decision."**

### Privacy Invariants During AI Analysis
1. **Zero Row Data Transmission:** The AI analysis service extracts and sends **only schema metadata** (table names, column names, PostgreSQL data types). No row data, table contents, or database credentials are ever transmitted to the LLM.
2. **Schema Cross-Validation:** LLM recommendations are validated against the PostgreSQL catalog. Any hallucinated column names that do not exist in the database are discarded.
3. **Structured Pydantic Output:** The LLM produces strictly typed JSON outputs validated via Pydantic schemas.

```mermaid
flowchart TD
    SCHEMA["PostgreSQL Schema Catalog"]
    EXTRACT["Metadata Extraction\n(Table name, Column names, Data types)"]
    SANITIZATION["Metadata Sanitization\n(Zero row data; schema metadata only)"]
    
    subgraph ANALYSIS["AI Analysis Engine"]
        LLM_CHECK{"LLM Configured & Available?"}
        LLM_CALL["LangChain Prompt Execution\n(OpenAI / Gemini)"]
        HEURISTIC["Deterministic Pattern Matching\n(Regex fallback on column names)"]
        VALIDATE["Schema Cross-Validation\n(Discard hallucinated columns)"]
    end

    RECS["Structured Recommendations\n(Sensitivity, Strategy, Confidence, Rationale)"]
    QUEUE["Persist in DB with Status: PENDING\n(masking_recommendations table)"]
    
    subgraph REVIEW["Administrator Review (Dashboard)"]
        ADMIN{"Admin Decision"}
        APPROVE["Approve Recommendation"]
        REJECT["Reject Recommendation"]
    end

    ACTIVE_POLICY["Active Masking Policy\n(masking_policies table)"]
    DB_FUNCTION["Deploy Stored Function\n(CREATE OR REPLACE FUNCTION maskgate_policy_<id>)"]
    REJECTED_REC["Recommendation Status: REJECTED\n(No policy or DB function created)"]

    SCHEMA --> EXTRACT
    EXTRACT --> SANITIZATION
    SANITIZATION --> LLM_CHECK
    LLM_CHECK -->|Yes| LLM_CALL
    LLM_CHECK -->|No / Error| HEURISTIC
    LLM_CALL --> VALIDATE
    HEURISTIC --> VALIDATE
    VALIDATE --> RECS
    RECS --> QUEUE
    QUEUE --> REVIEW
    ADMIN -->|Approve| APPROVE
    ADMIN -->|Reject| REJECT
    APPROVE --> ACTIVE_POLICY
    ACTIVE_POLICY --> DB_FUNCTION
    REJECT --> REJECTED_REC
```

*Stand-alone diagram source: [`docs/diagrams/ai-workflow.mmd`](docs/diagrams/ai-workflow.mmd)*

---

## 7. Masking Policy Lifecycle

MaskGate manages the complete lifecycle of masking recommendations and active policies:

```mermaid
flowchart TD
    subgraph DISCOVERY["1. Discovery & Analysis"]
        SCHEMA_SCAN["Schema Discovery"]
        AI_REC["AI Recommendation Generated\n(Status: PENDING)"]
    end

    subgraph REVIEW["2. Human Review"]
        ADMIN_REVIEW{"Administrator Review\n(/masking UI)"}
        REJECT_ACTION["Reject Recommendation\n(Status: REJECTED)"]
        APPROVE_ACTION["Approve Recommendation\n(Status: APPROVED)"]
    end

    subgraph POLICY_STATE["3. Policy State Management"]
        CREATE_POLICY["Create Active Masking Policy\n(Status: ACTIVE, is_active: true)"]
        CREATE_FUNC["Deploy PostgreSQL Stored Function\n(maskgate_policy_<id>)"]
        MANUAL_EDIT["Admin Update / Parameter Adjustment\n(e.g., visible_chars, bin_size)"]
        RECREATE_FUNC["Update DB Function\n(CREATE OR REPLACE)"]
        DEACTIVATE["Deactivate / Delete Policy\n(Status: DISABLED / DELETED)"]
        DROP_FUNC["Drop PostgreSQL Function\n(DROP FUNCTION maskgate_policy_<id>)"]
        REACTIVATE["Reactivate Policy\n(Status: ACTIVE)"]
    end

    subgraph EXECUTION["4. Query Execution"]
        QUERY_TRANSFORM["Query AST Rewriting & DB Masking"]
    end

    SCHEMA_SCAN --> AI_REC
    AI_REC --> ADMIN_REVIEW
    ADMIN_REVIEW -->|Reject| REJECT_ACTION
    ADMIN_REVIEW -->|Approve| APPROVE_ACTION
    APPROVE_ACTION --> CREATE_POLICY
    CREATE_POLICY --> CREATE_FUNC
    CREATE_FUNC --> QUERY_TRANSFORM

    CREATE_POLICY --> MANUAL_EDIT
    MANUAL_EDIT --> RECREATE_FUNC
    RECREATE_FUNC --> QUERY_TRANSFORM

    CREATE_POLICY --> DEACTIVATE
    DEACTIVATE --> DROP_FUNC
    DROP_FUNC --> REACTIVATE
    REACTIVATE --> CREATE_FUNC
```

*Stand-alone diagram source: [`docs/diagrams/policy-lifecycle.mmd`](docs/diagrams/policy-lifecycle.mmd)*

### Supported Masking Strategies

| Strategy | Description | Example Input | Example Output | Database Implementation |
| :--- | :--- | :--- | :--- | :--- |
| `NONE` | Returns original value untouched | `12345` | `12345` | `maskgate_fn_none(val)` |
| `REDACT` | Replaces value with asterisks matching length | `Confidential` | `************` | `maskgate_fn_redact(val)` |
| `PARTIAL` | Preserves outer characters while masking center | `sensitive_text` | `se**********xt` | `maskgate_fn_partial(val, 2)` |
| `EMAIL` | Preserves first character and domain | `john.smith@gmail.com` | `j***@gmail.com` | `maskgate_fn_email(val)` |
| `PHONE_LAST4`| Masks all digits except the last 4 | `+1-555-019-2834` | `******2834` | `maskgate_fn_phone_last4(val)` |
| `HASH` | Cryptographic hash (SHA256, MD5, SHA512) | `user_secret` | `a591a6d40bf4...` | `maskgate_fn_hash(val, 'sha256')` |
| `SSN` | Preserves only last 4 digits of SSN | `123-45-6789` | `***-**-6789` | `maskgate_fn_ssn(val)` |
| `CREDIT_CARD`| Preserves only last 4 digits of credit card | `4532-1234-5678-9012`| `************9012` | `maskgate_fn_credit_card(val)` |
| `DATE` | Truncates date to January 1st of the same year | `1985-06-15` | `1985-01-01` | `maskgate_fn_date(val)` |
| `GENERALIZATION`| Groups numbers into configurable ranges | `45230` | `45000-46000` | `maskgate_fn_generalization(val, 1000)` |
| `DO_NOT_SHOW` | Replaces value or omits column from query | `secret_token` | `[HIDDEN]` | `maskgate_fn_do_not_show(val)` |

---

## 8. Query Protection Pipeline

When a developer submits a query, MaskGate processes it through a deterministic multi-step pipeline:

```mermaid
flowchart TD
    USER_QUERY["User SQL Query"]
    
    subgraph VALIDATION["1. Security Validation & Guardrails"]
        VAL_CHECK{"Is Query Valid?"}
        REJECT_ERR["Raise 400 Bad Request\n(Keyword / Multi-statement / Non-SELECT)"]
    end

    subgraph PARSING["2. SQL AST & Structure Analysis"]
        CLEAN["Strip SQL Comments & String Literals"]
        EXTRACT_TABLES["Extract Tables, Aliases & JOINs"]
        APPLY_LIMIT["Inject Default LIMIT if missing"]
    end

    subgraph REWRITE["3. Query Rewriting (Stage 1: DB-Level Masking)"]
        ACTIVE_POLICIES["Fetch Active Policies for Referenced Tables"]
        EXPAND_WILDCARDS["Expand SELECT * or alias.* to explicit columns"]
        INJECT_FUNCS["Replace Protected Columns with maskgate_policy_<id>(col::text) AS col\n(or '[HIDDEN]' for DO_NOT_SHOW)"]
        TRANSFORMED_SQL["Rewritten SQL Query"]
    end

    subgraph EXEC["4. PostgreSQL Execution"]
        PG_EXEC["Execute SQL in PostgreSQL"]
        PG_MASK["PostgreSQL executes stored PL/pgSQL masking functions during projection"]
        PG_RESULTS["Query Results (Stage 1 Masked)"]
    end

    subgraph RUNTIME_SCAN["5. Stage 2: Runtime Sensitive-Data Detection"]
        AUTO_DETECT_CHECK{"mask_suspicious = true?"}
        LOCAL_REGEX["Scan Unmasked Cells with Regex (Email, Phone, SSN, CC, IP)"]
        LLM_SAMPLE_SCAN["Optional Bounded LLM Scan on Unmasked Sample Rows"]
        CELL_MASK["Apply in-memory masking to newly detected sensitive cells"]
    end

    FINAL_RESULT["Safe Masked Query Results + Execution Metadata"]

    USER_QUERY --> VAL_CHECK
    VAL_CHECK -->|No| REJECT_ERR
    VAL_CHECK -->|Yes| CLEAN
    CLEAN --> EXTRACT_TABLES
    EXTRACT_TABLES --> APPLY_LIMIT
    APPLY_LIMIT --> ACTIVE_POLICIES
    ACTIVE_POLICIES --> EXPAND_WILDCARDS
    EXPAND_WILDCARDS --> INJECT_FUNCS
    INJECT_FUNCS --> TRANSFORMED_SQL
    TRANSFORMED_SQL --> PG_EXEC
    PG_EXEC --> PG_MASK
    PG_MASK --> PG_RESULTS
    PG_RESULTS --> AUTO_DETECT_CHECK
    AUTO_DETECT_CHECK -->|Yes| LOCAL_REGEX
    LOCAL_REGEX --> LLM_SAMPLE_SCAN
    LLM_SAMPLE_SCAN --> CELL_MASK
    CELL_MASK --> FINAL_RESULT
    AUTO_DETECT_CHECK -->|No| FINAL_RESULT
```

*Stand-alone diagram source: [`docs/diagrams/query-pipeline.mmd`](docs/diagrams/query-pipeline.mmd)*

---

## 9. SQL AST Processing & Query Rewriter

The `SQLQueryParser` component performs lexical and syntactic parsing to safely rewrite developer queries before execution:

1. **Comment & String Sanitization:** Removes single-line comments (`--`), block comments (`/* ... */`), and normalizes string literals to prevent injection.
2. **Table & JOIN Resolution:** Identifies base tables, schemas, and alias bindings across `FROM`, `INNER JOIN`, `LEFT JOIN`, `RIGHT JOIN`, `FULL JOIN`, and `CROSS JOIN` constructs.
3. **Wildcard Expansion:**
   - Single-table `SELECT * FROM patients` expands to all table columns, replacing protected columns with `maskgate_policy_<id>(col::text) AS col`.
   - Table-alias wildcards (e.g., `p.*`) expand based on alias resolution.
   - For `DO_NOT_SHOW` policies, columns are omitted from `SELECT *` or replaced with `'[HIDDEN]'::text AS col`.
4. **Explicit Projection Mapping:** Handles direct column references, aliased projections (`SELECT email AS user_email`), and qualified column names (`p.email`).
5. **Default Limit Injection:** If no top-level `LIMIT` clause is present, the parser automatically appends `LIMIT 100` to prevent accidental unbounded data extraction.

---

## 10. Database-Level Masking

MaskGate manages two layers of stored functions inside PostgreSQL via `DBMaskingFunctionManager`:

1. **Base Immutable Functions:** Pre-compiled PL/pgSQL functions providing the core masking primitives (`maskgate_fn_email`, `maskgate_fn_phone_last4`, `maskgate_fn_partial`, `maskgate_fn_redact`, `maskgate_fn_hash`, etc.).
2. **Policy Wrapper Functions:** Dynamically created stored functions named `maskgate_policy_<id>(val text)` corresponding to each active policy.

```mermaid
flowchart TD
    subgraph ADMIN_FLOW["Policy Activation"]
        POLICY["Active Masking Policy (ID: <id>)\nTable: patients, Column: email, Strategy: EMAIL"]
        GEN_SQL["Generate PL/pgSQL Function Body\nmaskgate_policy_<id>(val text)"]
        EXEC_DDL["CREATE OR REPLACE FUNCTION maskgate_policy_<id>(val text)\nRETURNS text AS $$ ... $$ LANGUAGE plpgsql IMMUTABLE;"]
    end

    subgraph QUERY_FLOW["Query Execution at Runtime"]
        USER_SQL["User SQL: SELECT email FROM patients;"]
        REWRITE_SQL["Rewritten SQL: SELECT maskgate_policy_1(email::text) AS email FROM patients;"]
        PG_ENGINE["PostgreSQL Query Engine"]
        IMMUTABLE_FN["maskgate_policy_1(email) -> maskgate_fn_email(email)"]
        BASE_FN["PL/pgSQL Base Function: j***@example.com"]
        RESULT["Masked Result to Application"]
    end

    POLICY --> GEN_SQL
    GEN_SQL --> EXEC_DDL
    EXEC_DDL --> IMMUTABLE_FN

    USER_SQL --> REWRITE_SQL
    REWRITE_SQL --> PG_ENGINE
    PG_ENGINE --> IMMUTABLE_FN
    IMMUTABLE_FN --> BASE_FN
    BASE_FN --> RESULT
```

*Stand-alone diagram source: [`docs/diagrams/db-masking.mmd`](docs/diagrams/db-masking.mmd)*

---

## 11. Two-Stage Protection

MaskGate employs a defense-in-depth architecture combining deterministic database execution with runtime anomaly detection:

```mermaid
flowchart TD
    QUERY["User SQL Query"]

    subgraph STAGE1["Stage 1: PostgreSQL Database-Level Masking"]
        direction TB
        REWRITE["SQL AST Rewriting (injecting policy functions)"]
        PG_PROC["PostgreSQL Engine executes PL/pgSQL stored masking functions"]
        ZERO_MUTATION["Zero DB Mutation Guarantee (original tables untouched)"]
        STAGE1_OUT["Stage 1 Masked Query Results"]
        REWRITE --> PG_PROC
        PG_PROC --> ZERO_MUTATION
        ZERO_MUTATION --> STAGE1_OUT
    end

    subgraph STAGE2["Stage 2: Runtime Sensitive-Data Detection (Secondary Defense)"]
        direction TB
        CHECK["Scan unmasked columns / newly exposed data"]
        REGEX_SCAN["Deterministic Cell Regex (Email, Phone, SSN, CC, IP)"]
        LLM_SCAN["Bounded Semantic LLM Scan (Names, addresses, notes)"]
        IN_MEMORY["In-Memory Cell Masking for Uncovered PII"]
        CHECK --> REGEX_SCAN
        REGEX_SCAN --> LLM_SCAN
        LLM_SCAN --> IN_MEMORY
    end

    FINAL["Safe Masked Result Set + Audit Metadata"]

    QUERY --> STAGE1
    STAGE1_OUT --> STAGE2
    IN_MEMORY --> FINAL
```

*Stand-alone diagram source: [`docs/diagrams/two-stage-protection.mmd`](docs/diagrams/two-stage-protection.mmd)*

- **Stage 1 (Database-Level Masking):** Applies approved, active policies deterministically inside PostgreSQL during SQL projection. High-speed, zero-mutation, and verified against the catalog.
- **Stage 2 (Runtime Sensitive-Data Detection):** Scans remaining unmasked cells for data patterns that were not covered by existing policies (e.g., ad-hoc computed expressions or newly seeded tables). Uses cell-level regex pattern matching followed by bounded LLM sampling (limited to maximum 5 rows and 50 characters per cell) to prevent data leakage.

---

## 12. Security Controls

The following security controls are implemented and verified in the MaskGate codebase:

| Security Control | Implementation Mechanism | Status |
| :--- | :--- | :--- |
| **Read-Only SQL Enforcement** | `QueryService.validate_query` ensures queries begin with `SELECT` or `WITH ... SELECT` | Implemented |
| **DML / DDL Prevention** | Rejection of keywords: `DROP`, `DELETE`, `TRUNCATE`, `ALTER`, `CREATE`, `GRANT`, `REVOKE`, `INSERT`, `UPDATE` | Implemented |
| **Multi-Statement Blocking** | Rejection of semicolons separating multiple SQL statements | Implemented |
| **Zero Database Mutation** | Masking occurs purely in query projection; underlying table records are never updated or deleted | Implemented |
| **Metadata-Only AI Prompts** | Schema analysis prompts transmit only table names, column names, and data types (no row data) | Implemented |
| **Schema Cross-Validation** | Rejects LLM recommendations for nonexistent or hallucinated columns | Implemented |
| **Bounded LLM Sampling** | Runtime detection samples maximum 5 rows and truncates cells to 50 characters | Implemented |
| **Environment Variable Isolation** | Database credentials and API keys are loaded centrally via `pydantic-settings` from `.env` | Implemented |
| **Human Approval Boundary** | AI recommendations remain `PENDING` until explicitly approved by an administrator | Implemented |
| **Default Result Pagination** | Automatic injection of `LIMIT 100` on unbounded outer queries | Implemented |

---

## 13. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend Framework** | React 18 (`react`, `react-dom`) | Component-based user interface |
| **Build Tool & Bundler** | Vite 5 (`vite`, `@vitejs/plugin-react`) | Development server and production build bundling |
| **Styling & Design System** | Tailwind CSS 3 & Tailwind Animate | Responsive dark-mode styling and utility animations |
| **UI Components & Icons** | Radix UI primitives & Lucide React (`lucide-react`) | Accessible accessible UI controls, dialogs, dropdowns, and iconography |
| **Client Routing & State** | React Router DOM 6 & TanStack React Query 5 | Client-side routing and asynchronous server-state management |
| **HTTP Client** | Axios 1.6 | REST API communication with the FastAPI backend |
| **Backend Framework** | FastAPI 0.115 (`fastapi`, `uvicorn`) | High-performance asynchronous REST API framework |
| **Data Validation** | Pydantic 2.10 & Pydantic Settings 2.6 | Typed request/response schemas and environment configuration |
| **Database Engine** | PostgreSQL 14+ (`psycopg2`) | Relational database engine and PL/pgSQL stored procedures |
| **GenAI Orchestration** | LangChain 0.1 (`langchain`) | AI workflow orchestration and prompt management |
| **LLM Integrations** | `langchain-openai` & `langchain-google-genai` | Multi-model support for OpenAI GPT-4 and Google Gemini |
| **Testing Framework** | pytest 7.4 (`pytest`, `pytest-asyncio`) | Automated unit, integration, and security regression testing |

---

## 14. Project Structure

```text
MaskGate/
├── backend/                        # Python FastAPI backend application
│   ├── app/
│   │   ├── ai/                     # GenAI and LLM integration layer
│   │   │   ├── llm.py              # LangChain gateway (OpenAI & Gemini)
│   │   │   ├── llm_schemas.py      # Pydantic schemas for AI recommendations
│   │   │   ├── schema_analyzer.py  # AI schema analysis with heuristic fallback
│   │   │   └── sensitive_data_detector.py # Runtime sensitive data detector
│   │   ├── api/                    # API route definitions
│   │   │   └── routes/
│   │   │       ├── health.py       # Health check endpoints
│   │   │       ├── masking.py      # Masking policy & recommendation CRUD
│   │   │       ├── query.py        # SQL query execution & validation
│   │   │       └── schema.py       # Schema discovery & analysis triggers
│   │   ├── config/
│   │   │   └── settings.py         # Typed environment configuration
│   │   ├── database/               # PostgreSQL database interface
│   │   │   ├── base.py             # Database connector abstraction
│   │   │   ├── connection.py       # Threaded connection pool manager
│   │   │   ├── db_masking_functions.py # PL/pgSQL stored function manager
│   │   │   ├── postgresql.py       # PostgreSQLConnector implementation
│   │   │   └── repositories.py     # Policy and recommendation repositories
│   │   ├── masking/                # Deterministic masking engine
│   │   │   ├── engine.py           # In-memory masking engine
│   │   │   ├── policies.py         # Policy manager facade
│   │   │   └── strategies.py       # Deterministic strategy implementations
│   │   ├── schemas/                # API Pydantic schemas
│   │   │   ├── database.py         # Schema catalog models
│   │   │   ├── masking.py          # Policy & recommendation models
│   │   │   └── query.py            # Query execution models
│   │   ├── services/               # Business logic service layer
│   │   │   ├── masking_service.py  # Masking orchestration service
│   │   │   ├── query_service.py    # Query execution & AST pipeline service
│   │   │   └── schema_service.py   # Schema catalog discovery service
│   │   ├── utils/                  # Helpers and query parsing
│   │   │   └── query_parser.py     # SQL parser, AST analyzer, and rewriter
│   │   └── main.py                 # FastAPI application entry point
│   ├── tests/                      # Pytest automated test suite (13 test modules)
│   └── pytest.ini                  # Pytest configuration
├── frontend/                       # React 18 single-page application
│   ├── src/
│   │   ├── components/             # Reusable UI components & layouts
│   │   ├── pages/                  # Application views
│   │   │   ├── Dashboard.jsx       # Overview, system metrics, activity
│   │   │   ├── MaskingPolicies.jsx # AI review queue & policy editor
│   │   │   ├── QueryEditor.jsx     # SQL query editor & masked results
│   │   │   └── SchemaBrowser.jsx   # Database schema & table browser
│   │   ├── services/               # Frontend API client modules
│   │   ├── App.jsx                 # Route definitions & theme provider
│   │   └── main.jsx                # React entry point
│   ├── package.json                # Frontend dependencies and scripts
│   └── vite.config.js              # Vite configuration with API proxy
├── database/                       # Database DDL and seed scripts
│   ├── schema.sql                  # Application and demonstration tables
│   ├── seed.sql                    # Synthetic healthcare dataset
│   ├── connector.py                # Database initialization script
│   └── load_seed_data.py           # Seed loader utility
├── docs/                           # Technical documentation & design specs
│   ├── diagrams/                   # Standalone Mermaid (.mmd) diagram sources
│   ├── architecture.md             # Architecture design document
│   ├── masking.md                  # Masking engine technical specification
│   ├── runtime-detection.md        # Runtime detection specification
│   └── future-roadmap.md           # Research and production roadmap
├── scripts/                        # Automation shell scripts
│   ├── setup.sh                    # Automated environment setup script
│   ├── start.sh                    # Dual backend/frontend runner script
│   ├── test.sh                     # Backend test runner script
│   ├── migrate.sh                  # Database migration script
│   ├── backup.sh                   # Database backup utility
│   └── restore.sh                  # Database restore utility
├── requirements.txt                # Python backend dependencies
├── .env.example                    # Environment variable configuration template
└── README.md                       # Project documentation
```

---

## 15. Installation

### Prerequisites
- **Python:** Version 3.9 or higher
- **Node.js:** Version 18 or higher (with `npm`)
- **PostgreSQL:** Version 14 or higher
- **Git:** Version 2.x

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/faizamfairooz/MaskGate.git
cd MaskGate
```

---

### Step 2: Configure Environment Variables

Create your local `.env` configuration file from the template:

```bash
cp .env.example .env
```

Edit `.env` to configure your PostgreSQL credentials and optional LLM API keys.

---

### Step 3: Set Up Python Backend

Create and activate a Python virtual environment, then install requirements:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r ../requirements.txt

cd ..
```

---

### Step 4: Set Up PostgreSQL Database

Create the database and apply the initial schema and synthetic demonstration dataset:

```bash
# Create the PostgreSQL database (if not existing)
createdb -U postgres maskgate

# Apply schema DDL
psql -U postgres -d maskgate -f database/schema.sql

# Load synthetic healthcare demonstration data
psql -U postgres -d maskgate -f database/seed.sql
```

---

### Step 5: Set Up Frontend

Install Node.js dependencies:

```bash
cd frontend
npm install
cd ..
```

---

## 16. Environment Variables

The application loads configuration centrally via Pydantic in [`backend/app/config/settings.py`](backend/app/config/settings.py). Documented variable names:

| Variable Name | Required | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | Optional | `None` | Full PostgreSQL connection URL (e.g. `postgresql://user:pass@host:5432/dbname`) |
| `DB_HOST` | Required | `localhost` | PostgreSQL host address |
| `DB_PORT` | Required | `5432` | PostgreSQL port |
| `DB_NAME` | Required | `maskgate_test` | PostgreSQL database name |
| `DB_USER` | Required | `postgres` | PostgreSQL username |
| `DB_PASSWORD` | Required | `""` | PostgreSQL password |
| `API_HOST` | Optional | `0.0.0.0` | FastAPI server host bind address |
| `API_PORT` | Optional | `8000` | FastAPI server port |
| `DEBUG` | Optional | `True` | FastAPI debug mode flag |
| `OPENAI_API_KEY` | Optional | `None` | OpenAI API key for GPT-4 schema analysis |
| `GOOGLE_API_KEY` | Optional | `None` | Google AI Studio API key for Gemini schema analysis |
| `LLM_MODEL` | Optional | `gpt-4` | Model name for OpenAI integration |
| `LLM_TEMPERATURE` | Optional | `0.3` | Temperature for LLM sampling (0.0 to 1.0) |
| `ENABLE_RUNTIME_DETECTION` | Optional | `True` | Flag to enable Stage 2 runtime detection |
| `MAX_DETECTION_SAMPLE_ROWS` | Optional | `5` | Maximum query rows sampled for runtime LLM scan |
| `MAX_DETECTION_CELL_LENGTH` | Optional | `50` | Maximum character length per cell sent to runtime LLM |
| `LLM_DETECTION_TIMEOUT_SECONDS` | Optional | `5` | Timeout in seconds for LLM calls |
| `DEFAULT_QUERY_LIMIT` | Optional | `100` | Default LIMIT appended to unbounded SELECT queries |
| `SECRET_KEY` | Optional | `None` | Secret key for token signing |

> **Note:** If no LLM API key is provided, MaskGate automatically operates using its built-in deterministic heuristic engine.

---

## 17. Running the Application

### Option A: Using the Automated Runner Script

```bash
./scripts/start.sh
```

---

### Option B: Running Services Individually

#### 1. Start the Backend Server

```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **Backend API:** `http://localhost:8000`
- **Interactive OpenAPI Documentation:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`

#### 2. Start the Frontend Development Server

```bash
cd frontend
npm run dev
```

- **Admin Dashboard UI:** `http://localhost:3000` (or `http://localhost:5173`)

---

## 18. Demonstration Workflow

Follow this step-by-step procedure to evaluate MaskGate:

1. **Explore Schema Catalog:**
   - Navigate to the **Schema Browser** (`/schema`).
   - Select the `patients` table to inspect discovered columns, SQL data types, and primary/foreign keys.
2. **Trigger AI Schema Analysis:**
   - Click **"Analyze with AI"** on the `patients` table.
   - The backend runs metadata-only analysis and generates structured recommendations for sensitive fields (`email` -> `EMAIL`, `phone` -> `PHONE_LAST4`, `date_of_birth` -> `DATE`).
3. **Review & Approve Policies:**
   - Navigate to **Masking Policies** (`/masking`).
   - Inspect the **Pending AI Recommendations** queue.
   - Click **"Approve"** on the `email` recommendation. The policy status transitions to `ACTIVE`, and PostgreSQL automatically compiles the stored function `maskgate_policy_<id>`.
4. **Execute Protected Queries in Query Editor:**
   - Navigate to the **Query Editor** (`/query`).
   - Execute a wildcard query:
     ```sql
     SELECT * FROM patients;
     ```
   - Observe that `email` is dynamically masked at the database level (`j***@example.com`), while non-sensitive columns remain readable.
5. **Verify Multi-Table JOIN Masking:**
   - Execute a multi-table query:
     ```sql
     SELECT p.full_name, p.email, m.diagnosis, m.notes 
     FROM patients p 
     JOIN medical_records m ON p.patient_id = m.patient_id;
     ```
   - Observe that table aliases are resolved and masking is applied accurately across table boundaries.
6. **Test Runtime Sensitive-Data Detection (Stage 2):**
   - Toggle **"Detect Suspicious Data"** in the Query Editor.
   - Execute a query on unmasked text fields containing contact numbers or embedded emails.
   - Observe Stage 2 runtime detection identifying and masking the exposed cells with an audit summary.
7. **Verify Security Guardrails:**
   - Attempt a non-read-only query:
     ```sql
     DROP TABLE patients;
     ```
   - Observe immediate rejection by the validation engine with a clear security violation message.

---

## 19. Testing

MaskGate contains a comprehensive suite of unit, integration, and security regression tests located in [`backend/tests/`](backend/tests/):

### Test Modules

| Test Module | Coverage Scope |
| :--- | :--- |
| `test_health.py` | Health check and system status endpoints |
| `test_database.py` | PostgreSQL connection pool and query execution |
| `test_schema.py` | Catalog extraction and table schema discovery |
| `test_ai.py` | LangChain LLM schemas, prompt formatting, and fallback heuristics |
| `test_recommendation_review.py` | Recommendation approval and rejection lifecycle |
| `test_masking.py` | In-memory masking strategies and policy management |
| `test_deterministic_masking.py` | Edge cases for deterministic masking algorithms |
| `test_db_masking_functions.py` | PostgreSQL PL/pgSQL stored function generation and lifecycle |
| `test_policy_lifecycle_hardening.py`| Concurrent policy updates and conflict handling |
| `test_query_hardening.py` | SQL parser AST rewriting, aliases, JOINs, and LIMIT injection |
| `test_runtime_detection.py` | Stage 2 regex scanning and bounded LLM sampling |
| `test_strategy_compatibility_audit.py` | Cross-strategy compatibility across PostgreSQL data types |
| `test_e2e_integration.py` | End-to-end API workflows from schema discovery to masked query execution |

### Running the Test Suite

```bash
# Run tests with pytest
cd backend
source venv/bin/activate
pytest tests/ -v

# Or use the test script
./scripts/test.sh
```

> *Note: Test results should be generated during final validation on the target environment.*

---

## 20. Limitations & Future Roadmap

### Current Limitations
- **Query Interception Model:** MaskGate currently operates as a managed application and API gateway rather than a transparent PostgreSQL wire-protocol proxy.
- **SQL Dialect Scope:** The SQL parser and AST rewriter are optimized for standard PostgreSQL `SELECT` queries, subqueries, and `JOIN` constructs; complex non-standard window functions or dynamic PL/pgSQL blocks require explicit column aliasing.
- **Single Database Engine:** The current MVP is implemented specifically for PostgreSQL.

### Future Roadmap
- [ ] **PostgreSQL Wire-Protocol Proxy:** Implement a transparent TCP proxy speaking the PostgreSQL frontend/backend protocol to mask queries from standard SQL clients (psql, DBeaver, pgAdmin) without application changes.
- [ ] **Multi-Database Connectors:** Extend database abstraction to support MySQL, Oracle, Snowflake, and Microsoft SQL Server.
- [ ] **Role-Based Access Control (RBAC):** Fine-grained permission tiers allowing unmasked access for privileged database administrators while enforcing dynamic masking for standard developers.
- [ ] **Schema Drift Monitoring:** Automated background tasks to detect schema migrations and queue newly created columns for AI sensitivity analysis.
- [ ] **Enterprise SIEM Integration:** Real-time audit log streaming to enterprise security platforms (Splunk, Datadog).

---

## 21. Technical Diagrams & Export

Standalone Mermaid diagram definition files are maintained under [`docs/diagrams/`](docs/diagrams/):

- [`docs/diagrams/architecture.mmd`](docs/diagrams/architecture.mmd) — Full System Architecture
- [`docs/diagrams/ai-workflow.mmd`](docs/diagrams/ai-workflow.mmd) — AI Recommendation Workflow
- [`docs/diagrams/policy-lifecycle.mmd`](docs/diagrams/policy-lifecycle.mmd) — Masking Policy Lifecycle
- [`docs/diagrams/query-pipeline.mmd`](docs/diagrams/query-pipeline.mmd) — Query Protection Pipeline
- [`docs/diagrams/db-masking.mmd`](docs/diagrams/db-masking.mmd) — Database-Level Masking Functions
- [`docs/diagrams/two-stage-protection.mmd`](docs/diagrams/two-stage-protection.mmd) — Two-Stage Protection Flow

### Exporting Diagrams for Presentations & Reports

To render and export diagrams to high-resolution PNG or SVG for project reports or presentation slides:

```bash
# Install Mermaid CLI (optional)
npm install -g @mermaid-js/mermaid-cli

# Export architecture diagram to PNG
mmdc -i docs/diagrams/architecture.mmd -o docs/diagrams/architecture.png -b transparent

# Export query pipeline diagram to SVG
mmdc -i docs/diagrams/query-pipeline.mmd -o docs/diagrams/query-pipeline.svg
```

Diagrams can also be copied directly into [Mermaid Live Editor](https://mermaid.live/) for visual export.

---

## 22. Project Information & Acknowledgments

This project is developed as part of the **Ascentic AI Launch Pad** program.

- **Project:** MaskGate (GenAI-Assisted Dynamic Data Masking System for PostgreSQL)
- **Program:** Ascentic AI Launch Pad
- **Objective:** Demonstrate GenAI-driven database schema analysis, policy recommendations, and deterministic multi-stage data masking for enterprise data privacy.
- **License:** Developed for academic and demonstration purposes.
