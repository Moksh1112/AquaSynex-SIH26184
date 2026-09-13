# Backend Progress

## Status
IN PROGRESS

## Completed
- [x] Repository inspection
- [x] Configuration
- [x] Database connection
- [x] Database models
- [x] Seed data
- [x] Case APIs
- [x] Prediction service
- [x] Prediction API
- [x] Prediction persistence
- [x] Alerts
- [x] Authentication
- [x] RBAC
- [x] Audit logging
- [x] Tests
- [ ] Integration validation

## Current Task
Completed Phase H (Audit Logging & Security Hardening). Ready for Phase I.

## Phase H Summary (Audit Logging)
* **AuditService:** Implemented `audit_service.py` to abstract logging logic, ensuring database connection issues do not propagate and crash core business functions.
* **Audit Repository & Schemas:** Added `crud_audit.py` and `schemas/audit.py` using the existing `AuditLog` model.
* **Audited Actions:** 
  * Login (SUCCESS/FAILED)
  * Case Access (`/cases`, `/cases/{id}`)
  * Alert Access (`/alerts`, `/alerts/{id}`)
  * Alert Status Update (SUCCESS/FAILED)
  * Prediction Generation (SUCCESS/FAILED)
  * Access Denied (RBAC rejections)
* **Security Hardening:** Ensured passwords, password hashes, and JWT tokens are NEVER logged. Captured `user_id` where applicable or used resource descriptions for failed logins.
* **Audit Retrieval:** Added `GET /audit` endpoint restricted to `Administrator`.
* **Testing:** Added comprehensive API tests covering audit scenarios. Total tests: 45 passed, 4 skipped, 0 failed.

## Phase G Summary
* Implemented `POST /auth/login` endpoint with JWT Bearer token authentication.
* Password hashing uses `passlib` (bcrypt scheme) with `bcrypt<4.1` pinned for compatibility.
* JWT tokens carry `sub` (username) and `role` claims. Sensitive data is excluded from tokens.
* `JWT_SECRET` is read from the existing `Settings` configuration (not hardcoded).
* Created reusable `get_current_user` and `require_role(*roles)` dependencies in `deps.py`.
* Protected all business endpoints (`/cases`, `/predict`, `/alerts`) with authentication.
* RBAC policy: All roles can read cases, use predictions, and read alerts. Only Admin and LEA Investigator can mutate alert status. I4C Analyst and Bank Officer are denied alert mutation (403).
* `GET /health` and `POST /auth/login` remain public.
* Unauthenticated requests return 401. Unauthorized role returns 403.
* Frozen `POST /predict` contract is unchanged — authentication is injected as a dependency, not modifying the request/response payload.

## Roles (from existing User model)
| Role | Value | Cases | Predict | Alerts Read | Alert Mutate | Audit |
|---|---|---|---|---|---|---|
| ADMIN | Administrator | ✓ | ✓ | ✓ | ✓ | ✓ |
| LEA_INVESTIGATOR | LEA Investigator | ✓ | ✓ | ✓ | ✓ | ✗ (403) |
| I4C_ANALYST | I4C Analyst | ✓ | ✓ | ✓ | ✗ (403) | ✗ (403) |
| BANK_OFFICER | Bank Officer | ✓ | ✓ | ✓ | ✗ (403) | ✗ (403) |

## Files Changed (Phase H)
- `backend/app/schemas/audit.py` (Created Audit schemas)
- `backend/app/crud/crud_audit.py` (Audit repository)
- `backend/app/services/audit_service.py` (Audit service with exception catching)
- `backend/app/api/routes/audit.py` (Added `GET /audit` endpoint for Admin)
- `backend/app/api/deps.py` (Added audit logging to `require_role` for RBAC denials)
- `backend/app/api/routes/auth.py` (Audit logging for login SUCCESS/FAILED)
- `backend/app/api/routes/cases.py` (Audit logging for case READ)
- `backend/app/api/routes/predictions.py` (Audit logging for PREDICT SUCCESS/FAILED)
- `backend/app/api/routes/alerts.py` (Audit logging for alert READ and UPDATE_STATUS)
- `backend/tests/test_audit_api.py` (Comprehensive API tests for auditing)

## Tests
- `python -m pytest tests/ -v` passed (45 Passed, 4 Skipped).
- Auth tests, JWT tests, Protected endpoints, RBAC tests.
- Audit tests: successful login, failed login (password not leaked), case/alert/prediction access logging, RBAC denial logging, audit retrieval access restrictions.
- All Phase D, E, F, G tests continue passing.
- DB-dependent integration tests are explicitly skipped.

## Blockers
- **Docker/Postgres unavailable**: Integration tests remain blocked.

## Next Task
Phase I.
