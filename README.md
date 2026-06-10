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

## Status

In progress — JWT authentication, 
role-based access control, HIPAA audit logging, Docker Compose, and AWS deployment.
