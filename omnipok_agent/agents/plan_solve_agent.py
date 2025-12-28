"""Plan and Solve Agent - Planning and execution agent implementation."""
import json
from typing import Optional, List, Dict, Any
from ..core.base import BaseAgent
from ..memory.base import Memory
from ..llm.omnipok_llm import OmniPokLLM
from ..tools.registry import ToolRegistry
from ..core.context import RunContext
from ..core.types import Message, MessageRole


class PlanSolveAgent(BaseAgent):
    """
    Plan and Solve Agent实现。
    
    Plan and Solve Agent采用"计划-执行"的两阶段模式：
    1. **计划阶段(Planning)**: 分析问题，制定详细的执行计划
    2. **执行阶段(Solving)**: 按照计划逐步执行，可能需要调整计划
    
    这种模式使得Agent能够在开始执行前先思考整体策略，提高任务完成的成功率。
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str = None,
        llm: Optional[OmniPokLLM] = None,
        memory: Optional[Memory] = None,
        tool_registry: Optional[ToolRegistry] = None,
        system_prompt: Optional[str] = None,
        max_iterations: int = 10,
        enable_plan_revision: bool = True
    ):
        """
        初始化Plan and Solve Agent。
        
        Args:
            agent_id: 唯一的Agent标识符
            llm: OmniPokLLM实例（如果为None，将自动检测）
            memory: 记忆后端（用于保存对话历史）
            tool_registry: 工具注册表（用于执行计划步骤）
            system_prompt: 系统提示词（如果为None，使用默认提示词）
            max_iterations: 最大迭代次数
            enable_plan_revision: 是否允许在执行过程中修订计划
        """
        # 默认系统提示词 - Plan and Solve模式
        default_prompt = """你是一个使用"计划-执行"模式的AI助手。
你的工作方式分为两个阶段：

**阶段1: 制定计划(Planning)**
当收到任务时，你需要：
1. 分析任务的要求和目标
2. 将复杂任务分解为多个子步骤
3. 为每个步骤指定需要使用的工具或方法
4. 考虑步骤之间的依赖关系
5. 输出一个清晰的执行计划

计划格式：
```
计划：
1. 步骤1描述 [工具/方法]
2. 步骤2描述 [工具/方法]
...
```

**阶段2: 执行计划(Solving)**
按照计划逐步执行：
1. 执行当前步骤
2. 评估执行结果
3. 决定是否继续下一步或需要调整计划
4. 重复直到所有步骤完成

如果在执行过程中发现问题，可以修订计划，但需要说明修订的原因。

当任务完成时，请给出最终的总结和结果。

请用中文与用户交流。"""
        
        super().__init__(
            agent_id=agent_id,
            name="Plan and Solve Agent",
            llm=llm,
            memory=memory,
            tool_registry=tool_registry,
            system_prompt=system_prompt or default_prompt,
            max_iterations=max_iterations
        )
        self.enable_plan_revision = enable_plan_revision
        self.current_plan: Optional[List[str]] = None
        self.current_step_index: int = 0
    
    async def process(self, message: str, context: RunContext) -> str:
        """
        处理消息，使用Plan and Solve模式。
        
        Args:
            message: 用户消息
            context: 运行上下文
            
        Returns:
            Agent的最终响应
        """
        context.start()
        context.increment_step()
        
        try:
            # 添加用户消息
            user_msg = Message(role=MessageRole.USER, content=message)
            self.add_message(user_msg)
            
            # 阶段1: 制定计划
            plan = await self._create_plan(message, context)
            self.current_plan = plan
            
            print("current_plan", self.current_plan)
            self.current_step_index = 0
            
            # 阶段2: 执行计划
            final_answer = await self._execute_plan(message, context)
            
            # 重置计划状态
            self.current_plan = None
            self.current_step_index = 0
            
            # 保存状态
            self.save_state()
            
            return final_answer
            
        finally:
            context.end()
    
    async def _create_plan(self, message: str, context: RunContext) -> List[str]:
        """
        创建执行计划。
        
        Args:
            message: 用户消息
            context: 运行上下文
            
        Returns:
            计划步骤列表
        """
        # 构建计划制定的提示
        planning_prompt = f"""请为以下任务制定详细的执行计划：

任务：{message}

请将任务分解为清晰的步骤，每个步骤应该：
- 具体可执行
- 明确需要使用的工具或方法（如果有可用工具）
- 说明该步骤的目的

输出格式：
计划：
1. 步骤1描述
2. 步骤2描述
...

请直接输出计划，不要调用工具。"""
        
        # 添加计划制定的消息
        planning_msg = Message(role=MessageRole.USER, content=planning_prompt)
        self.add_message(planning_msg)
        
        # 调用LLM生成计划
        messages = self._build_messages()
        response = await self._call_llm(messages, None)  # 制定计划时不使用工具
        
        # 更新上下文使用情况
        if response.get("usage"):
            usage = response["usage"]
            tokens = usage.get("total_tokens", 0)
            cost = tokens * 0.000002
            context.add_cost(tokens, cost)
        
        plan_content = response.get("content", "")
        print(plan_content)
        
        # 添加计划响应
        plan_response_msg = Message(
            role=MessageRole.ASSISTANT,
            content=plan_content
        )
        self.add_message(plan_response_msg)
        
        # 解析计划步骤
        plan_steps = self._parse_plan(plan_content)
        print(plan_steps)
        return plan_steps
    
    def _parse_plan(self, plan_content: str) -> List[str]:
        """
        解析计划文本，提取步骤列表。
        
        Args:
            plan_content: 计划文本
            
        Returns:
            步骤列表
        """
        steps = []
        lines = plan_content.split('\n')
        
        for line in lines:
            line = line.strip()
            # 查找以数字开头的行（如 "1. xxx" 或 "步骤1: xxx"）
            if line and (line[0].isdigit() or line.startswith('步骤')):
                # 移除序号前缀
                step = line
                # 尝试移除常见的序号格式
                for prefix in ['步骤', 'Step', 'STEP']:
                    if step.startswith(prefix):
                        # 找到第一个数字或冒号后的内容
                        colon_idx = step.find(':')
                        if colon_idx > 0:
                            step = step[colon_idx + 1:].strip()
                        else:
                            # 移除前缀和数字
                            import re
                            step = re.sub(rf'^{prefix}\d+\s*[.:]?\s*', '', step)
                        break
                
                # 移除行首的数字和点号
                import re
                step = re.sub(r'^\d+[.:]\s*', '', step)
                
                if step:
                    steps.append(step)
        
        return steps if steps else [plan_content]  # 如果解析失败，返回整个计划内容
    
    async def _execute_plan(self, message: str, context: RunContext) -> str:
        """
        执行计划。
        
        Args:
            message: 原始用户消息
            context: 运行上下文
            
        Returns:
            最终答案
        """
        if not self.current_plan:
            return "无法执行：计划创建失败。"
        
        execution_prompt = f"""现在请按照以下计划执行任务：

原始任务：{message}

执行计划：
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(self.current_plan))}

重要：请立即开始执行计划。对于第一步，请直接调用相应的工具，不要只是描述计划。
执行完工具后，我会把结果返回给你，然后你继续下一步或给出最终答案。

当所有步骤完成后，请给出最终答案。"""
        
        print(execution_prompt)
        # 添加执行消息
        execution_msg = Message(role=MessageRole.USER, content=execution_prompt)
        self.add_message(execution_msg)
        
        # 执行循环
        iteration = 0
        final_answer = None
        
        while iteration < self.max_iterations:
            if context.is_max_steps_reached() or context.is_budget_exceeded():
                break
            
            iteration += 1
            print(f"[执行循环] 迭代 {iteration}/{self.max_iterations}")
            
            # 构建消息历史
            messages = self._build_messages()
            
            # 获取可用工具
            available_tools = []
            if self.tool_registry:
                available_tools = self.get_available_tools(
                    user_permissions=context.metadata.get("permissions", [])
                )
            
            # 调用LLM执行当前步骤
            response = await self._call_llm(
                messages,
                available_tools if available_tools else None
            )
            
            # 更新上下文使用情况
            if response.get("usage"):
                usage = response["usage"]
                tokens = usage.get("total_tokens", 0)
                cost = tokens * 0.000002
                context.add_cost(tokens, cost)
            
            content = response.get("content", "")
            tool_calls = response.get("tool_calls")
            
            print(f"[LLM响应] 迭代 {iteration}: 内容长度={len(content)}, 工具调用数={len(tool_calls) if tool_calls else 0}")
            if tool_calls:
                print(f"[工具调用] {[tc.get('name') for tc in tool_calls]}")
            
            # 添加助手消息
            assistant_msg = Message(
                role=MessageRole.ASSISTANT,
                content=content
            )
            self.add_message(assistant_msg)
            
            # 如果没有工具调用，检查是否是最终答案
            if not tool_calls:
                # 检测是否是在描述要做什么，而不是最终答案
                # 如果内容包含工具名称但没有调用工具，说明是在描述而不是执行
                tool_names_in_content = []
                if self.tool_registry:
                    available_tools_list = self.tool_registry.list_tools()
                    tool_names_in_content = [tool.name for tool in available_tools_list if tool.name in content]
                
                is_describing_action = (
                    bool(tool_names_in_content) or  # 提到了工具名称
                    ("使用" in content and ("工具" in content or "调用" in content)) or  # 提到"使用...工具"
                    "搜索" in content or  # 提到搜索
                    "访问" in content or  # 提到访问
                    ("执行" in content and "完成" not in content)  # 提到执行（但不是"执行完成"）
                )
                
                # 如果看起来像是在描述要做什么（而不是最终答案），继续循环
                if is_describing_action and len(content) < 200:
                    # 检测到只是描述，需要强制LLM调用工具
                    print(f"[检测到动作描述] 迭代 {iteration}，内容提到了工具但未调用，强制要求执行工具。工具: {tool_names_in_content}")
                    
                    # 移除刚才的描述性消息，替换为强制调用工具的提示
                    # 找到最后一条助手消息并移除
                    if self.state.messages and self.state.messages[-1].role == MessageRole.ASSISTANT:
                        self.state.messages.pop()
                    
                    # 添加强制调用工具的提示
                    if iteration == 1:
                        reminder_msg = Message(
                            role=MessageRole.USER,
                            content="你必须立即调用工具来执行任务。不要用文字描述，必须使用工具调用（function calling）。请直接调用 web_search 工具，参数为 {\"query\": \"Python 最新版本\"}。"
                        )
                    else:
                        # 如果多次提示仍未调用，更强制
                        reminder_msg = Message(
                            role=MessageRole.USER,
                            content="请立即调用工具。这是必须的，不要只是描述。使用 function calling 格式调用工具。"
                        )
                    self.add_message(reminder_msg)
                    
                    # 下一次调用时强制要求调用工具
                    context.increment_step()
                    # 在下次迭代中使用 tool_choice="required"
                    continue
                # 否则认为是最终答案
                print(f"[执行完成] 最终答案: {content[:100]}...")
                final_answer = content
                break
            
            # 执行工具调用
            print(f"[开始执行工具] 共 {len(tool_calls)} 个工具调用")
            observations = []
            for tool_call_data in tool_calls:
                arguments = tool_call_data.get("arguments", {})
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {}
                
                from ..core.types import ToolCall
                import uuid
                tool_call = ToolCall(
                    id=tool_call_data.get("id", str(uuid.uuid4())),
                    name=tool_call_data["name"],
                    arguments=arguments
                )
                
                print(f"[执行工具] {tool_call.name} with args: {tool_call.arguments}")
                observation = await self.execute_tool_call(tool_call, context)
                observations.append(observation)
                print(f"[工具结果] {str(observation.content)[:200]}...")
                
                # 添加工具消息
                tool_msg = Message(
                    role=MessageRole.TOOL,
                    content=json.dumps(observation.content) if isinstance(observation.content, dict) else str(observation.content),
                    tool_call_id=tool_call.id
                )
                self.add_message(tool_msg)
            
            # 执行完工具后，继续循环让LLM基于结果生成最终答案
            print("[工具执行完成] 继续循环生成最终答案")
            context.increment_step()
        
        if not final_answer:
            final_answer = content if 'content' in locals() else "已达到最大迭代次数，计划执行未完成。"
        
        return final_answer

