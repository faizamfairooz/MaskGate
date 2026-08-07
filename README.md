# 🛡️ MaskGate

**A Proxy-Based Dynamic Data Masking Framework for PostgreSQL**

MaskGate enables developers to query production-like databases securely by masking sensitive information in real time while maintaining data relationships and supporting GDPR-compliant access.

---

## 🎯 Problem

Developers debugging production issues need realistic data, but GDPR prohibits accessing real PII (Personal Identifiable Information). Traditional masking tools are static, manual, and break data relationships.

---

## 💡 Solution

MaskGate provides an **intelligent intermediate layer** between developers and databases:

- 🔍 **Auto-detects** PII columns using hybrid rules + Gen AI
- 🎭 **Dynamically masks** sensitive data while preserving relationships
- 📝 **Audits** every access for GDPR compliance
- 🛠️ **Integrates** with VS Code and CLI for seamless debugging

---

## 🏗️ Architecture

