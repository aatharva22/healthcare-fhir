from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from groq import Groq
import os
import json
from dotenv import load_dotenv
from schemas import ClinicalNoteInput
from models import Patient, Observation, Condition, MedicationRequest, User
from datetime import datetime
from auth import get_current_user, require_role


load_dotenv()

router = APIRouter(prefix="/ai", tags=["AI"])
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are a clinical data extraction engine used in a FHIR-compliant healthcare API.
Extract structured medical data from physician notes.

RULES:
- Return ONLY valid JSON. No explanation, no markdown, no backticks.
- Never invent data not present in the note.
- If a category has no data, return an empty array [].
- Expand abbreviations: QD=once daily, BID=twice daily, TID=three times daily, HTN=hypertension, BP=blood pressure, DM=diabetes mellitus.

OUTPUT FORMAT:
{
  "observations": [
    {"code": "string", "value": "string", "unit": "string or null", "status": "final"}
  ],
  "medications": [
    {"medication_name": "string", "dosage": "string", "frequency": "string", "status": "active", "notes": "string or null"}
  ],
  "conditions": [
    {"code": "string", "description": "string", "clinical_status": "active", "notes": "string or null"}
  ]
}

EXAMPLE:
Input: "Pt BP 140/90, started lisinopril 10mg QD, dx HTN"
Output:
{
  "observations": [{"code": "blood-pressure", "value": "140/90", "unit": "mmHg", "status": "final"}],
  "medications": [{"medication_name": "Lisinopril", "dosage": "10mg", "frequency": "once daily", "status": "active", "notes": null}],
  "conditions": [{"code": "I10", "description": "Essential hypertension", "clinical_status": "active", "notes": null}]
}
"""
SUMMARY_PROMPT = """
You are a clinical summarization assistant for a FHIR-compliant healthcare API.
Write a concise, professional clinical summary based on structured patient data.

RULES:
- Return plain text only. No JSON, no markdown, no bullet points.
- Never invent data not present in the input.
- If a category has no data, skip that section entirely.
- Keep it to 2-3 paragraphs maximum.
- Write in third person (e.g. "The patient presents with...")
- Use professional but accessible clinical language.

STRUCTURE:
Paragraph 1: Patient demographics and active conditions.
Paragraph 2: Current medications and recent observations/vitals.
Paragraph 3: Any notable concerns, flags, or follow-up recommendations.
"""

@router.post("/extract")
def extract_prescription(input:ClinicalNoteInput, db:Session = Depends(get_db), current_user:User = Depends(require_role(["doctor", "admin"]))):
    patient = db.query(Patient).filter(Patient.id == input.patient_id ).first()
    if patient is None:
        raise HTTPException(status_code = 404, detail = f"No patient found with given id {input.id} assosiated with the input")
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract FHIR resources from this note: {input.note}"}
        ],
        temperature=0.1
    )

    raw = response.choices[0].message.content
    
    try:
        extracted = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="AI returned invalid JSON. Try again."
        )

    return {
        "patient_id": input.patient_id,
        "extracted": extracted
    }



@router.post("/extract-and-save")
def extract_and_save(input:ClinicalNoteInput, db:Session = Depends(get_db), current_user:User = Depends(require_role(["doctor", "admin"]))):
    patient = db.query(Patient).filter(Patient.id == input.patient_id ).first()
    if patient is None:
        raise HTTPException(status_code = 404, detail = f"No patient found with given id {input.id} assosiated with the input")
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract FHIR resources from this note: {input.note}"}
        ],
        temperature=0.1
    )

    raw = response.choices[0].message.content
    
    try:
        extracted = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="AI returned invalid JSON. Try again."
        )
    
    observations = []

    for obs in extracted.get("observations",[]):
        obs["patient_id"] = input.patient_id
        obs["effective_date"] = datetime.now()
        new_obs = Observation(** obs)
        db.add(new_obs)
        observations.append(new_obs)
    
    medications = []

    for med in extracted.get("medications",[]):
        med["patient_id"] = input.patient_id
        med["prescribed_date"] = datetime.now()
        new_med = MedicationRequest(** med)
        db.add(new_med)
        medications.append(new_med)
    
    conditions = []

    for con in extracted.get("conditions",[]):
        con["patient_id"] = input.patient_id
        con["onset_date"] = datetime.now()
        new_con = Condition(** con)
        db.add(new_con)
        conditions.append(new_con)
    
    db.commit()

    for con in conditions:
        db.refresh(con)
    for med in medications:
        db.refresh(med)
    for  obs in observations:
        db.refresh(obs)

    return {
    "patient_id": input.patient_id,
    "saved": {
        "observations_count": len(observations),
        "medications_count": len(medications),
        "conditions_count": len(conditions),
        "observation_ids": [o.id for o in observations],
        "medication_ids": [m.id for m in medications],
        "condition_ids": [c.id for c in conditions]
    }
}

@router.post("/ai/summarize/{patient_id}")
def summarize(patient_id:str, db:Session = Depends(get_db), current_User:User = Depends(require_role(["doctor", "admin"]))):
    patient = db.query(Patient).filter(Patient.id == patient_id ).first()
    if patient is None:
        raise HTTPException(status_code = 404, detail = f"No patient found with given id {patient_id} ")
    medications = db.query(MedicationRequest).filter(patient_id == MedicationRequest.patient_id).all()
    conditions = db.query(Condition).filter(patient_id == Condition.patient_id).all()
    observations = db.query(Observation).filter(patient_id == Observation.patient_id).all()

    context = f"""
    Patient: {patient.family_name}, {patient.given_name}
    Date of Birth: {patient.birth_date}
    Gender: {patient.gender}

    Active Conditions:
    {chr(10).join([f"- {c.description} ({c.code})" for c in conditions]) or "None recorded"}

    Current Medications:
    {chr(10).join([f"- {m.medication_name} {m.dosage} {m.frequency}" for m in medications]) or "None recorded"}

    Recent Observations:
    {chr(10).join([f"- {o.code}: {o.value} {o.unit or ''}" for o in observations]) or "None recorded"}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": f"Summarize this patient's clinical data:\n{context}"}
        ],
        temperature=0.3
    )

    summary = response.choices[0].message.content

    return {
        "patient_id": patient_id,
        "patient_name": f"{patient.given_name} {patient.family_name}",
        "summary": summary
    }


    
