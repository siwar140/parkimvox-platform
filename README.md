# ParkImVox Platform

Plateforme web de suivi de la maladie de Parkinson par analyse vocale.

## Fonctionnalités

- **Médecin** : prédit le pourcentage de la maladie à partir d'un enregistrement
  audio (modèle CNN), consulte la liste de ses patients et leur historique de
  consultations, ajoute des remarques, échange des messages avec ses patients.
- **Patient** : login, consultation de son profil, de son historique de
  consultations et des remarques du médecin, échange de messages avec son médecin.
- **Données** : sauvegardées dans MongoDB Atlas (utilisateurs, profils,
  consultations, messages).

## Architecture

```
parkimvox_platform/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── main.py          # point d'entrée
│   │   ├── config.py        # variables d'environnement
│   │   ├── database.py      # connexion MongoDB Atlas (motor)
│   │   ├── security.py      # JWT + hashing des mots de passe
│   │   ├── models/schemas.py
│   │   ├── routers/         # auth, patients, doctors, messages
│   │   └── ml/inference.py  # chargement du modèle + prédiction
│   ├── models_data/         # à compléter : best_model.keras + norm_stats.json
│   ├── requirements.txt
│   └── .env.example
└── frontend/                 # HTML/CSS/JS simple (aucun build nécessaire)
    ├── login.html
    ├── patient_dashboard.html
    ├── doctor_dashboard.html
    ├── css/style.css
    └── js/api.js
```

## Installation

### 1. Base de données — MongoDB Atlas
1. Créez un cluster gratuit sur https://www.mongodb.com/cloud/atlas
2. Créez un utilisateur de base de données + autorisez votre IP (Network Access)
3. Récupérez l'URI de connexion (`mongodb+srv://...`)

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows : venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# -> éditez .env avec votre MONGO_URI et un JWT_SECRET aléatoire
```

Placez votre modèle dans `backend/models_data/` (voir
`backend/models_data/README.md` pour le détail, notamment le fichier
`norm_stats.json` à générer depuis votre notebook).

Lancez l'API :
```bash
uvicorn app.main:app --reload
```
L'API est disponible sur http://127.0.0.1:8000 et sa documentation
interactive sur http://127.0.0.1:8000/docs

### 3. Frontend
Aucune installation nécessaire (HTML/CSS/JS pur). Servez le dossier
`frontend/` avec un petit serveur statique, par exemple :
```bash
cd frontend
python -m http.server 5500
```
Puis ouvrez http://127.0.0.1:5500/login.html

Si votre frontend n'est pas servi sur `http://127.0.0.1:5500`, mettez à jour
`CORS_ORIGINS` dans `backend/.env` et `API_BASE_URL` dans `frontend/js/api.js`.

## Utilisation

1. Un médecin crée son compte (onglet "Créer un compte" → "Médecin").
2. Un patient crée son compte et indique le **nom d'utilisateur** du médecin
   pour lui être assigné (ou l'assigne plus tard).
3. Le médecin voit le patient apparaître dans sa liste, peut uploader un
   enregistrement audio → le modèle CNN calcule le pourcentage de la maladie,
   ajouter des remarques, et échanger des messages avec le patient.
4. Le patient consulte son historique de consultations et discute avec son
   médecin depuis son propre tableau de bord.

## Sécurité — points à durcir avant une mise en production réelle

- Le fichier `.env` (secrets) ne doit jamais être commité.
- HTTPS obligatoire en production (les JWT circulent en clair sinon).
- Ajouter une limite de taille/type sur les fichiers audio uploadés.
- Le stockage des données de santé doit respecter la réglementation en
  vigueur (consentement, hébergement de données de santé, chiffrement, etc.) —
  la plateforme actuelle est un prototype fonctionnel, pas une solution
  certifiée pour données médicales réelles.
