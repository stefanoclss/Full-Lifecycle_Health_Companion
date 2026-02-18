from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import strategies
import os
from utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ArcVault Health Companion Server...")
    yield
    logger.info("Shutting down ArcVault Health Companion Server...")

app = FastAPI(title="ArcVault Health Companion", lifespan=lifespan)

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



# ... strategies init ...

@app.post("/api/run/{strategy_id}")
async def run_strategy(strategy_id: str, request: ActionRequest):
    """Executes an action on a specific strategy."""
    logger.info(f"API Request: Run Strategy '{strategy_id}'")
    
    if strategy_id not in loaded_strategies:
        logger.warning(f"Strategy '{strategy_id}' not found")
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    strategy = loaded_strategies[strategy_id]
    try:
        result = strategy.process_action(request.data)
        logger.info(f"Strategy '{strategy_id}' executed successfully")
        return result
    except Exception as e:
        logger.error(f"Error executing strategy '{strategy_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ... mount static ...

# Serve static files with no-cache headers for development
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

class NoCacheStaticMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.endswith('.js') or request.url.path.endswith('.html'):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheStaticMiddleware)

# Mount static files (MUST be last to not override API routes)
app.mount("/", StaticFiles(directory=os.path.join(BASE_DIR, "static"), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Note: reloader might cause double logging on startup, acceptable for dev
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
