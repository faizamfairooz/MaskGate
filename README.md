# 🛡️ MaskGate

> **A Proxy-Based Dynamic Data Masking Framework for PostgreSQL**

MaskGate is a secure database proxy that enables developers to access PostgreSQL databases without exposing sensitive information. It intercepts SQL queries, applies dynamic data masking based on configurable policies, records audit logs, and returns privacy-preserving results. The framework is designed to support GDPR-compliant database access while maintaining a seamless developer experience.

---

## 📖 Overview

Developers often require access to production-like data to reproduce and debug issues. However, granting direct access to production databases can expose Personally Identifiable Information (PII), creating security and compliance risks under regulations such as the General Data Protection Regulation (GDPR).

MaskGate addresses this challenge by acting as an intelligent proxy between developers and PostgreSQL databases. Instead of allowing direct database connections, every SQL request passes through the proxy, where masking rules and access policies are enforced before the query reaches the database.

---

## 🎯 Objectives

- Protect sensitive data during database access.
- Apply dynamic data masking without modifying the original database.
- Reduce the risk of unauthorized access to production data.
- Maintain database usability for developers.
- Provide audit logs for accountability and compliance.
- Design an extensible architecture for future support of additional database systems.

---

## ✨ Features

- Dynamic Data Masking
- PostgreSQL Database Proxy
- Secure TCP-Based Communication
- Role-Based Access Control (RBAC)
- Configurable Masking Rules
- Audit Logging
- Administrator Management Panel
- VS Code Integration
- Modular Database Connector Architecture
- Future Multi-Database Support

---

## 🏗️ System Architecture

```text
                  +----------------------+
                  |      VS Code         |
                  | (SQL Client/Extension)|
                  +----------+-----------+
                             |
                             |
                     TCP Connection
                             |
                             ▼
                 +----------------------+
                 |     MaskGate Proxy   |
                 |----------------------|
                 | Authentication       |
                 | Authorization        |
                 | Query Parser         |
                 | Dynamic Masking      |
                 | Audit Logger         |
                 +----------+-----------+
                            |
                            ▼
                 +----------------------+
                 |     PostgreSQL       |
                 +----------------------+
```

---

## ⚙️ Technology Stack

| Component | Technology |
|----------|------------|
| Programming Language | Go |
| Database | PostgreSQL |
| Communication | TCP Socket |
| Query Processing | PostgreSQL Wire Protocol |
| Frontend | React (Admin Dashboard) |
| IDE Integration | VS Code Extension |
| Authentication | JWT (Planned) |
| Version Control | Git & GitHub |

---

## 📂 Project Structure

```text
MaskGate/
│
├── docs/
│   ├── proposal/
│   ├── architecture/
│   └── research/
│
├── proxy-server/
│
├── masking-engine/
│
├── database/
│   ├── schema/
│   └── migrations/
│
├── admin-panel/
│
├── vscode-extension/
│
├── examples/
│
├── README.md
└── LICENSE
```

---

## 🔒 Dynamic Data Masking

Example:

Original query:

```sql
SELECT id, name, email, phone
FROM users;
```

Returned result:

| id | name | email | phone |
|----|------|--------|--------|
| 1 | J*** D** | j***@gmail.com | ********45 |

The original data remains unchanged inside PostgreSQL.

---

## 📋 Audit Logging

Every database request is recorded with relevant metadata.

Example audit record:

| Field | Value |
|-------|-------|
| User | developer01 |
| Role | Backend Developer |
| Query | SELECT * FROM users |
| Masking Applied | Email, Phone |
| Timestamp | 2026-08-07 10:35 UTC |
| Status | Success |

---

## 🚀 Future Enhancements

- MySQL Connector
- MongoDB Connector
- Microsoft SQL Server Connector
- Oracle Database Connector
- AI-Assisted Masking Rule Suggestions
- Enterprise Policy Management
- Cloud Deployment Support

---

## 👨‍💻 Development Status

Current Phase:

- [x] Research
- [ ] System Design
- [ ] PostgreSQL Proxy
- [ ] Dynamic Masking Engine
- [ ] VS Code Extension
- [ ] Admin Dashboard
- [ ] Testing
- [ ] Documentation

---

## 📚 Research Focus

MaskGate focuses on:

- Dynamic Data Masking
- Secure Database Proxy Design
- Privacy-Preserving Database Access
- GDPR Compliance
- Database Security
- Secure Software Engineering

---

## 🤝 Contributors

- **Faizam Fairooz** — Project Developer
- **Supervisor:** *Arnaldo Pasangha*
- **Co-Supervisor:** *Venura Pesanjith*

---

## 📄 License

This project is being developed as part of an undergraduate research project. The license will be determined before the public release.
