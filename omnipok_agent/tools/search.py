"""Web search tools for agents using SerpApi."""
import os
import asyncio
from typing import Optional
from langchain_core.tools import tool


@tool
async def web_search(query: str) -> str:
    """
    一个基于SerpApi的实战网页搜索引擎工具。
    它会智能地解析搜索结果，优先返回直接答案或知识图谱信息。
    
    Args:
        query: 搜索查询字符串
        
    Returns:
        搜索结果文本，优先返回直接答案、知识图谱或前几个搜索结果摘要
    """
    print(f"🔍 正在执行 [SerpApi] 网页搜索: {query}")
    
    try:
        # 尝试导入 SerpApi
        try:
            from serpapi import SerpApiClient
        except ImportError:
            return (
                "错误: 未安装 google-search-results 库。\n"
                "请运行: pip install google-search-results"
            )
        
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return (
                "错误: SERPAPI_API_KEY 未在 .env 文件中配置。\n"
                "请前往 https://serpapi.com/ 注册免费账户并获取API密钥。"
            )
        
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",  # 国家代码
            "hl": "zh-cn",  # 语言代码
        }
        
        # SerpApi 客户端是同步的，使用 asyncio.to_thread 避免阻塞
        def _execute_search():
            client = SerpApiClient(params)
            return client.get_dict()
        
        results = await asyncio.to_thread(_execute_search)
        
        # 智能解析: 优先寻找最直接的答案
        if "answer_box_list" in results and results["answer_box_list"]:
            answers = []
            for answer_box in results["answer_box_list"]:
                if "answer" in answer_box:
                    answers.append(answer_box["answer"])
                elif "snippet" in answer_box:
                    answers.append(answer_box["snippet"])
            if answers:
                return "\n\n".join(answers)
        
        if "answer_box" in results and results["answer_box"]:
            answer_box = results["answer_box"]
            if "answer" in answer_box:
                return answer_box["answer"]
            elif "snippet" in answer_box:
                return answer_box["snippet"]
            elif "title" in answer_box and "snippet" in answer_box:
                return f"{answer_box['title']}\n{answer_box['snippet']}"
        
        if "knowledge_graph" in results and results["knowledge_graph"]:
            kg = results["knowledge_graph"]
            description = kg.get("description", "")
            if description:
                return description
        
        # 如果没有直接答案，则返回前三个有机结果的摘要
        if "organic_results" in results and results["organic_results"]:
            snippets = []
            for i, res in enumerate(results["organic_results"][:3], 1):
                title = res.get("title", "")
                snippet = res.get("snippet", "")
                link = res.get("link", "")
                if title or snippet:
                    result_text = f"[{i}] {title}"
                    if snippet:
                        result_text += f"\n{snippet}"
                    if link:
                        result_text += f"\n来源: {link}"
                    snippets.append(result_text)
            
            if snippets:
                return "\n\n".join(snippets)
        
        return f"对不起，没有找到关于 '{query}' 的信息。"
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 搜索时发生错误: {error_msg}")
        return f"搜索时发生错误: {error_msg}"

# Set metadata after tool creation
web_search.metadata = {"required_permissions": ["search.web"]}

