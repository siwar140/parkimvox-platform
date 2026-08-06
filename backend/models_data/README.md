# Dossier des fichiers du modèle

Placez ici deux fichiers avant de démarrer le backend :

## 1. `best_model.keras`
Copiez directement le fichier généré par votre notebook (`ModelCheckpoint`
sauvegarde déjà sous ce nom).

## 2. `norm_stats.json`
Ce fichier n'existe pas encore automatiquement — il faut l'exporter depuis
votre notebook, juste après avoir calculé `train_mean` et `train_std` :

```python
import json
with open("norm_stats.json", "w") as f:
    json.dump({"mean": float(train_mean), "std": float(train_std)}, f)
```

Puis copiez ce fichier ici : `backend/models_data/norm_stats.json`.

**Important** : sans ce fichier, l'API ne pourra pas normaliser les
spectrogrammes de la même façon qu'à l'entraînement, et les prédictions
seront incorrectes.

## À propos de `audio_to_spectrogram()` (dans `app/ml/inference.py`)

Cette fonction reproduit les paramètres mentionnés dans votre pipeline
(n_fft=512, hop_length=128, sr=16000, échelle dB [-80, 0]), mais votre
notebook actuel charge des `.npy` déjà générés — il ne contient pas le
code exact qui transforme un fichier audio brut en spectrogramme.
**Vérifiez et ajustez cette fonction pour qu'elle corresponde EXACTEMENT**
à votre script original de génération de spectrogrammes, sinon les
prédictions en production ne correspondront pas à celles obtenues à
l'entraînement.
