# LangGraph Orchestration

基于 LangGraph 的编排系统实现，提供更好的工作流管理、可视化和调试能力。

## 概述

LangGraph 使用状态图（StateGraph）来管理工作流，相比传统的线性编排方式，具有以下优势：

- **可视化**: 自动生成工作流图，便于理解和调试
- **状态管理**: 统一的状态管理，易于追踪
- **条件路由**: 灵活的条件分支和循环
- **调试支持**: 集成 LangSmith，更好的调试体验
- **扩展性**: 易于添加新节点和边

## 安装

确保已安装 LangGraph：

```bash
pip install langgraph>=0.0.20
```

## 使用方式

### 1. LangGraph Supervisor

使用 LangGraph 实现的 Supervisor，管理多个 agent 的任务分配：

```python
from src.agent.orchestration.langgraph import LangGraphSupervisor
from src.agent.core import RunContext, Task
from src.agent.orchestration import SimpleRouter, OrchestrationPolicy

# 创建 agents
agent1 = TextAgent(agent_id="agent-1", name="Agent 1")
agent2 = CodeAgent(agent_id="agent-2", programming_language="python")

# 创建 supervisor
supervisor = LangGraphSupervisor(
    agents=[agent1, agent2],
    router=SimpleRouter(),
    policy=OrchestrationPolicy(),
    max_retries=3
)

# 分配任务
task = Task(id="task-1", description="Write a Python function")
context = RunContext(tenant_id="t1", user_id="u1")

agent_id = await supervisor.assign_task(task, context)
```

### 2. LangGraph GroupChat

使用 LangGraph 实现的多 agent 协作对话：

```python
from src.agent.orchestration.langgraph import LangGraphGroupChat
from src.agent.core import RunContext

# 创建 agents
agent1 = TextAgent(agent_id="agent-1", name="Agent 1")
agent2 = TextAgent(agent_id="agent-2", name="Agent 2")

# 创建 group chat
groupchat = LangGraphGroupChat(
    agents=[agent1, agent2],
    max_rounds=5
)

# 处理消息
context = RunContext(tenant_id="t1", user_id="u1")
responses = await groupchat.process_message(
    message="What is AI?",
    sender_id="user-1",
    context=context
)
```

### 3. 可视化工作流

LangGraph 支持工作流可视化：

```python
# 可视化 supervisor 工作流
supervisor.visualize(output_path="supervisor_graph.png")

# 可视化 group chat 工作流
groupchat.visualize(output_path="groupchat_graph.png")
```

注意：可视化功能需要 IPython，安装方式：
```bash
pip install ipython
```

## 工作流结构

### Supervisor 工作流

```
Entry: route
  ↓
validate (条件分支)
  ├─ continue → execute
  └─ reject → END
  ↓
execute (条件分支)
  ├─ success → END
  ├─ retry → retry → execute
  └─ fail → END
```

### GroupChat 工作流

```
Entry: agent_0
  ↓
agent_1
  ↓
agent_2
  ↓
... (循环)
  ├─ continue → agent_0
  └─ end → END
```

## 状态定义

### SupervisorState

```python
@dataclass
class SupervisorState:
    task: Task
    context: RunContext
    selected_agent: Optional[BaseAgent] = None
    result: Optional[str] = None
    error: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    history: List[Dict] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
```

### GroupChatState

```python
@dataclass
class GroupChatState:
    message: str
    context: RunContext
    agents: List[BaseAgent]
    current_agent_index: int = 0
    responses: List[Dict] = field(default_factory=list)
    conversation_history: List[Message] = field(default_factory=list)
    round: int = 0
    max_rounds: int = 10
    should_continue: bool = True
```

## 节点实现

系统包含以下节点：

- **route_node**: 路由节点，选择合适的 agent
- **validate_node**: 验证节点，检查任务是否可以分配
- **execute_node**: 执行节点，运行 agent 处理任务
- **retry_node**: 重试节点，处理失败重试
- **agent_node**: Agent 节点，处理 group chat 中的消息

## 向后兼容

LangGraph 实现保持了与现有接口的兼容性：

- `LangGraphSupervisor` 实现了与 `Supervisor` 相同的接口
- `LangGraphGroupChat` 实现了与 `GroupChat` 相同的接口
- 可以无缝替换现有实现

## 迁移指南

### 从 Supervisor 迁移到 LangGraphSupervisor

```python
# 旧代码
from src.agent.orchestration import Supervisor
supervisor = Supervisor(agents=[...], router=...)

# 新代码
from src.agent.orchestration.langgraph import LangGraphSupervisor
supervisor = LangGraphSupervisor(agents=[...], router=...)

# API 保持不变
agent_id = await supervisor.assign_task(task, context)
```

### 从 GroupChat 迁移到 LangGraphGroupChat

```python
# 旧代码
from src.agent.orchestration import GroupChat
groupchat = GroupChat(agents=[...])

# 新代码
from src.agent.orchestration.langgraph import LangGraphGroupChat
groupchat = LangGraphGroupChat(agents=[...])

# API 保持不变
responses = await groupchat.process_message(message, sender_id, context)
```

## 示例

查看 `examples/langgraph_orchestration_example.py` 获取完整的使用示例。

## 注意事项

1. **依赖**: 需要安装 `langgraph>=0.0.20`
2. **可视化**: 可视化功能需要 `ipython`
3. **状态追踪**: 当前实现中，任务历史存储在状态中，跨执行的状态追踪需要额外实现
4. **性能**: LangGraph 添加了状态管理开销，但对于复杂工作流，整体性能更好

## 未来扩展

- [ ] 持久化状态追踪
- [ ] 更复杂的条件路由
- [ ] 并行执行支持
- [ ] 与 LangSmith 集成
- [ ] 工作流版本管理

