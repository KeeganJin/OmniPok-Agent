"""LangGraph-based supervisor implementation."""
from typing import List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from ...core.base import BaseAgent
from ...core.context import RunContext
from ...core.types import Task, TaskStatus
from ...orchestration.router import Router, SimpleRouter
from ...orchestration.policies import OrchestrationPolicy
from .state import SupervisorState
from .nodes import route_node, validate_node, execute_node, retry_node


def should_continue(state: SupervisorState) -> str:
    """
    Conditional edge function: Determine if validation should continue.
    
    Args:
        state: Current supervisor state
        
    Returns:
        "continue" if validation passed, "reject" otherwise
    """
    if state.status == TaskStatus.FAILED:
        return "reject"
    return "continue"


def check_result(state: SupervisorState) -> str:
    """
    Conditional edge function: Check execution result and decide next step.
    
    Args:
        state: Current supervisor state
        
    Returns:
        "success" if completed, "retry" if should retry, "fail" otherwise
    """
    if state.status == TaskStatus.COMPLETED:
        return "success"
    
    if state.status == TaskStatus.FAILED:
        # Check if should retry
        policy = state.context.metadata.get("policy")
        if policy and policy.retry_policy:
            if state.retry_count < state.max_retries:
                if policy.retry_policy.should_retry(state.error or "", state.retry_count):
                    return "retry"
        return "fail"
    
    return "fail"


def build_supervisor_graph(
    agents: List[BaseAgent],
    router: Optional[Router] = None,  # noqa: ARG001
    policy: Optional[OrchestrationPolicy] = None  # noqa: ARG001
) -> StateGraph:
    """
    Build the supervisor state graph.
    
    Args:
        agents: List of agents to manage
        router: Router for task assignment
        policy: Orchestration policy
        
    Returns:
        Compiled state graph
    """
    # Create graph
    graph = StateGraph(SupervisorState)
    
    # Add nodes
    graph.add_node("route", route_node)
    graph.add_node("validate", validate_node)
    graph.add_node("execute", execute_node)
    graph.add_node("retry", retry_node)
    
    # Define edges
    graph.set_entry_point("route")
    graph.add_edge("route", "validate")
    
    # Conditional edge: validate -> execute or reject
    graph.add_conditional_edges(
        "validate",
        should_continue,
        {
            "continue": "execute",
            "reject": END
        }
    )
    
    # Conditional edge: execute -> success, retry, or fail
    graph.add_conditional_edges(
        "execute",
        check_result,
        {
            "success": END,
            "retry": "retry",
            "fail": END
        }
    )
    
    # Retry edge: retry -> execute
    graph.add_edge("retry", "execute")
    
    return graph


class LangGraphSupervisor:
    """
    LangGraph-based supervisor for managing multiple agents.
    
    This implementation uses LangGraph StateGraph to manage the orchestration
    workflow, providing better visualization, debugging, and state management.
    """
    
    def __init__(
        self,
        agents: List[BaseAgent],
        router: Optional[Router] = None,
        policy: Optional[OrchestrationPolicy] = None,
        max_retries: int = 3
    ):
        """
        Initialize LangGraph supervisor.
        
        Args:
            agents: List of agents to manage
            router: Router for task assignment (default: SimpleRouter)
            policy: Orchestration policy
            max_retries: Maximum number of retries
        """
        self.agents = {agent.agent_id: agent for agent in agents}
        self.router = router or SimpleRouter()
        self.policy = policy
        self.max_retries = max_retries
        
        # Build and compile graph
        self.graph = build_supervisor_graph(agents, router, policy)
        self.compiled = self.graph.compile()
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register a new agent."""
        self.agents[agent.agent_id] = agent
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[BaseAgent]:
        """List all registered agents."""
        return list(self.agents.values())
    
    async def assign_task(
        self,
        task: Task,
        context: RunContext
    ) -> Optional[str]:
        """
        Assign a task to an appropriate agent using LangGraph.
        
        Args:
            task: The task to assign
            context: The run context
            
        Returns:
            Agent ID if task was assigned successfully, None otherwise
        """
        # Prepare context metadata
        context.metadata = context.metadata or {}
        context.metadata["router"] = self.router
        context.metadata["policy"] = self.policy
        context.metadata["available_agents"] = list(self.agents.values())
        
        # Create initial state
        initial_state = SupervisorState(
            task=task,
            context=context,
            max_retries=self.max_retries
        )
        
        # Execute graph
        try:
            final_state = await self.compiled.ainvoke(initial_state)
            
            if final_state.status == TaskStatus.COMPLETED:
                return final_state.selected_agent.agent_id if final_state.selected_agent else None
            else:
                return None
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            return None
    
    def get_task(self, task_id: str) -> Optional[Task]:  # noqa: ARG002
        """Get a task by ID (for compatibility, tasks are stored in state)."""
        # Note: In LangGraph implementation, tasks are managed through state
        # This method is kept for compatibility but may need state tracking
        return None
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:  # noqa: ARG002
        """List all tasks (for compatibility)."""
        # Note: In LangGraph implementation, tasks are managed through state
        # This method is kept for compatibility but may need state tracking
        return []
    
    def visualize(self, output_path: Optional[str] = None) -> None:
        """
        Visualize the supervisor graph.
        
        Args:
            output_path: Optional path to save the visualization
        """
        try:
            from IPython.display import Image, display
            
            # Generate visualization
            image = self.graph.get_graph().draw_mermaid_png()
            
            if output_path:
                with open(output_path, "wb") as f:
                    f.write(image)
            
            display(Image(image))
        except ImportError:
            print("IPython not available. Install with: pip install ipython")
        except Exception as e:
            print(f"Visualization error: {e}")

