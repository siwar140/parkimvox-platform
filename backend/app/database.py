"""
Connexion à MongoDB Atlas avec Motor (driver async officiel).
Toutes les collections utilisées par la plateforme sont exposées ici.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db_name]

# Collections
users_collection = db["users"]                    # comptes (patients + médecins), login unifié
patient_profiles_collection = db["patient_profiles"]
doctor_profiles_collection = db["doctor_profiles"]
consultations_collection = db["consultations"]     # historique + résultats de prédiction
messages_collection = db["messages"]               # messagerie médecin <-> patient


async def ensure_indexes():
    """À appeler au démarrage : garantit l'unicité des usernames et accélère les requêtes."""
    await users_collection.create_index("username", unique=True)
    await patient_profiles_collection.create_index("user_id", unique=True)
    await doctor_profiles_collection.create_index("user_id", unique=True)
    await consultations_collection.create_index([("patient_id", 1), ("date", -1)])
    await messages_collection.create_index([("participants", 1), ("timestamp", 1)])
