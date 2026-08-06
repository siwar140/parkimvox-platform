from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from app.database import (
    patient_profiles_collection,
    doctor_profiles_collection,
    users_collection,
    consultations_collection,
)
from app.models.schemas import PatientProfileOut, ConsultationOut, AssignDoctor
from app.security import get_current_user, require_role

router = APIRouter(prefix="/patients", tags=["Patients"])


async def _build_patient_profile_out(profile: dict, user: dict) -> PatientProfileOut:
    doctor_name = None
    if profile.get("doctor_id"):
        doctor_user = await users_collection.find_one({"_id": profile["doctor_id"]})
        if doctor_user:
            doctor_name = doctor_user["full_name"]

    return PatientProfileOut(
        id=str(profile["_id"]),
        user_id=str(user["_id"]),
        username=user["username"],
        full_name=user["full_name"],
        age=profile.get("age"),
        sexe=profile.get("sexe"),
        telephone=profile.get("telephone"),
        doctor_id=str(profile["doctor_id"]) if profile.get("doctor_id") else None,
        doctor_name=doctor_name,
    )


@router.get("/me", response_model=PatientProfileOut)
async def get_my_profile(current_user: dict = Depends(require_role("patient"))):
    profile = await patient_profiles_collection.find_one({"user_id": current_user["_id"]})
    if not profile:
        raise HTTPException(status_code=404, detail="Profil patient introuvable")
    return await _build_patient_profile_out(profile, current_user)


@router.put("/me/doctor", response_model=PatientProfileOut)
async def assign_my_doctor(payload: AssignDoctor, current_user: dict = Depends(require_role("patient"))):
    doctor_user = await users_collection.find_one({"username": payload.doctor_username, "role": "doctor"})
    if not doctor_user:
        raise HTTPException(status_code=404, detail="Médecin introuvable")

    await patient_profiles_collection.update_one(
        {"user_id": current_user["_id"]},
        {"$set": {"doctor_id": doctor_user["_id"]}},
    )
    profile = await patient_profiles_collection.find_one({"user_id": current_user["_id"]})
    return await _build_patient_profile_out(profile, current_user)


@router.get("/me/consultations", response_model=list[ConsultationOut])
async def get_my_consultations(current_user: dict = Depends(require_role("patient"))):
    cursor = consultations_collection.find({"patient_id": current_user["_id"]}).sort("date", -1)
    results = []
    async for c in cursor:
        results.append(ConsultationOut(
            id=str(c["_id"]),
            patient_id=str(c["patient_id"]),
            doctor_id=str(c["doctor_id"]),
            date=c["date"],
            prediction_percentage=c.get("prediction_percentage"),
            prediction_label=c.get("prediction_label"),
            threshold_used=c.get("threshold_used"),
            doctor_remarks=c.get("doctor_remarks"),
            audio_filename=c.get("audio_filename"),
        ))
    return results
