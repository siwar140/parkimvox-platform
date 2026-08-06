from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from app.database import messages_collection, users_collection, patient_profiles_collection
from app.models.schemas import MessageCreate, MessageOut
from app.security import get_current_user

router = APIRouter(prefix="/messages", tags=["Messagerie"])


async def _check_relation_allowed(user_a_id: ObjectId, user_b_id: ObjectId) -> bool:
    """Vérifie qu'un patient et un médecin sont bien liés avant d'autoriser leurs échanges."""
    user_a = await users_collection.find_one({"_id": user_a_id})
    user_b = await users_collection.find_one({"_id": user_b_id})
    if not user_a or not user_b:
        return False

    if user_a["role"] == "patient" and user_b["role"] == "doctor":
        patient_id, doctor_id = user_a_id, user_b_id
    elif user_a["role"] == "doctor" and user_b["role"] == "patient":
        patient_id, doctor_id = user_b_id, user_a_id
    else:
        return False

    profile = await patient_profiles_collection.find_one({"user_id": patient_id})
    return bool(profile and profile.get("doctor_id") == doctor_id)


@router.post("", response_model=MessageOut)
async def send_message(payload: MessageCreate, current_user: dict = Depends(get_current_user)):
    receiver_id = ObjectId(payload.receiver_id)

    if not await _check_relation_allowed(current_user["_id"], receiver_id):
        raise HTTPException(status_code=403, detail="Échange non autorisé entre ces deux comptes")

    doc = {
        "sender_id": current_user["_id"],
        "receiver_id": receiver_id,
        "participants": sorted([str(current_user["_id"]), str(receiver_id)]),
        "content": payload.content,
        "timestamp": datetime.now(timezone.utc),
        "read": False,
    }
    result = await messages_collection.insert_one(doc)
    doc["_id"] = result.inserted_id

    return MessageOut(
        id=str(doc["_id"]),
        sender_id=str(doc["sender_id"]),
        receiver_id=str(doc["receiver_id"]),
        content=doc["content"],
        timestamp=doc["timestamp"],
        read=doc["read"],
    )


@router.get("/{other_user_id}", response_model=list[MessageOut])
async def get_conversation(other_user_id: str, current_user: dict = Depends(get_current_user)):
    other_id = ObjectId(other_user_id)

    if not await _check_relation_allowed(current_user["_id"], other_id):
        raise HTTPException(status_code=403, detail="Échange non autorisé entre ces deux comptes")

    participants = sorted([str(current_user["_id"]), str(other_id)])
    cursor = messages_collection.find({"participants": participants}).sort("timestamp", 1)

    results = []
    async for m in cursor:
        results.append(MessageOut(
            id=str(m["_id"]),
            sender_id=str(m["sender_id"]),
            receiver_id=str(m["receiver_id"]),
            content=m["content"],
            timestamp=m["timestamp"],
            read=m["read"],
        ))

    # Marque comme lus les messages reçus par l'utilisateur courant
    await messages_collection.update_many(
        {"participants": participants, "receiver_id": current_user["_id"], "read": False},
        {"$set": {"read": True}},
    )
    return results
