# Memory System

记忆系统为Agent提供短时记忆和长时记忆功能，支持会话级别的临时存储和持久化存储。

## 架构

记忆系统包含以下组件：

- **ShortTermMemory**: 短时记忆，使用内存存储，适合会话期间的临时信息
- **LongTermMemory**: 长时记忆，使用SQLite持久化存储，适合重要信息的长期保存
- **MemoryManager**: 记忆管理器，统一管理短时和长时记忆，自动决定存储策略

## 快速开始

### 1. 使用短时记忆

```python
from src.agent.memory import ShortTermMemory
from src.agent.core.types import Message, MessageRole

# 创建短时记忆（最多存储100条消息）
memory = ShortTermMemory(max_messages=100)

# 添加消息
message = Message(role=MessageRole.USER, content="Hello")
memory.add_message("agent-1", message)

# 获取消息
messages = memory.get_messages("agent-1", limit=10)
```

### 2. 使用长时记忆

```python
from src.agent.memory import LongTermMemory
from src.agent.core.types import Message, MessageRole

# 创建长时记忆（使用SQLite持久化）
memory = LongTermMemory(
    db_path="data/agent_memory.db",  # 可选，默认在data目录
    default_importance=50  # 默认重要性评分
)

# 添加重要消息
message = Message(role=MessageRole.USER, content="Important info")
memory.add_message("agent-1", message, importance=80)

# 获取消息（支持按时间、重要性筛选）
from datetime import datetime, timedelta
since = datetime.now() - timedelta(days=7)
messages = memory.get_messages(
    "agent-1",
    limit=50,
    since=since,
    min_importance=60
)
```

### 3. 使用记忆管理器（推荐）

```python
from src.agent.memory import MemoryManager
from src.agent.core.types import Message, MessageRole
from src.agent.agents import TextAgent

# 创建记忆管理器
memory = MemoryManager(
    auto_archive_threshold=50,  # 短时记忆满50条时自动归档
    importance_threshold=30     # 重要性>=30的消息会保存到长时记忆
)

# 在Agent中使用
agent = TextAgent(
    agent_id="my-agent",
    memory=memory,
    # ... 其他参数
)

# 记忆管理器会自动：
# - 所有消息存储在短时记忆（快速访问）
# - 重要消息同时保存到长时记忆（持久化）
# - 自动合并短时和长时记忆的查询结果
```

## 特性

### 短时记忆（ShortTermMemory）

- ✅ 快速的内存存储
- ✅ 自动限制消息数量（防止内存溢出）
- ✅ 会话级别，进程重启后丢失
- ✅ 适合临时对话历史

### 长时记忆（LongTermMemory）

- ✅ SQLite持久化存储
- ✅ 支持按时间、重要性查询
- ✅ 跨会话持久化
- ✅ 支持消息归档和清理
- ✅ 为未来向量数据库集成预留接口

### 记忆管理器（MemoryManager）

- ✅ 统一接口，自动管理短时和长时记忆
- ✅ 智能重要性评估
- ✅ 自动归档机制
- ✅ 合并查询结果
- ✅ 完全兼容现有Memory接口

## 重要性评分

系统会自动评估消息的重要性（0-100分）：

- **系统消息**: 80分
- **用户消息**: 50分（长消息+10分）
- **带工具调用的助手消息**: 60分
- **元数据标记**: 根据metadata中的`important`或`importance`字段

只有重要性 >= `importance_threshold` 的消息才会保存到长时记忆。

## 数据库结构

SQLite数据库包含以下表：

- **messages**: 存储所有消息
- **agent_states**: 存储Agent状态
- **memory_summaries**: 存储记忆摘要（预留）

## 向后兼容

新的记忆系统完全兼容现有的`Memory`接口，现有代码无需修改即可使用：

```python
# 现有代码仍然有效
from src.agent.core import InMemoryMemory
memory = InMemoryMemory()

# 新代码可以使用新的记忆系统
from src.agent.memory import MemoryManager
memory = MemoryManager()
```

两者都实现了相同的`Memory`接口，可以互换使用。

## 示例

查看 `examples/memory_example.py` 获取完整的使用示例。

## 未来扩展

- [ ] 向量数据库支持（用于语义搜索）
- [ ] 记忆摘要和压缩
- [ ] 记忆检索优化
- [ ] 多租户支持
- [ ] 记忆分析工具

