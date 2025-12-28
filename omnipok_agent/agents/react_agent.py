"""ReAct Agent - Reasoning and Acting agent implementation."""
import json
from typing import Optional, Dict, Any
from ..core.base import BaseAgent
from ..core.memory import Memory
from ..core.llm import OmniPokLLM
from ..core.tool_registry import ToolRegistry
from ..core.context import RunContext
from ..core.types import Message, MessageRole


class ReActAgent(BaseAgent):
    """
    ReAct (Reasoning and Acting) Agent实现。
    
    ReAct Agent采用"推理-行动-观察"的循环模式：
    1. 推理(Reasoning): 分析当前情况，决定下一步行动
    2. 行动(Acting): 执行工具调用或其他操作
    3. 观察(Observation): 收集执行结果，用于下一轮推理
    
    这种模式使得Agent能够在解决问题的过程中持续思考和调整策略。
    """
    
    def __init__(
        self,
        agent_id: str,
        llm: Optional[OmniPokLLM] = None,
        memory: Optional[Memory] = None,
        tool_registry: Optional[ToolRegistry] = None,
        system_prompt: Optional[str] = None,
        max_iterations: int = 10
    ):
        """
        初始化ReAct Agent。
        
        Args:
            agent_id: 唯一的Agent标识符
            llm: OmniPokLLM实例（如果为None，将自动检测）
            memory: 记忆后端（用于保存对话历史）
            tool_registry: 工具注册表（必需，用于执行行动）
            system_prompt: 系统提示词（如果为None，使用默认提示词）
            max_iterations: 最大迭代次数
        """
        # 默认系统提示词 - ReAct模式
        default_prompt = """你是一个使用ReAct（推理和行动）模式的AI助手。
你的工作方式是：
1. **思考(Thought)**: 分析当前情况和问题，决定下一步需要做什么
2. **行动(Action)**: 根据思考结果，调用相应的工具来获取信息或执行操作
3. **观察(Observation)**: 分析工具返回的结果
4. 重复以上步骤，直到找到答案或完成任务

请在你的回答中清楚地标注：
- **Thought**: 你的思考过程
- **Action**: 你要执行的操作（使用工具调用）
- **Observation**: 观察到的结果

当你有足够的信息来回答问题时，请直接给出最终答案，而不是继续调用工具。

请用中文与用户交流。"""
        
        super().__init__(
            agent_id=agent_id,
            name="ReAct Agent",
            llm=llm,
            memory=memory,
            tool_registry=tool_registry,
            system_prompt=system_prompt or default_prompt,
            max_iterations=max_iterations
        )
    
    async def process(self, message: str, context: RunContext) -> str:
        """
        处理消息，使用ReAct模式。
        
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
            
            # ReAct循环：思考-行动-观察
            iteration = 0
            final_answer = None
            
            while iteration < self.max_iterations:
                # 检查是否超过最大步数或预算
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
                
                # 调用LLM进行推理
                response = await self._call_llm(
                    messages, 
                    available_tools if available_tools else None
                )
                
                # 更新上下文使用情况
                if response.get("usage"):
                    usage = response["usage"]
                    tokens = usage.get("total_tokens", 0)
                    cost = tokens * 0.000002  # 粗略估计
                    context.add_cost(tokens, cost)
                
                content = response.get("content", "")
                tool_calls = response.get("tool_calls")
                
                # 添加助手消息（包含思考过程）
                assistant_msg = Message(
                    role=MessageRole.ASSISTANT,
                    content=content
                )
                self.add_message(assistant_msg)
                
                # 如果没有工具调用，说明已经给出最终答案
                if not tool_calls:
                    final_answer = content
                    break
                
                # 执行工具调用（行动）
                observations = []
                for tool_call_data in tool_calls:
                    # 解析arguments
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
                    
                    # 执行工具调用
                    observation = await self.execute_tool_call(tool_call, context)
                    observations.append(observation)
                    
                    # 添加工具消息（观察结果）
                    tool_msg = Message(
                        role=MessageRole.TOOL,
                        content=json.dumps(observation.content) if isinstance(observation.content, dict) else str(observation.content),
                        tool_call_id=tool_call.id
                    )
                    self.add_message(tool_msg)
                
                # 如果没有观察结果，退出循环
                if not observations:
                    final_answer = content
                    break
                
                # 继续下一轮推理
                context.increment_step()
            
            # 如果没有最终答案，使用最后一次的响应
            if not final_answer:
                final_answer = content if 'content' in locals() else "已达到最大迭代次数，无法完成任务。"
            
            # 保存状态
            self.save_state()
            
            return final_answer
            
        finally:
            context.end()

