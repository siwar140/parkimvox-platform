from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import ensure_indexes
from app.routers import auth, patients, doctors, messages

app = FastAPI(
    title="ParkImVox Platform API",
    description="Plateforme de suivi Parkinson : prédiction vocale, dossiers patients, messagerie médecin-patient.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(doctors.router)
app.include_router(messages.router)


@app.on_event("startup")
async def startup_event():
    await ensure_indexes()


@app.get("/")
async def root():
    return {"status": "ok", "message": "ParkImVox Platform API en ligne"}
