"""
Cell抽象基类 - FuturEmbryo框架的基石

定义所有Cell的基础接口和行为，支持同步和异步操作
集成IERT生命元素和上下文工程系统
"""
import time
import uuid
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, Awaitable, List
from .state import CellState
from .config import get_config
from .exceptions import CellExecutionError, CellTimeoutError, CellConfigurationError
from .iert_elements import IERTElementManager
from .context_architecture import ContextStructure, ContextArchitectureManager, ContextUnit, ContextType


class Cell(ABC):
    """Cell抽象基类 - 所有智能体功能的最小单位"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Cell
        
        Args:
            config: Cell配置字典，可覆盖全局配置
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        self.cell_id = f"{self.name}_{uuid.uuid4().hex[:8]}"
        self.state = CellState.IDLE
        
        # 执行统计
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.last_execution_time = None
        self.last_error = None
        
        # 配置参数（支持局部覆盖全局配置）
        # 对于LLMCell，特别是使用工具时，需要更长的超时时间
        default_timeout = 300.0 if self.__class__.__name__ == "LLMCell" else 30.0
        self.timeout = self.config.get("timeout", default_timeout)
        self.max_retries = self.config.get("max_retries", get_config("default_max_retries", 3))
        
        # 🧬 新增：IERT生命元素系统
        self.life_elements = IERTElementManager(self.config)
        
        # 🧠 新增：上下文工程系统  
        self.context_manager = ContextArchitectureManager()
        self.primary_context_id = self.context_manager.create_structure(
            f"cell_{self.cell_id}_context", 
            max_units=self.config.get("max_context_units", 50)
        )
        
        # 🎯 新增：数字生命属性
        self.generation = self.config.get("generation", 1)
        self.evolution_history: List[Dict[str, Any]] = []
        self.life_card: Optional[Dict[str, Any]] = None
        self.collaboration_partners: List[str] = []
        
        # 设置日志
        self.logger = logging.getLogger(f"futurembryo.{self.name}")
        self.logger.setLevel(get_config("log_level", "INFO"))
        
        # 创建日志处理器（如果不存在）
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(get_config("log_format"))
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.info(f"Created {self.name} with ID: {self.cell_id} | DLL: {self.life_elements.get_signature()}")
        
        # 初始化身份上下文
        self._initialize_identity_context()
    
    @abstractmethod
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑 - 子类必须实现
        
        Args:
            context: 输入上下文字典
            
        Returns:
            Dict[str, Any]: 处理结果字典
        """
        pass
    
    async def process_async(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        异步处理逻辑 - 子类可以重写以提供原生异步支持
        默认实现会将同步process方法包装为异步
        
        Args:
            context: 输入上下文字典
            
        Returns:
            Dict[str, Any]: 处理结果字典
        """
        # 默认实现：在线程池中执行同步方法
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.process, context)
    
    def __call__(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        统一调用接口 - 自动处理状态管理、错误处理、日志记录
        
        Args:
            context: 输入上下文字典
            
        Returns:
            Dict[str, Any]: 包含处理结果和元数据的字典
        """
        start_time = time.time()
        self.execution_count += 1
        
        try:
            # 状态转换：IDLE -> STARTING
            self._set_state(CellState.STARTING)
            self.logger.info(f"Starting execution #{self.execution_count}")
            
            # 输入验证
            validated_context = self._validate_input(context)
            
            # 状态转换：STARTING -> PROCESSING
            self._set_state(CellState.PROCESSING)
            
            # 执行核心逻辑（带超时控制）
            result = self._execute_with_timeout(validated_context)
            
            # 状态转换：PROCESSING -> COMPLETING
            self._set_state(CellState.COMPLETING)
            
            # 输出验证
            validated_result = self._validate_output(result)
            
            # 状态转换：COMPLETING -> COMPLETED
            self._set_state(CellState.COMPLETED)
            
            # 记录执行时间
            execution_time = time.time() - start_time
            self.last_execution_time = execution_time
            self.total_execution_time += execution_time
            
            self.logger.info(f"Execution completed in {execution_time:.3f}s")
            
            # 返回标准格式结果
            return self._format_response(validated_result, execution_time, success=True)
            
        except Exception as e:
            # 状态转换：ANY -> ERROR
            self._set_state(CellState.ERROR)
            self.last_error = e
            
            execution_time = time.time() - start_time
            error_msg = f"Execution failed after {execution_time:.3f}s: {str(e)}"
            self.logger.error(error_msg)
            
            # 返回错误格式结果
            return self._format_response(
                None, execution_time, success=False, error=str(e)
            )
    
    async def __call_async__(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        异步统一调用接口 - 自动处理状态管理、错误处理、日志记录
        
        Args:
            context: 输入上下文字典
            
        Returns:
            Dict[str, Any]: 包含处理结果和元数据的字典
        """
        start_time = time.time()
        self.execution_count += 1
        
        try:
            # 状态转换：IDLE -> STARTING
            self._set_state(CellState.STARTING)
            self.logger.info(f"Starting async execution #{self.execution_count}")
            
            # 输入验证
            validated_context = self._validate_input(context)
            
            # 状态转换：STARTING -> PROCESSING
            self._set_state(CellState.PROCESSING)
            
            # 执行核心逻辑（异步带超时控制）
            result = await self._execute_async_with_timeout(validated_context)
            
            # 状态转换：PROCESSING -> COMPLETING
            self._set_state(CellState.COMPLETING)
            
            # 输出验证
            validated_result = self._validate_output(result)
            
            # 状态转换：COMPLETING -> COMPLETED
            self._set_state(CellState.COMPLETED)
            
            # 记录执行时间
            execution_time = time.time() - start_time
            self.last_execution_time = execution_time
            self.total_execution_time += execution_time
            
            self.logger.info(f"Async execution completed in {execution_time:.3f}s")
            
            # 返回标准格式结果
            return self._format_response(validated_result, execution_time, success=True)
            
        except Exception as e:
            # 状态转换：ANY -> ERROR
            self._set_state(CellState.ERROR)
            self.last_error = e
            
            execution_time = time.time() - start_time
            error_msg = f"Async execution failed after {execution_time:.3f}s: {str(e)}"
            self.logger.error(error_msg)
            
            # 返回错误格式结果
            return self._format_response(
                None, execution_time, success=False, error=str(e)
            )
    
    async def _execute_async_with_timeout(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行带超时控制"""
        try:
            # 使用asyncio.wait_for进行超时控制
            result = await asyncio.wait_for(
                self.process_async(context), 
                timeout=self.timeout
            )
            return result
        except asyncio.TimeoutError:
            raise CellTimeoutError(self.name, self.timeout)
        except Exception as e:
            raise CellExecutionError(self.name, str(e), e)
    
    def _set_state(self, new_state: CellState):
        """设置Cell状态"""
        old_state = self.state
        self.state = new_state
        self.logger.debug(f"State changed: {old_state} -> {new_state}")
    
    def _validate_input(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """输入验证 - 子类可重写"""
        if not isinstance(context, dict):
            raise CellConfigurationError(f"Input context must be a dict, got {type(context)}")
        return context
    
    def _validate_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """输出验证 - 子类可重写"""
        if not isinstance(result, dict):
            raise CellExecutionError(
                self.name, 
                f"Process method must return a dict, got {type(result)}"
            )
        return result
    
    def _execute_with_timeout(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """带超时控制的执行"""
        import threading
        import signal
        
        # 检查是否在主线程中
        is_main_thread = threading.current_thread() is threading.main_thread()
        
        if is_main_thread and hasattr(signal, 'SIGALRM'):
            # 在主线程中使用信号超时控制
            def timeout_handler(signum, frame):
                raise CellTimeoutError(self.name, self.timeout)
            
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(self.timeout))
                
                result = self.process(context)
                
                signal.alarm(0)
                return result
                
            except CellTimeoutError:
                signal.alarm(0)
                raise
            except Exception as e:
                signal.alarm(0)
                raise CellExecutionError(self.name, str(e), e)
        else:
            # 在子线程中或不支持信号的系统中，直接执行（暂时不支持超时）
            try:
                result = self.process(context)
                return result
            except Exception as e:
                raise CellExecutionError(self.name, str(e), e)
    
    def _format_response(self, data: Any, execution_time: float, 
                        success: bool = True, error: str = None) -> Dict[str, Any]:
        """格式化响应结果"""
        response = {
            "success": success,
            "data": data,
            "error": error,
            "metadata": {
                "cell_id": self.cell_id,
                "cell_name": self.name,
                "cell_state": self.state.value,
                "execution_count": self.execution_count,
                "execution_time": execution_time,
                "timestamp": time.time()
            }
        }
        return response
    
    def get_status(self) -> Dict[str, Any]:
        """获取Cell当前状态信息"""
        avg_execution_time = (
            self.total_execution_time / self.execution_count 
            if self.execution_count > 0 else 0
        )
        
        return {
            "cell_id": self.cell_id,
            "cell_name": self.name,
            "state": self.state.value,
            "execution_count": self.execution_count,
            "avg_execution_time": avg_execution_time,
            "last_execution_time": self.last_execution_time,
            "last_error": str(self.last_error) if self.last_error else None,
            "config": self.config
        }
    
    def reset(self):
        """重置Cell状态"""
        self.state = CellState.IDLE
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.last_execution_time = None
        self.last_error = None
        self.logger.info(f"Cell {self.cell_id} reset")
    
    # 🧬 数字生命核心方法
    
    def _initialize_identity_context(self):
        """初始化身份上下文"""
        context_structure = self.context_manager.get_structure(self.primary_context_id)
        if context_structure:
            # 添加身份信息到上下文
            identity_unit = ContextUnit(
                type=ContextType.IDENTITY,
                content={
                    "cell_name": self.name,
                    "cell_id": self.cell_id,
                    "dll_signature": self.life_elements.get_signature(),
                    "generation": self.generation,
                    "role": self.config.get("role", "general_cell"),
                    "capabilities": self.config.get("capabilities", [])
                },
                priority=1.0,  # 身份信息总是高优先级
                metadata={"source": "initialization", "immutable": True}
            )
            context_structure.add_unit(f"identity_{self.cell_id}", identity_unit)
    
    def get_life_elements(self) -> IERTElementManager:
        """获取生命元素管理器"""
        return self.life_elements
    
    def get_dll_signature(self) -> str:
        """获取DLL签名"""
        return self.life_elements.get_signature()
    
    def get_detailed_signature(self) -> Dict[str, Any]:
        """获取详细的DLL签名"""
        return self.life_elements.get_detailed_signature()
    
    def evolve(self, feedback: Dict[str, Any], environment: Optional[Dict[str, Any]] = None) -> 'Cell':
        """
        Cell进化方法 - 基于反馈和环境进化出新的Cell实例
        
        Args:
            feedback: 反馈信息，包含性能指标和用户评价
            environment: 环境信息，影响进化策略
            
        Returns:
            Cell: 进化后的新Cell实例
        """
        try:
            # 分析反馈，生成进化策略
            evolution_strategy = self._analyze_feedback(feedback)
            
            # 基于策略和环境进化配置
            new_config = self._evolve_config(evolution_strategy, environment)
            
            # 创建新的Cell实例
            evolved_cell = self.__class__(new_config)
            evolved_cell.generation = self.generation + 1
            evolved_cell.evolution_history = self.evolution_history.copy()
            evolved_cell.evolution_history.append({
                "generation": evolved_cell.generation,
                "parent_id": self.cell_id,
                "strategy": evolution_strategy,
                "feedback": feedback,
                "environment": environment,
                "timestamp": time.time()
            })
            
            self.logger.info(f"Cell evolved: {self.cell_id} -> {evolved_cell.cell_id} (Gen {evolved_cell.generation})")
            return evolved_cell
            
        except Exception as e:
            self.logger.error(f"Evolution failed: {e}")
            return self  # 进化失败返回原实例
    
    def _analyze_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """分析反馈，确定进化方向"""
        strategy = {}
        
        # 性能维度分析
        performance = feedback.get("performance", {})
        if performance.get("accuracy", 1.0) < 0.7:
            strategy["improve_accuracy"] = True
        if performance.get("speed", 1.0) < 0.7:
            strategy["optimize_speed"] = True
        if performance.get("efficiency", 1.0) < 0.6:
            strategy["enhance_efficiency"] = True
            
        # 用户满意度分析
        user_satisfaction = feedback.get("user_satisfaction", 0.8)
        if user_satisfaction < 0.8:
            strategy["enhance_user_experience"] = True
            
        # 资源使用效率分析
        resource_efficiency = feedback.get("resource_efficiency", 1.0)
        if resource_efficiency < 0.6:
            strategy["optimize_resources"] = True
            
        return strategy
    
    def _evolve_config(self, strategy: Dict[str, Any], environment: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """基于策略进化配置"""
        new_config = self.config.copy()
        
        # 根据策略调整IERT元素
        if strategy.get("improve_accuracy"):
            # 信息维度优化
            current_info = self.life_elements.get_element("I")
            if current_info:
                new_config["context_window"] = min(current_info.context_window * 1.2, 8192)
                if "temperature" in new_config:
                    new_config["temperature"] = max(0.1, new_config["temperature"] - 0.1)
                    
        if strategy.get("optimize_speed"):
            # 能量维度优化
            current_energy = self.life_elements.get_element("E")
            if current_energy:
                new_config["power_mode"] = "turbo"
                new_config["max_tokens"] = min(new_config.get("max_tokens", 1000), 500)
                
        if strategy.get("enhance_user_experience"):
            # 关系维度优化
            current_relation = self.life_elements.get_element("R")
            if current_relation:
                new_config["social_weight"] = min(current_relation.social_weight + 0.1, 1.0)
                new_config["collaboration_style"] = "cooperative"
                
        # 环境适应性调整
        if environment:
            if environment.get("resource_constraint", False):
                new_config["power_mode"] = "low"
            if environment.get("high_concurrency", False):
                new_config["interaction_mode"] = "async"
            if environment.get("quality_focus", False):
                new_config["temperature"] = 0.3
                
        # 增加generation标记
        new_config["generation"] = self.generation + 1
        
        return new_config
    
    def sense_environment(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """
        感知环境变化
        
        Args:
            environment: 环境状态信息
            
        Returns:
            Dict: 环境分析结果和适应建议
        """
        environmental_pressure = {
            "resource_availability": environment.get("resources", 1.0),
            "competition_level": environment.get("competition", 0.0),
            "user_expectation": environment.get("expectations", 0.8),
            "system_load": environment.get("load", 0.5),
            "data_quality": environment.get("data_quality", 0.9),
            "network_latency": environment.get("latency", 0.1)
        }
        
        # 计算适应性得分
        adaptation_score = self._calculate_adaptation_score(environmental_pressure)
        
        return {
            "environmental_pressure": environmental_pressure,
            "adaptation_score": adaptation_score,
            "recommended_adjustments": self._suggest_adaptations(environmental_pressure),
            "current_fitness": self._calculate_current_fitness(environmental_pressure)
        }
    
    def _calculate_adaptation_score(self, pressure: Dict[str, float]) -> float:
        """计算环境适应性得分"""
        # 基于IERT四个维度计算适应性
        scores = []
        
        # 信息适应性
        info_element = self.life_elements.get_element("I")
        if info_element:
            info_score = min(info_element.context_window / 4096, 1.0) * pressure["data_quality"]
            scores.append(info_score)
        
        # 能量适应性  
        energy_element = self.life_elements.get_element("E")
        if energy_element:
            energy_score = (1.0 - energy_element.computational_cost / 5.0) * pressure["resource_availability"]
            scores.append(energy_score)
        
        # 关系适应性
        relation_element = self.life_elements.get_element("R")
        if relation_element:
            relation_score = relation_element.social_weight * (1.0 - pressure["competition_level"])
            scores.append(relation_score)
        
        # 时间适应性
        time_element = self.life_elements.get_element("T")
        if time_element:
            time_score = min(time_element.response_time_sla / 10.0, 1.0) * pressure["user_expectation"]
            scores.append(time_score)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _suggest_adaptations(self, pressure: Dict[str, float]) -> List[str]:
        """建议适应性调整"""
        suggestions = []
        
        if pressure["resource_availability"] < 0.5:
            suggestions.append("降低计算复杂度")
        if pressure["competition_level"] > 0.7:
            suggestions.append("增强协作能力")
        if pressure["user_expectation"] > 0.8:
            suggestions.append("提升响应质量")
        if pressure["system_load"] > 0.8:
            suggestions.append("优化并发处理")
        if pressure["data_quality"] < 0.6:
            suggestions.append("增强数据过滤")
        if pressure["network_latency"] > 0.3:
            suggestions.append("启用本地缓存")
            
        return suggestions
    
    def _calculate_current_fitness(self, pressure: Dict[str, float]) -> float:
        """计算当前适应度"""
        adaptation_score = self._calculate_adaptation_score(pressure)
        performance_score = min(self.execution_count / 100.0, 1.0)  # 执行经验
        error_penalty = max(0, 1.0 - (0.1 if self.last_error else 0))
        
        return (adaptation_score + performance_score + error_penalty) / 3.0
    
    def generate_life_card(self) -> Dict[str, Any]:
        """生成数字生命名片"""
        if self.life_card is None:
            self.life_card = {
                "identity": {
                    "name": self.name,
                    "cell_id": self.cell_id,
                    "dll_signature": self.get_dll_signature(),
                    "generation": self.generation,
                    "role": self.config.get("role", "general_cell")
                },
                "capabilities": {
                    "core_abilities": self._extract_core_abilities(),
                    "life_elements": self.life_elements.to_dict(),
                    "specializations": self.config.get("specializations", [])
                },
                "interface": {
                    "process_method": "process",
                    "input_format": "Dict[str, Any]",
                    "output_format": "Dict[str, Any]",
                    "async_supported": hasattr(self, "process_async")
                },
                "collaboration": {
                    "interaction_mode": self.life_elements.get_element("R").interaction_mode,
                    "collaboration_style": self.life_elements.get_element("R").collaboration_style,
                    "social_weight": self.life_elements.get_element("R").social_weight,
                    "partners": self.collaboration_partners.copy()
                },
                "evolution": {
                    "generation": self.generation,
                    "evolution_history": len(self.evolution_history),
                    "adaptation_score": getattr(self, "_last_adaptation_score", 0.8)
                },
                "performance": {
                    "execution_count": self.execution_count,
                    "avg_execution_time": self.total_execution_time / max(self.execution_count, 1),
                    "success_rate": 1.0 if self.last_error is None else 0.8,
                    "last_active": time.time()
                }
            }
        
        return self.life_card.copy()
    
    def _extract_core_abilities(self) -> List[str]:
        """提取核心能力"""
        abilities = []
        
        # 基于类名推断能力
        if "LLM" in self.name:
            abilities.extend(["text_generation", "reasoning", "conversation"])
        if "Mind" in self.name:
            abilities.extend(["thinking", "analysis", "decision_making"])
        if "Memory" in self.name:
            abilities.extend(["storage", "retrieval", "knowledge_management"])
        if "Tool" in self.name:
            abilities.extend(["tool_usage", "integration", "automation"])
        
        # 从配置中提取
        abilities.extend(self.config.get("abilities", []))
        abilities.extend(self.config.get("skills", []))
        
        return list(set(abilities))  # 去重
    
    def update_context(self, context_type: ContextType, content: Any, priority: float = 0.5):
        """更新上下文"""
        context_structure = self.context_manager.get_structure(self.primary_context_id)
        if context_structure:
            unit_id = f"{context_type.value}_{int(time.time())}"
            unit = ContextUnit(
                type=context_type,
                content=content,
                priority=priority,
                metadata={"updated_by": "cell", "cell_id": self.cell_id}
            )
            context_structure.add_unit(unit_id, unit)
    
    def get_context_summary(self) -> Dict[str, Any]:
        """获取上下文摘要"""
        context_structure = self.context_manager.get_structure(self.primary_context_id)
        if context_structure:
            return context_structure.get_summary()
        return {}
    
    def clone(self) -> 'Cell':
        """克隆Cell（用于分裂等操作）"""
        # 创建相同类型的新实例
        new_cell = self.__class__(config=self.config.copy())
        new_cell.generation = self.generation
        new_cell.evolution_history = self.evolution_history.copy()
        self.logger.info(f"Cloned to new cell: {new_cell.cell_id}")
        return new_cell
    
    def __str__(self) -> str:
        return f"{self.name}(id={self.cell_id}, dll={self.get_dll_signature()}, gen={self.generation})"
    
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(cell_id='{self.cell_id}', "
                f"dll='{self.get_dll_signature()}', generation={self.generation}, "
                f"executions={self.execution_count})") 