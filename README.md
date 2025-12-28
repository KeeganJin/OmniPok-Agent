# OmniPok Agent Framework

一个灵活且可扩展的多智能体框架，基于 Python 和 FastAPI 构建。

## 初步的交互界面
[初步交互界面](./images/UI.png)

## Todo
[] !! Update Tool USE!! 目前tool use部分出了一点小小小小bug。。。



## ✨ 特性

- 🤖 **多智能体支持**：创建和管理多个专业化的智能体
- 🔧 **工具系统**：可扩展的工具注册表，支持基于权限的访问控制
- 💾 **内存管理**：可插拔的内存后端（内存、SQLite、向量存储）
- 🎯 **任务编排**：Supervisor 模式实现任务路由和协调
- 💬 **群聊功能**：多智能体协作和对话
- 🌐 **REST API**：基于 FastAPI 的 RESTful API
- 🎨 **Web UI**：Chainlit 交互式聊天界面，支持多模态
- 📊 **上下文管理**：支持预算、超时和步骤限制的运行上下文
- 📚 **RAG 支持**：检索增强生成，支持知识库管理和文档问答

## 📁 项目结构

```
OmniPok-Agent/
├── omnipok_agent/              # 主框架包（领域驱动设计）
│   ├── core/                   # 核心抽象和基础类型
│   │   ├── base.py            # BaseAgent 抽象类
│   │   ├── context.py         # RunContext
│   │   ├── types.py           # 类型定义
│   │   └── exceptions.py      # 异常类
│   ├── agents/                 # Agent 实现
│   │   ├── text_agent.py
│   │   ├── code_agent.py
│   │   ├── chat_agent.py
│   │   └── ...
│   ├── orchestration/          # 编排系统
│   │   ├── supervisor.py
│   │   ├── router.py
│   │   ├── groupchat.py
│   │   └── langgraph/         # LangGraph 实现
│   ├── tools/                  # 工具实现
│   │   ├── registry.py        # 工具注册表
│   │   ├── http.py
│   │   └── db.py
│   ├── memory/                 # 内存管理
│   │   ├── base.py
│   │   ├── in_memory.py
│   │   ├── short_term.py
│   │   ├── long_term.py
│   │   └── manager.py
│   ├── llm/                    # LLM 集成
│   │   └── omnipok_llm.py
│   ├── rag/                    # RAG 模块
│   │   ├── document.py        # 文档数据模型
│   │   ├── loader.py          # 文档加载器
│   │   ├── splitter.py        # 文本分割器
│   │   ├── embedding.py       # 嵌入模型
│   │   ├── vector_store.py    # 向量存储
│   │   ├── retriever.py       # 检索器
│   │   ├── knowledge_base.py  # 知识库管理器
│   │   └── rag_agent.py       # RAG Agent
│   └── config/                 # 配置管理
│       └── agent_config.py
│
├── applications/                # 应用层
│   ├── api/                    # FastAPI 应用
│   │   ├── main.py
│   │   └── routes.py
│   ├── ui/                     # Chainlit UI
│   │   ├── chainlit_app.py
│   │   └── chainlit_main.py
│   └── services/               # 服务层
│       └── agent_service.py
│
├── examples/                    # 示例代码
├── config/                      # 配置文件
└── tests/                       # 测试目录
```


## 🚀 快速开始

### 1. 安装

```bash
# 克隆仓库（如果从 Git 克隆）
git clone <repository-url>
cd OmniPok-Agent

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件（项目根目录）：

```bash
# LLM 配置（至少配置一个）
OPENAI_API_KEY=your-openai-api-key-here
LLM_MODEL_ID=gpt-4
LLM_BASE_URL=https://api.openai.com/v1

# 或者使用其他提供商
# DASHSCOPE_API_KEY=your-dashscope-key  # 阿里云通义千问
# DEEPSEEK_API_KEY=your-deepseek-key    # DeepSeek
```

### 3. 基本使用示例

创建 `example.py`：

```python
import asyncio
from omnipok_agent.core import BaseAgent, RunContext
from omnipok_agent.memory import InMemoryMemory
from omnipok_agent.llm import OmniPokLLM

async def main():
    # 创建 LLM 实例（自动检测环境变量配置）
    llm = OmniPokLLM()
    
    # 创建智能体
    agent = BaseAgent(
        agent_id="my-agent",
        name="我的助手",
        llm=llm,
        system_prompt="你是一个有用的AI助手",
        memory=InMemoryMemory()
    )
    
    # 创建运行上下文
    context = RunContext(
        tenant_id="tenant-1",
        user_id="user-1",
        budget=10.0,
        max_steps=10
    )
    
    # 处理消息
    response = await agent.process("你好，请介绍一下你自己", context)
    print(f"回复: {response}")
    print(f"使用的Token: {context.tokens_used}")
    print(f"成本: ${context.cost_incurred:.4f}")

if __name__ == "__main__":
    asyncio.run(main())
```

运行：

```bash
python example.py
```

### 4. 使用预定义的 Agent

```python
import asyncio
from omnipok_agent.agents import TextAgent
from omnipok_agent.core import RunContext
from omnipok_agent.llm import OmniPokLLM

async def main():
    # 创建文本处理 Agent
    agent = TextAgent(
        agent_id="text-agent-1",
        llm=OmniPokLLM(),
        system_prompt="你是一个专业的文本处理助手"
    )
    
    context = RunContext(tenant_id="t1", user_id="u1")
    response = await agent.process("请总结一下人工智能的发展历史", context)
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

### 5. 使用工具

```python
import asyncio
from omnipok_agent.core import BaseAgent, RunContext
from omnipok_agent.tools import global_registry, http_get
from omnipok_agent.llm import OmniPokLLM
from omnipok_agent.memory import InMemoryMemory

async def main():
    # 注册工具
    global_registry.register(tool=http_get)
    
    # 创建带工具的 Agent
    agent = BaseAgent(
        agent_id="tool-agent",
        name="工具助手",
        llm=OmniPokLLM(),
        memory=InMemoryMemory(),
        tool_registry=global_registry
    )
    
    context = RunContext(tenant_id="t1", user_id="u1")
    # Agent 现在可以使用 http_get 工具
    response = await agent.process(
        "请访问 https://api.github.com 并获取信息",
        context
    )
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🌐 运行 Web 应用

### 启动 FastAPI 服务

```bash
uvicorn applications.api.main:app --reload
```

然后访问：
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 启动 Chainlit UI

**方式一：使用便捷脚本（推荐）**

```bash
python run_chainlit.py
```

**方式二：直接使用 chainlit**

```bash
chainlit run applications/ui/chainlit_main.py
```

然后访问 http://localhost:8000 开始聊天。

## ⚙️ 配置 Agent

### 方式一：使用配置文件（推荐）

创建 `config/agents.json`（参考 `config/agents.json.example`）：

```json
{
  "defaults": {
    "llm_provider": "openai",
    "llm_model": "gpt-4",
    "llm_api_key_env": "OPENAI_API_KEY"
  },
  "agents": [
    {
      "agent_type": "TextAgent",
      "agent_id": "text-agent-1",
      "name": "文本处理助手",
      "enabled": true
    },
    {
      "agent_type": "CodeAgent",
      "agent_id": "code-agent-1",
      "name": "代码助手",
      "programming_language": "python",
      "enabled": true
    }
  ]
}
```

### 方式二：环境变量

```bash
export OPENAI_API_KEY="your-api-key"
export DEFAULT_LLM_MODEL="gpt-4"
export AGENTS_CONFIG='[{"agent_type":"TextAgent","agent_id":"text-agent-1","name":"Text Agent","enabled":true}]'
```

## 📚 API 端点

- `POST /api/v1/chat` - 与 Agent 聊天
- `POST /api/v1/tasks` - 创建和分配任务
- `GET /api/v1/tasks/{task_id}` - 获取任务状态
- `GET /api/v1/agents` - 列出所有 Agent

## 🔧 扩展框架

### 创建自定义 Agent

```python
from omnipok_agent.core import BaseAgent
from omnipok_agent.core.types import Message, ToolCall, Observation
from omnipok_agent.core import RunContext

class MyCustomAgent(BaseAgent):
    async def process(self, message: str, context: RunContext) -> str:
        # 你的实现
        return "自定义回复"
    
    async def execute_tool_call(
        self, 
        tool_call: ToolCall, 
        context: RunContext
    ) -> Observation:
        # 你的工具调用实现
        pass
```

### 添加工具

工具需要是 LangChain Tool 实例：

```python
from langchain_core.tools import tool
from omnipok_agent.tools import global_registry

@tool
async def my_tool(param1: str, param2: int) -> dict:
    """工具描述。"""
    return {"result": "success"}

# 注册工具
global_registry.register(tool=my_tool)
```

### 自定义内存后端

```python
from omnipok_agent.memory.base import Memory
from omnipok_agent.core.types import AgentState, Message

class MyMemoryBackend(Memory):
    def save(self, agent_id: str, state: AgentState) -> None:
        # 你的实现
        pass
    
    def load(self, agent_id: str) -> AgentState:
        # 你的实现
        pass
    
    # 实现其他必需的方法...
```

## 📖 更多示例

查看 `examples/` 目录了解更多示例：

- `simple_agent_example.py` - 基础 Agent 使用
- `memory_example.py` - 内存系统使用
- `langgraph_orchestration_example.py` - 任务编排示例
- `rag_example.py` - RAG 模块使用示例

## 📚 使用 RAG 模块

RAG (Retrieval-Augmented Generation) 模块提供了知识库管理和检索增强生成功能。

### 基本使用

```python
import asyncio
from omnipok_agent.rag import KnowledgeBase, RAGAgent, Document, OpenAIEmbedding
from omnipok_agent.core import RunContext
from omnipok_agent.llm import OmniPokLLM
from omnipok_agent.memory import InMemoryMemory

async def main():
    # 1. 创建知识库
    kb = KnowledgeBase(
        kb_id="my-kb",
        embedding_model=OpenAIEmbedding(model="text-embedding-3-small")
    )
    
    # 2. 添加文档到知识库
    kb.add_document(Document(
        content="Python是一种高级编程语言...",
        metadata={"title": "Python介绍"}
    ))
    
    # 或者从文件加载
    # kb.add_file("document.txt")
    # kb.add_directory("documents/", recursive=True)
    
    # 3. 创建 RAG Agent
    agent = RAGAgent(
        agent_id="rag-agent",
        knowledge_base=kb,
        llm=OmniPokLLM(),
        memory=InMemoryMemory(),
        top_k=5  # 检索前5个相关文档
    )
    
    # 4. 使用 Agent 进行问答
    context = RunContext(tenant_id="t1", user_id="u1")
    response = await agent.process("Python是什么？", context)
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

### 知识库管理

```python
from omnipok_agent.rag import KnowledgeBase, DocumentLoader

# 创建知识库
kb = KnowledgeBase(kb_id="my-knowledge-base")

# 添加单个文档
kb.add_document(Document(content="文档内容", metadata={"source": "doc1"}))

# 从文件加载
kb.add_file("document.txt")

# 从目录加载所有支持的文件
kb.add_directory("documents/", recursive=True)

# 搜索知识库
results = kb.search("查询内容", top_k=5)

# 删除文档
kb.delete_documents(["doc-id-1", "doc-id-2"])

# 清空知识库
kb.clear()
```

### 支持的文档格式

- `.txt` - 纯文本文件
- `.md` - Markdown 文件

### RAG Agent 配置

```python
agent = RAGAgent(
    agent_id="rag-agent",
    knowledge_base=kb,
    llm=OmniPokLLM(),
    memory=InMemoryMemory(),
    top_k=5,              # 检索文档数量
    include_sources=True  # 是否在回答中包含来源信息
)
```

## 🛠️ 支持的 LLM 提供商

- OpenAI (GPT-4, GPT-3.5)
- 阿里云通义千问 (Qwen)
- DeepSeek
- ModelScope
- 月之暗面 (Kimi/Moonshot)
- 智谱AI (GLM)
- Ollama (本地部署)
- vLLM (本地部署)
- 其他兼容 OpenAI API 的服务

## 📝 开发

### 运行测试

```bash
# 待实现
pytest tests/
```

### 代码格式化

```bash
black omnipok_agent/ applications/
ruff check omnipok_agent/ applications/
```

## 📄 License

MIT

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**快速链接**：
- 📖 [完整文档](./docs/)
- 💡 [示例代码](./examples/)
- 🔧 [配置文件示例](./config/agents.json.example)
