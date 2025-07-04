"""
MindCell - 思维Cell实现

专门处理思考逻辑、推理过程和认知功能
"""
import logging
from typing import Dict, Any, List, Optional
from ..core.cell import Cell
from ..core.config import get_api_key, get_api_base_url, get_config
from ..core.exceptions import CellConfigurationError


class MindCell(Cell):
    """思维Cell - 专门处理思考逻辑和推理过程"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化MindCell
        
        Args:
            config: Cell配置，可包含：
                - model_name: 用于思考的模型名称
                - thinking_modes: 支持的思考模式配置
                - max_thinking_tokens: 思考过程最大token数
        """
        super().__init__(config)
        
        # API配置
        self.api_key = self.config.get("api_key")
        self.base_url = self.config.get("base_url")
        self.timeout = self.config.get("timeout", 300)
        
        # 思考模式配置
        self.thinking_modes = self.config.get("thinking_modes", {
            "chain_of_thought": True,    # 思维链
            "step_by_step": True,        # 逐步推理
            "reflection": True,          # 反思模式
            "planning": True,            # 规划模式
            "analysis": True             # 分析模式
        })
        
        # 模型配置
        self.model_name = self.config.get("model_name", "gpt-4")
        self.max_thinking_tokens = self.config.get("max_thinking_tokens", 1000)
        
        # 检测模型能力
        self.model_capabilities = self._detect_model_capabilities()
        
        self.logger.info(f"MindCell initialized with model: {self.model_name}")
        self.logger.info(f"Thinking capabilities: {self.model_capabilities}")
    
    async def process_async(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        异步版本的思考过程处理 - 用于纯异步调用链
        
        Args:
            context: 包含以下字段：
                - action: 操作类型 (默认"generate_thinking")
                - user_input: 用户问题或输入
                - conversation_context: 对话上下文（可选）
                - thinking_mode: 思考模式
                - mind_rule: 思维规则/个性化思考指导（可选）
                
        Returns:
            Dict包含思考过程结果
        """
        user_input = context.get("user_input", "")
        thinking_mode = context.get("thinking_mode", "reflection")
        mind_rule = context.get("mind_rule", None)
        
        if not user_input:
            raise CellConfigurationError("user_input is required for MindCell processing")
        
        try:
            return await self._generate_thinking_process_async(user_input, thinking_mode, context, mind_rule)
                
        except Exception as e:
            self.logger.error(f"MindCell async processing failed: {e}")
            return {
                "thinking_process": f"思考过程出现错误: {str(e)}",
                "confidence": 0.0,
                "thinking_mode": thinking_mode,
                "mind_rule_applied": mind_rule is not None,
                "error": str(e)
            }

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理思考过程
        
        Args:
            context: 包含以下字段：
                - action: 操作类型 (默认"generate_thinking")
                - user_input: 用户问题或输入
                - conversation_context: 对话上下文（可选）
                - thinking_mode: 思考模式 ("chain_of_thought", "step_by_step", "reflection", "planning", "analysis")
                - mind_rule: 思维规则/个性化思考指导（可选）
                
        Returns:
            Dict包含：
                - thinking_process: 详细的思考过程（LLM完整输出）
                - confidence: 置信度 (0.0-1.0)
                - thinking_mode: 使用的思考模式
                - mind_rule_applied: 是否应用了思维规则
        """
        user_input = context.get("user_input", "")
        thinking_mode = context.get("thinking_mode", "reflection")
        mind_rule = context.get("mind_rule", None)
        
        if not user_input:
            raise CellConfigurationError("user_input is required for MindCell processing")
        
        try:
            return self._generate_thinking_process(user_input, thinking_mode, context, mind_rule)
                
        except Exception as e:
            self.logger.error(f"MindCell processing failed: {e}")
            return {
                "thinking_process": f"思考过程出现错误: {str(e)}",
                "confidence": 0.0,
                "thinking_mode": thinking_mode,
                "mind_rule_applied": mind_rule is not None,
                "error": str(e)
            }
    
    async def _generate_thinking_process_async(self, user_input: str, mode: str, context: Dict, mind_rule: str = None) -> Dict[str, Any]:
        """异步版本的思考过程生成 - 核心方法"""
        conversation_context = context.get("conversation_context", "")
        
        # 构建思考提示词
        thinking_prompt = self._build_thinking_prompt(user_input, conversation_context, mode, mind_rule)
        
        # 异步调用LLM生成思考过程
        thinking_content = await self._call_llm_async(thinking_prompt, mode, mind_rule)
        
        return {
            "thinking_process": thinking_content,  # 直接使用LLM的完整输出
            "confidence": 0.85,
            "thinking_mode": mode,
            "mind_rule_applied": mind_rule is not None
        }
    
    def _generate_thinking_process(self, user_input: str, mode: str, context: Dict, mind_rule: str = None) -> Dict[str, Any]:
        """生成思考过程 - 核心方法"""
        conversation_context = context.get("conversation_context", "")
        
        # 构建思考提示词
        thinking_prompt = self._build_thinking_prompt(user_input, conversation_context, mode, mind_rule)
        
        # 调用LLM生成思考过程
        thinking_content = self._call_llm(thinking_prompt, mode, mind_rule)
        
        return {
            "thinking_process": thinking_content,  # 直接使用LLM的完整输出
            "confidence": 0.85,
            "thinking_mode": mode,
            "mind_rule_applied": mind_rule is not None
        }
    
    def _build_thinking_prompt(self, user_input: str, context: str, mode: str, mind_rule: str = None) -> str:
        """构建思考提示词 - 统一的提示词构建方法"""
        
        # 基础提示词
        base_prompt = f"""请对以下问题进行深度思考分析：

问题：{user_input}"""
        
        if context:
            base_prompt += f"\n上下文：{context}"
        
        # 根据思考模式添加具体指导
        mode_instructions = {
            "chain_of_thought": """

请按照思维链方式逐步分析：
1. 理解问题的核心含义
2. 识别关键影响因素
3. 进行逻辑推理分析
4. 得出合理结论

请详细展示你的思考过程。""",
            
            "reflection": """

请按照反思性思维进行深度分析：
1. 深入思考问题的本质和核心
2. 识别重要的影响因素和变量
3. 探索可能的解决方法和路径
4. 预测可能的结果和影响
5. 进行批判性反思和评估

请展示你的深度反思过程。""",
            
            "step_by_step": """

请按照逐步分析的方式：
1. 分解问题的各个组成部分
2. 逐一分析每个部分
3. 综合各部分的分析结果
4. 形成整体性的结论

请详细展示每个步骤的分析。""",
            
            "planning": """

请制定详细的解决方案：
1. 目标明确和现状分析
2. 路径规划和步骤分解
3. 资源需求和时间估算
4. 风险评估和备选方案

请提供结构化的规划过程。""",
            
            "analysis": """

请进行深入分析：
1. 问题定义和背景分析
2. 关键要素和影响因素
3. 多角度分析和推理
4. 综合评估和建议

请展示你的分析过程。"""
        }
        
        base_prompt += mode_instructions.get(mode, mode_instructions["analysis"])
        
        # 如果有MindRule，添加个性化思维指导
        if mind_rule:
            base_prompt += f"""

🧠 重要：请在思考过程中体现以下个性化思维特征：
{mind_rule}

请让你的思考过程和分析风格充分体现这些思维特征，用符合这种个性的方式来分析问题、表达观点。"""
        
        return base_prompt
    
    def _call_llm(self, thinking_prompt: str, mode: str, mind_rule: str = None) -> str:
        """调用LLM进行思考 - 唯一的LLM调用方法"""
        
        try:
            # 导入LLMCell来进行真实的LLM调用
            from ..cells.llm_cell import LLMCell
            
            # 创建临时的LLMCell实例进行思考，传递完整配置
            thinking_llm = LLMCell(
                model_name=self.model_name,
                config={
                    "api_key": self.api_key or get_api_key(),
                    "base_url": self.base_url or get_api_base_url(),
                    "timeout": self.timeout
                }
            )
            
            # 构建思考请求
            thinking_context = {
                "messages": [
                    {
                        "role": "system",
                        "content": """你是一个专业的深度思考助手，能够进行各种模式的智能分析和推理。

你的任务是：
1. 根据指定的思维模式进行深度思考
2. 如果提供了个性化思维规则，要在思考中充分体现这些特征
3. 生成详细、深入、有洞察力的思考过程
4. 确保思考过程逻辑清晰、结构完整、个性鲜明

请提供高质量的思考分析，充分体现个性化思维特征。"""
                    },
                    {
                        "role": "user",
                        "content": thinking_prompt
                    }
                ]
            }
            
            # 调用LLM进行真实思考
            result = thinking_llm.process(thinking_context)
            
            # 检查返回结果的格式
            if isinstance(result, dict):
                thinking_content = result.get("response", str(result))
            else:
                thinking_content = str(result)
            
            # 确保返回的是有效内容
            if thinking_content and len(thinking_content.strip()) > 50:
                self.logger.info(f"LLM思考成功生成，内容长度: {len(thinking_content)}")
                return thinking_content
            else:
                self.logger.warning(f"LLM思考内容过短或为空，使用智能降级")
                return self._fallback_thinking(thinking_prompt, mode, mind_rule)
                
        except Exception as e:
            self.logger.warning(f"LLM思考调用失败，使用智能降级: {e}")
            return self._fallback_thinking(thinking_prompt, mode, mind_rule)
    
    async def _call_llm_async(self, thinking_prompt: str, mode: str, mind_rule: str = None) -> str:
        """异步调用LLM进行思考 - 纯异步版本"""
        
        try:
            # 导入LLMCell来进行真实的LLM调用
            from ..cells.llm_cell import LLMCell
            
            # 创建临时的LLMCell实例进行思考，传递完整配置
            thinking_llm = LLMCell(
                model_name=self.model_name,
                config={
                    "api_key": self.api_key or get_api_key(),
                    "base_url": self.base_url or get_api_base_url(),
                    "timeout": self.timeout,
                    "enable_tools": False  # 思考过程中不需要工具调用
                }
            )
            
            # 构建思考请求的消息
            messages = [
                {
                    "role": "system",
                    "content": """你是一个专业的深度思考助手，能够进行各种模式的智能分析和推理。

你的任务是：
1. 根据指定的思维模式进行深度思考
2. 如果提供了个性化思维规则，要在思考中充分体现这些特征
3. 生成详细、深入、有洞察力的思考过程
4. 确保思考过程逻辑清晰、结构完整、个性鲜明

请提供高质量的思考分析，充分体现个性化思维特征。"""
                },
                {
                    "role": "user",
                    "content": thinking_prompt
                }
            ]
            
            # 直接使用LLMCell的异步方法
            result = await thinking_llm._handle_conversation_with_tools(
                messages,
                temperature=0.7,
                max_tokens=self.max_thinking_tokens
            )
            
            thinking_content = result.get("response", "")
            
            # 确保返回的是有效内容
            if thinking_content and len(thinking_content.strip()) > 50:
                self.logger.info(f"异步LLM思考成功生成，内容长度: {len(thinking_content)}")
                return thinking_content
            else:
                self.logger.warning(f"异步LLM思考内容过短或为空，使用智能降级")
                return self._fallback_thinking(thinking_prompt, mode, mind_rule)
                
        except Exception as e:
            self.logger.warning(f"异步LLM思考调用失败，使用智能降级: {e}")
            return self._fallback_thinking(thinking_prompt, mode, mind_rule)
    
    def _fallback_thinking(self, prompt: str, mode: str, mind_rule: str = None) -> str:
        """智能降级思考过程"""
        
        # 从提示词中提取用户问题
        user_question = self._extract_user_question(prompt)
        
        thinking_parts = []
        
        if mode == "reflection":
            thinking_parts.append(f"让我深入反思这个问题：{user_question}")
            thinking_parts.append("")
            thinking_parts.append("问题本质：需要从多个角度深入分析这个问题的核心")
            thinking_parts.append("关键要素：识别影响决策的重要因素")
            thinking_parts.append("解决思路：探索可行的解决方案和策略")
            thinking_parts.append("预期结果：评估不同选择可能带来的结果")
        elif mode == "chain_of_thought":
            thinking_parts.append(f"让我用思维链方式分析：{user_question}")
            thinking_parts.append("")
            thinking_parts.append("步骤1：理解问题核心和背景")
            thinking_parts.append("步骤2：识别关键影响因素")
            thinking_parts.append("步骤3：进行逻辑推理分析")
            thinking_parts.append("步骤4：得出合理结论")
        else:
            thinking_parts.append(f"让我分析这个问题：{user_question}")
            thinking_parts.append("")
            thinking_parts.append("分析要点：问题的核心要素和影响因素")
            thinking_parts.append("推理过程：基于逻辑和经验进行分析")
            thinking_parts.append("初步结论：综合考虑得出的观点")
        
        # 如果有MindRule，添加个性化思考
        if mind_rule:
            thinking_parts.append("")
            thinking_parts.append("=== 基于个性化思维规则的深度思考 ===")
            
            # 根据MindRule的特征生成个性化思考
            if "直接" in mind_rule or "火爆" in mind_rule or "犀利" in mind_rule:
                thinking_parts.append(f"说实话，{user_question}这个问题我必须直接告诉你真相。")
                thinking_parts.append("从投资的角度，我需要评估收益潜力、风险水平、市场时机等关键因素。")
            elif "温和" in mind_rule or "细腻" in mind_rule or "优雅" in mind_rule or "多愁善感" in mind_rule:
                thinking_parts.append(f"容我细细思量，关于{user_question}这个问题...")
                thinking_parts.append("以我的理解，这个问题需要细致入微的分析，考虑各方面的因素和可能的影响。")
            else:
                thinking_parts.append(f"基于我的思维特色，对'{user_question}'进行深度思考：")
                thinking_parts.append("结合我独特的分析视角和判断标准来处理这个问题。")
        
        return "\n".join(thinking_parts)
    
    def _extract_user_question(self, prompt: str) -> str:
        """从提示词中提取用户问题"""
        lines = prompt.split("\n")
        for line in lines:
            if line.startswith("问题："):
                return line.replace("问题：", "").strip()
        
        # 如果没找到标准格式，尝试其他方式提取
        for line in lines:
            line = line.strip()
            if line and not line.startswith(("请", "分析", "思考", "上下文")):
                return line
        
        return "未能识别的问题"
    
    def _detect_model_capabilities(self) -> Dict[str, bool]:
        """检测模型是否支持思考过程"""
        model_name = self.model_name.lower()
        
        # 支持思考过程的模型列表
        thinking_models = ["o1", "o1-preview", "o1-mini", "claude-3-5-sonnet", "gpt-4", "gpt-3.5", "claude"]
        
        supports_thinking = any(model in model_name for model in thinking_models)
        
        return {
            "supports_thinking": supports_thinking,
            "supports_reflection": True,
            "supports_planning": True,
            "supports_analysis": True
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取MindCell状态"""
        status = super().get_status()
        status.update({
            "model_name": self.model_name,
            "thinking_modes": self.thinking_modes,
            "model_capabilities": self.model_capabilities,
            "max_thinking_tokens": self.max_thinking_tokens
        })
        return status 