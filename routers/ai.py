from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from groq import Groq
import os
import json
from dotenv import load_dotenv
from schemas import ClinicalNoteInput
from models import Patient, Observation, Condition, MedicationRequest
from datetime import datetime

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


@router.post("/extract")
def extract_prescription(input:ClinicalNoteInput, db:Session = Depends(get_db)):
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
def extract_and_save(input:ClinicalNoteInput, db:Session = Depends(get_db)):
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



    
