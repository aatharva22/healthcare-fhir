"""
Seed script for the Healthcare FHIR API.
Creates demo users + a fully-loaded patient record for testing.
Run with: python seed.py
"""

from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Patient, Observation, MedicationRequest, Condition
from auth import hash_password
from datetime import datetime, date

def seed():
    db: Session = SessionLocal()
    
    try:
        # ─── 1. Users ──────────────────────────────────────────────
        users = [
            {"email": "admin@hospital.com", "password": "admin123", "full_name": "Admin User", "role": "admin"},
            {"email": "dr.jones@hospital.com", "password": "doctor123", "full_name": "Dr. Jones", "role": "doctor"},
            {"email": "alice@email.com", "password": "patient123", "full_name": "Alice Smith", "role": "patient"},
        ]
        
        created_users = {}
        for u in users:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if existing:
                print(f"User exists: {u['email']}")
                created_users[u["role"]] = existing
                continue
            user = User(
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                full_name=u["full_name"],
                role=u["role"]
            )
            db.add(user)
            db.flush()
            created_users[u["role"]] = user
            print(f"Created user: {u['email']}")
        
        alice_user = created_users["patient"]
        
        # ─── 2. Alice's Patient Record ─────────────────────────────
        alice_patient = db.query(Patient).filter(Patient.user_id == alice_user.id).first()
        if not alice_patient:
            alice_patient = Patient(
                user_id=alice_user.id,
                family_name="Smith",
                given_name="Alice",
                gender="female",
                birth_date=date(1985, 4, 12),
                active=True
            )
            db.add(alice_patient)
            db.flush()
            print(f"Created patient record for Alice: {alice_patient.id}")
        else:
            print(f"Alice's patient record exists: {alice_patient.id}")
        
        # Clear existing clinical data for Alice (for clean reseeds)
        db.query(Observation).filter(Observation.patient_id == alice_patient.id).delete()
        db.query(MedicationRequest).filter(MedicationRequest.patient_id == alice_patient.id).delete()
        db.query(Condition).filter(Condition.patient_id == alice_patient.id).delete()
        
        # ─── 3. Observations ───────────────────────────────────────
        observations = [
            {"code": "blood-pressure", "value": "140/90", "unit": "mmHg", "status": "final"},
            {"code": "heart-rate", "value": "78", "unit": "bpm", "status": "final"},
            {"code": "blood-glucose", "value": "165", "unit": "mg/dL", "status": "final"},
            {"code": "body-weight", "value": "72", "unit": "kg", "status": "final"},
            {"code": "hba1c", "value": "7.2", "unit": "%", "status": "final"},
            {"code": "ldl-cholesterol", "value": "145", "unit": "mg/dL", "status": "final"},
        ]
        for o in observations:
            db.add(Observation(
                patient_id=alice_patient.id,
                code=o["code"],
                value=o["value"],
                unit=o["unit"],
                status=o["status"],
                effective_date=datetime.utcnow()
            ))
        print(f"Created {len(observations)} observations")
        
        # ─── 4. Medications ────────────────────────────────────────
        medications = [
            {"medication_name": "Lisinopril", "dosage": "10mg", "frequency": "once daily", "notes": "For hypertension management"},
            {"medication_name": "Metformin", "dosage": "500mg", "frequency": "twice daily", "notes": "For type 2 diabetes, take with meals"},
            {"medication_name": "Atorvastatin", "dosage": "20mg", "frequency": "once daily at bedtime", "notes": "For high cholesterol"},
        ]
        for m in medications:
            db.add(MedicationRequest(
                patient_id=alice_patient.id,
                medication_name=m["medication_name"],
                dosage=m["dosage"],
                frequency=m["frequency"],
                status="active",
                prescribed_date=datetime.utcnow(),
                notes=m["notes"]
            ))
        print(f"Created {len(medications)} medications")
        
        # ─── 5. Conditions ─────────────────────────────────────────
        conditions = [
            {"code": "I10", "description": "Essential hypertension", "notes": "Diagnosed during annual checkup, well-controlled on medication"},
            {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications", "notes": "Recently diagnosed, A1c trending down"},
            {"code": "E78.5", "description": "Hyperlipidemia, unspecified", "notes": "Started statin therapy"},
        ]
        for c in conditions:
            db.add(Condition(
                patient_id=alice_patient.id,
                code=c["code"],
                description=c["description"],
                clinical_status="active",
                onset_date=datetime.utcnow(),
                notes=c["notes"]
            ))
        print(f"Created {len(conditions)} conditions")
        
        # ─── Commit ────────────────────────────────────────────────
        db.commit()
        
        print("\n" + "=" * 60)
        print("SEED COMPLETE")
        print("=" * 60)
        print(f"Alice's Patient ID: {alice_patient.id}")
        print("\nTest Credentials:")
        print("  Admin   : admin@hospital.com / admin123")
        print("  Doctor  : dr.jones@hospital.com / doctor123")
        print("  Patient : alice@email.com / patient123")
        print("=" * 60)
    
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    