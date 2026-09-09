import os

base_dir = "c:/Users/ASUS/OneDrive/Desktop/SIH26184-COLLAB"

structure = {
    # ROOT FILES
    ".gitignore": """# Python
__pycache__/
*.py[cod]
.venv/
venv/
.env

# Node
node_modules/
dist/
build/

# IDE
.vscode/
.idea/

# macOS
.DS_Store
""",
    ".env.example": """DATABASE_URL=postgresql://user:password@localhost:5432/sih26184
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=sih26184

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

API_URL=http://localhost:8000
JWT_SECRET=your-secret-key-here
""",
    "docker-compose.yml": """version: '3.8'

services:
  backend:
    build:
      context: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - postgres
      - neo4j

  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:3000"
    env_file:
      - .env

  postgres:
    image: postgis/postgis:15-3.3
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
      POSTGRES_DB: ${POSTGRES_DB:-sih26184}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  neo4j:
    image: neo4j:5
    environment:
      NEO4J_AUTH: ${NEO4J_USERNAME:-neo4j}/${NEO4J_PASSWORD:-password}
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data

volumes:
  postgres_data:
  neo4j_data:
""",
    "README.md": """# SIH26184 — Predictive Cash-Out Intelligence System

## Project Overview
This repository contains the full Predictive Cash-Out Intelligence System.
The system traces money flows, evaluates candidate ATM locations geographically and temporally, and scores them using Machine Learning.

## Architecture
See [ARCHITECTURE.md](ARCHITECTURE.md)

## Setup and Run
1. Copy `.env.example` to `.env` and fill in values.
2. Run `docker-compose up -d` to start database, neo4j, frontend, and backend.

## Team Ownership
See [DEVELOPMENT.md](DEVELOPMENT.md) for module ownership and branch workflows.
""",
    "ARCHITECTURE.md": """# Architecture

DATA
↓
FEATURES
↓
MONEY GRAPH
↓
SPATIAL + TEMPORAL
↓
CANDIDATES
↓
ML
↓
TOP-5
↓
TIME
↓
SHAP
↓
RISK
↓
ALERT
↓
DASHBOARD
""",
    "API_CONTRACT.md": """# API Contract

## `POST /predict`
Frozen contract for prediction.

**Request**
```json
{
  "case_id": "C10231"
}
```

**Response**
```json
{
  "case_id": "C10231",
  "risk": "HIGH",
  "time_window": "22:00-23:00",
  "predictions": [
    {
      "rank": 1,
      "atm_id": "ATM-184",
      "probability": 0.82,
      "latitude": 19.076,
      "longitude": 72.877,
      "risk": "HIGH"
    },
    {
      "rank": 2,
      "atm_id": "ATM-092",
      "probability": 0.74,
      "latitude": 19.081,
      "longitude": 72.882,
      "risk": "HIGH"
    }
  ],
  "explanation": [
    "High recent transaction velocity",
    "Similar historical cash-out behaviour",
    "High-risk connected account",
    "Short transfer-to-withdrawal interval"
  ]
}
```
""",
    "DATA_DICTIONARY.md": """# Data Dictionary

- `users`: Users of the dashboard
- `complaints`: Cybercrime complaints
- `accounts`: Bank accounts
- `transactions`: Transfers between accounts
- `withdrawals`: ATM cash withdrawals
- `atms`: ATM locations and metadata
- `h3_cells`: Spatial bins
- `predictions`: Stored ML results
- `alerts`: Actionable alerts for officers
- `audit_logs`: RBAC access logs
""",
    "DEMO_SCENARIO.md": """# Demo Scenario

Case: C10231
Fraud amount: ₹4,80,000
Money trail: V001 → M001 → M002 → M003
Predicted location: ATM-184
Example score: 82%
Example window: 10–11 PM
""",
    "DEVELOPMENT.md": """# Development

## Branches
- `main`: stable
- `dev`: integration
- Feature branches: `feat/<module>/<name>`

## Ownership
- **Developer 1**: ML / Data / Spatial / Graph
- **Developer 2**: Backend / API / Security
- **Developer 3**: Frontend / GIS UI

## Coding Rules
- Add type hints to Python functions
- Document stubs with TODOs
- Follow API_CONTRACT.md strictly for `/predict`
""",
    
    # BACKEND
    "backend/README.md": "# Backend API\nFastAPI backend for SIH26184.",
    "backend/requirements.txt": "fastapi\nuvicorn\npydantic\nsqlalchemy\npsycopg2-binary\nneo4j\npython-jose\npasslib\n",
    "backend/app/__init__.py": "",
    "backend/app/main.py": """from fastapi import FastAPI
from app.api.router import api_router

app = FastAPI(title="SIH26184 API", version="1.0.0")

app.include_router(api_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is running."}
""",
    "backend/app/core/__init__.py": "",
    "backend/app/core/config.py": """import os

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/sih26184")
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    JWT_SECRET = os.getenv("JWT_SECRET", "secret")

settings = Settings()
""",
    "backend/app/core/security.py": """# Security utilities (JWT, password hashing)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    raise NotImplementedError("Password verification not implemented yet")

def create_access_token(data: dict) -> str:
    raise NotImplementedError("Token generation not implemented yet")
""",
    "backend/app/core/constants.py": """# System constants
ROLE_LEA_INVESTIGATOR = "LEA_INVESTIGATOR"
ROLE_BANK_OFFICER = "BANK_OFFICER"
ROLE_I4C_ANALYST = "I4C_ANALYST"
ROLE_ADMIN = "ADMIN"
""",
    "backend/app/db/__init__.py": "",
    "backend/app/db/database.py": """# SQLAlchemy engine setup
def get_engine():
    raise NotImplementedError("Database engine setup not implemented yet")
""",
    "backend/app/db/session.py": """# Database session maker
def get_db():
    raise NotImplementedError("DB session dependency not implemented yet")
""",
    # Models
    "backend/app/models/__init__.py": "",
    "backend/app/models/complaint.py": """# SQLAlchemy Complaint model
""",
    "backend/app/models/account.py": "",
    "backend/app/models/transaction.py": "",
    "backend/app/models/withdrawal.py": "",
    "backend/app/models/atm.py": "",
    "backend/app/models/prediction.py": "",
    "backend/app/models/alert.py": "",
    "backend/app/models/user.py": "",
    "backend/app/models/audit_log.py": "",
    # Schemas
    "backend/app/schemas/__init__.py": "",
    "backend/app/schemas/complaint.py": """from pydantic import BaseModel

class ComplaintBase(BaseModel):
    case_id: str
    fraud_amount: float
""",
    "backend/app/schemas/prediction.py": """from pydantic import BaseModel
from typing import List

class PredictRequest(BaseModel):
    case_id: str

class PredictionItem(BaseModel):
    rank: int
    atm_id: str
    probability: float
    latitude: float
    longitude: float
    risk: str

class PredictResponse(BaseModel):
    case_id: str
    risk: str
    time_window: str
    predictions: List[PredictionItem]
    explanation: List[str]
""",
    "backend/app/schemas/alert.py": """from pydantic import BaseModel

class AlertBase(BaseModel):
    alert_id: str
    case_id: str
    atm_id: str
    risk: str
    status: str
    recommended_action: str
""",
    "backend/app/schemas/auth.py": """from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str
""",
    "backend/app/schemas/common.py": "",
    
    # API Routes
    "backend/app/api/__init__.py": "",
    "backend/app/api/router.py": """from fastapi import APIRouter
from app.api.routes import cases, predictions, locations, graph, alerts, auth, audit

api_router = APIRouter()
api_router.include_router(cases.router, tags=["cases"])
api_router.include_router(predictions.router, tags=["predictions"])
api_router.include_router(locations.router, tags=["locations"])
api_router.include_router(graph.router, tags=["graph"])
api_router.include_router(alerts.router, tags=["alerts"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(audit.router, tags=["audit"])
""",
    "backend/app/api/routes/__init__.py": "",
    "backend/app/api/routes/cases.py": """from fastapi import APIRouter

router = APIRouter()

@router.get("/cases")
def get_cases():
    return {"status": "stub", "message": "List of cases not implemented yet"}

@router.get("/cases/{case_id}")
def get_case(case_id: str):
    return {"status": "stub", "message": f"Case {case_id} details not implemented yet"}
""",
    "backend/app/api/routes/predictions.py": """from fastapi import APIRouter
from app.schemas.prediction import PredictRequest, PredictResponse
from app.services.prediction_service import get_mock_prediction

router = APIRouter()

@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    \"\"\"
    Returns a prediction for the given case_id.
    Currently returns a mock prediction complying with the API contract.
    \"\"\"
    return get_mock_prediction(request.case_id)
""",
    "backend/app/api/routes/locations.py": """from fastapi import APIRouter

router = APIRouter()

@router.get("/locations")
def get_locations():
    return {"status": "stub", "message": "Locations not implemented yet"}
""",
    "backend/app/api/routes/graph.py": """from fastapi import APIRouter

router = APIRouter()

@router.get("/graph/{case_id}")
def get_graph(case_id: str):
    return {"status": "stub", "message": "Graph data not implemented yet"}
""",
    "backend/app/api/routes/alerts.py": """from fastapi import APIRouter

router = APIRouter()

@router.get("/alerts")
def get_alerts():
    return {"status": "stub", "message": "Alerts list not implemented yet"}

@router.post("/alerts")
def create_alert():
    return {"status": "stub", "message": "Create alert not implemented yet"}
""",
    "backend/app/api/routes/auth.py": """from fastapi import APIRouter
from app.schemas.auth import LoginRequest

router = APIRouter()

@router.post("/auth/login")
def login(request: LoginRequest):
    return {"status": "stub", "token": "mock-jwt-token"}
""",
    "backend/app/api/routes/audit.py": """from fastapi import APIRouter

router = APIRouter()

@router.get("/audit")
def get_audit():
    return {"status": "stub", "message": "Audit logs not implemented yet"}
""",

    # Services
    "backend/app/services/__init__.py": "",
    "backend/app/services/prediction_service.py": """from app.schemas.prediction import PredictResponse

def get_mock_prediction(case_id: str) -> dict:
    \"\"\"
    Returns a mock prediction complying with the shared API contract.
    \"\"\"
    return {
        "case_id": case_id,
        "risk": "HIGH",
        "time_window": "22:00-23:00",
        "predictions": [
            {
                "rank": 1,
                "atm_id": "ATM-184",
                "probability": 0.82,
                "latitude": 19.076,
                "longitude": 72.877,
                "risk": "HIGH"
            },
            {
                "rank": 2,
                "atm_id": "ATM-092",
                "probability": 0.74,
                "latitude": 19.081,
                "longitude": 72.882,
                "risk": "HIGH"
            }
        ],
        "explanation": [
            "High recent transaction velocity",
            "Similar historical cash-out behaviour",
            "High-risk connected account",
            "Short transfer-to-withdrawal interval"
        ]
    }
""",
    "backend/app/services/case_service.py": """def get_case_details(case_id: str):
    raise NotImplementedError("Not implemented")
""",
    "backend/app/services/graph_service.py": """def get_money_flow(case_id: str):
    raise NotImplementedError("Not implemented")
""",
    "backend/app/services/spatial_service.py": """def get_nearby_atms(lat: float, lon: float):
    raise NotImplementedError("Not implemented")
""",
    "backend/app/services/alert_service.py": """def generate_alert(case_id: str, atm_id: str):
    raise NotImplementedError("Not implemented")
""",
    "backend/app/services/auth_service.py": """def authenticate_user():
    raise NotImplementedError("Not implemented")
""",
    "backend/app/services/audit_service.py": """def record_audit_event(user: str, role: str, action: str, case_id: str):
    raise NotImplementedError("Not implemented")
""",
    
    # Tests
    "backend/tests/__init__.py": "",
    "backend/tests/test_health.py": """from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Backend is running."}
""",
    "backend/tests/test_cases.py": "",
    "backend/tests/test_predictions.py": """from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_predict_mock():
    response = client.post("/predict", json={"case_id": "C10231"})
    assert response.status_code == 200
    assert response.json()["case_id"] == "C10231"
""",
    "backend/tests/test_alerts.py": "",

    # ML Module
    "ml/README.md": "# ML Subsystem\\nMachine learning models, feature engineering, and candidate generation.",
    "ml/features/__init__.py": "",
    "ml/features/transaction_features.py": """def generate_features(transactions):
    \"\"\"
    Generate features from transaction data.
    
    TODO: Implement velocity, volume, and frequency features.
    \"\"\"
    raise NotImplementedError("Not implemented yet")
""",
    "ml/features/behavioural_features.py": "",
    "ml/features/temporal_features.py": "",
    "ml/features/spatial_features.py": "",
    "ml/features/graph_features.py": "",
    
    "ml/candidate_generation/__init__.py": "",
    "ml/candidate_generation/generator.py": """def generate_candidates(case_id: str) -> list:
    \"\"\"
    Generate plausible ATM/location candidates for a case.

    TODO:
    Implement geographic, historical and behavioural candidate generation.
    \"\"\"
    return []
""",

    "ml/training/__init__.py": "",
    "ml/training/train.py": """def train_model(features, labels):
    \"\"\"
    Train the ML model.
    \"\"\"
    raise NotImplementedError("Training not implemented yet")
""",
    "ml/training/evaluate.py": """def evaluate_model(model, features, labels):
    raise NotImplementedError("Evaluation not implemented yet")
""",
    "ml/training/split.py": "",

    "ml/prediction/__init__.py": "",
    "ml/prediction/predictor.py": """def predict_candidates(model, candidates):
    raise NotImplementedError("Prediction not implemented yet")
""",
    "ml/prediction/ranking.py": """def rank_candidates(scores) -> list:
    raise NotImplementedError("Ranking not implemented yet")
""",
    "ml/prediction/time_window.py": """def predict_time_window(case_id: str) -> str:
    raise NotImplementedError("Time window prediction not implemented yet")
""",
    
    "ml/explainability/__init__.py": "",
    "ml/explainability/shap_explainer.py": """def explain_prediction(prediction_data):
    raise NotImplementedError("SHAP explainability not implemented yet")
""",

    "ml/models/.gitkeep": "",
    
    "ml/scripts/generate_data.py": "",
    "ml/scripts/train_model.py": "",
    
    "ml/tests/test_features.py": "",
    "ml/tests/test_candidates.py": "",
    "ml/tests/test_prediction.py": "",
    
    # GRAPH Module
    "graph/README.md": "# Neo4j Graph Queries and Constraints",
    "graph/schema/graph_schema.md": """# Graph Schema
Nodes:
- Complaint
- Account
- Transaction
- Device
- IP
- ATM

Relationships:
- Account -[:TRANSFERRED_TO]-> Account
- Account -[:USED]-> Device
- Account -[:USED]-> IP
- Account -[:PERFORMED]-> Transaction
- Account -[:WITHDREW_AT]-> ATM
""",
    "graph/cypher/create_constraints.cypher": "// Create constraints for unique nodes\n",
    "graph/cypher/seed_data.cypher": "// Seed basic graph structure\n",
    "graph/cypher/sample_queries.cypher": "// Sample graph queries\n",
    "graph/queries/.gitkeep": "",

    # SPATIAL Module
    "spatial/README.md": "# Spatial Subsystem",
    "spatial/h3/h3_service.py": """def lat_lon_to_h3(lat: float, lon: float, resolution: int = 8) -> str:
    \"\"\"Convert latitude and longitude to an H3 cell index.\"\"\"
    raise NotImplementedError("Not implemented")

def get_nearby_cells(h3_index: str, k: int = 1) -> list:
    \"\"\"Get k-ring of nearby H3 cells.\"\"\"
    raise NotImplementedError("Not implemented")
""",
    "spatial/h3/h3_utils.py": "",
    "spatial/postgis/spatial_queries.sql": "-- PostGIS queries stub\n",
    "spatial/geo/distance.py": """def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    \"\"\"Calculate Haversine distance between two points.\"\"\"
    raise NotImplementedError("Not implemented")
""",
    "spatial/geo/preprocessing.py": "",

    # FRONTEND Module
    "frontend/README.md": "# Frontend\nReact Application",
    "frontend/package.json": """{
  "name": "sih26184-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }
}
""",
    "frontend/.env.example": "VITE_API_URL=http://localhost:8000\n",
    "frontend/src/main.jsx": """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
""",
    "frontend/src/App.jsx": """import React from 'react';

function App() {
  return (
    <div>
      <h1>SIH26184 — Predictive Cash-Out Intelligence System</h1>
      <p>Frontend scaffold. API connection, mapping, and routing to be implemented.</p>
    </div>
  );
}

export default App;
""",
    # Components empty files
    "frontend/src/components/layout/.gitkeep": "",
    "frontend/src/components/dashboard/CaseSummary.jsx": "",
    "frontend/src/components/cases/TransactionTimeline.jsx": "",
    "frontend/src/components/predictions/PredictionCard.jsx": "",
    "frontend/src/components/predictions/Top5Table.jsx": "",
    "frontend/src/components/predictions/ExplanationPanel.jsx": "",
    "frontend/src/components/map/PredictiveMap.jsx": "",
    "frontend/src/components/graph/MoneyFlowGraph.jsx": "",
    "frontend/src/components/alerts/AlertCard.jsx": "",
    "frontend/src/components/common/RiskBadge.jsx": "",
    "frontend/src/components/auth/.gitkeep": "",
    
    # Pages empty files
    "frontend/src/pages/CommandCenter.jsx": "",
    "frontend/src/pages/Cases.jsx": "",
    "frontend/src/pages/CaseInvestigation.jsx": "",
    "frontend/src/pages/Prediction.jsx": "",
    "frontend/src/pages/Alerts.jsx": "",
    "frontend/src/pages/AuditLogs.jsx": "",
    "frontend/src/pages/Login.jsx": "",

    # Services
    "frontend/src/services/api.js": """export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
""",
    "frontend/src/services/caseService.js": "",
    "frontend/src/services/predictionService.js": "",
    "frontend/src/services/alertService.js": "",
    
    # Types
    "frontend/src/types/case.ts": "",
    "frontend/src/types/prediction.ts": "",
    "frontend/src/types/alert.ts": "",
    "frontend/src/types/user.ts": "",
    
    # Mock data
    "frontend/src/data/mockPrediction.json": """{
  "case_id": "C10231",
  "risk": "HIGH",
  "time_window": "22:00-23:00",
  "predictions": [
    {
      "rank": 1,
      "atm_id": "ATM-184",
      "probability": 0.82,
      "latitude": 19.076,
      "longitude": 72.877,
      "risk": "HIGH"
    }
  ],
  "explanation": [
    "High recent transaction velocity",
    "Similar historical cash-out behaviour",
    "High-risk connected account"
  ]
}
""",
    # Additional directories
    "frontend/src/hooks/.gitkeep": "",
    "frontend/src/utils/.gitkeep": "",
    "frontend/src/styles/.gitkeep": "",
    "frontend/public/.gitkeep": "",
    
    # DATABASE Module
    "database/README.md": "# Database Migrations and Seeding",
    "database/migrations/.gitkeep": "",
    "database/seed/seed.sql": "-- Placeholder for initial database seed\n",

    # DOCS
    "docs/architecture/.gitkeep": "",
    "docs/api/.gitkeep": "",
    "docs/ml/.gitkeep": "",
    "docs/graph/.gitkeep": "",
    "docs/spatial/.gitkeep": "",
    "docs/frontend/.gitkeep": "",
    "docs/deployment/.gitkeep": "",

    # SCRIPTS
    "scripts/setup.sh": "#!/bin/bash\necho 'Setup script stub'",
    "scripts/run_backend.sh": "#!/bin/bash\ncd backend && uvicorn app.main:app --reload",
    "scripts/run_frontend.sh": "#!/bin/bash\ncd frontend && npm run dev",
    "scripts/health_check.sh": "#!/bin/bash\ncurl -s http://localhost:8000/health",
}

for rel_path, content in structure.items():
    full_path = os.path.join(base_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# create empty folders not covered
empty_dirs = [
    "ml/data/raw",
    "ml/data/processed",
    "ml/data/synthetic",
    "ml/notebooks",
]
for ed in empty_dirs:
    os.makedirs(os.path.join(base_dir, ed), exist_ok=True)

print("Scaffold complete.")
