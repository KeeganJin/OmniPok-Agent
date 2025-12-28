"""
测试用例：使用 Plan and Solve Agent 处理需要多次搜索的真实任务

本测试展示 Plan and Solve Agent 如何：
1. 接收一个需要多次搜索的复杂任务
2. 自动分解任务为多个步骤
3. 使用真实的搜索工具（SerpApi）进行多次搜索
4. 聚合分析多个搜索结果并生成最终报告

测试场景：
研究2024年三大AI公司的战略布局，包括OpenAI、Google DeepMind和Anthropic，
需要分别搜索每个公司的信息，然后对比分析它们的差异和共同点。

注意：
- 本测试使用真实的LLM和搜索工具
- 需要配置 SERPAPI_API_KEY 环境变量
- 需要配置 LLM 相关环境变量（LLM_API_KEY 等）
- 会产生真实的API调用费用
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 加载环境变量
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

from omnipok_agent.core import RunContext
from omnipok_agent.memory import InMemoryMemory
from omnipok_agent.tools import ToolRegistry, web_search
from omnipok_agent.llm import OmniPokLLM
from omnipok_agent.agents import PlanSolveAgent


def check_environment():
    """检查必要的环境变量是否已配置"""
    errors = []
    warnings = []
    
    # 检查SerpApi密钥
    if not os.getenv("SERPAPI_API_KEY"):
        errors.append(
            "❌ SERPAPI_API_KEY 未配置\n"
            "   请前往 https://serpapi.com/ 注册免费账户并获取API密钥\n"
            "   然后在 .env 文件中添加: SERPAPI_API_KEY=your-api-key"
        )
    
    # 检查LLM配置
    if not os.getenv("LLM_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        warnings.append(
            "⚠️  LLM配置未检测到\n"
            "   请在 .env 文件中配置以下之一：\n"
            "   - LLM_API_KEY 和 LLM_BASE_URL (通用配置)\n"
            "   - OPENAI_API_KEY (OpenAI)\n"
            "   - DEEPSEEK_API_KEY (DeepSeek)\n"
            "   - DASHSCOPE_API_KEY (通义千问)\n"
            "   等等..."
        )
    
    return errors, warnings


async def test_plan_solve_multiple_search_task():
    """
    测试Plan and Solve Agent处理需要多次搜索的复杂任务
    
    任务描述：
    研究2024年三大AI公司的战略布局，包括OpenAI、Google DeepMind和Anthropic，
    需要分别搜索每个公司的信息，然后对比分析它们的差异和共同点。
    """
    print("=" * 80)
    print("测试: Plan and Solve Agent 处理多次搜索任务（真实执行）")
    print("=" * 80)
    print()
    
    # 检查环境配置
    errors, warnings = check_environment()
    
    if errors:
        print("环境配置错误：")
        for error in errors:
            print(error)
        print()
        print("请配置必要的环境变量后重试。")
        return False
    
    if warnings:
        print("环境配置警告：")
        for warning in warnings:
            print(warning)
        print()
        response = input("是否继续？(y/n): ")
        if response.lower() != 'y':
            return False
        print()
    
    # 1. 设置工具注册表
    tool_registry = ToolRegistry()
    
    # 注册搜索工具
    tool_registry.register(
        tool=web_search,
        required_permissions=["search.web"]
    )
    
    print("✅ 工具注册完成")
    print(f"   - web_search: 网页搜索工具（SerpApi）")
    print()
    
    # 2. 创建LLM实例
    print("🤖 初始化LLM...")
    try:
        llm = OmniPokLLM()
        print(f"   ✅ LLM已初始化")
        print(f"   - Provider: {llm.provider}")
        print(f"   - Model: {llm.model}")
        print()
    except Exception as e:
        print(f"   ❌ LLM初始化失败: {e}")
        print("   请检查LLM相关环境变量配置")
        return False
    
    # 3. 创建Plan and Solve Agent
    print("🤖 创建 Plan and Solve Agent...")
    agent = PlanSolveAgent(
        agent_id="ai-companies-research-agent",
        llm=llm,
        memory=InMemoryMemory(),
        tool_registry=tool_registry,
        max_iterations=20,  # 增加迭代次数以支持多次搜索
        enable_plan_revision=True
    )
    print("   ✅ Agent创建完成")
    print()
    
    # 4. 创建运行上下文
    context = RunContext(
        tenant_id="test-tenant",
        user_id="test-user",
        budget=5.0,  # 设置预算限制（美元）
        max_steps=25,  # 增加最大步数
        timeout=600.0,  # 10分钟超时
        metadata={
            "permissions": ["search.web"]
        }
    )
    
    # 5. 定义复杂任务
    complex_task = """请帮我研究2024年三大AI公司的战略布局和发展方向，包括：
1. OpenAI - 了解其最新产品、战略重点和商业模式
2. Google DeepMind - 了解其在AI领域的布局和主要研究方向
3. Anthropic - 了解Claude模型的发展和公司战略

要求：
1. 分别搜索这三个公司的相关信息
2. 收集每个公司的关键信息（产品、技术、战略等）
3. 对比分析这三个公司的差异和共同点
4. 总结它们的竞争优势和发展趋势
5. 生成一份综合研究报告

请使用搜索工具获取最新的信息，并进行深入分析。"""
    
    print("📋 任务描述:")
    print(complex_task)
    print()
    print("-" * 80)
    print("开始执行...")
    print("-" * 80)
    print()
    print("💡 提示：")
    print("   - Agent会先制定执行计划")
    print("   - 然后按照计划使用搜索工具获取信息")
    print("   - 最后聚合分析结果生成报告")
    print("   - 这可能需要几分钟时间，请耐心等待...")
    print()
    
    # 6. 执行任务
    try:
        response = await agent.process(complex_task, context)
        
        print()
        print("-" * 80)
        print("✅ 任务执行完成！")
        print("-" * 80)
        print()
        print("📊 Agent的最终响应:")
        print("=" * 80)
        print(response)
        print("=" * 80)
        print()
        
        # 7. 显示执行统计
        print("📈 执行统计:")
        print(f"  - 总步数: {context.steps_taken}")
        print(f"  - Token使用: {context.tokens_used:,}")
        print(f"  - 成本: ${context.cost_incurred:.6f}")
        if context.start_time and context.end_time:
            duration = (context.end_time - context.start_time).total_seconds()
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            print(f"  - 执行时间: {minutes}分{seconds}秒")
        
        # 显示预算使用情况
        if context.budget:
            budget_usage = (context.cost_incurred / context.budget) * 100
            print(f"  - 预算使用: {budget_usage:.2f}% (${context.cost_incurred:.6f} / ${context.budget:.2f})")
        print()
        
        # 8. 显示Agent的计划（如果有）
        if hasattr(agent, 'current_plan') and agent.current_plan:
            print("📝 Agent制定的计划:")
            for i, step in enumerate(agent.current_plan, 1):
                print(f"  {i}. {step}")
            print()
        
        # 9. 显示消息历史统计
        if agent.state and agent.state.messages:
            tool_calls_count = sum(
                1 for msg in agent.state.messages
                if msg.tool_calls and len(msg.tool_calls) > 0
            )
            print("💬 对话统计:")
            print(f"  - 总消息数: {len(agent.state.messages)}")
            print(f"  - 工具调用次数: {tool_calls_count}")
            print()
        
        # 10. 验证结果
        print("🔍 验证:")
        assert response is not None, "Agent应该返回响应"
        assert len(response) > 0, "响应不应为空"
        assert context.steps_taken > 0, "应该执行了至少一步"
        
        # 检查是否进行了搜索
        if agent.state and agent.state.messages:
            has_search = any(
                msg.tool_calls and any(
                    tc.name == "web_search" for tc in msg.tool_calls
                )
                for msg in agent.state.messages
                if msg.tool_calls
            )
            if has_search:
                print("  ✅ 使用了搜索工具")
            else:
                print("  ⚠️  未检测到搜索工具调用（可能是直接回答或使用了其他方法）")
        
        print("  ✅ 所有基本验证通过！")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("❌ 执行过程中出现错误:")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {str(e)}")
        print()
        print("详细错误信息:")
        import traceback
        traceback.print_exc()
        print()
        return False


async def main():
    """主函数"""
    print()
    print("🚀 启动 Plan and Solve Agent 多次搜索任务测试")
    print()
    
    success = await test_plan_solve_multiple_search_task()
    
    print()
    print("=" * 80)
    if success:
        print("🎉 测试成功完成！")
        print("=" * 80)
        print()
        print("这个测试展示了 Plan and Solve Agent 如何：")
        print("1. ✅ 接收复杂任务并自动分解为多个步骤")
        print("2. ✅ 使用真实的搜索工具进行多次搜索")
        print("3. ✅ 按照计划逐步执行任务")
        print("4. ✅ 聚合分析多个搜索结果并生成最终报告")
        print()
        print("💡 提示:")
        print("   - 这是一个真实的测试，会调用真实的API")
        print("   - 会产生API调用费用（SerpApi和LLM）")
        print("   - 可以通过调整 budget 参数控制成本")
    else:
        print("❌ 测试失败或中断")
        print("=" * 80)
        print()
        print("可能的原因：")
        print("   - 环境变量未正确配置")
        print("   - API密钥无效或额度不足")
        print("   - 网络连接问题")
        print("   - 执行超时或超出预算")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

