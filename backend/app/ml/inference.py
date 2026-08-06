"""
VERSION TEMPORAIRE — simule une prédiction sans charger le vrai modèle.
Sert uniquement à tester l'API + MongoDB. Le vrai fichier est sauvegardé
dans inference_REAL.py.bak, à restaurer une fois best_model.keras et
norm_stats.json prêts.
"""
import random
from app.config import settings


def predict_from_audio(audio_path: str) -> dict:
    # Génère une fausse probabilité aléatoire à la place du modèle réel
    probability = random.uniform(0, 1)
    percentage = round(probability * 100, 2)
    label = "Patologicas" if probability >= settings.decision_threshold else "Control"

    return {
        "prediction_percentage": percentage,
        "prediction_label": label,
        "threshold_used": settings.decision_threshold,
    }