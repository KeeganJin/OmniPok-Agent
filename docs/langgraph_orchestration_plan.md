# LangGraph Orchestration 重构方案

## 概述

使用 LangGraph 重构 orchestration 系统，利用其状态图（StateGraph）来管理多agent工作流，提供更好的可视化、调试和扩展能力。

## 当前架构分析

### 现有组件

1. **Supervisor**: 管理多个agent，分配任务
2. **Router**: 路由任务到合适的agent
3. **GroupChat**: 多agent协作对话
4. **Policies**: 预算、权限、重试策略

### 当前限制

- 工作流是线性的，难以表达复杂的分支和循环
- 状态管理分散，难以追踪
- 缺乏可视化工具
- 调试困难

## LangGraph 架构设计

### 核心概念

- **StateGraph**: 状态图，定义工作流结构
- **Nodes**: 节点（agent执行逻辑）
- **Edges**: 边（条件路由）
- **State**: 共享状态

### 新架构

```
src/agent/orchestration/
├── __init__.py
├── langgraph/                    # LangGraph实现（新增）
│   ├── __init__.py
│   ├── supervisor_graph.py       # Supervisor状态图
│   ├── groupchat_graph.py        # GroupChat状态图
│   ├── state.py                  # 状态定义
│   └── nodes.py                  # 节点实现
├── supervisor.py                 # 保留（兼容层）
├── router.py                     # 保留
├── policies.py                   # 保留
└── groupchat.py                  # 保留（兼容层）
```

## 实现方案

### 1. Supervisor状态图

使用LangGraph StateGraph实现Supervisor：

```python
# 状态定义
@dataclass
class SupervisorState:
    task: Task
    context: RunContext
    selected_agent: Optional[BaseAgent] = None
    result: Optional[str] = None
    error: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    history: List[Dict] = field(default_factory=list)

# 状态图结构
graph = StateGraph(SupervisorState)
graph.add_node("route", route_node)      # 路由节点
graph.add_node("validate", validate_node) # 验证节点
graph.add_node("execute", execute_node)   # 执行节点
graph.add_node("retry", retry_node)       # 重试节点

# 边定义
graph.set_entry_point("route")
graph.add_edge("route", "validate")
graph.add_conditional_edges(
    "validate",
    should_continue,  # 条件函数
    {
        "continue": "execute",
        "reject": END
    }
)
graph.add_conditional_edges(
    "execute",
    check_result,
    {
        "success": END,
        "retry": "retry",
        "fail": END
    }
)
```

### 2. GroupChat状态图

使用LangGraph实现多agent协作：

```python
# 状态定义
@dataclass
class GroupChatState:
    message: str
    context: RunContext
    agents: List[BaseAgent]
    current_agent_index: int = 0
    responses: List[Dict] = field(default_factory=list)
    conversation_history: List[Message] = field(default_factory=list)
    round: int = 0
    should_continue: bool = True

# 状态图结构
graph = StateGraph(GroupChatState)
for agent in agents:
    graph.add_node(f"agent_{agent.agent_id}", create_agent_node(agent))

# 循环结构
graph.add_edge("start", "agent_0")
for i in range(len(agents) - 1):
    graph.add_edge(f"agent_{i}", f"agent_{i+1}")
graph.add_conditional_edges(
    f"agent_{len(agents)-1}",
    should_continue_conversation,
    {
        "continue": "agent_0",  # 循环
        "end": END
    }
)
```

### 3. 节点实现

```python
async def route_node(state: SupervisorState) -> SupervisorState:
    """路由节点：选择agent"""
    router = state.context.metadata.get("router")
    selected = router.route(state.task, available_agents)
    state.selected_agent = selected
    return state

async def execute_node(state: SupervisorState) -> SupervisorState:
    """执行节点：运行agent"""
    if not state.selected_agent:
        state.status = TaskStatus.FAILED
        return state
    
    try:
        result = await state.selected_agent.process(
            state.task.description,
            state.context
        )
        state.result = result
        state.status = TaskStatus.COMPLETED
    except Exception as e:
        state.error = str(e)
        state.status = TaskStatus.FAILED
    
    return state
```

### 4. 兼容层

为了保持向后兼容，创建适配器：

```python
class LangGraphSupervisor:
    """LangGraph实现的Supervisor，兼容现有接口"""
    
    def __init__(self, agents, router, policy):
        self.graph = build_supervisor_graph(agents, router, policy)
        self.compiled = self.graph.compile()
    
    async def assign_task(self, task, context):
        """兼容现有接口"""
        initial_state = SupervisorState(task=task, context=context)
        result = await self.compiled.ainvoke(initial_state)
        return result.selected_agent.agent_id if result.status == TaskStatus.COMPLETED else None
```

## 优势

1. **可视化**: LangGraph提供工作流可视化
2. **状态管理**: 统一的状态管理，易于追踪
3. **条件路由**: 灵活的条件分支和循环
4. **调试**: 集成LangSmith，更好的调试体验
5. **扩展性**: 易于添加新节点和边

## 迁移策略

### 阶段1: 并行实现
- 实现LangGraph版本
- 保留现有实现
- 通过配置选择使用哪个版本

### 阶段2: 逐步迁移
- 新功能使用LangGraph
- 现有功能保持兼容
- 提供迁移工具

### 阶段3: 完全迁移
- 移除旧实现
- 统一使用LangGraph

## 依赖更新

需要在 `pyproject.toml` 中添加：

```toml
dependencies = [
    # ... 现有依赖
    "langgraph>=0.0.20",
]
```

## 示例代码

### 使用LangGraph Supervisor

```python
from src.agent.orchestration.langgraph import LangGraphSupervisor
from src.agent.core import RunContext, Task

# 创建supervisor
supervisor = LangGraphSupervisor(
    agents=[agent1, agent2, agent3],
    router=SimpleRouter(),
    policy=OrchestrationPolicy()
)

# 分配任务
task = Task(id="task-1", description="Process this")
context = RunContext(tenant_id="t1", user_id="u1")
agent_id = await supervisor.assign_task(task, context)
```

### 使用LangGraph GroupChat

```python
from src.agent.orchestration.langgraph import LangGraphGroupChat

# 创建group chat
groupchat = LangGraphGroupChat(
    agents=[agent1, agent2, agent3],
    memory=memory_manager
)

# 处理消息
responses = await groupchat.process_message(
    message="Hello everyone",
    sender_id="user-1",
    context=context
)
```

## 实施步骤

1. ✅ 添加LangGraph依赖
2. ✅ 定义状态结构
3. ✅ 实现Supervisor状态图
4. ✅ 实现GroupChat状态图
5. ✅ 创建兼容层
6. ✅ 更新文档和示例
7. ✅ 测试和验证

## 注意事项

- 保持现有API接口不变
- 提供平滑的迁移路径
- 确保性能不降低
- 充分利用LangGraph的特性（可视化、调试等）

