# Plan and Solve Agent 复杂任务测试

## 测试说明

本测试展示了如何使用 `PlanSolveAgent` 处理复杂任务，包括：

1. **任务分解**：Agent 自动将复杂任务分解为多个可执行的步骤
2. **工具使用**：使用不同的工具（HTTP GET/POST、数据库查询/执行）完成各个步骤
3. **结果聚合**：收集、分析并聚合结果，生成最终报告

## 测试场景

测试场景是分析多个城市的气象数据：
- 从API获取北京、上海、广州的气象数据
- 进行统计分析（平均温度、最高/最低温度等）
- 将结果存储到数据库
- 生成综合报告

## 运行测试

### 方式1：使用模拟LLM（推荐用于快速测试）

默认情况下，测试使用模拟的LLM响应，无需配置API密钥：

```bash
cd tests/integration
python test_plan_solve_agent_complex_task.py
```

### 方式2：使用真实LLM

如果需要使用真实的LLM来测试，需要：

1. 配置环境变量（创建或编辑 `.env` 文件）：

```bash
# 使用真实LLM
USE_REAL_LLM=true

# 配置LLM API密钥（根据你使用的提供商选择）
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=your-base-url
LLM_MODEL_ID=your-model-id

# 或者使用特定提供商的配置
# OpenAI
OPENAI_API_KEY=sk-...

# DeepSeek
DEEPSEEK_API_KEY=sk-...

# 等等...
```

2. 运行测试：

```bash
USE_REAL_LLM=true python test_plan_solve_agent_complex_task.py
```

## 测试输出

测试会输出：
- Agent 制定的执行计划
- 每个步骤的执行过程
- 工具调用情况（HTTP请求、数据库操作等）
- 最终的分析报告
- 执行统计（步数、Token使用、成本等）

## 预期行为

1. **计划阶段**：Agent 分析任务并制定包含多个步骤的执行计划
2. **执行阶段**：
   - 步骤1-3：使用 `http_get` 工具获取三个城市的气象数据
   - 步骤4：分析收集到的数据
   - 步骤5：使用 `db_execute` 将结果存储到数据库
   - 步骤6：使用 `db_query` 验证数据
   - 步骤7：生成最终报告
3. **结果聚合**：Agent 综合所有步骤的结果，生成包含统计分析和详细情况的报告

## 注意事项

- 使用模拟LLM时，测试不会产生真实的API调用费用
- 模拟工具会打印执行日志，便于理解Agent的执行流程
- 真实LLM测试可能需要较长时间，取决于网络和模型响应速度

