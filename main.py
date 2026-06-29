from fastapi import FastAPI
from audit import AuditLogMiddleware
from routers import patient, observation, medication_request, condition, metadata, ai, auth, audit_log
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://lumen-emr.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(AuditLogMiddleware)


app.include_router(audit_log.router)
app.include_router(patient.router)
app.include_router(observation.router)
app.include_router(medication_request.router)
app.include_router(condition.router)
app.include_router(metadata.router)
app.include_router(ai.router)
app.include_router(auth.router)


@app.get("/")
def hello_world():
    return {"messgae":"Hello World!"}

