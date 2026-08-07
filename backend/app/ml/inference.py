"""
Module d'inférence : reconstruit l'architecture du CNN en code (pour éviter
les soucis de compatibilité entre versions de Keras lors du chargement d'un
fichier .keras), charge les poids entraînés (.h5), et transforme un fichier
audio en prédiction (pourcentage de probabilité + label).

Paramètres de génération de spectrogramme confirmés depuis le script
d'entraînement original (spectrograms_creation.py, dossier spectnumpy_8K) :
sr=8000, n_fft=512, hop_length=256, win_length=512, center=False,
amplitude_to_db SANS ref=np.max (échelle dB "brute", pas de recadrage).

norm_stats.json contient {"mean": -42.3466, "std": 19.0233}, les valeurs
exactes calculées sur X_train lors de l'entraînement.
"""
import json
import numpy as np
import librosa
import tensorflow as tf
from tensorflow.keras import layers, models

from app.config import settings

IMG_HEIGHT = 257
IMG_WIDTH = 59
SR = 8000
N_FFT = 512
HOP_LENGTH = 256
WIN_LENGTH = 512

_model = None
_norm_stats = None


def _build_architecture():
    """Reconstruit exactement l'architecture du notebook (4 blocs Conv2D)."""
    return models.Sequential([
        layers.Input(shape=(IMG_HEIGHT, IMG_WIDTH, 1)),
        layers.Conv2D(16, (3, 3), padding="same", activation="relu"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        layers.Conv2D(32, (3, 3), padding="same", activation="relu"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        layers.Conv2D(64, (3, 3), padding="same", activation="relu"),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        layers.Conv2D(64, (3, 3), padding="same", activation="relu"),
        layers.Dropout(0.25),
        layers.GlobalAveragePooling2D(),
        layers.Dense(32, activation="relu"),
        layers.Dense(1, activation="sigmoid"),
    ])


def load_model():
    global _model
    if _model is None:
        _model = _build_architecture()
        _model.load_weights(settings.model_path)
    return _model


def load_norm_stats():
    global _norm_stats
    if _norm_stats is None:
        with open(settings.norm_stats_path, "r") as f:
            _norm_stats = json.load(f)
    return _norm_stats


def audio_to_spectrogram(audio_path: str) -> np.ndarray:
    """Audio -> spectrogramme dB de forme (257, 59), fidèle au script d'entraînement."""
    y, _ = librosa.load(audio_path, sr=SR)
    stft = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH, win_length=WIN_LENGTH, center=False)
    spec_db = librosa.amplitude_to_db(np.abs(stft))  # pas de ref=np.max, comme à l'entraînement

    # Ajuste la largeur temporelle à IMG_WIDTH (crop ou pad) — l'audio réel n'a pas
    # forcément exactement la même durée que les clips d'entraînement
    if spec_db.shape[1] > IMG_WIDTH:
        spec_db = spec_db[:, :IMG_WIDTH]
    elif spec_db.shape[1] < IMG_WIDTH:
        pad = IMG_WIDTH - spec_db.shape[1]
        spec_db = np.pad(spec_db, ((0, 0), (0, pad)), mode="constant", constant_values=spec_db.min())

    return spec_db.astype(np.float32)


def predict_from_audio(audio_path: str) -> dict:
    model = load_model()
    stats = load_norm_stats()

    spec = audio_to_spectrogram(audio_path)
    spec = (spec - stats["mean"]) / stats["std"]
    spec = spec[np.newaxis, ..., np.newaxis]  # (1, 257, 59, 1)

    probability = float(model.predict(spec, verbose=0)[0][0])
    percentage = round(probability * 100, 2)
    label = "Patologicas" if probability >= settings.decision_threshold else "Control"

    return {
        "prediction_percentage": percentage,
        "prediction_label": label,
        "threshold_used": settings.decision_threshold,
    }