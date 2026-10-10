# Security Architecture & Specification

## 1. Threat Model (STRIDE)
We employ STRIDE methodology for component-level threat modeling:
- **Spoofing**: Mitigated via strict JWT and robust identity verification.
- **Tampering**: All payloads validated with Pydantic; TLS 1.3 for data in transit.
- **Repudiation**: Comprehensive audit logging (who accessed what, when).
- **Information Disclosure**: Secrets encrypted at rest (AES-256-GCM) and never exposed to the frontend.
- **Denial of Service**: Cloudflare WAF, strict API rate limiting, resource quotas.
- **Elevation of Privilege**: Granular RBAC (Role-Based Access Control).

### 1.1 Threat Actors
- Script kiddies, Credential stuffers, Insider threats, Competitive scraping bots.

## 2. Authentication & Authorization

### 2.1 JWT Lifecycle
- **Access Tokens**: Short-lived (15 minutes).
- **Refresh Tokens**: Long-lived (7 days), stored in HttpOnly, secure cookies.
- **2FA**: TOTP-based Multi-Factor Authentication required for account access.

### 2.2 RBAC Model
- **Free**: 100 req/min limit, delayed data, basic indicators.
- **Pro**: 1000 req/min limit, real-time data, advanced orderflow.
- **Institutional**: 10000 req/min limit, raw tick access, programmatic API.
- **Admin**: Full system access (IP restricted, VPN required).

## 3. Credential Management & Broker Isolation
- **Storage**: HashiCorp Vault / AWS Secrets Manager in production. Local `.env` (gitignored) for dev.
- **Broker API Keys**: Encrypted in Postgres. Decrypted strictly in backend memory per active session.
- **Frontend Isolation**: Broker credentials are NEVER sent to the client. The backend acts as a secure proxy.
- **Logging**: Zero plaintext logging of credentials. Scrubbers implemented on all log outputs.

## 4. API & Application Security
- **Rate Limiting**: Enforced via Redis token bucket algorithm per IP and User ID.
- **Input Validation**: Pydantic models on all FastAPI endpoints. Reject unexpected schema fields.
- **Injection Prevention**: Parameterized SQL (via SQLAlchemy/asyncpg) exclusively.
- **XSS Prevention**: Strict Content Security Policy (CSP) headers.
- **CORS**: Allowlisted origins only (`https://alphapulse-stock-scanner.vercel.app` and specific dev ports).

## 5. Infrastructure Security
- **Perimeter**: Cloudflare WAF, DDoS protection.
- **Transit**: TLS 1.3 everywhere.
- **Containers**: Docker containers run as non-root, read-only root filesystems where possible, memory/CPU limits applied.
- **Kubernetes**: Network policies enforce namespace isolation.
- **CI/CD**: Secrets injected dynamically, never baked into images or printed in CI logs.

## 6. Compliance & Auditing
- **OWASP Top 10**: CI pipeline checks against OWASP standards.
- **GDPR**: Data deletion endpoints, anonymized telemetry.
- **Audit Logging**: TimescaleDB for immutable event logs (Auth events, key usage, billing changes).

## 7. Dependency Security
- Snyk and GitHub Dependabot for automated vulnerability scanning.
- Strict version pinning.
- License compliance checker in pipeline.

## 8. Incident Response Runbooks
- **Credential Compromise**: Force global logout, invalidate all JWTs/sessions, rotate internal API keys.
- **Data Breach**: Isolate affected DB shards, trigger forensic logging, notify stakeholders within 72h.
- **DDoS Attack**: Escalate Cloudflare 'Under Attack' mode, aggressive rate-limit IP subnets.
