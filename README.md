# 🧬 BAMI – Bioactive Molecule Intelligence

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

# 🧬 XGBioactive: AI-Based Bioactivity Prediction

<p align="center">
  <strong>Machine Learning-Based Molecular Bioactivity Prediction and Analysis</strong>
</p>

<p align="center">
  An AI-powered platform for computationally screening molecules against selected biological targets using XGBoost, RDKit, and other machine learning algorithms.
</p>

---

## 📌 Overview

**XGBioactive** is an AI-powered bioactivity prediction platform designed to help researchers analyze chemical compounds and estimate their biological activity against selected molecular targets.

The application combines machine learning, cheminformatics, and external chemical information databases to provide a unified molecular analysis workflow.

Users can submit a molecule using its SMILES (Simplified Molecular Input Line Entry System) representation. The system processes the molecular structure, extracts relevant chemical features, and passes them to trained machine learning models to generate bioactivity predictions.

The platform currently focuses on two important biological targets:

- **COX-2 (Cyclooxygenase-2):** An enzyme associated with prostaglandin production and inflammatory processes.
- **EGFR (Epidermal Growth Factor Receptor):** A receptor involved in cellular signaling, growth, and proliferation.

The system also provides molecular descriptor analysis, drug-likeness assessment, molecular structure visualization, and external reference information.

> **Important:** XGBioactive provides computational predictions for research and screening purposes. Its predictions are not experimental confirmation, clinical evidence, or a guarantee of drug efficacy or safety.

---

## 🎯 Problem Statement

Traditional experimental screening of chemical compounds can be expensive, time-consuming, and resource-intensive.

Researchers working with large chemical libraries need efficient ways to prioritize molecules for further investigation.

Some common challenges include:

- Analyzing large numbers of chemical compounds.
- Identifying potentially bioactive molecules.
- Understanding molecular properties.
- Comparing the performance of different prediction algorithms.
- Accessing relevant chemical and drug information.
- Organizing and reviewing screening results.

### Proposed Solution

XGBioactive addresses these challenges through a machine learning-based molecular analysis platform.

It accepts molecular structures, processes them using RDKit, extracts chemical features, and applies target-specific prediction models to estimate biological activity.

The platform helps researchers prioritize molecules for further laboratory investigation.

---

## 🎯 Project Objectives

1. Predict molecular bioactivity against selected biological targets.
2. Implement XGBoost-based classification models.
3. Compare multiple machine learning algorithms.
4. Convert SMILES representations into meaningful molecular features.
5. Analyze important molecular descriptors.
6. Evaluate drug-likeness using Lipinski's Rule of Five.
7. Support individual molecule analysis and batch screening.
8. Retrieve chemical and drug-related information through external databases.
9. Provide an interactive interface for molecular analysis.
10. Export prediction results for further research.

---

## ✨ Key Features

### 1. Molecular Bioactivity Prediction

- Predict Active or Inactive classifications.
- Support target-specific prediction workflows.
- Use trained machine learning models.
- Display prediction results through the web interface.

### 2. Multiple Machine Learning Algorithms

The COX-2 comparison workflow supports five algorithms:

| Algorithm | Description |
|---|---|
| XGBoost | Extreme Gradient Boosting |
| Random Forest | Ensemble of decision trees |
| Linear SVM | Linear Support Vector Machine |
| Naive Bayes | Probabilistic classification |
| RBF Network | Radial Basis Function Network |

XGBoost is configured as the highlighted/default model.

### 3. Molecular Structure Processing

- Accept molecular structures through SMILES.
- Validate molecular input using RDKit.
- Convert SMILES into molecular objects.
- Calculate molecular descriptors.
- Support molecular structure visualization.

### 4. Molecular Descriptor Analysis

The platform calculates six important molecular properties:

| Descriptor | Meaning |
|---|---|
| Molecular Weight (MW) | Total molecular mass |
| LogP | Estimated lipophilicity |
| HBD | Hydrogen Bond Donors |
| HBA | Hydrogen Bond Acceptors |
| TPSA | Topological Polar Surface Area |
| Rotatable Bonds | Molecular flexibility indicator |

### 5. Drug-Likeness Analysis

The platform implements Lipinski's Rule of Five to assess selected molecular properties.

| Property | General Threshold |
|---|---|
| Molecular Weight | ≤ 500 Da |
| LogP | ≤ 5 |
| Hydrogen Bond Donors | ≤ 5 |
| Hydrogen Bond Acceptors | ≤ 10 |

The system identifies rule violations and displays whether the molecule satisfies the implemented criteria.

Meeting these criteria does not prove that a compound is an effective or safe drug.

### 6. Batch Molecule Screening

The batch-screening workflow is designed to analyze multiple molecules through CSV input.

It supports:

- Processing multiple molecular structures.
- Individual molecular validation.
- Generating prediction results.
- Displaying screening results in tabular form.
- Exporting results for further analysis.

### 7. External Database Integration

XGBioactive integrates external chemical and drug information sources.

| Database | Purpose |
|---|---|
| PubChem | Chemical compound information and molecular records |
| ChEMBL | Bioactivity and drug-indication information |
| DailyMed | Official drug labeling and indication information |

These integrations help provide additional information about submitted compounds.

Database availability and compound coverage may affect the information returned.

### 8. Results and Data Export

- Display prediction results.
- Present molecular descriptor information.
- Show drug-likeness assessment.
- Provide screening summaries.
- Support CSV result export.

---

## 🧠 Machine Learning Architecture

XGBioactive uses machine learning classification to estimate the biological activity of chemical compounds.

### XGBoost

Extreme Gradient Boosting (XGBoost) is an ensemble learning algorithm based on gradient-boosted decision trees.

It builds multiple decision trees sequentially, with later trees learning from errors made by earlier trees.

The combined predictions produce the final classification.

**Why XGBoost?**

- Effective for structured numerical data.
- Can learn nonlinear relationships.
- Supports classification problems.
- Provides efficient inference after training.

### Model Comparison

The project includes a comparison workflow involving:

1. XGBoost
2. Random Forest
3. Linear Support Vector Machine
4. Naive Bayes
5. Radial Basis Function Network

The models are evaluated using:

- Accuracy
- Precision
- Recall
- F1-score
- ROC-AUC

The evaluation workflow uses a molecule-grouped 80:20 training/testing holdout for the six-descriptor comparison.

---

## 🧪 Molecular Representation and Feature Extraction

### What is SMILES?

SMILES is a text-based representation of a chemical molecule.

Instead of entering a molecular drawing, users can provide a string describing its atoms, bonds, and molecular structure.

For example:

```text
CCO
```

This represents ethanol.

### RDKit Processing

RDKit is used for molecular parsing, validation, and descriptor calculation.

The general processing workflow is:

1. Receive the SMILES string.
2. Parse the string using RDKit.
3. Validate the molecular structure.
4. Create an RDKit molecular object.
5. Calculate the required molecular features.
6. Pass the features to the corresponding trained model.

### COX-2 Feature Extraction

The six molecular descriptors supplied to the comparison models are:

```python
features = [
    molecular_weight,
    rotatable_bonds,
    h_bond_acceptors,
    h_bond_donors,
    tpsa,
    logp
]
```

The feature order must remain consistent with the order used during model training.

### EGFR Feature Extraction

The EGFR model configuration uses Morgan fingerprints:

| Parameter | Value |
|---|---|
| Fingerprint | Morgan |
| Radius | 2 |
| Number of bits | 2048 |
| Representation | Binary |
| Chirality | Enabled |
| Active label | 1 |
| Inactive label | 0 |

Morgan fingerprints encode molecular substructures into a fixed-length bit vector.

**Note:** COX-2 descriptor-based inference and EGFR fingerprint-based inference use different feature representations. Their trained models must receive the exact feature format used during training.

---

## 🔬 Biological Targets

### COX-2 – Cyclooxygenase-2

COX-2 is an enzyme involved in the production of prostaglandins, which play important roles in inflammation and other physiological processes.

The project uses computational bioactivity prediction to help identify compounds that may be worth investigating against COX-2.

### EGFR – Epidermal Growth Factor Receptor

EGFR is a cell-surface receptor involved in cellular signaling, growth, and proliferation.

The EGFR prediction workflow helps researchers computationally screen molecules for potential activity against this target.

Both workflows use target-specific models and should be interpreted independently.

---

## ⚙️ System Architecture

The application follows a frontend-backend-machine-learning architecture.

```text
                 USER
                   |
                   |
          SMILES / CSV INPUT
                   |
                   |
             FRONTEND
          HTML / CSS / JS
                   |
                   |
             FASTAPI
             BACKEND
                   |
                   |
            INPUT VALIDATION
                   |
                   |
                RDKit
          MOLECULAR PROCESSING
                   |
                   |
           FEATURE EXTRACTION
                   |
                   |
           TARGET SELECTION
             /         \
            /           \
         COX-2           EGFR
           |               |
      Descriptor       Morgan
       Features      Fingerprints
           |               |
           |               |
      ML MODELS        XGBOOST
           |               |
           |               |
           +-------+-------+
                   |
                   |
             PREDICTION
                   |
                   |
          MOLECULAR ANALYSIS
                   |
          +--------+--------+
          |        |        |
       Results  Descriptors  Drug
                            Likeness
                   |
                   |
            RESULTS DISPLAY
                   |
                   |
              CSV EXPORT
```

### Architecture Components

| Component | Responsibility |
|---|---|
| Frontend | User interaction and result presentation |
| FastAPI | API requests and backend processing |
| RDKit | Molecular validation and feature extraction |
| XGBoost | Bioactivity classification |
| Other ML models | Comparative classification |
| External APIs | Chemical and drug information lookup |

---

## 🔄 Complete Project Workflow

The application follows this general workflow:

**Step 1: User Input**

The user enters a SMILES string or provides molecules through a supported CSV workflow.

**Step 2: Backend Request**

The frontend sends the input to the FastAPI backend.

**Step 3: Molecular Validation**

RDKit parses the SMILES string and checks whether the molecular structure is valid.

**Step 4: Molecular Feature Extraction**

The system calculates the features required by the selected target-specific model.

**Step 5: Target Selection**

The appropriate COX-2 or EGFR prediction workflow is selected.

**Step 6: Model Inference**

The corresponding trained model processes the molecular features.

**Step 7: Result Generation**

The model returns an activity classification, which is formatted for presentation.

**Step 8: Additional Analysis**

The application can calculate molecular descriptors, evaluate drug-likeness, and retrieve available external compound information.

**Step 9: Results Display**

The frontend presents the generated information.

**Step 10: Export**

Users can export supported screening results for further analysis.

---

## 🛠️ Technology Stack

### Frontend

- HTML5
- CSS3
- JavaScript

### Backend

- Python
- FastAPI
- Pydantic

### Machine Learning

- XGBoost
- Scikit-learn
- Joblib
- NumPy

### Cheminformatics

- RDKit

### External Data Sources

- PubChem
- ChEMBL
- DailyMed

### Development Tools

- Visual Studio Code
- Git
- GitHub
- Python Virtual Environment

---

## 📂 Project Structure

The following is a logical representation of the application structure. Adjust directory names to match the actual repository before publishing.

```text
XGBioactive/
│
├── Backend/
│   ├── main.py
│   ├── models/
│   │   ├── xgb_cox2_model.json
│   │   └── comparison/
│   │       ├── xgboost.joblib
│   │       ├── random_forest.joblib
│   │       ├── lsvm.joblib
│   │       ├── naive_bayes.joblib
│   │       └── rbfn.joblib
│   │
│   └── requirements.txt
│
├── Frontend/
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── assets/
│
├── EGFR_model_artifacts/
│   └── models/
│       └── egfr_xgboost_model.pkl
│
├── result/
│   └── model_metrics.csv
│
├── README.md
└── .gitignore
```

Model artifact names and locations must match the backend configuration. The EGFR model path is configured separately from the COX-2 comparison models.

---

## 🚀 Installation and Setup

### Prerequisites

Install the following before running the application:

- Python 3.10 or a compatible version supported by the selected dependencies.
- pip
- Git
- A supported operating system.
- Required trained model artifacts.

RDKit installation can depend on the Python version and operating system.

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/XGBioactive.git
```

### 2. Navigate to the Project

```bash
cd XGBioactive
```

### 3. Create a Virtual Environment

```bash
python3 -m venv venv
```

### 4. Activate the Virtual Environment

**macOS / Linux**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r Backend/requirements.txt
```

If your requirements file is located elsewhere, adjust the path accordingly.

### 6. Configure Model Files

Place the trained model files in the locations expected by the backend.

Ensure that the required COX-2 and EGFR model artifacts are available.

### 7. Start the Backend

Navigate to the directory containing `main.py`:

```bash
cd Backend
```

Run:

```bash
uvicorn main:app --reload
```

If your FastAPI application is inside another Python module, adjust the Uvicorn import path.

### 8. Access the API

```text
http://127.0.0.1:8000
```

FastAPI interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### 9. Run the Frontend

Open the frontend entry point using your configured development server or browser setup.

Ensure that the frontend API base URL points to the running backend.

---

## 🔌 API Endpoints

The following endpoints are defined in the available FastAPI backend.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/predict` | Molecular bioactivity prediction |
| POST | `/predict` | Prediction alias |
| POST | `/api/v1/drug-likeness` | Drug-likeness analysis |
| POST | `/drug-likeness` | Drug-likeness alias |
| POST | `/api/v1/clinical-uses` | External clinical-use lookup |
| GET | `/models` | Available model status |
| GET | `/api/v1/model-metrics` | Model evaluation metrics |

### Example: Bioactivity Prediction

**Request**

```http
POST /api/v1/predict
Content-Type: application/json
```

```json
{
  "smiles": "CCO"
}
```

The backend validates the molecule and generates the corresponding prediction response.

**Note:** `CCO` is an input example, not a claim that ethanol should be classified as Active or Inactive.

### Example: Drug-Likeness Analysis

```http
POST /api/v1/drug-likeness
Content-Type: application/json
```

```json
{
  "smiles": "CCO"
}
```

The response includes:

- Molecular descriptors.
- Lipinski rule results.
- Number of rule violations.
- Overall rule assessment.

### Example: Model Metrics

```http
GET /api/v1/model-metrics
```

Returns available evaluation information for the trained model comparison.

---

## 📊 Model Evaluation

The model comparison workflow evaluates classification performance using standard machine learning metrics.

| Metric | Purpose |
|---|---|
| Accuracy | Overall proportion of correct predictions |
| Precision | Proportion of predicted positives that are correct |
| Recall | Proportion of actual positives correctly identified |
| F1-score | Harmonic mean of precision and recall |
| ROC-AUC | Ability to distinguish between classes across thresholds |

The evaluation uses a molecule-grouped 80:20 holdout for the six-descriptor comparison.

Actual model results should be taken from the project's generated evaluation file rather than assumed or manually estimated.

---

## 🔐 Limitations

- Predictions depend on the quality and coverage of training datasets.
- Different biological targets require different trained models.
- Invalid or unsupported molecular structures cannot be processed.
- Prediction confidence does not establish biological certainty.
- External database records may be unavailable or incomplete.
- Drug-likeness rules do not establish clinical suitability.
- Laboratory experiments are necessary to validate computational predictions.
- A positive prediction does not guarantee therapeutic effectiveness.

---

## 🔮 Future Scope

Potential future improvements include:

- Expanding target-specific training datasets.
- Improving model generalization and calibration.
- Adding molecular explainability using feature attribution.
- Integrating additional biological targets.
- Improving batch screening capabilities.
- Adding richer molecular visualization.
- Supporting more chemical file formats.
- Improving external database coverage.
- Validating predictions through laboratory experiments.

---

## 👨‍💻 Development Team

**Project:** XGBioactive – AI-Based Bioactivity Prediction

**Institution:** NGIT, Osmania University

**Department:** Computer Science and Engineering

**Project Lead / Contributor:** Mandala Sai Karthikeya

---

## 📚 References and Resources

- [RDKit Documentation](https://www.rdkit.org/docs/)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Scikit-learn Documentation](https://scikit-learn.org/)
- [PubChem](https://pubchem.ncbi.nlm.nih.gov/)
- [ChEMBL](https://www.ebi.ac.uk/chembl/)
- [DailyMed](https://dailymed.nlm.nih.gov/)
- [Lipinski's Rule of Five](https://doi.org/10.1016/S0169-409X(00)00129-0)

---

## 📄 Disclaimer

XGBioactive is an academic and research-oriented computational tool.

The predictions and molecular analyses generated by this application are intended to support preliminary research and molecule prioritization.

They must not be interpreted as medical advice, clinical recommendations, or proof of drug efficacy, safety, or therapeutic activity.

All predictions require appropriate scientific interpretation and experimental validation.

---

<p align="center">
  <strong>Built with Python, RDKit, XGBoost and FastAPI.</strong>
  <br>
  Exploring molecular bioactivity through artificial intelligence.
</p>
