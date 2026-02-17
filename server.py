from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import strategies
import os

app = FastAPI(title="ArcVault Health Companion")

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "ml_models")
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_DIR = os.path.join(DATA_DIR, "db")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")

# Ensure directories exist
for path in [MODELS_DIR, DB_DIR, UPLOADS_DIR]:
    os.makedirs(path, exist_ok=True)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize strategies
loaded_strategies = {
    "home_triage": strategies.HomeTriageStrategy(),
    "intake": strategies.IntakeStrategy(),
    "consult": strategies.ConsultStrategy(),
    "pharmacy": strategies.PharmacyStrategy(),
    "monitoring": strategies.MonitoringStrategy()
}

class ActionRequest(BaseModel):
    data: Dict[str, Any]

@app.get("/api/strategies")
async def get_strategies():
    """Returns a list of available strategies with their metadata."""
    return [
        {"id": key, **strategy.get_metadata()}
        for key, strategy in loaded_strategies.items()
    ]

@app.post("/api/run/{strategy_id}")
async def run_strategy(strategy_id: str, request: ActionRequest):
    """Executes an action on a specific strategy."""
    if strategy_id not in loaded_strategies:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    strategy = loaded_strategies[strategy_id]
    result = strategy.process_action(request.data)
    return result

# Mount static files (Frontend)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
