# OmniPok Agent Framework

A flexible and extensible multi-agent framework built with Python and FastAPI.

## Features

- **Multi-Agent Support**: Create and manage multiple specialized agents
- **Tool System**: Extensible tool registry with permission-based access control
- **Memory Management**: Pluggable memory backends (in-memory, Redis, vector stores)
- **Orchestration**: Supervisor pattern for task routing and coordination
- **Group Chat**: Multi-agent collaboration and conversation
- **REST API**: FastAPI-based RESTful API for agent interactions
- **Web UI**: Chainlit and Gradio interfaces for interactive agent chat
- **Context Management**: Run context with budget, timeout, and step limits

## Project Structure

```
src/
├─ app/                         # FastAPI/Chainlit入口
│  ├─ api/                      # FastAPI routes
│  ├─ ui/                       # UI interfaces
│  │  ├─ chainlit_app.py        # Chainlit UI
│  │  ├─ gradio_app.py          # Gradio UI
│  │  └─ chainlit_main.py       # Chainlit entry point
│  └─ main.py                   # FastAPI app entry
├─ agent/
│  ├─ core/                     # 核心抽象和接口
│  │  ├─ base.py                # BaseAgent 抽象类
│  │  ├─ context.py             # RunContext
│  │  ├─ types.py               # 类型定义
│  │  ├─ tool_registry.py       # 工具注册系统
│  │  └─ memory.py              # 内存接口
│  ├─ tools/                     # 工具实现
│  │  ├─ http.py                # HTTP 工具
│  │  └─ db.py                  # 数据库工具
│  ├─ agents/                    # Agent 实现
│  │  ├─ base_agent_impl.py     # 基础实现
│  │  └─ support_agent.py       # 支持 Agent
│  └─ orchestration/            # 编排系统
│     ├─ router.py              # 任务路由
│     ├─ supervisor.py          # Supervisor
│     ├─ groupchat.py           # 群聊
│     └─ policies.py            # 策略
├─ llm/                         # LLM 集成
├─ observability/               # 可观测性
└─ common/                      # 通用工具
```

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Basic Usage

```python
from src.agent.core import RunContext, InMemoryMemory, global_registry
from src.agent.agents import BaseAgentImpl
from src.agent.tools import http_get

# Register a tool
global_registry.register(
    name="http_get",
    description="Make an HTTP GET request",
    func=http_get
)

# Create an agent (requires LLM client)
memory = InMemoryMemory()
agent = BaseAgentImpl(
    agent_id="agent-1",
    name="My Agent",
    llm_client=your_llm_client,  # Implement your LLM client
    memory=memory,
    tool_registry=global_registry
)

# Create context
context = RunContext(
    tenant_id="tenant-1",
    user_id="user-1",
    budget=10.0,
    max_steps=10
)

# Process a message
response = await agent.process("Hello, world!", context)
print(response)
```

### 2. Using Supervisor

```python
from src.agent.orchestration import Supervisor, SimpleRouter
from src.agent.core import RunContext, Task

# Create supervisor
supervisor = Supervisor(
    agents=[agent1, agent2, agent3],
    router=SimpleRouter()
)

# Create and assign a task
task = Task(id="task-1", description="Process this task")
context = RunContext(tenant_id="t1", user_id="u1")
agent_id = await supervisor.assign_task(task, context)
```

### 3. Running the API

```bash
uvicorn src.app.main:app --reload
```

Then visit `http://localhost:8000/docs` for API documentation.

### 4. Running Chainlit UI

**Option 1: Using the convenience script (recommended)**
```bash
python run_chainlit.py
```

**Option 2: Using chainlit directly**
```bash
# From project root
chainlit run src/app/ui/chainlit_main.py
```

**Option 3: Using python module**
```bash
# From project root
python -m chainlit run src/app/ui/chainlit_main.py
```

Then visit `http://localhost:8000` (default Chainlit port).

### 5. Running Gradio UI

```bash
python src/app/ui/gradio_main.py
```

Or with custom options:

```bash
python src/app/ui/gradio_main.py --port 7860 --host 0.0.0.0 --share
```

Then visit `http://localhost:7860`.

## API Endpoints

- `POST /api/v1/chat` - Chat with an agent
- `POST /api/v1/tasks` - Create and assign a task
- `GET /api/v1/tasks/{task_id}` - Get task status
- `GET /api/v1/agents` - List all agents

## UI Features

### Chainlit UI
- Interactive chat interface
- Agent selection
- Real-time conversation
- Usage statistics display

### Gradio UI
- Web-based chat interface
- Agent dropdown selection
- Conversation history
- Agent information display

## Extending the Framework

### Creating a Custom Agent

```python
from src.agent.core import BaseAgent
from src.agent.core.types import Message, ToolCall, Observation
from src.agent.core.context import RunContext

class MyCustomAgent(BaseAgent):
    async def process(self, message: str, context: RunContext) -> str:
        # Your implementation
        return "Response"
    
    async def execute_tool_call(self, tool_call: ToolCall, context: RunContext) -> Observation:
        # Your implementation
        pass
```

### Adding a Tool

```python
from src.agent.tools import global_registry

async def my_tool(param1: str, param2: int) -> dict:
    """Tool description."""
    return {"result": "success"}

global_registry.register(
    name="my_tool",
    description="My custom tool",
    func=my_tool,
    required_permissions=["permission1"]
)
```

### Custom Memory Backend

```python
from src.agent.core.memory import Memory
from src.agent.core.types import AgentState, Message

class MyMemoryBackend(Memory):
    def save(self, agent_id: str, state: AgentState) -> None:
        # Your implementation
        pass
    
    # Implement other required methods
```

## License

MIT
