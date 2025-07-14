"""
Cell抽象基类 - FuturEmbryo框架的基石

定义所有Cell的基础接口和行为，支持同步和异步操作
"""
import time
import uuid
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, Awaitable
from .state import CellState
from .config import get_config
from .exceptions import CellExecutionError, CellTimeoutError, CellConfigurationError


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
        
        # 设置日志
        self.logger = logging.getLogger(f"futurembryo.{self.name}")
        self.logger.setLevel(get_config("log_level", "INFO"))
        
        # 创建日志处理器（如果不存在）
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(get_config("log_format"))
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.info(f"Created {self.name} with ID: {self.cell_id}")
    
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
    
    def clone(self) -> 'Cell':
        """克隆Cell（用于分裂等操作）"""
        # 创建相同类型的新实例
        new_cell = self.__class__(config=self.config.copy())
        self.logger.info(f"Cloned to new cell: {new_cell.cell_id}")
        return new_cell
    
    def __str__(self) -> str:
        return f"{self.name}(id={self.cell_id}, state={self.state.value})"
    
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(cell_id='{self.cell_id}', "
                f"state={self.state.value}, executions={self.execution_count})") 