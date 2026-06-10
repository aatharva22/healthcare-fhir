from fastapi import FastAPI
from routers import patient, observation, medication_request, condition, metadata, ai

app = FastAPI()
app.include_router(patient.router)
app.include_router(observation.router)
app.include_router(medication_request.router)
app.include_router(condition.router)
app.include_router(metadata.router)
app.include_router(ai.router)


@app.get("/")
def hello_world():
    return {"messgae":"Hello World!"}

