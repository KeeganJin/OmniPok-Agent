"""FastAPI application entry point."""
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router, set_supervisor
from ..services.agent_service import get_agent_service

# Load environment variables
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

app = FastAPI(
    title="OmniPok Agent Framework",
    description="A flexible multi-agent framework",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    # Initialize agent service and get supervisor
    agent_service = get_agent_service()
    agent_service.initialize()
    supervisor = agent_service.get_supervisor()
    
    # Set supervisor for API routes
    set_supervisor(supervisor)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "OmniPok Agent Framework",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

