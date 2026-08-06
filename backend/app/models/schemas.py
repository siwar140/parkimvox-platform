"""
Schémas Pydantic : validation des entrées/sorties de l'API.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ---------- Auth ----------

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: Literal["patient", "doctor"]
    full_name: str

    # Champs optionnels selon le rôle
    age: Optional[int] = None
    sexe: Optional[str] = None
    telephone: Optional[str] = None
    specialite: Optional[str] = None
    hopital: Optional[str] = None
    doctor_username: Optional[str] = None  # médecin assigné, si le patient en connaît un


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str


class UserOut(BaseModel):
    id: str
    username: str
    role: str
    full_name: str


# ---------- Profils ----------

class PatientProfileOut(BaseModel):
    id: str
    user_id: str
    username: str
    full_name: str
    age: Optional[int] = None
    sexe: Optional[str] = None
    telephone: Optional[str] = None
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None


class DoctorProfileOut(BaseModel):
    id: str
    user_id: str
    username: str
    full_name: str
    specialite: Optional[str] = None
    hopital: Optional[str] = None


# ---------- Consultations ----------

class ConsultationOut(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    date: datetime
    prediction_percentage: Optional[float] = None
    prediction_label: Optional[str] = None
    threshold_used: Optional[float] = None
    doctor_remarks: Optional[str] = None
    audio_filename: Optional[str] = None


class RemarksUpdate(BaseModel):
    doctor_remarks: str


class AssignDoctor(BaseModel):
    doctor_username: str


# ---------- Messagerie ----------

class MessageCreate(BaseModel):
    receiver_id: str
    content: str = Field(..., min_length=1, max_length=2000)


class MessageOut(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    content: str
    timestamp: datetime
    read: bool
