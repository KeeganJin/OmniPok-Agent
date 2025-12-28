"""Reflection Agent - Self-reflection and improvement agent implementation."""
import json
from typing import Optional, Dict, Any
from ..core.base import BaseAgent
from ..core.memory import Memory
from ..core.llm import OmniPokLLM
from ..core.tool_registry import ToolRegistry
from ..core.context import RunContext
from ..core.types import Message, MessageRole


class ReflectionAgent(BaseAgent):
    """
    Reflection Agent实现。
    
    Reflection Agent采用"执行-反思-改进"的模式：
    1. **执行阶段(Execution)**: 执行任务，生成初始答案
    2. **反思阶段(Reflection)**: 对答案进行自我评估和反思
    3. **改进阶段(Refinement)**: 根据反思结果改进答案（如果需要）
    
    这种模式使得Agent能够自我检查和改进，提高答案的质量和准确性。
    """
    
    def __init__(
        self,
        agent_id: str,
        llm: Optional[OmniPokLLM] = None,
        memory: Optional[Memory] = None,
        tool_registry: Optional[ToolRegistry] = None,
        system_prompt: Optional[str] = None,
        max_iterations: int = 10,
        max_reflection_rounds: int = 3
    ):
        """
        初始化Reflection Agent。
        
        Args:
            agent_id: 唯一的Agent标识符
            llm: OmniPokLLM实例（如果为None，将自动检测）
            memory: 记忆后端（用于保存对话历史）
            tool_registry: 工具注册表（用于执行任务）
            system_prompt: 系统提示词（如果为None，使用默认提示词）
            max_iterations: 最大迭代次数（每轮执行）
            max_reflection_rounds: 最大反思轮数
        """
        # 默认系统提示词 - Reflection模式
        default_prompt = """你是一个使用"执行-反思-改进"模式的AI助手。
你的工作方式分为三个阶段：

**阶段1: 执行(Execution)**
首先，认真分析任务并执行：
- 理解任务的要求
- 使用必要的工具获取信息
- 生成初步的答案

**阶段2: 反思(Reflection)**
完成执行后，对自己的答案进行反思：
- 检查答案是否完整回答了问题
- 检查答案的准确性和逻辑性
- 识别可能的错误或遗漏
- 评估答案的质量

**阶段3: 改进(Refinement)**
如果需要改进：
- 指出发现的问题
- 重新思考或重新执行部分任务
- 生成改进后的答案

如果答案已经足够好，可以直接提交最终答案。

请用中文与用户交流。"""
        
        super().__init__(
            agent_id=agent_id,
            name="Reflection Agent",
            llm=llm,
            memory=memory,
            tool_registry=tool_registry,
            system_prompt=system_prompt or default_prompt,
            max_iterations=max_iterations
        )
        self.max_reflection_rounds = max_reflection_rounds
    
    async def process(self, message: str, context: RunContext) -> str:
        """
        处理消息，使用Reflection模式。
        
        Args:
            message: 用户消息
            context: 运行上下文
            
        Returns:
            Agent的最终响应（经过反思和改进）
        """
        context.start()
        context.increment_step()
        
        try:
            # 添加用户消息
            user_msg = Message(role=MessageRole.USER, content=message)
            self.add_message(user_msg)
            
            # 执行-反思-改进循环
            best_answer = None
            reflection_round = 0
            
            while reflection_round < self.max_reflection_rounds:
                reflection_round += 1
                
                # 阶段1: 执行任务
                initial_answer = await self._execute_task(message, context)
                
                if reflection_round == 1:
                    best_answer = initial_answer
                
                # 阶段2: 反思答案
                reflection_result = await self._reflect_on_answer(
                    message, 
                    initial_answer, 
                    context
                )
                
                # 如果反思认为答案足够好，结束循环
                if reflection_result.get("is_satisfactory", False):
                    best_answer = initial_answer
                    break
                
                # 阶段3: 改进答案
                if reflection_round < self.max_reflection_rounds:
                    improved_answer = await self._refine_answer(
                        message,
                        initial_answer,
                        reflection_result.get("issues", []),
                        context
                    )
                    best_answer = improved_answer
                    
                    # 将改进后的答案作为新的起点
                    improvement_msg = Message(
                        role=MessageRole.USER,
                        content=f"根据反思，请改进以下答案：\n\n原始答案：{initial_answer}\n\n发现问题：{', '.join(reflection_result.get('issues', []))}"
                    )
                    self.add_message(improvement_msg)
            
            # 保存状态
            self.save_state()
            
            return best_answer or "无法完成任务。"
            
        finally:
            context.end()
    
    async def _execute_task(self, message: str, context: RunContext) -> str:
        """
        执行任务，生成初始答案。
        
        Args:
            message: 用户消息
            context: 运行上下文
            
        Returns:
            初始答案
        """
        execution_prompt = f"""请认真分析并完成以下任务：

任务：{message}

请使用必要的工具获取信息，然后生成一个完整的答案。"""
        
        # 如果这是第一次执行，直接使用原始消息
        # 否则使用执行提示
        if len(self.state.messages) <= 1:  # 只有用户消息
            current_message = message
        else:
            execution_msg = Message(role=MessageRole.USER, content=execution_prompt)
            self.add_message(execution_msg)
            current_message = execution_prompt
        
        # 执行循环
        iteration = 0
        final_answer = None
        original_step_count = context.steps_taken
        
        while iteration < self.max_iterations:
            if context.is_max_steps_reached() or context.is_budget_exceeded():
                break
            
            iteration += 1
            
            # 构建消息历史
            messages = self._build_messages()
            
            # 获取可用工具
            available_tools = []
            if self.tool_registry:
                available_tools = self.get_available_tools(
                    user_permissions=context.metadata.get("permissions", [])
                )
            
            # 调用LLM
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
            
            # 添加助手消息
            assistant_msg = Message(
                role=MessageRole.ASSISTANT,
                content=content
            )
            self.add_message(assistant_msg)
            
            # 如果没有工具调用，说明执行完成
            if not tool_calls:
                final_answer = content
                break
            
            # 执行工具调用
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
                
                observation = await self.execute_tool_call(tool_call, context)
                observations.append(observation)
                
                # 添加工具消息
                tool_msg = Message(
                    role=MessageRole.TOOL,
                    content=json.dumps(observation.content) if isinstance(observation.content, dict) else str(observation.content),
                    tool_call_id=tool_call.id
                )
                self.add_message(tool_msg)
            
            if not observations:
                final_answer = content
                break
            
            context.increment_step()
        
        if not final_answer:
            final_answer = content if 'content' in locals() else "执行失败。"
        
        return final_answer
    
    async def _reflect_on_answer(
        self,
        original_question: str,
        answer: str,
        context: RunContext
    ) -> Dict[str, Any]:
        """
        对答案进行反思。
        
        Args:
            original_question: 原始问题
            answer: 生成的答案
            context: 运行上下文
            
        Returns:
            反思结果字典，包含is_satisfactory和issues字段
        """
        reflection_prompt = f"""请对以下答案进行反思和评估：

原始问题：{original_question}

生成的答案：{answer}

请评估：
1. 答案是否完整回答了问题？
2. 答案是否准确和正确？
3. 答案的逻辑是否清晰？
4. 是否存在错误、遗漏或不准确的地方？

请以JSON格式回答，格式如下：
{{
    "is_satisfactory": true/false,
    "issues": ["问题1", "问题2", ...],
    "reasoning": "你的评估理由"
}}

如果答案足够好，is_satisfactory应该为true，issues应该为空数组。
如果答案有问题，is_satisfactory应该为false，并在issues中列出所有发现的问题。"""
        
        reflection_msg = Message(role=MessageRole.USER, content=reflection_prompt)
        self.add_message(reflection_msg)
        
        # 调用LLM进行反思（不使用工具）
        messages = self._build_messages()
        response = await self._call_llm(messages, None)
        
        # 更新上下文使用情况
        if response.get("usage"):
            usage = response["usage"]
            tokens = usage.get("total_tokens", 0)
            cost = tokens * 0.000002
            context.add_cost(tokens, cost)
        
        reflection_content = response.get("content", "")
        
        # 添加反思响应
        reflection_response_msg = Message(
            role=MessageRole.ASSISTANT,
            content=reflection_content
        )
        self.add_message(reflection_response_msg)
        
        # 解析反思结果
        try:
            # 尝试从内容中提取JSON
            import re
            json_match = re.search(r'\{[^}]+\}', reflection_content, re.DOTALL)
            if json_match:
                reflection_result = json.loads(json_match.group())
            else:
                # 如果没有找到JSON，尝试解析整个内容
                reflection_result = json.loads(reflection_content)
            
            return {
                "is_satisfactory": reflection_result.get("is_satisfactory", False),
                "issues": reflection_result.get("issues", []),
                "reasoning": reflection_result.get("reasoning", "")
            }
        except (json.JSONDecodeError, KeyError):
            # 如果解析失败，尝试从文本中推断
            content_lower = reflection_content.lower()
            is_satisfactory = "满意" in content_lower or "足够" in content_lower or "可以" in content_lower
            return {
                "is_satisfactory": is_satisfactory,
                "issues": [] if is_satisfactory else ["需要改进"],
                "reasoning": reflection_content
            }
    
    async def _refine_answer(
        self,
        original_question: str,
        previous_answer: str,
        issues: list,
        context: RunContext
    ) -> str:
        """
        根据反思结果改进答案。
        
        Args:
            original_question: 原始问题
            previous_answer: 之前的答案
            issues: 发现的问题列表
            context: 运行上下文
            
        Returns:
            改进后的答案
        """
        refinement_prompt = f"""原始问题：{original_question}

之前的答案：{previous_answer}

发现的问题：{', '.join(issues) if issues else '无'}

请根据发现的问题，改进之前的答案。改进后的答案应该：
1. 解决所有发现的问题
2. 保持原有答案中的正确部分
3. 更加完整、准确和清晰

请直接输出改进后的答案，不要调用工具（除非需要获取新的信息）。"""
        
        refinement_msg = Message(role=MessageRole.USER, content=refinement_prompt)
        self.add_message(refinement_msg)
        
        # 构建消息历史
        messages = self._build_messages()
        
        # 获取可用工具（可能需要获取新信息）
        available_tools = []
        if self.tool_registry:
            available_tools = self.get_available_tools(
                user_permissions=context.metadata.get("permissions", [])
            )
        
        # 调用LLM改进答案
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
        
        # 如果还有工具调用，执行它们
        if tool_calls:
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
                
                observation = await self.execute_tool_call(tool_call, context)
                observations.append(observation)
                
                tool_msg = Message(
                    role=MessageRole.TOOL,
                    content=json.dumps(observation.content) if isinstance(observation.content, dict) else str(observation.content),
                    tool_call_id=tool_call.id
                )
                self.add_message(tool_msg)
            
            # 如果有观察结果，再次调用LLM生成最终答案
            if observations:
                messages = self._build_messages()
                response = await self._call_llm(messages, None)
                content = response.get("content", "")
                
                if response.get("usage"):
                    usage = response["usage"]
                    tokens = usage.get("total_tokens", 0)
                    cost = tokens * 0.000002
                    context.add_cost(tokens, cost)
        
        # 添加改进后的答案
        refined_msg = Message(
            role=MessageRole.ASSISTANT,
            content=content
        )
        self.add_message(refined_msg)
        
        return content

