import os
import shutil
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from bson import ObjectId

from app.database import (
    doctor_profiles_collection,
    patient_profiles_collection,
    users_collection,
    consultations_collection,
)
from app.models.schemas import DoctorProfileOut, PatientProfileOut, ConsultationOut, RemarksUpdate
from app.security import get_current_user, require_role
from app.ml.inference import predict_from_audio

router = APIRouter(prefix="/doctors", tags=["Médecins"])

UPLOAD_DIR = "uploaded_audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/me", response_model=DoctorProfileOut)
async def get_my_profile(current_user: dict = Depends(require_role("doctor"))):
    profile = await doctor_profiles_collection.find_one({"user_id": current_user["_id"]})
    if not profile:
        raise HTTPException(status_code=404, detail="Profil médecin introuvable")
    return DoctorProfileOut(
        id=str(profile["_id"]),
        user_id=str(current_user["_id"]),
        username=current_user["username"],
        full_name=current_user["full_name"],
        specialite=profile.get("specialite"),
        hopital=profile.get("hopital"),
    )


@router.get("/me/patients", response_model=list[PatientProfileOut])
async def list_my_patients(current_user: dict = Depends(require_role("doctor"))):
    cursor = patient_profiles_collection.find({"doctor_id": current_user["_id"]})
    results = []
    async for profile in cursor:
        patient_user = await users_collection.find_one({"_id": profile["user_id"]})
        if not patient_user:
            continue
        results.append(PatientProfileOut(
            id=str(profile["_id"]),
            user_id=str(patient_user["_id"]),
            username=patient_user["username"],
            full_name=patient_user["full_name"],
            age=profile.get("age"),
            sexe=profile.get("sexe"),
            telephone=profile.get("telephone"),
            doctor_id=str(current_user["_id"]),
            doctor_name=current_user["full_name"],
        ))
    return results


@router.get("/patients/{patient_id}/consultations", response_model=list[ConsultationOut])
async def get_patient_consultations(patient_id: str, current_user: dict = Depends(require_role("doctor"))):
    cursor = consultations_collection.find(
        {"patient_id": ObjectId(patient_id), "doctor_id": current_user["_id"]}
    ).sort("date", -1)
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


@router.post("/patients/{patient_id}/consultations", response_model=ConsultationOut)
async def create_consultation(
    patient_id: str,
    audio_file: UploadFile = File(...),
    current_user: dict = Depends(require_role("doctor")),
):
    """Le médecin envoie un enregistrement audio du patient -> le modèle prédit le % de la maladie."""
    profile = await patient_profiles_collection.find_one({"user_id": ObjectId(patient_id)})
    if not profile or profile.get("doctor_id") != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Ce patient ne vous est pas assigné")

    # Sauvegarde temporaire du fichier audio pour l'inférence
    filename = f"{uuid.uuid4().hex}_{audio_file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)

    try:
        prediction = predict_from_audio(filepath)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la prédiction du modèle : {e}")

    consultation_doc = {
        "patient_id": ObjectId(patient_id),
        "doctor_id": current_user["_id"],
        "date": datetime.now(timezone.utc),
        "audio_filename": filename,
        "prediction_percentage": prediction["prediction_percentage"],
        "prediction_label": prediction["prediction_label"],
        "threshold_used": prediction["threshold_used"],
        "doctor_remarks": None,
    }
    result = await consultations_collection.insert_one(consultation_doc)
    consultation_doc["_id"] = result.inserted_id

    return ConsultationOut(
        id=str(consultation_doc["_id"]),
        patient_id=str(consultation_doc["patient_id"]),
        doctor_id=str(consultation_doc["doctor_id"]),
        date=consultation_doc["date"],
        prediction_percentage=consultation_doc["prediction_percentage"],
        prediction_label=consultation_doc["prediction_label"],
        threshold_used=consultation_doc["threshold_used"],
        doctor_remarks=consultation_doc["doctor_remarks"],
        audio_filename=consultation_doc["audio_filename"],
    )


@router.put("/consultations/{consultation_id}/remarks", response_model=ConsultationOut)
async def update_remarks(
    consultation_id: str,
    payload: RemarksUpdate,
    current_user: dict = Depends(require_role("doctor")),
):
    consultation = await consultations_collection.find_one({"_id": ObjectId(consultation_id)})
    if not consultation or consultation["doctor_id"] != current_user["_id"]:
        raise HTTPException(status_code=404, detail="Consultation introuvable")

    await consultations_collection.update_one(
        {"_id": ObjectId(consultation_id)},
        {"$set": {"doctor_remarks": payload.doctor_remarks}},
    )
    consultation = await consultations_collection.find_one({"_id": ObjectId(consultation_id)})

    return ConsultationOut(
        id=str(consultation["_id"]),
        patient_id=str(consultation["patient_id"]),
        doctor_id=str(consultation["doctor_id"]),
        date=consultation["date"],
        prediction_percentage=consultation.get("prediction_percentage"),
        prediction_label=consultation.get("prediction_label"),
        threshold_used=consultation.get("threshold_used"),
        doctor_remarks=consultation.get("doctor_remarks"),
        audio_filename=consultation.get("audio_filename"),
    )
