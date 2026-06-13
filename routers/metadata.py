from fastapi import APIRouter, Depends
from models import User
from auth import get_current_user


router = APIRouter(tags = ["Metadata"])
@router.get("/metadata")
def get_capability_statement(current_user:User = Depends(get_current_user)):
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2026-06-08",
        "kind": "instance",
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": "Patient",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"}
                        ]
                    },
                    {
                        "type": "Observation",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"}
                        ]
                    },
                    {
                        "type": "MedicationRequest",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"}
                        ]
                    },
                    {
                        "type": "Condition",
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                            {"code": "search-type"}
                        ]
                    }
                ]
            }
        ]
    }