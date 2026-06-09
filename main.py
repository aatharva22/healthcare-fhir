from fastapi import FastAPI
from routers import patient, observation, medication_request, condition

app = FastAPI()
app.include_router(patient.router)
app.include_router(observation.router)
app.include_router(medication_request.router)
app.include_router(condition.router)

@app.get("/")
def hello_world():
    return {"messgae":"Hello World!"}

