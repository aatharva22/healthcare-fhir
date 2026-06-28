# Healthcare FHIR API — Implementation Notes (v1)

A complete reference of what was built, how each piece works, and why.

---

## Project Overview

A FHIR R4 and HIPAA-aligned healthcare backend with an AI documentation layer.

**Live URL:** https://healthcare-fhir.onrender.com/docs
**Source:** https://github.com/aatharva22/healthcare-fhir

---

## Architecture at a Glance

```
Client (Swagger UI, curl, or future frontend)
    │
    │ HTTPS request with JWT in Authorization header
    ▼
FastAPI Application
    │
    ├── Audit Middleware (logs every request)
    │
    ├── Routers
    │       ├── auth.py                  → register, login
    │       ├── patient.py               → 6 endpoints + $everything
    │       ├── observation.py           → 5 CRUD endpoints
    │       ├── medication_request.py    → 5 CRUD endpoints
    │       ├── condition.py             → 5 CRUD endpoints
    │       ├── ai.py                    → extract, extract-and-save, summarize
    │       ├── audit_log.py             → admin-only log viewer
    │       └── metadata.py              → FHIR CapabilityStatement
    │
    ├── Dependencies
    │       ├── get_db                   → database session per request
    │       ├── get_current_user         → JWT validation + user lookup
    │       └── require_role             → RBAC enforcement factory
    │
    ▼
SQLAlchemy ORM
    │
    ▼
PostgreSQL (Docker locally, Neon in production)
```

---

## File-by-File Breakdown

### `main.py`
Entry point. Creates the FastAPI app, registers middleware, registers all routers.

```python
app = FastAPI()
app.add_middleware(AuditLogMiddleware)
app.include_router(patient.router)
# ... etc
```

Keeps the file lean by delegating all endpoint logic to router files.

---

### `database.py`
The database connection layer. Contains four critical objects:

- **`engine`** — the SQLAlchemy connection pool to PostgreSQL
- **`SessionLocal`** — a session factory that creates fresh database sessions
- **`Base`** — the parent class all SQLAlchemy models inherit from
- **`get_db()`** — a dependency that yields a session and closes it after the request, even if it crashes (`try/finally` pattern)

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

The `yield + finally` pattern guarantees no connection leaks.

---

### `models.py`
SQLAlchemy models — Python classes that map to PostgreSQL tables.

| Model | Table | Purpose |
|---|---|---|
| `User` | `users` | Stores users with role, hashed password, active flag |
| `Patient` | `patients` | FHIR Patient resource, linked to a User via `user_id` |
| `Observation` | `observations` | Clinical observations (vitals, lab results) |
| `MedicationRequest` | `medication_requests` | Prescriptions |
| `Condition` | `conditions` | Diagnoses with ICD-10 codes |
| `AuditLog` | `audit_logs` | HIPAA audit trail |

Each model:
- Inherits from `Base`
- Defines columns using `Column(Type, ...)` with constraints (`nullable`, `unique`, `default`, `primary_key`)
- Uses `ForeignKey("table.column")` to express relationships (e.g., observations belong to patients)
- Uses `default=lambda: str(uuid.uuid4())` for UUID primary keys (lambda ensures fresh UUID per row, not at module load)

---

### `schemas.py`
Pydantic schemas — validate request bodies and shape response data.

Two schemas per resource:
- **`*Create`** — what the client sends when creating/updating (no `id`)
- **`*Response`** — what the API returns (includes `id`, has `from_attributes = True`)

**Why `from_attributes = True`:**
The response endpoint returns SQLAlchemy objects, not dicts. By default, Pydantic only accepts dicts (`obj["key"]`). Setting `from_attributes = True` tells Pydantic to use attribute access (`obj.key`) — which is how SQLAlchemy objects expose data. This is the bridge between database models and API responses.

It's only needed on `*Response` schemas because requests come in as JSON (already dict-like), but responses receive SQLAlchemy objects.

Special schemas:
- **`PatientEverything`** — bundles a patient + observations + medications + conditions into one FHIR Bundle response for the `$everything` endpoint
- **`Token`** — wraps the JWT in the login response
- **`AuditLogResponse`** — exposes audit log entries to admins

---

### `auth.py`
The authentication engine. Provides:

- **`hash_password(plain)`** — bcrypt-hashes a password for storage
- **`verify_password(plain, hashed)`** — checks a submitted password against a stored hash
- **`create_access_token(data)`** — creates a JWT containing the user's email + expiry
- **`get_current_user(token, db)`** — dependency that validates JWT and returns the User object
- **`require_role(allowed_roles)`** — dependency factory for RBAC; returns a dependency that 403s if the user's role isn't in the allowed list

**The bcrypt password flow:**
- Storage: `hashed_password` column stores the bcrypt hash (one-way; cannot be reversed)
- Login: compare submitted password's hash to stored hash, never the plain text

**The `require_role` pattern:**
```python
def require_role(allowed_roles):
    def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(403)
        return current_user
    return role_checker
```

`require_role` is a function that **returns another function**. The inner function is the actual dependency. This is called a **closure** — the inner function "remembers" `allowed_roles`. This pattern lets you parameterize a dependency, which FastAPI's `Depends` system can't do directly.

---

### `audit.py`
The audit logging middleware. Runs on every request via `BaseHTTPMiddleware`:

```python
class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)   # endpoint runs
        # then log the request: user, method, path, status, IP, timestamp
        return response
```

**Why middleware instead of decorators on each endpoint:**
- One piece of code covers all 23+ endpoints
- Cannot be forgotten on a new endpoint
- Logs even when endpoints crash (still records the failure)
- Cleanly separates concerns: logging logic isn't mixed with business logic

The middleware manually decodes the JWT (since `Depends` isn't available in middleware) and looks up the user. The double decode (middleware + dependency) is intentional — the two layers serve different purposes:
- **Middleware:** observability (record what happened)
- **Dependency:** security (enforce who can do what)

---

### `routers/`
Each file is a self-contained router for one resource:

- **`auth.py`** — `POST /auth/register`, `POST /auth/login`
- **`patient.py`** — full CRUD + `GET /{id}/$everything`
- **`observation.py`** — full CRUD with FHIR search params (`patient_id`, `code`, `status`)
- **`medication_request.py`** — full CRUD with search params
- **`condition.py`** — full CRUD with search params
- **`ai.py`** — three AI endpoints (extract, extract-and-save, summarize)
- **`audit_log.py`** — admin-only `GET /audit/logs`
- **`metadata.py`** — `GET /metadata` (FHIR CapabilityStatement)

Each router uses `prefix` and `tags` so endpoints are scoped and grouped in `/docs`.

**Standard endpoint pattern:**
```python
@router.post("", response_model=ResourceResponse, status_code=201)
def create_resource(
    resource: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    new = Resource(**resource.model_dump())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new
```

**Role rules across all resources:**
| Action | Allowed Roles |
|---|---|
| Create / Update | doctor, admin |
| Delete | admin only |
| Read | any authenticated user (patients only see their own data) |

---

### `create_tables.py`
A one-time script that imports all models and runs `Base.metadata.create_all(bind=engine)`. Creates all tables in PostgreSQL if they don't already exist.

---

### `seed.py`
Loads three demo users (admin, doctor, patient) and a fully populated patient record (Alice) with 6 observations, 3 medications, and 3 conditions for testing the AI summary endpoint.

---

## How the AI Layer Works

### `POST /ai/extract`
Takes a free-text clinical note + patient_id. Calls Llama 3.3 70B via Groq with a heavily engineered system prompt that:
- Defines the role ("clinical data extraction engine")
- Specifies exact JSON output format
- Lists medical abbreviations to expand (QD, BID, HTN, BP, etc.)
- Forbids markdown, backticks, or hallucinations
- Includes one few-shot example

Temperature is `0.1` for deterministic, consistent extraction.

Returns the structured JSON without persisting anything.

### `POST /ai/extract-and-save`
Same as above, but saves each extracted resource (observations, medications, conditions) to PostgreSQL with the correct `patient_id` foreign key. Uses a single `db.commit()` at the end for atomicity — if any save fails, everything rolls back.

### `POST /ai/summarize/{patient_id}`
Reverse direction. Pulls all of a patient's structured data, formats it as a context string, and asks the LLM to generate a professional clinical narrative. Temperature is `0.3` for slightly more natural language.

---

## How JWT Authentication Works (Walkthrough Example)

### Step 1: Dr. Jones Logs In

```
POST /auth/login
username: dr.jones@hospital.com
password: doctor123
```

### Step 2: Server Verifies Credentials

```python
user = db.query(User).filter(User.email == form.username).first()
if not user or not verify_password(form.password, user.hashed_password):
    raise HTTPException(401)
```

`verify_password()` hashes the submitted password with bcrypt and compares it to the stored hash. Passwords are never stored or compared in plain text.

### Step 3: Create a Token

```python
token = create_access_token({"sub": "dr.jones@hospital.com"})
```

Inside `create_access_token`:
- Copy the input dict
- Add expiry: 30 minutes from `datetime.utcnow()`
- Call `jwt.encode(dict_copy, SECRET_KEY, algorithm="HS256")`

The encoder produces three parts joined by dots:

**Part 1 — Header (base64-encoded JSON)**
```json
{"alg":"HS256","typ":"JWT"}
```
Encoded: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9`

**Part 2 — Payload (base64-encoded JSON)**
```json
{"sub":"dr.jones@hospital.com","exp":1781344200}
```
Encoded: `eyJzdWIiOiJkci5qb25lc0Bob3NwaXRhbC5jb20iLCJleHAiOjE3ODEzNDQyMDB9`

**Part 3 — Signature**
HMAC-SHA256 over `header.payload` using `SECRET_KEY`. This is the proof that the token came from our server. Without the SECRET_KEY, this signature cannot be forged.

**Full token:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkci5qb25lc0Bob3NwaXRhbC5jb20iLCJleHAiOjE3ODEzNDQyMDB9.xK9mN2pR7vQ4tY1uI8oP3wE6sD0fH5gA9bC2nM7yV4
```

### Step 4: Server Returns Token

```json
{
  "access_token": "eyJhbGc...xK9mN2pR7vQ4...",
  "token_type": "bearer"
}
```

### Step 5: Client Sends Token With Every Future Request

```
GET /fhir/Patient
Authorization: Bearer eyJhbGc...xK9mN2pR7vQ4...
```

### Step 6: `get_current_user` Validates

```python
def get_current_user(token = Depends(oauth2_scheme), db = Depends(get_db)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    # Validates signature (catches tampering)
    # Validates exp (catches expired tokens)
    
    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise credentials_exception
    return user
```

`jwt.decode()` does three things:
1. Splits the token at the dots
2. Recreates the signature using `SECRET_KEY` and compares with the token's signature → rejects if mismatched
3. Checks `exp` against current UTC time → rejects if expired

If all pass, the payload is returned as a dict. The email is pulled out (`payload.get("sub")`) and the user is loaded from the database.

### Why Look Up the User Every Time?

Even though the token already contains the email, we re-query the database because:
1. The user might have been deactivated since the token was issued
2. The user might have been deleted
3. The user's role might have changed
4. We need the fresh `User` object for the endpoint to use

This is the **stateful** approach to JWT — slower than trusting the token entirely, but safer for healthcare where permissions must reflect current reality.

### Why a Different SECRET_KEY in Production vs Local?

A token signed with the local SECRET_KEY cannot be verified by the production server (different keys → different signatures). This is **good** — it prevents a leaked dev key from compromising production. Tokens are environment-scoped by design.

---

## Database Schema Reference

### `users`
| Column | Type | Notes |
|---|---|---|
| `id` | String | UUID primary key |
| `email` | String | Unique, indexed |
| `hashed_password` | String | bcrypt hash |
| `role` | String | "admin", "doctor", or "patient" |
| `full_name` | String | Nullable |
| `is_active` | Boolean | Default true |
| `created_at` | DateTime | Server default `now()` |

### `patients`
| Column | Type | Notes |
|---|---|---|
| `id` | String | UUID primary key |
| `user_id` | String | FK to `users.id`, nullable |
| `family_name` | String | Required |
| `given_name` | String | Required |
| `gender`, `birth_date`, `active` | varies | Optional |

### `observations`, `medication_requests`, `conditions`
All have:
- `id` UUID PK
- `patient_id` FK to `patients.id`
- Resource-specific columns
- Default `status` or `clinical_status` of "final" or "active"

### `audit_logs`
| Column | Type |
|---|---|
| `id` | String UUID |
| `user_email` | String, nullable |
| `user_role` | String, nullable |
| `action` | String (READ/CREATE/UPDATE/DELETE) |
| `method` | String (HTTP method) |
| `path` | String |
| `status_code` | Integer |
| `ip_address` | String |
| `timestamp` | DateTime |

---

## Deployment Architecture

**Local Development:**
- PostgreSQL runs in Docker via `docker-compose.yml`
- App runs in Docker too (Dockerfile builds the image)
- One command starts everything: `docker compose up`

**Production:**
- App deployed on Render (free tier; sleeps after 15 min)
- Database hosted on Neon (managed Postgres, free tier)
- Environment variables managed via Render's UI:
  - `DATABASE_URL` → Neon connection string
  - `SECRET_KEY` → unique production secret
  - `GROQ_API_KEY` → Llama API key

---

## Security Model Summary

| Layer | Mechanism |
|---|---|
| Password storage | bcrypt hashing, 72-byte truncation handled |
| Authentication | JWT with 30-minute expiry, HS256 signed |
| Authorization | RBAC via `require_role` dependency factory |
| Patient data access | Ownership filtering by `user_id` |
| PHI audit trail | Middleware logs every request with user identity |
| Secrets | `.env` gitignored, separate dev/prod keys |
| Transport | HTTPS in production (via Render) |

---

## Open Questions / Future Work (v2 Ideas)

- **Frontend dashboard** — React/Next.js UI for doctors and patients
- **SMART on FHIR** — proper OAuth 2.0 flow for patient-facing apps
- **HL7 v2 to FHIR conversion** — bridge for legacy hospital systems
- **Streaming AI responses** — Server-Sent Events for faster perceived latency
- **Database migrations** — Alembic instead of `drop + create`
- **Test suite** — Pytest covering happy paths, auth, RBAC, AI
- **Real medical code validation** — check ICD-10 / LOINC / RxNorm against canonical sets
- **Rate limiting on AI endpoints** — prevent LLM cost abuse
- **Structured logging + metrics** — `structlog`, Prometheus

---

## Test Credentials (Pre-Seeded on Live Demo)

| Role | Email | Password |
|---|---|---|
| Admin | admin@hospital.com | admin123 |
| Doctor | dr.jones@hospital.com | doctor123 |
| Patient | alice@email.com | patient123 |

Alice has a pre-loaded patient record with hypertension, type 2 diabetes, and hyperlipidemia — six observations, three medications, three conditions. Ideal for testing the AI summary endpoint.

---

## Final State of v1

- 23 FHIR endpoints across 4 resources
- AI extraction and AI summarization
- JWT authentication with RBAC across 3 roles
- HIPAA-aligned audit logging via middleware
- Docker Compose for local dev
- Deployed to Render with Neon Postgres
- Live demo with pre-seeded test data
- Screenshots and README documentation

**Total commits:** ~15
**Total lines of code:** ~1,500
**Time invested:** ~3 weeks part-time