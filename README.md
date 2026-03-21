# CA Firm Management App (MVP)

A simple FastAPI + SQLite application for chartered accountancy firms to manage:

- Client master data.
- Assignment planning (due dates, ownership, progress).
- Billing and payment status.
- Reminder scheduling.
- Excel bulk upload with preview, validation, duplicate checks, error reporting, and audit logs.

---

## 1) Feature Architecture

### A. Core Modules

1. **Identity & Users**
   - Roles: `admin`, `partner`, `manager`, `staff`.
   - Admin can provision users.

2. **Client Master**
   - Stores client code, legal identity, PAN/GSTIN, contact details, status, ownership (partner/manager).

3. **Assignment Tracker**
   - Tracks deliverables such as GST return, TDS filing, ITR, audit.
   - Captures period, due date, responsible person, progress %, and assignment status.

4. **Billing & Collections**
   - Links invoices to clients (and optionally to assignments).
   - Tracks gross, tax, paid amount, and payment status (`unpaid`, `partial`, `paid`).

5. **Reminders**
   - Schedules reminders by channel (`email`, `sms`, `whatsapp`, `call`).
   - Supports assignment-level due reminders and general client reminders.

6. **Bulk Upload Engine**
   - Accepts `.xlsx` template with strict headers.
   - Performs field-level validation, duplicate detection (within file + database), and row-level preview before commit.

7. **Audit Trail**
   - Logs critical create/update/upload actions with actor and payload summary.

### B. Technical Architecture (MVP)

- **API Layer**: FastAPI endpoints for all modules.
- **Validation Layer**: Pydantic + custom regex/domain checks.
- **Persistence**: SQLAlchemy ORM over SQLite.
- **Ingestion Layer**: `openpyxl` parser for Excel preview/commit flow.
- **Observability**: `audit_logs` and `upload_errors` tables.

---

## 2) Database Schema

### Primary Entities

- `users`
- `clients`
- `assignments`
- `billing_records`
- `reminders`
- `upload_sessions`
- `upload_errors`
- `audit_logs`

### Entity Relationships

- `clients (1) -> (N) assignments`
- `clients (1) -> (N) billing_records`
- `clients (1) -> (N) reminders`
- `upload_sessions (1) -> (N) upload_errors`

### Design Notes

- Unique keys: `clients.client_code`, `clients.pan`, `billing_records.invoice_number`.
- Upload staging: valid rows stored on `upload_sessions.staged_valid_rows` (JSON) for two-step preview/commit.
- Audit captures entity, action, actor, timestamp, and details.

---

## 3) Excel Bulk Upload Workflow

### Template Headers (strict order)

```text
client_code, client_name, entity_type, pan, gstin, email, phone, assigned_partner, assigned_manager, status
```

### Step-by-Step

1. **Upload Preview** (`POST /bulk-upload/preview`)
   - Validates file extension (`.xlsx`), readability, and header template.
   - Validates each row:
     - Required fields.
     - PAN / phone / GSTIN format.
     - Status value (`active`/`inactive`).
     - Duplicate in-file (`client_code`, `pan`).
     - Duplicate in database (`client_code`, `pan`).
   - Writes granular issues into `upload_errors`.
   - Returns summary and row-level preview.

2. **User Review**
   - Client can inspect valid and invalid rows from preview response.
   - Invalid rows can be corrected in source and reuploaded.

3. **Commit Upload** (`POST /bulk-upload/commit/{session_id}`)
   - Inserts only staged valid rows.
   - Re-checks duplicates before final insert to handle concurrent data changes.
   - Marks session as committed and logs inserted/skipped counts.

---

## 4) Business Workflows

### A. Client Onboarding

1. Create client manually (`POST /clients`) or via bulk upload preview+commit.
2. Assign partner and manager ownership.
3. Verify client appears in `GET /clients`.

### B. Assignment Lifecycle

1. Create assignment with due date and responsibility (`POST /assignments`).
2. Track progress (`PATCH /assignments/{id}/progress`).
3. List upcoming deliverables (`GET /dashboard/upcoming-dues`).

### C. Billing Lifecycle

1. Create invoice (`POST /billing`).
2. Track payment status (`unpaid`, `partial`, `paid`) by paid amount.

### D. Reminder Lifecycle

1. Add reminder for due tasks (`POST /reminders`).
2. Use date + channel for operational follow-up.

### E. Compliance & Accountability

- Every critical mutation records audit events (`GET /audit-logs`).

---

## 5) API Endpoints (MVP)

- `POST /users`
- `POST /clients`
- `GET /clients`
- `POST /assignments`
- `PATCH /assignments/{assignment_id}/progress`
- `POST /billing`
- `POST /reminders`
- `GET /dashboard/upcoming-dues`
- `POST /bulk-upload/preview`
- `POST /bulk-upload/commit/{session_id}`
- `GET /audit-logs`

---

## 6) MVP Implementation Plan

### Phase 1 (Week 1) — Foundation

- Bootstrap FastAPI app, ORM models, migrations strategy.
- Seed admin user and role policy.
- Implement client + assignment + billing + reminder CRUD.

### Phase 2 (Week 2) — Bulk Upload

- Add Excel template contract.
- Implement preview parser and validation engine.
- Implement row-level error capture + upload sessions.
- Add commit step with duplicate recheck.

### Phase 3 (Week 3) — Operations & Governance

- Add upcoming-due dashboard endpoint.
- Add full audit logging coverage.
- Add basic smoke tests and API examples.

### Phase 4 (Post-MVP)

- Replace SQLite with PostgreSQL.
- Add authentication (JWT/SSO) and row-level permissions.
- Add scheduler for auto reminder dispatch (email/WhatsApp/SMS integrations).
- Add analytics dashboards (team workload, aging receivables, SLA adherence).

---

## 7) Run Locally

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

Open API docs: `http://127.0.0.1:8000/docs`
