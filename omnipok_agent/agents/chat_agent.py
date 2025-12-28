"""Simple chat agent implementation - the most basic chatbot."""
from typing import Optional
from ..core.base import BaseAgent
from ..memory.base import Memory
from ..llm.omnipok_llm import OmniPokLLM


class ChatAgent(BaseAgent):
    """
    最基础的聊天机器人Agent。
    
    这是一个简单的对话Agent，专注于：
    - 自然对话
    - 上下文理解
    - 友好交流
    
    不包含工具调用等复杂功能，适合作为最基础的聊天机器人使用。
    """
    
    def __init__(
        self,
        agent_id: str,
        llm: Optional[OmniPokLLM] = None,
        memory: Optional[Memory] = None,
        system_prompt: Optional[str] = None
    ):
        """
        初始化聊天机器人Agent。
        
        Args:
            agent_id: 唯一的Agent标识符
            llm: OmniPokLLM实例（如果为None，将自动检测）
            memory: 记忆后端（用于保存对话历史）
            system_prompt: 系统提示词（如果为None，使用默认提示词）
        """
        # 默认系统提示词
        default_prompt = """你是一个友好、有帮助的AI聊天助手。
你的目标是：
- 与用户进行自然、流畅的对话
- 理解用户的意图并提供有用的回答
- 保持友好和专业的语气
- 记住对话上下文，提供连贯的回复

请用中文与用户交流。"""
        
        super().__init__(
            agent_id=agent_id,
            name="Chat Agent",
            llm=llm,
            memory=memory,
            tool_registry=None,  # 聊天机器人不需要工具
            system_prompt=system_prompt or default_prompt
        )
    
    async def chat_stream(self, message: str, context) -> str:
        """
        流式聊天方法，实时返回响应片段。
        
        Args:
            message: 用户消息
            context: 运行上下文
            
        Returns:
            完整的响应文本
        """
        context.start()
        context.increment_step()
        
        try:
            # 添加用户消息
            from ..core.types import Message, MessageRole
            user_msg = Message(role=MessageRole.USER, content=message)
            self.add_message(user_msg)
            
            # 构建消息历史
            messages = self._build_messages()
            
            # 使用流式调用
            full_response = ""
            print("🤖 AI: ", end="", flush=True)
            for chunk in self.llm.think(messages):
                print(chunk, end="", flush=True)
                full_response += chunk
            
            print()  # 换行
            
            # 添加助手消息
            assistant_msg = Message(
                role=MessageRole.ASSISTANT,
                content=full_response
            )
            self.add_message(assistant_msg)
            
            # 保存状态
            self.save_state()
            
            return full_response
            
        finally:
            context.end()
    
    async def chat(self, message: str, context) -> str:
        """
        非流式聊天方法，一次性返回完整响应。
        
        Args:
            message: 用户消息
            context: 运行上下文
            
        Returns:
            完整的响应文本
        """
        # 使用父类的process方法（非流式）
        return await self.process(message, context)

