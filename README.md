# XGBioactive

A web application for predicting COX-2 molecular bioactivity from SMILES. The frontend displays a molecule structure, molecular descriptors, and an XGBoost prediction. A separate comparison endpoint runs five descriptor-based classifiers.

## Requirements

- Python 3.10 or later
- Node.js 20.12 or later
- `pip`
- A modern web browser

## Setup

From the project root, create and activate a virtual environment, then install the backend dependencies:

```bash
cd /path/to/XGBioactiveNew
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r Backend/requirements.txt
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.

## Run locally

From the project root, start both the API and frontend in one terminal:

```bash
npm run dev
```

Open <http://127.0.0.1:5501/>. Press `Ctrl+C` to stop both services.

Alternatively, start each service in its own terminal. Start the API:

```bash
cd /path/to/XGBioactiveNew/Backend
../.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then start the static frontend:

```bash
cd /path/to/XGBioactiveNew/Frontend
python3 -m http.server 5501 --bind 127.0.0.1
```

Open <http://127.0.0.1:5501/>. Keep both terminals running while using the app. The frontend sends API requests to port `8000`.

## Firebase authentication setup

The prediction dashboard and drug-likeness page require a signed-in Firebase
user. Login and registration use Firebase Email/Password Authentication. A
user's full name is saved as their Firebase Authentication `displayName`; no
Firestore database is required for the current profile fields.

1. In the [Firebase console](https://console.firebase.google.com/), create or
   select a project and add a **Web app**.
2. Under **Authentication → Sign-in method**, enable **Email/Password**.
3. Under **Authentication → Settings → Authorized domains**, add `localhost`
   for local use and the deployed app's hostname for production.
4. Copy the Web app's API key, Auth domain, Project ID, and App ID into a
   `.env` file in the project root (next to `package.json`):

   ```bash
   FIREBASE_API_KEY=your-web-api-key
   FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_APP_ID=your-web-app-id
   ```

   These web settings are public client configuration, not service-account
   credentials. `.env` is excluded from Git. Restrict the Firebase API key to
   the app's domains in Google Cloud Console.
5. The backend verifies Firebase ID-token signatures with Google's public
   signing certificates. It needs `FIREBASE_PROJECT_ID`, but no Firebase
   service-account key or other private credential.
6. Run `npm run dev`. The dev script loads the root `.env` file before starting
   FastAPI. For Render, configure the four web settings as service environment
   variables; no service-account key is required.

The API returns only the public Firebase Web app configuration from
`/api/v1/firebase-config`. The backend verifies token signatures and project
audience on the prediction, batch-screening, drug-likeness, clinical-use, and
model-data endpoints. This keyless verification does not check whether a user
has been disabled or a token revoked; those checks require privileged Firebase
Admin credentials. The static dashboard also redirects signed-out users to
`login.html`.

Useful API pages:

- Health check: <http://127.0.0.1:8000/health>
- Interactive API documentation: <http://127.0.0.1:8000/docs>
- Model metrics: <http://127.0.0.1:8000/api/v1/model-metrics>

## Deploy to Render

The root `render.yaml` configures one Free Web Service. FastAPI serves the
frontend and API from the same Render URL; the Free plan may spin down after
inactivity. In Render, create a **Blueprint** from this GitHub repository and
deploy the `xgbioactive` service. Set `FIREBASE_API_KEY`,
`FIREBASE_AUTH_DOMAIN`, `FIREBASE_PROJECT_ID`, and `FIREBASE_APP_ID` in the
service environment. The health check is available at `/health`.

## Model evaluation

The trained models and evaluated metrics are included in the repository. To regenerate them, activate the virtual environment and run from the `Backend` directory:

```bash
cd /path/to/XGBioactiveNew/Backend
../.venv/bin/python -m app.models.compare_models
```

The evaluation script reads `data/processed/CHEMBL230_Preprocessed_Data_V2 copy.csv`, calculates six RDKit descriptors from the SMILES, and evaluates the five classifiers using a fixed molecule-grouped 80/20 holdout split. It writes the model files under `Backend/app/models/comparison/` and metrics under `Backend/result/model_metrics.csv`.

## Prediction API

Prediction endpoints require a Firebase ID token in the `Authorization:
Bearer <token>` header. After signing in through the app, the frontend obtains
and sends this token automatically. For a manual API request, supply a valid
Firebase ID token as `FIREBASE_ID_TOKEN`:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/predict-xgb \
  -H "Authorization: Bearer $FIREBASE_ID_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"smiles":"CC(=O)Oc1ccccc1C(=O)O"}'
```

Run the five descriptor-based classifiers with the same authorization header:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/predict \
  -H "Authorization: Bearer $FIREBASE_ID_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"smiles":"CC(=O)Oc1ccccc1C(=O)O"}'
```

Both endpoints accept a JSON object with a `smiles` string. Invalid SMILES return HTTP `422`.

## Batch molecule screening

The web app's **Batch Screen** section accepts one SMILES per line or a CSV with a `SMILES` header. Select COX-2, EGFR, or Both; batches are limited to 500 molecules. Invalid SMILES are reported per row and do not stop the rest of the batch. Results can be downloaded directly as an Excel-friendly CSV.

The batch endpoint reuses the same trained COX-2 and EGFR inference routes as single-molecule predictions, including the EGFR probability calibration and stored classification threshold:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/batch-predict \
  -H "Authorization: Bearer $FIREBASE_ID_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"target":"Both","smiles":["CCO","not-a-smiles"]}'
```

The response preserves input order and reports validation status, per-target predictions and probabilities, and row-level errors.

## Project layout

```text
Backend/
  app/main.py                 FastAPI application and prediction endpoints
  app/models/                 Trained models and comparison training code
  tests/test_firebase_auth.py Firebase authentication and API authorization tests
  result/                     Evaluation metrics and plots
Frontend/
  index.html                  Web application
  login.html                  Firebase sign-in page
  register.html               Firebase registration page
  auth.js                     Firebase authentication and route guard
  firebase-config.js          Firebase web configuration loader
  script.js                   Frontend behavior and API integration
  style.css                   Application styles
data/
  processed/                  Labeled dataset used for model comparison
  raw/                        Source dataset
notebooks/                    Analysis notebook and related artifacts
```
