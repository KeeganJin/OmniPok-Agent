"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router, set_supervisor
from ..agent.core import InMemoryMemory, global_registry
from ..agent.orchestration import Supervisor, SimpleRouter
from ..agent.tools import http_get, http_post, http_put, http_delete

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
    # Register tools
    global_registry.register(
        name="http_get",
        description="Make an HTTP GET request",
        func=http_get
    )
    global_registry.register(
        name="http_post",
        description="Make an HTTP POST request",
        func=http_post
    )
    global_registry.register(
        name="http_put",
        description="Make an HTTP PUT request",
        func=http_put
    )
    global_registry.register(
        name="http_delete",
        description="Make an HTTP DELETE request",
        func=http_delete
    )
    
    # Initialize supervisor with empty agents list
    # Agents should be added via configuration or API
    router = SimpleRouter()
    supervisor = Supervisor(agents=[], router=router)
    
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

