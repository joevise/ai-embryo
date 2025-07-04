"""
提示词管理器 - 配置化提示词系统

负责从配置文件加载和管理所有提示词，支持动态替换和个性化定制
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging


class PromptManager:
    """
    提示词管理器
    
    功能：
    1. 从YAML配置文件加载提示词
    2. 支持模板变量替换
    3. 提供角色特定的提示词生成
    4. 支持运行时动态更新
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化提示词管理器
        
        Args:
            config_path: 提示词配置文件路径，默认使用项目内的prompts.yaml
        """
        self.logger = logging.getLogger(__name__)
        
        # 确定配置文件路径
        if config_path is None:
            current_dir = Path(__file__).parent.parent
            config_path = current_dir / "configs" / "prompts.yaml"
        
        self.config_path = Path(config_path)
        self.prompts = {}
        
        # 加载提示词配置
        self.load_prompts()
    
    def load_prompts(self):
        """从配置文件加载提示词"""
        try:
            if not self.config_path.exists():
                self.logger.warning(f"Prompts config file not found: {self.config_path}")
                self._create_default_prompts()
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.prompts = yaml.safe_load(f)
            
            self.logger.info(f"Prompts loaded from {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load prompts config: {e}")
            self._create_default_prompts()
    
    def _create_default_prompts(self):
        """创建默认提示词（作为后备）"""
        self.prompts = {
            "role_prompts": {
                "assistant": "你是一个智能助手。",
                "researcher": "你是一个专业的研究员。",
                "analyst": "你是一个数据分析师。",
                "writer": "你是一个专业写作者。"
            },
            "system_capabilities": {
                "user_awareness": "你具有用户感知能力。",
                "mention_system": "你支持@引用系统。"
            }
        }
    
    def get_role_prompt(self, role: str) -> str:
        """
        获取角色特定的提示词
        
        Args:
            role: 角色名称
            
        Returns:
            str: 角色提示词
        """
        role_prompts = self.prompts.get("role_prompts", {})
        return role_prompts.get(role, role_prompts.get("assistant", "你是一个智能助手。"))
    
    def get_system_prompt(self, 
                         role: str,
                         personality: List[str] = None,
                         capabilities: List[str] = None,
                         base_prompt: str = "You are a helpful AI assistant.",
                         **kwargs) -> str:
        """
        生成完整的系统提示词
        
        Args:
            role: 角色名称
            personality: 性格特征列表
            capabilities: 能力列表
            base_prompt: 基础提示词
            **kwargs: 其他模板变量
            
        Returns:
            str: 完整的系统提示词
        """
        try:
            # 获取各个组件
            role_prompt = self.get_role_prompt(role)
            
            # 格式化性格和能力
            personality_str = "、".join(personality or ["专业", "友好"])
            capabilities_str = "、".join(capabilities or ["通用对话"])
            
            # 获取系统能力说明
            capabilities_section = self.prompts.get("system_capabilities", {})
            user_awareness = capabilities_section.get("user_awareness", "")
            mention_system = capabilities_section.get("mention_system", "")
            behavior_guidelines = capabilities_section.get("behavior_guidelines", "")
            
            # 构建完整提示词
            system_capabilities = f"{user_awareness}\n\n{mention_system}"
            
            # 使用模板
            template = self.prompts.get("system_prompt_template", 
                                      "{base_prompt}\n\n{role_prompt}\n\n你的核心特质：{personality}\n你的主要能力：{capabilities}\n\n{system_capabilities}\n\n{behavior_guidelines}")
            
            prompt = template.format(
                base_prompt=base_prompt,
                role_prompt=role_prompt,
                personality=personality_str,
                capabilities=capabilities_str,
                system_capabilities=system_capabilities,
                behavior_guidelines=behavior_guidelines,
                **kwargs
            )
            
            return prompt.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to generate system prompt: {e}")
            # 返回简单的后备提示词
            return f"{base_prompt}\n\n{self.get_role_prompt(role)}"
    
    def get_context_aware_prompt(self,
                                base_prompt: str,
                                user_context: Dict[str, Any],
                                mention_contents: Dict[str, Any]) -> str:
        """
        生成上下文感知的提示词
        
        Args:
            base_prompt: 基础系统提示词
            user_context: 用户上下文信息
            mention_contents: @引用内容
            
        Returns:
            str: 增强的上下文感知提示词
        """
        try:
            enhanced_parts = [base_prompt]
            
            # 用户信息部分
            user_info_parts = []
            
            # 用户画像
            profile = user_context.get("user_profile", {})
            if profile.get("interests"):
                interests = ", ".join(profile["interests"])
                user_info_parts.append(f"用户兴趣：{interests}")
            
            if profile.get("expertise_areas"):
                expertise = ", ".join(profile["expertise_areas"])
                user_info_parts.append(f"用户专业领域：{expertise}")
            
            if profile.get("communication_style"):
                user_info_parts.append(f"用户偏好的沟通风格：{profile['communication_style']}")
            
            # 用户偏好
            preferences = user_context.get("user_preferences", {})
            if preferences.get("communication_prefs"):
                comm_prefs = preferences["communication_prefs"]
                high_pref = max(comm_prefs.items(), key=lambda x: x[1], default=None)
                if high_pref and high_pref[1] > 0.6:
                    user_info_parts.append(f"用户偏好：{high_pref[0]}")
            
            # 最近记忆
            recent_memories = user_context.get("recent_memories", [])
            if recent_memories:
                important_memories = [m["content"] for m in recent_memories[:2] if m.get("importance", 0) > 0.7]
                if important_memories:
                    user_info_parts.append(f"重要记忆：{'; '.join(important_memories)}")
            
            # @引用内容
            mention_info_parts = []
            for mention, content in mention_contents.items():
                if content.get("mention_type") == "user":
                    mention_info_parts.append(f"@{mention}已加载到上下文中")
            
            # 组合增强提示词
            if user_info_parts:
                enhanced_parts.append("\n当前用户信息：")
                enhanced_parts.extend([f"- {info}" for info in user_info_parts])
            
            if mention_info_parts:
                enhanced_parts.append("\n当前上下文：")
                enhanced_parts.extend([f"- {info}" for info in mention_info_parts])
            
            enhanced_parts.append("\n请根据用户信息个性化你的回复。")
            
            return "\n".join(enhanced_parts)
            
        except Exception as e:
            self.logger.error(f"Failed to generate context-aware prompt: {e}")
            return base_prompt
    
    def get_help_prompt(self, help_type: str = "general") -> str:
        """
        获取帮助提示词
        
        Args:
            help_type: 帮助类型 (general, mention)
            
        Returns:
            str: 帮助内容
        """
        help_prompts = self.prompts.get("help_prompts", {})
        return help_prompts.get(f"{help_type}_help", "抱歉，暂无相关帮助信息。")
    
    def get_error_prompt(self, error_type: str, **kwargs) -> str:
        """
        获取错误处理提示词
        
        Args:
            error_type: 错误类型
            **kwargs: 模板变量
            
        Returns:
            str: 错误提示信息
        """
        error_prompts = self.prompts.get("error_handling", {})
        template = error_prompts.get(error_type, "抱歉，出现了未知错误。")
        
        try:
            return template.format(**kwargs)
        except:
            return template
    
    def get_specialized_prompt(self, specialty: str) -> str:
        """
        获取专业化提示词
        
        Args:
            specialty: 专业类型
            
        Returns:
            str: 专业化提示词
        """
        specialized_prompts = self.prompts.get("specialized_prompts", {})
        return specialized_prompts.get(specialty, "")
    
    def reload_prompts(self):
        """重新加载提示词配置（用于运行时更新）"""
        self.logger.info("Reloading prompts configuration...")
        self.load_prompts()
    
    def get_all_available_roles(self) -> List[str]:
        """获取所有可用的角色列表"""
        return list(self.prompts.get("role_prompts", {}).keys())
    
    def validate_prompts(self) -> Dict[str, Any]:
        """
        验证提示词配置的完整性
        
        Returns:
            Dict: 验证结果
        """
        validation_result = {
            "valid": True,
            "missing_sections": [],
            "missing_roles": [],
            "warnings": []
        }
        
        # 检查必需的配置节
        required_sections = ["role_prompts", "system_capabilities", "help_prompts"]
        for section in required_sections:
            if section not in self.prompts:
                validation_result["missing_sections"].append(section)
                validation_result["valid"] = False
        
        # 检查基本角色
        required_roles = ["assistant", "researcher", "analyst", "writer"]
        role_prompts = self.prompts.get("role_prompts", {})
        for role in required_roles:
            if role not in role_prompts:
                validation_result["missing_roles"].append(role)
                validation_result["valid"] = False
        
        return validation_result


# 全局提示词管理器实例
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """获取全局提示词管理器实例"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager

def reload_global_prompts():
    """重新加载全局提示词配置"""
    global _prompt_manager
    if _prompt_manager is not None:
        _prompt_manager.reload_prompts()