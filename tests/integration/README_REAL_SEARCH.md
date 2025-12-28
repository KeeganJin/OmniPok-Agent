# Plan and Solve Agent 真实搜索任务测试

## 测试说明

本测试展示了如何使用 `PlanSolveAgent` 处理需要**多次搜索**的复杂任务，使用**真实的工具**（SerpApi）和**真实的LLM**。

### 测试场景

研究2024年三大AI公司的战略布局：
- 分别搜索 OpenAI、Google DeepMind、Anthropic 的信息
- 收集每个公司的关键信息
- 对比分析差异和共同点
- 生成综合研究报告

### 功能展示

1. **任务分解**：Agent 自动将复杂任务分解为多个搜索步骤
2. **多次搜索**：使用 `web_search` 工具进行多次独立搜索
3. **结果聚合**：收集、分析并聚合多个搜索结果
4. **智能报告**：生成包含对比分析和总结的报告

## 环境配置

### 1. 安装依赖

```bash
pip install google-search-results
```

或者安装所有依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建或编辑项目根目录下的 `.env` 文件：

```bash
# SerpApi 配置（必需）
SERPAPI_API_KEY=your-serpapi-api-key-here

# LLM 配置（必需，选择一种）
# 方式1: 通用配置
LLM_API_KEY=your-llm-api-key
LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL_ID=your-model-name

# 方式2: OpenAI
OPENAI_API_KEY=sk-...

# 方式3: DeepSeek
DEEPSEEK_API_KEY=sk-...
# 或
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL_ID=deepseek-chat

# 方式4: 通义千问
DASHSCOPE_API_KEY=sk-...

# 其他配置...
```

### 3. 获取 SerpApi 密钥

1. 访问 [SerpApi官网](https://serpapi.com/)
2. 注册免费账户（每月100次搜索）
3. 在 Dashboard 获取 API Key
4. 将 API Key 添加到 `.env` 文件

## 运行测试

```bash
cd tests/integration
python test_plan_solve_agent_real_search.py
```

## 测试输出

测试会实时显示：

1. **环境检查**：验证API密钥配置
2. **Agent初始化**：LLM和工具注册状态
3. **任务执行过程**：
   - Agent制定的执行计划
   - 每次搜索的执行日志
   - 工具调用详情
4. **最终结果**：
   - 综合研究报告
   - 执行统计（步数、Token、成本）
   - 工具调用次数

## 预期行为

### 计划阶段

Agent会制定类似如下的计划：

```
计划：
1. 使用web_search工具搜索"OpenAI 2024 战略布局 最新产品"
2. 使用web_search工具搜索"Google DeepMind 2024 AI布局 研究方向"
3. 使用web_search工具搜索"Anthropic Claude 2024 公司战略"
4. 分析每个公司的关键信息（产品、技术、商业模式等）
5. 对比分析三个公司的差异和共同点
6. 总结竞争优势和发展趋势
7. 生成综合研究报告
```

### 执行阶段

1. **步骤1-3**：依次使用 `web_search` 搜索三个公司
2. **步骤4**：分析收集到的信息
3. **步骤5-6**：进行对比和总结
4. **步骤7**：生成最终报告

### 最终报告

报告将包含：
- 每个公司的关键信息
- 对比分析（差异和共同点）
- 竞争优势分析
- 发展趋势总结

## 注意事项

### 成本控制

- **SerpApi**：免费账户每月100次搜索，超出需要付费
- **LLM API**：根据使用的模型和Token数量计费
- 测试中设置了预算限制（`budget=5.0`），可以调整

### 执行时间

- 每次搜索需要1-3秒
- 多个搜索 + LLM处理可能需要几分钟
- 设置了10分钟超时（`timeout=600.0`）

### 网络要求

- 需要能够访问 SerpApi 和 LLM API
- 如果在中国大陆，可能需要配置代理

### 错误处理

测试包含完整的错误处理：
- 环境变量检查
- API调用异常处理
- 预算和超时检查
- 详细的错误信息输出

## 自定义任务

你可以修改测试中的 `complex_task` 变量来测试其他需要多次搜索的任务，例如：

```python
complex_task = """请研究以下主题：
1. 人工智能在医疗领域的应用
2. 人工智能在教育领域的应用
3. 人工智能在金融领域的应用
然后对比分析这三个领域的应用特点和趋势。"""
```

## 调试技巧

1. **查看详细日志**：搜索工具会输出执行日志
2. **调整迭代次数**：如果任务复杂，可以增加 `max_iterations`
3. **调整预算**：如果成本过高，可以降低 `budget` 参数
4. **检查消息历史**：Agent保存了完整的对话历史，可以查看执行过程

## 故障排除

### SerpApi 错误

- **"API key无效"**：检查 `.env` 文件中的 `SERPAPI_API_KEY` 是否正确
- **"额度用尽"**：免费账户每月100次，检查使用量
- **"网络错误"**：检查网络连接，可能需要配置代理

### LLM 错误

- **"API key未配置"**：检查LLM相关的环境变量
- **"模型不存在"**：检查 `LLM_MODEL_ID` 是否正确
- **"请求超时"**：增加 `timeout` 参数或检查网络

### Agent 执行问题

- **"达到最大迭代次数"**：任务可能太复杂，增加 `max_iterations`
- **"超出预算"**：任务成本过高，增加 `budget` 或简化任务
- **"执行超时"**：增加 `timeout` 参数

## 扩展功能

可以基于此测试扩展：
- 添加更多搜索工具（如 Bing、DuckDuckGo）
- 添加数据存储功能（将结果保存到数据库）
- 添加结果缓存（避免重复搜索）
- 支持多语言搜索

