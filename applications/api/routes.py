"""FastAPI routes for the agent framework."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid

from omnipok_agent.core import RunContext, Task, TaskStatus
from omnipok_agent.orchestration import Supervisor

router = APIRouter(prefix="/api/v1", tags=["agents"])


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message")
    agent_id: Optional[str] = Field(None, description="Specific agent ID to use")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: str = Field(..., description="User ID")
    budget: Optional[float] = Field(None, description="Budget limit")
    max_steps: Optional[int] = Field(None, description="Maximum steps")
    timeout: Optional[float] = Field(None, description="Timeout in seconds")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    agent_id: str
    request_id: str
    tokens_used: int
    cost_incurred: float
    steps_taken: int


class TaskRequest(BaseModel):
    """Request model for task endpoint."""
    description: str = Field(..., description="Task description")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: str = Field(..., description="User ID")
    budget: Optional[float] = Field(None, description="Budget limit")
    max_steps: Optional[int] = Field(None, description="Maximum steps")
    timeout: Optional[float] = Field(None, description="Timeout in seconds")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class TaskResponse(BaseModel):
    """Response model for task endpoint."""
    task_id: str
    status: TaskStatus
    assigned_agent: Optional[str]
    result: Optional[str]
    error: Optional[str]


# Dependency to get supervisor instance
# In production, this would be injected via dependency injection
_supervisor: Optional[Supervisor] = None


def get_supervisor() -> Supervisor:
    """Get supervisor instance."""
    if _supervisor is None:
        raise HTTPException(status_code=500, detail="Supervisor not initialized")
    return _supervisor


def set_supervisor(supervisor: Supervisor) -> None:
    """Set supervisor instance."""
    global _supervisor
    _supervisor = supervisor


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    supervisor: Supervisor = Depends(get_supervisor)
):
    """
    Chat with an agent.
    
    Args:
        request: Chat request
        supervisor: Supervisor instance
        
    Returns:
        Chat response
    """
    # Create context
    context = RunContext(
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        budget=request.budget,
        max_steps=request.max_steps,
        timeout=request.timeout,
        metadata=request.metadata
    )
    
    # Get agent
    if request.agent_id:
        agent = supervisor.get_agent(request.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
    else:
        # Use first available agent
        agents = supervisor.list_agents()
        if not agents:
            raise HTTPException(status_code=503, detail="No agents available")
        agent = agents[0]
    
    # Process message
    try:
        response = await agent.process(request.message, context)
        
        return ChatResponse(
            response=response,
            agent_id=agent.agent_id,
            request_id=context.request_id,
            tokens_used=context.tokens_used,
            cost_incurred=context.cost_incurred,
            steps_taken=context.steps_taken
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    request: TaskRequest,
    supervisor: Supervisor = Depends(get_supervisor)
):
    """
    Create and assign a task.
    
    Args:
        request: Task request
        supervisor: Supervisor instance
        
    Returns:
        Task response
    """
    # Create task
    task = Task(
        id=str(uuid.uuid4()),
        description=request.description
    )
    
    # Create context
    context = RunContext(
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        budget=request.budget,
        max_steps=request.max_steps,
        timeout=request.timeout,
        metadata=request.metadata
    )
    
    # Assign task
    await supervisor.assign_task(task, context)
    
    return TaskResponse(
        task_id=task.id,
        status=task.status,
        assigned_agent=task.assigned_agent,
        result=str(task.result) if task.result else None,
        error=task.error
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    supervisor: Supervisor = Depends(get_supervisor)
):
    """
    Get task status.
    
    Args:
        task_id: Task ID
        supervisor: Supervisor instance
        
    Returns:
        Task response
    """
    task = supervisor.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return TaskResponse(
        task_id=task.id,
        status=task.status,
        assigned_agent=task.assigned_agent,
        result=str(task.result) if task.result else None,
        error=task.error
    )


@router.get("/agents")
async def list_agents(supervisor: Supervisor = Depends(get_supervisor)):
    """
    List all available agents.
    
    Args:
        supervisor: Supervisor instance
        
    Returns:
        List of agents
    """
    agents = supervisor.list_agents()
    return {
        "agents": [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "available_tools": len(agent.get_available_tools())
            }
            for agent in agents
        ]
    }

