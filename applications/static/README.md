# 前端使用说明

## 功能特性

1. **创建智能体**
   - 选择智能体类型（TextAgent、CodeAgent、SupportAgent）
   - 设置智能体ID和名称
   - 对于CodeAgent，可以选择编程语言

2. **选择智能体**
   - 查看所有可用的智能体列表
   - 点击选择要使用的智能体

3. **聊天功能**
   - 与选定的智能体进行对话
   - 显示Token使用量、成本和执行步骤

## 使用方法

1. 启动FastAPI服务：
   ```bash
   uvicorn applications.api.main:app --reload
   ```

2. 在浏览器中访问：
   ```
   http://localhost:8000
   ```

3. 创建或选择一个智能体，然后开始对话！

## API端点

- `GET /` - 前端页面
- `POST /api/v1/agents/create` - 创建新智能体
- `GET /api/v1/agents` - 获取智能体列表
- `POST /api/v1/chat` - 发送聊天消息

