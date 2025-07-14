"""
Dynamic Agent Factory - AI驱动的智能体动态创建

基于任务需求和AI分析，动态生成专门的智能体，并配置相应的工具能力
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.user_aware_agent_v2 import UserAwareAgent
from pathlib import Path
import json
import sys

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from futurembryo.cells.llm_cell import LLMCell
from futurembryo.cells.tool_cell import ToolCell
from futurembryo.core.tool_registry import ToolRegistry, create_default_registry
from futurembryo.core.tool_config import ToolConfigManager, ToolsConfig, FunctionToolConfig
# 延迟导入避免循环依赖
from futurembryo.core.context_builder import ContextBuilder


class DynamicAgentFactory:
    """动态智能体工厂 - AI驱动的智能体创建"""
    
    def __init__(self, base_config_path: Optional[str] = None):
        """
        初始化动态智能体工厂
        
        Args:
            base_config_path: 基础配置文件路径
        """
        self.logger = logging.getLogger(__name__)
        self.base_config_path = base_config_path
        self.created_agents: Dict[str, 'UserAwareAgent'] = {}
        
        # 工具注册中心
        self.tool_registry = None
        self.tool_config_manager = ToolConfigManager()
        
        # 基础LLM配置
        self.base_llm_config = {
            "model": "anthropic/claude-sonnet-4-20250514",
            "temperature": 0.7,
            "max_tokens": 2000,
            "enable_tools": True,
            "tool_choice": "auto",
            "max_tool_calls": 3
        }
        
        self.logger.info("🏭 Dynamic Agent Factory initialized")
    
    async def initialize(self):
        """初始化工厂（异步操作）"""
        try:
            # 创建默认工具注册中心
            self.tool_registry = create_default_registry()
            self.logger.info("✅ Tool registry initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize tool registry: {e}")
            raise
    
    async def create_agent_from_design(self, agent_design: Dict[str, Any], user_id: str = "default"):
        """
        根据AI设计创建智能体
        
        Args:
            agent_design: AI生成的智能体设计配置
            user_id: 用户ID
            
        Returns:
            UserAwareAgent: 创建的智能体实例
        """
        # 动态导入以避免循环依赖
        from agents.user_aware_agent_v2 import UserAwareAgent
        
        try:
            agent_id = agent_design.get("agent_id", "dynamic_agent")
            agent_name = agent_design.get("name", agent_id)
            
            self.logger.info(f"🎯 Creating dynamic agent: {agent_name} ({agent_id})")
            
            # 1. 配置工具能力
            tool_cell = await self._create_tool_cell_for_agent(agent_design)
            
            # 2. 配置LLM
            llm_config = self._create_llm_config_for_agent(agent_design)
            
            # 3. 创建上下文构建器
            context_builder = ContextBuilder(
                user_id=user_id,
                enable_memory=agent_design.get("enable_memory", True),
                tool_cell=tool_cell
            )
            
            # 4. 构建智能体配置
            agent_config = {
                "name": agent_name,
                "role": agent_design.get("role", "assistant"),
                "system_prompt": agent_design.get("system_prompt", f"You are {agent_name}, a helpful AI assistant."),
                "capabilities": agent_design.get("capabilities", []),
                "llm_config": llm_config,
                "memory_config": {
                    "collection_name": f"{agent_id}_memory",
                    "max_memory_items": agent_design.get("max_memory_items", 100)
                }
            }
            
            # 5. 创建智能体
            agent = UserAwareAgent(
                agent_id=agent_id,
                agent_config=agent_config,
                context_builder=context_builder
            )
            
            # 6. 存储智能体
            self.created_agents[agent_id] = agent
            
            self.logger.info(f"✅ Dynamic agent created successfully: {agent_name}")
            self.logger.info(f"   - Tools: {len(await tool_cell.get_available_tools())} available")
            self.logger.info(f"   - Capabilities: {agent_config['capabilities']}")
            
            return agent
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create dynamic agent: {e}")
            raise
    
    async def _create_tool_cell_for_agent(self, agent_design: Dict[str, Any]) -> ToolCell:
        """为智能体创建配置好的工具Cell"""
        try:
            # 获取智能体需要的工具类型
            required_tools = agent_design.get("required_tools", [])
            tool_categories = agent_design.get("tool_categories", ["basic"])
            
            self.logger.info(f"🔧 Configuring tools for agent:")
            self.logger.info(f"   - Required tools: {required_tools}")
            self.logger.info(f"   - Tool categories: {tool_categories}")
            
            # 创建工具配置
            tools_config = self._build_tools_config(required_tools, tool_categories)
            
            # 创建ToolCell
            tool_cell = ToolCell(tools_config)
            
            # 验证工具是否正确加载
            available_tools = await tool_cell.get_available_tools()
            self.logger.info(f"✅ Tool cell created with {len(available_tools)} tools")
            
            return tool_cell
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create tool cell: {e}")
            # 创建基础工具Cell作为fallback
            return ToolCell({"auto_load_defaults": True})
    
    def _build_tools_config(self, required_tools: List[str], tool_categories: List[str]) -> Dict[str, Any]:
        """构建工具配置 - 基于fullagent的真实工具配置"""
        config = {
            "auto_load_defaults": True,  # 加载基础工具（add, multiply, text_length, text_upper）
            "tools": [],
            "mcp_servers": []
        }
        
        # 根据实际需求添加真实可用的MCP工具
        available_mcp_tools = {
            "knowledge_search": {
                "name": "context7",
                "command": ["npx", "-y", "@upstash/context7-mcp"],
                "description": "技术文档查询工具"
            },
            "news_search": {
                "name": "dynamic-knowledgebase-mcp", 
                "type": "sse",
                "url": "http://1.94.7.13:3001/sse",
                "description": "最新政经新闻动态知识库MCP服务器",
                "headers": {
                    "Authorization": "Bearer qX7p9Lk2YtRgV5mNcBz8SoWvZbJdEeAhHfP4"
                }
            }
        }
        
        # 根据工具类别和需求决定是否添加MCP工具
        if any(cat in ["research", "knowledge", "information", "search"] for cat in tool_categories):
            # 添加知识搜索工具
            if "knowledge_search" in required_tools or "research" in tool_categories:
                config["mcp_servers"].append(available_mcp_tools["knowledge_search"])
                self.logger.info("✅ Added context7 MCP tool for knowledge search")
            
            # 添加新闻搜索工具
            if "news_search" in required_tools or "current_events" in tool_categories:
                config["mcp_servers"].append(available_mcp_tools["news_search"])
                self.logger.info("✅ Added dynamic-knowledgebase MCP tool for news search")
        
        # 记录实际配置的工具
        self.logger.info(f"🔧 Built tools config with {len(config['mcp_servers'])} MCP servers")
        for server in config["mcp_servers"]:
            self.logger.info(f"   - {server['name']}: {server['description']}")
        
        return config
    
    def _create_llm_config_for_agent(self, agent_design: Dict[str, Any]) -> Dict[str, Any]:
        """为智能体创建LLM配置"""
        config = self.base_llm_config.copy()
        
        # 根据智能体设计调整参数
        if agent_design.get("creativity_level") == "high":
            config["temperature"] = 0.9
        elif agent_design.get("creativity_level") == "low":
            config["temperature"] = 0.3
        
        # 调整最大tokens
        if agent_design.get("task_complexity") == "complex":
            config["max_tokens"] = 3000
        elif agent_design.get("task_complexity") == "simple":
            config["max_tokens"] = 1000
        
        # 工具调用配置
        if agent_design.get("tool_usage") == "intensive":
            config["max_tool_calls"] = 5
        elif agent_design.get("tool_usage") == "minimal":
            config["max_tool_calls"] = 1
        
        return config
    
    def get_created_agent(self, agent_id: str) -> Optional['UserAwareAgent']:
        """获取已创建的智能体"""
        return self.created_agents.get(agent_id)
    
    def list_created_agents(self) -> List[str]:
        """列出所有已创建的智能体ID"""
        return list(self.created_agents.keys())
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体状态"""
        agent = self.get_created_agent(agent_id)
        if not agent:
            return {"exists": False}
        
        return {
            "exists": True,
            "agent_id": agent_id,
            "name": getattr(agent, 'name', agent_id),
            "status": agent.get_status() if hasattr(agent, 'get_status') else "unknown"
        }
    
    async def cleanup_agent(self, agent_id: str) -> bool:
        """清理智能体资源"""
        try:
            if agent_id in self.created_agents:
                agent = self.created_agents[agent_id]
                # 可以添加清理逻辑，如关闭连接等
                del self.created_agents[agent_id]
                self.logger.info(f"🗑️ Agent cleaned up: {agent_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"❌ Failed to cleanup agent {agent_id}: {e}")
            return False
    
    async def cleanup_all_agents(self):
        """清理所有智能体"""
        for agent_id in list(self.created_agents.keys()):
            await self.cleanup_agent(agent_id)
        self.logger.info("🧹 All dynamic agents cleaned up")


# 全局工厂实例
_global_factory = None

async def get_dynamic_agent_factory() -> DynamicAgentFactory:
    """获取全局动态智能体工厂实例"""
    global _global_factory
    if _global_factory is None:
        _global_factory = DynamicAgentFactory()
        await _global_factory.initialize()
    return _global_factory


# 便捷函数
async def create_agent_from_ai_design(agent_design: Dict[str, Any], user_id: str = "default"):
    """便捷函数：根据AI设计创建智能体"""
    factory = await get_dynamic_agent_factory()
    return await factory.create_agent_from_design(agent_design, user_id)


async def get_or_create_agent(agent_id: str, agent_design: Dict[str, Any], user_id: str = "default"):
    """获取现有智能体或创建新的智能体"""
    factory = await get_dynamic_agent_factory()
    
    # 先尝试获取现有智能体
    agent = factory.get_created_agent(agent_id)
    if agent:
        return agent
    
    # 创建新智能体
    return await factory.create_agent_from_design(agent_design, user_id)