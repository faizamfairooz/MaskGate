# MaskGate Architecture

## Overview

MaskGate is a comprehensive database security platform that provides AI-powered sensitive data detection and masking capabilities. The architecture follows a modular, service-oriented design with clear separation of concerns.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│                    (React + Vite)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Dashboard│  │ Schema   │  │ Masking  │  │ Query    │  │
│  │          │  │ Browser  │  │ Policies │  │ Editor   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API                             │
│                     (FastAPI)                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Health   │  │ Schema   │  │ Masking  │  │ Query    │  │
│  │ Routes   │  │ Routes   │  │ Routes   │  │ Routes   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Services   │     │      AI      │     │   Masking    │
│              │     │              │     │              │
│ Schema       │     │ LLM Client   │     │ Engine       │
│ Masking      │     │ Schema       │     │ Strategies   │
│ Query        │     │ Analyzer     │     │ Policies     │
└──────────────┘     └──────────────┘     └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                    ┌──────────────────┐
                    │    Database      │
                    │   (PostgreSQL)   │
                    └──────────────────┘
```

## Component Overview

### Frontend Layer

- **Framework**: React 18 with Vite for fast development
- **Routing**: React Router for client-side navigation
- **State Management**: TanStack Query for server state
- **HTTP Client**: Axios for API communication
- **Components**:
  - Dashboard: Overview and statistics
  - Schema Browser: Database schema exploration
  - Masking Policies: Policy management interface
  - Query Editor: SQL query execution with masking

### Backend API Layer

- **Framework**: FastAPI for high-performance async API
- **Authentication**: JWT-based authentication (planned)
- **CORS**: Configured for frontend integration
- **Routes**:
  - `/api/health`: Health check endpoints
  - `/api/schema`: Schema analysis and browsing
  - `/api/masking`: Policy management and application
  - `/api/query`: Query execution with masking

### Service Layer

- **SchemaService**: Database schema operations and analysis
- **MaskingService**: Policy management and masking application
- **QueryService**: Query execution and validation
- **Pattern Detection**: AI-powered sensitive data identification

### AI Layer

- **LLM Client**: OpenAI and Google AI Studio integration for advanced analysis
- **Schema Analyzer**: Pattern recognition in database schemas
- **Sensitive Data Detector**: Real-time data classification
- **Runtime Detection**: Secondary safety layer for query results
- **Fallback**: Rule-based detection when LLM unavailable

### Masking Layer

- **Masking Engine**: Core masking application logic
- **Strategies**: 11 different masking approaches
  - Redaction, Partial Mask, Hash, Email Mask
  - Phone Mask, SSN Mask, Credit Card Mask
  - Tokenization, Noise Addition, Date Mask, Generalization
- **Policy Manager**: Policy lifecycle management
- **Strategy Factory**: Dynamic strategy instantiation

### Database Layer

- **Connection Pool**: Efficient connection management
- **PostgreSQL Implementation**: Type-safe database operations
- **Schema**: Multi-table structure for policies, audit, and sample data
- **Indexes**: Optimized for common query patterns

## Data Flow

### Schema Analysis Flow

1. User requests schema analysis via frontend
2. API routes request to SchemaService
3. SchemaService fetches schema from database
4. AI Analyzer identifies sensitive columns
5. Results returned through API to frontend

### Query Execution Flow

1. User submits SQL query in Query Editor
2. API validates query for security
3. QueryService executes query against database
4. MaskingService applies applicable deterministic policies
5. **Runtime Sensitive Data Detection** (secondary safety layer):
   - Pattern-based detection for columns not covered by policies
   - LLM-based detection for additional sensitive data
   - Deterministic masking applied based on detection results
6. Results returned with masking information
7. Query logged in history for audit

### Policy Management Flow

1. User creates masking policy via UI
2. API validates policy configuration
3. PolicyManager stores policy in database
4. MaskingEngine uses policy for future queries
5. Audit log records policy changes

## Security Considerations

### Data Protection

- All sensitive data is masked before leaving the database
- Policies are enforced at the service layer
- Audit trail tracks all data access
- Connection pooling prevents connection leaks

### API Security

- CORS configuration limits cross-origin requests
- Input validation on all API endpoints
- SQL injection prevention through parameterized queries
- Query validation prevents dangerous operations

### Authentication & Authorization

- JWT-based authentication (planned implementation)
- Role-based access control (planned implementation)
- User-specific policy management
- Audit logging for compliance

## Scalability Considerations

### Performance

- Connection pooling reduces database overhead
- Caching for schema analysis results
- Asynchronous processing for AI operations
- Efficient indexing on database tables

### Extensibility

- Modular architecture allows easy component addition
- Strategy pattern for new masking algorithms
- Plugin architecture for AI providers
- REST API for third-party integration

## Deployment Architecture

### Development Environment

- Frontend: Vite dev server on port 3000
- Backend: Uvicorn on port 8000
- Database: PostgreSQL on port 5432
- Hot reload for both frontend and backend

### Production Environment

- Frontend: Static files served by nginx
- Backend: Gunicorn with Uvicorn workers
- Database: PostgreSQL with connection pooling
- Load balancer for horizontal scaling
- Monitoring and logging infrastructure

## Technology Stack

### Frontend
- React 18.2.0
- React Router 6.20.0
- Axios 1.6.2
- TanStack Query 5.12.0
- Vite 5.0.8

### Backend
- FastAPI 0.104.1
- Uvicorn 0.24.0
- Pydantic 2.5.0
- SQLAlchemy 2.0.23
- Psycopg2 2.9.9

### AI/ML
- OpenAI 1.3.7
- Custom pattern matching algorithms

### Database
- PostgreSQL 14+
- JSONB for flexible policy storage

## Future Enhancements

- Multi-database support (MySQL, SQL Server)
- Real-time data streaming
- Advanced anomaly detection
- Automated policy recommendation
- Compliance reporting (GDPR, CCPA)
- Data lineage tracking
- Performance monitoring dashboard
