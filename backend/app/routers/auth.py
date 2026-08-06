from fastapi import APIRouter, HTTPException, Depends, status
from bson import ObjectId

from app.database import users_collection, patient_profiles_collection, doctor_profiles_collection
from app.models.schemas import UserRegister, UserLogin, Token, UserOut
from app.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister):
    existing = await users_collection.find_one({"username": payload.username})
    if existing:
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur existe déjà")

    user_doc = {
        "username": payload.username,
        "hashed_password": hash_password(payload.password),
        "role": payload.role,
        "full_name": payload.full_name,
    }
    result = await users_collection.insert_one(user_doc)
    user_id = result.inserted_id

    if payload.role == "patient":
        doctor_id = None
        if payload.doctor_username:
            doctor_user = await users_collection.find_one(
                {"username": payload.doctor_username, "role": "doctor"}
            )
            if not doctor_user:
                raise HTTPException(status_code=400, detail="Médecin introuvable")
            doctor_id = doctor_user["_id"]

        await patient_profiles_collection.insert_one({
            "user_id": user_id,
            "age": payload.age,
            "sexe": payload.sexe,
            "telephone": payload.telephone,
            "doctor_id": doctor_id,
        })
    else:  # doctor
        await doctor_profiles_collection.insert_one({
            "user_id": user_id,
            "specialite": payload.specialite,
            "hopital": payload.hopital,
        })

    token = create_access_token({"sub": str(user_id), "role": payload.role})
    return Token(access_token=token, role=payload.role, full_name=payload.full_name)


@router.post("/login", response_model=Token)
async def login(payload: UserLogin):
    user = await users_collection.find_one({"username": payload.username})
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Nom d'utilisateur ou mot de passe incorrect")

    token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    return Token(access_token=token, role=user["role"], full_name=user["full_name"])


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)):
    return UserOut(
        id=str(current_user["_id"]),
        username=current_user["username"],
        role=current_user["role"],
        full_name=current_user["full_name"],
    )
