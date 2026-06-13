# Healthcare FHIR API

A production-grade, FHIR-compliant patient data API built with FastAPI and PostgreSQL. 
Designed to mirror the architecture used by real healthcare systems, the API implements 
the HL7 FHIR R4 standard for storing and exchanging clinical data across four core 
resources: Patient, Observation, MedicationRequest, and Condition.

The project includes an AI layer powered by Llama 3.3 70B (via Groq) that extracts 
structured FHIR resources from free-text clinical notes and generates concise patient 
summaries — addressing one of the biggest operational pain points in modern healthcare: 
clinical documentation burden.

Built as a portfolio project to demonstrate real-world healthcare engineering skills 
including FHIR compliance, medical data modeling, LLM integration, and production-style 
API design.

## Why I Built This

Physicians in the US spend an average of two hours on documentation for every one hour of direct patient care. This administrative burden is consistently ranked as one of the top causes of clinician burnout and contributes to billions of dollars in wasted healthcare spending annually.

This project explores how modern AI can offload that work. The same Llama 3.3 70B model that extracts FHIR resources from a free-text note in this API is the same class of model that companies like Abridge, Nuance DAX, and Suki use to power their clinical assistants.

The goal: build a system where a physician can type a few sentences after an appointment and have the API automatically:

- Extract observations (vitals, lab results)
- Generate prescriptions (with dosage and frequency)
- Record diagnoses (with appropriate ICD-10 codes)
- Save everything to the patient record in FHIR R4 format

…and then, on demand, generate a clinical summary of the patient's full history in seconds.

This API is the backend that could power exactly that workflow.

## Try It Live

**Live API**: [https://healthcare-fhir.onrender.com/docs#/default](https://healthcare-fhir.onrender.com/docs#/default)

> Free tier server sleeps after 15 minutes of inactivity. First request may take ~50 seconds to wake up.

### Pre-Seeded Test Credentials

Click the **Authorize** button in the Swagger UI and log in with any of the accounts below.

| Role | Email | Password |
|---|---|---|
| Admin | `admin@hospital.com` | `admin123` |
| Doctor | `dr.jones@hospital.com` | `doctor123` |
| Patient | `alice@email.com` | `patient123` |

### What Each Role Can Do

- **Admin** — full access including audit logs and deletes
- **Doctor** — create, read, update all patient data; cannot delete (admin only)
- **Patient** — read-only access to their own records only

### Sample Patient Record

A pre-seeded patient (Alice Smith) is linked to the patient role above. Use this UUID to test resource-specific endpoints:

### Suggested Test Flow

1. Log in as a **doctor**
2. Hit `GET /fhir/Patient` — see all patients
3. Hit `GET /fhir/Patient/{id}/$everything` with Alice's UUID — see her complete clinical picture
4. Try `POST /ai/extract-and-save` with a clinical note (sample below) — watch the AI extract structured data
5. Log out, log in as the **patient** — try the same endpoints to see RBAC in action (only Alice's data visible)
6. Log in as **admin** — view `/audit/logs` to see every action that's been recorded

### Sample Clinical Note for AI Extraction

```json
{
  "patient_id": "0ba30031-df24-4e46-84ca-14b35a9e4b1c",
  "note": "Patient presents with BP 140/90, complaining of headache for 3 days. History of hypertension. Started on lisinopril 10mg daily. Follow up in 2 weeks."
}
```

The AI will extract this into a FHIR Observation (blood pressure), MedicationRequest (lisinopril prescription), and Condition (hypertension with ICD-10 code I10).

## Key Features

- 20 FHIR-compliant CRUD endpoints across 4 clinical resources
- AI-powered clinical note extraction — converts free-text physician notes into 
  structured FHIR resources using Llama 3.3 70B
- AI patient summarization — generates professional clinical summaries from patient data
- FHIR $everything operation — returns complete patient clinical picture in one request
- CapabilityStatement at /metadata — standard FHIR server discovery endpoint
- FHIR-style search parameters on all list endpoints
- PostgreSQL persistence via SQLAlchemy ORM
- Pydantic v2 validation on all request and response models
- Dockerized PostgreSQL for consistent local development

## Tech Stack

- FastAPI
- SQLAlchemy + PostgreSQL (Docker)
- Pydantic v2
- Groq API (Llama 3.3 70B)
- python-dotenv
- Docker
- JWT


