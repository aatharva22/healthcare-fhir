from fastapi import FastAPI
from routers import patient, observation

app = FastAPI()
app.include_router(patient.router)
app.include_router(observation.router)

@app.get("/")
def hello_world():
    return {"messgae":"Hello World!"}

