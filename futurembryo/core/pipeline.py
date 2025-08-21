"""
Pipeline - Cell组合和流水线处理

提供多种Cell组合模式：顺序执行、并行执行、条件分支等

新增功能：
- 透明化执行过程：详细显示每个步骤的执行状态和结果
- 智能上下文传递：自动构建包含前一步结果的上下文输入
- Cell标准接口：返回符合Cell规范的响应格式
- 可配置输出：支持详细/简洁两种输出模式
"""
import asyncio
import time
from typing import Dict, Any, List, Optional, Union, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..core.cell import Cell
from ..core.state import CellState
from ..core.exceptions import CellExecutionError, CellConfigurationError


class PipelineStep:
    """流水线步骤"""
    
    def __init__(self, cell: Cell, name: Optional[str] = None, 
                 condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
                 transform_input: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
                 transform_output: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None):
        """
        初始化流水线步骤
        
        Args:
            cell: 要执行的Cell
            name: 步骤名称（可选）
            condition: 执行条件函数（可选）
            transform_input: 输入转换函数（可选）
            transform_output: 输出转换函数（可选）
        """
        self.cell = cell
        self.name = name or f"{cell.__class__.__name__}_{id(cell)}"
        self.condition = condition
        self.transform_input = transform_input
        self.transform_output = transform_output
    
    def should_execute(self, context: Dict[str, Any]) -> bool:
        """判断是否应该执行此步骤"""
        if self.condition is None:
            return True
        return self.condition(context)
    
    def prepare_input(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """准备输入数据"""
        if self.transform_input is None:
            return context
        return self.transform_input(context)
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """处理输出数据"""
        if self.transform_output is None:
            return output
        return self.transform_output(output)


class Pipeline(Cell):
    """流水线Cell - 组合多个Cell进行顺序或并行执行"""
    
    def __init__(self, steps: List[Union[Cell, PipelineStep]] = None, 
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化Pipeline
        
        Args:
            steps: 流水线步骤列表
            config: 配置字典，可包含：
                - execution_mode: 执行模式 ("sequential", "parallel", "conditional")
                - max_workers: 并行执行时的最大工作线程数
                - stop_on_error: 是否在错误时停止执行
                - timeout: 整个流水线的超时时间（秒）
                - merge_outputs: 是否合并所有步骤的输出
                - verbose: 是否显示详细执行过程 (默认True)
                - show_step_details: 是否显示每步完整输出 (默认False)
        """
        super().__init__(config)
        
        # 配置参数
        self.execution_mode = self.config.get("execution_mode", "sequential")
        self.max_workers = self.config.get("max_workers", 4)
        self.stop_on_error = self.config.get("stop_on_error", True)
        self.timeout = self.config.get("timeout", 300)  # 5分钟
        self.merge_outputs = self.config.get("merge_outputs", True)
        self.show_step_details = self.config.get("show_step_details", False)  # 是否显示每步完整输出
        self.verbose = self.config.get("verbose", True)  # 是否显示执行过程
        
        # 流水线步骤
        self.steps: List[PipelineStep] = []
        if steps:
            for step in steps:
                self.add_step(step)
        
        self.logger.info(f"Pipeline initialized with {len(self.steps)} steps, "
                        f"mode: {self.execution_mode}")
    
    def add_step(self, step: Union[Cell, PipelineStep], 
                 name: Optional[str] = None,
                 condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
                 transform_input: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
                 transform_output: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None) -> 'Pipeline':
        """
        添加流水线步骤
        
        Args:
            step: Cell或PipelineStep
            name: 步骤名称
            condition: 执行条件
            transform_input: 输入转换函数
            transform_output: 输出转换函数
            
        Returns:
            Pipeline实例（支持链式调用）
        """
        if isinstance(step, PipelineStep):
            self.steps.append(step)
        elif isinstance(step, Cell):
            pipeline_step = PipelineStep(
                cell=step,
                name=name,
                condition=condition,
                transform_input=transform_input,
                transform_output=transform_output
            )
            self.steps.append(pipeline_step)
        else:
            raise CellConfigurationError(f"Invalid step type: {type(step)}")
        
        self.logger.debug(f"Added step: {self.steps[-1].name}")
        return self
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行流水线 - 作为Cell组件的标准入口
        
        Args:
            context: 输入上下文
            
        Returns:
            Cell标准格式的执行结果
        """
        if not self.steps:
            self.logger.warning("Pipeline has no steps to execute")
            return {
                "success": False,
                "data": {"response": "Pipeline没有步骤可执行"},
                "error": "No steps to execute",
                "metadata": {"steps_executed": 0, "results": []}
            }
        
        start_time = time.time()
        
        try:
            # 根据执行模式选择执行方法
            if self.execution_mode == "sequential":
                result = self._execute_sequential(context)
            elif self.execution_mode == "parallel":
                result = self._execute_parallel_enhanced(context)
            elif self.execution_mode == "conditional":
                result = self._execute_conditional_enhanced(context)
            else:
                raise CellConfigurationError(f"Unknown execution mode: {self.execution_mode}")
            
            # 记录总执行时间
            total_execution_time = time.time() - start_time
            self.last_execution_time = total_execution_time
            
            # 如果结果已经包含Cell标准格式，直接返回
            if "success" in result and "data" in result:
                result["metadata"]["total_pipeline_time"] = total_execution_time
                return result
            
            # 否则转换为Cell标准格式（向后兼容）
            return {
                "success": result.get("steps_executed", 0) > 0,
                "data": {
                    "response": "Pipeline执行完成",
                    "execution_details": result
                },
                "error": None,
                "metadata": {
                    "execution_time": total_execution_time,
                    "pipeline_result": result
                }
            }
        
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Pipeline execution failed after {execution_time:.3f}s: {e}")
            return {
                "success": False,
                "data": {"response": f"Pipeline执行失败: {str(e)}"},
                "error": str(e),
                "metadata": {
                    "execution_time": execution_time,
                    "failed_at": "pipeline_process"
                }
            }
    
    def _execute_sequential(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """顺序执行所有步骤 - 增强版：透明化过程，正确传递上下文"""
        results = []
        current_context = context.copy()
        executed_count = 0
        
        # 获取原始用户输入
        original_input = context.get("input", "")
        current_input = original_input
        
        # 显示Pipeline开始执行
        if self.verbose:
            print(f"\n🚀 Pipeline开始执行 ({len(self.steps)}个步骤)")
            print("=" * 60)
        
        for i, step in enumerate(self.steps):
            try:
                # 检查执行条件
                if not step.should_execute(current_context):
                    if self.verbose:
                        print(f"⏭️  跳过步骤{i+1}: {step.name} (不满足条件)")
                    continue
                
                # 显示步骤开始
                if self.verbose:
                    print(f"\n🔄 执行步骤{i+1}/{len(self.steps)}: {step.name}")
                    print(f"📝 Cell类型: {step.cell.__class__.__name__}")
                
                # 智能准备输入
                if i == 0:
                    # 第一步使用原始输入
                    step_input = step.prepare_input(current_context)
                    if self.verbose:
                        print(f"📥 输入: 原始查询 ({len(original_input)} 字符)")
                else:
                    # 后续步骤：构建包含前一步结果的上下文输入
                    if step.transform_input:
                        # 如果定义了自定义输入转换，使用它
                        step_input = step.prepare_input(current_context)
                    else:
                        # 默认AI工作流输入构建策略
                        contextual_input = f"""请基于以下信息继续工作：

前一步的结果：
{current_input}

原始用户需求：{original_input}

请根据上述信息完成当前步骤的任务。"""
                        
                        step_input = {
                            "input": contextual_input,
                            "previous_output": current_input,
                            "original_query": original_input,
                            "step_index": i
                        }
                    
                    if self.verbose:
                        print(f"📥 输入: 基于前一步结果构建的上下文 ({len(step_input.get('input', '')) if isinstance(step_input.get('input'), str) else 'N/A'} 字符)")
                
                # 记录开始时间
                start_time = time.time()
                
                # 执行步骤
                step_result = step.cell(step_input)
                execution_time = time.time() - start_time
                
                # 处理输出
                processed_result = step.process_output(step_result)
                
                # 提取步骤响应内容
                step_response = ""
                if step_result.get("success", True):
                    if "data" in step_result and "response" in step_result["data"]:
                        step_response = step_result["data"]["response"]
                    elif "response" in step_result:
                        step_response = step_result["response"]
                    elif isinstance(step_result.get("data"), str):
                        step_response = step_result["data"]
                    else:
                        step_response = str(processed_result)
                    
                    # 更新下一步的输入
                    current_input = step_response
                    
                    # 显示步骤成功结果
                    if self.verbose:
                        print(f"✅ 步骤完成 ({execution_time:.2f}s)")
                        print(f"📝 输出长度: {len(step_response)} 字符")
                        print(f"📄 输出预览: {step_response[:150]}{'...' if len(step_response) > 150 else ''}")
                        
                        # 如果配置了详细输出，显示完整内容
                        if self.show_step_details:
                            print(f"📄 完整输出:")
                            print("=" * 40)
                            print(step_response)
                            print("=" * 40)
                    
                else:
                    if self.verbose:
                        print(f"❌ 步骤失败 ({execution_time:.2f}s)")
                        print(f"🔍 错误: {step_result.get('error', '未知错误')}")
                
                # 记录结果
                step_info = {
                    "step_name": step.name,
                    "step_index": i,
                    "success": step_result.get("success", True),
                    "result": processed_result,
                    "execution_time": execution_time,
                    "response": step_response,  # 新增：直接记录响应内容
                    "input_length": len(step_input.get("input", "")) if isinstance(step_input.get("input"), str) else 0,
                    "output_length": len(step_response)
                }
                results.append(step_info)
                executed_count += 1
                
                # 更新上下文（改进版）
                if self.merge_outputs and step_result.get("success", True):
                    # 更智能的上下文更新
                    current_context[f"step_{i}_result"] = processed_result
                    current_context[f"step_{i}_response"] = step_response
                    current_context["last_response"] = step_response
                    current_context["last_step_index"] = i
                    
                    # 保留重要的Cell数据
                    if "data" in step_result:
                        current_context.update(step_result["data"])
                
            except Exception as e:
                execution_time = time.time() - start_time if 'start_time' in locals() else 0
                
                if self.verbose:
                    print(f"❌ 步骤异常 ({execution_time:.2f}s)")
                    print(f"🔍 异常信息: {str(e)}")
                
                error_info = {
                    "step_name": step.name,
                    "step_index": i,
                    "success": False,
                    "error": str(e),
                    "execution_time": execution_time,
                    "response": "",
                    "input_length": 0,
                    "output_length": 0
                }
                results.append(error_info)
                
                self.logger.error(f"Step {step.name} failed: {e}")
                
                if self.stop_on_error:
                    if self.verbose:
                        print(f"🛑 Pipeline执行中止 (stop_on_error=True)")
                    break
        
        if self.verbose:
            print("\n" + "=" * 60)
            print(f"🏁 Pipeline执行完成: {executed_count}/{len(self.steps)} 步骤成功")
        
        # 构建Pipeline级别的最终响应
        successful_results = [r for r in results if r.get("success", False)]
        if successful_results:
            # 智能选择最终输出：优先选择有意义内容的步骤
            final_step = None
            
            # 1. 优先选择LLMCell的响应（通常包含最有意义的内容）
            for result in successful_results:
                step_name_lower = result.get("step_name", "").lower()
                response = result.get("response", "")
                # 检查是否是LLMCell且有有意义的响应
                if ("llmcell" in step_name_lower and 
                    response and 
                    len(response) > 50 and 
                    not response.startswith("{")):  # 避免选择JSON格式的响应
                    final_step = result
                    break
            
            # 2. 如果没有找到合适的LLMCell，寻找writer/summarizer等
            if not final_step:
                for result in reversed(successful_results):
                    step_name_lower = result.get("step_name", "").lower()
                    response = result.get("response", "")
                    if (any(keyword in step_name_lower for keyword in ["writer", "summarizer", "final"]) and
                        response and len(response) > 50):
                        final_step = result
                        break
            
            # 3. 最后选择第一个有意义内容的步骤
            if not final_step:
                for result in successful_results:
                    response = result.get("response", "")
                    if response and len(response) > 50 and not response.startswith("{"):
                        final_step = result
                        break
            
            # 4. 如果还是没有，选择最后一个成功步骤
            if not final_step:
                final_step = successful_results[-1]
            
            final_response = final_step.get("response", "")
            pipeline_success = True
        else:
            final_response = "Pipeline执行失败：没有步骤成功完成"
            pipeline_success = False
        
        return {
            "execution_mode": "sequential",
            "steps_total": len(self.steps),
            "steps_executed": executed_count,
            "results": results,
            "final_context": current_context if self.merge_outputs else None,
            # 新增：Pipeline作为Cell的标准返回格式
            "success": pipeline_success,
            "data": {
                "response": final_response,
                "step_details": results,
                "execution_summary": {
                    "total_steps": len(self.steps),
                    "successful_steps": len(successful_results),
                    "failed_steps": len(results) - len(successful_results),
                    "total_execution_time": sum(r.get("execution_time", 0) for r in results)
                }
            },
            "error": None if pipeline_success else "Pipeline execution incomplete",
            "metadata": {
                "pipeline_mode": "sequential",
                "merge_outputs": self.merge_outputs,
                "stop_on_error": self.stop_on_error
            }
        }
    
    def _execute_parallel(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """并行执行所有步骤"""
        results = []
        executed_count = 0
        
        # 过滤需要执行的步骤
        steps_to_execute = [
            (i, step) for i, step in enumerate(self.steps)
            if step.should_execute(context)
        ]
        
        if not steps_to_execute:
            self.logger.warning("No steps to execute after condition filtering")
            return {
                "execution_mode": "parallel",
                "steps_total": len(self.steps),
                "steps_executed": 0,
                "results": []
            }
        
        # 使用线程池并行执行
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_step = {}
            for i, step in steps_to_execute:
                step_input = step.prepare_input(context)
                future = executor.submit(self._execute_step_safe, step, step_input, i)
                future_to_step[future] = (i, step)
            
            # 收集结果
            for future in as_completed(future_to_step, timeout=self.timeout):
                i, step = future_to_step[future]
                try:
                    step_result = future.result()
                    results.append(step_result)
                    if step_result["success"]:
                        executed_count += 1
                    
                    self.logger.debug(f"Step {step.name} completed")
                    
                except Exception as e:
                    error_info = {
                        "step_name": step.name,
                        "step_index": i,
                        "success": False,
                        "error": str(e),
                        "execution_time": 0
                    }
                    results.append(error_info)
                    self.logger.error(f"Step {step.name} failed: {e}")
        
        # 按步骤索引排序结果
        results.sort(key=lambda x: x["step_index"])
        
        return {
            "execution_mode": "parallel",
            "steps_total": len(self.steps),
            "steps_executed": executed_count,
            "results": results
        }
    
    def _execute_parallel_enhanced(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """并行执行所有步骤 - 增强版"""
        if self.verbose:
            print(f"\n🚀 Pipeline并行执行 ({len(self.steps)}个步骤)")
            print("=" * 60)
        
        # 调用原有的并行执行逻辑
        result = self._execute_parallel(context)
        
        # 显示并行执行结果
        results = result.get("results", [])
        successful_results = [r for r in results if r.get("success", False)]
        
        if self.verbose:
            print(f"🏁 并行执行完成: {len(successful_results)}/{len(results)} 步骤成功")
        
        # 转换为Cell标准格式
        if successful_results:
            # 并行模式下，选择第一个成功的结果或特定类型的结果
            final_step = successful_results[0]  # 可以根据需要调整选择策略
            final_response = final_step.get("result", {}).get("data", {}).get("response", "并行执行完成")
            pipeline_success = True
        else:
            final_response = "Pipeline并行执行失败：没有步骤成功完成"
            pipeline_success = False
        
        return {
            **result,
            "success": pipeline_success,
            "data": {
                "response": final_response,
                "step_details": results,
                "execution_summary": {
                    "total_steps": len(self.steps),
                    "successful_steps": len(successful_results),
                    "failed_steps": len(results) - len(successful_results),
                    "execution_mode": "parallel"
                }
            },
            "error": None if pipeline_success else "Pipeline parallel execution incomplete"
        }
    
    def _execute_conditional(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """条件执行 - 根据前一步的结果决定是否执行下一步"""
        results = []
        current_context = context.copy()
        executed_count = 0
        
        for i, step in enumerate(self.steps):
            try:
                # 检查执行条件（基于当前上下文）
                if not step.should_execute(current_context):
                    self.logger.debug(f"Skipping step {step.name} due to condition")
                    continue
                
                # 准备输入
                step_input = step.prepare_input(current_context)
                
                # 执行步骤
                self.logger.debug(f"Conditionally executing step {i+1}/{len(self.steps)}: {step.name}")
                step_result = step.cell(step_input)
                
                # 处理输出
                processed_result = step.process_output(step_result)
                
                # 记录结果
                step_info = {
                    "step_name": step.name,
                    "step_index": i,
                    "success": step_result.get("success", True),
                    "result": processed_result,
                    "execution_time": step.cell.last_execution_time
                }
                results.append(step_info)
                executed_count += 1
                
                # 更新上下文
                if step_result.get("success", True):
                    if "data" in step_result:
                        current_context.update(step_result["data"])
                    current_context[f"step_{i}_result"] = processed_result
                    current_context["last_step_success"] = True
                else:
                    current_context["last_step_success"] = False
                    if self.stop_on_error:
                        break
                
                self.logger.debug(f"Step {step.name} completed, context updated")
                
            except Exception as e:
                error_info = {
                    "step_name": step.name,
                    "step_index": i,
                    "success": False,
                    "error": str(e),
                    "execution_time": getattr(step.cell, 'last_execution_time', 0)
                }
                results.append(error_info)
                current_context["last_step_success"] = False
                
                self.logger.error(f"Step {step.name} failed: {e}")
                
                if self.stop_on_error:
                    break
        
        return {
            "execution_mode": "conditional",
            "steps_total": len(self.steps),
            "steps_executed": executed_count,
            "results": results,
            "final_context": current_context
        }
    
    def _execute_conditional_enhanced(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """条件执行 - 增强版"""
        if self.verbose:
            print(f"\n🚀 Pipeline条件执行 ({len(self.steps)}个步骤)")
            print("=" * 60)
        
        # 调用原有的条件执行逻辑
        result = self._execute_conditional(context)
        
        # 显示条件执行结果
        results = result.get("results", [])
        successful_results = [r for r in results if r.get("success", False)]
        
        if self.verbose:
            print(f"🏁 条件执行完成: {len(successful_results)}/{len(results)} 步骤成功")
        
        # 转换为Cell标准格式
        if successful_results:
            final_step = successful_results[-1]  # 条件执行取最后一个成功步骤
            final_response = final_step.get("result", {}).get("data", {}).get("response", "条件执行完成")
            pipeline_success = True
        else:
            final_response = "Pipeline条件执行失败：没有步骤成功完成"
            pipeline_success = False
        
        return {
            **result,
            "success": pipeline_success,
            "data": {
                "response": final_response,
                "step_details": results,
                "execution_summary": {
                    "total_steps": len(self.steps),
                    "successful_steps": len(successful_results),
                    "failed_steps": len(results) - len(successful_results),
                    "execution_mode": "conditional"
                }
            },
            "error": None if pipeline_success else "Pipeline conditional execution incomplete"
        }
    
    def _execute_step_safe(self, step: PipelineStep, step_input: Dict[str, Any], 
                          step_index: int) -> Dict[str, Any]:
        """安全执行单个步骤（用于并行执行）"""
        try:
            step_result = step.cell(step_input)
            processed_result = step.process_output(step_result)
            
            return {
                "step_name": step.name,
                "step_index": step_index,
                "success": step_result.get("success", True),
                "result": processed_result,
                "execution_time": step.cell.last_execution_time
            }
        except Exception as e:
            return {
                "step_name": step.name,
                "step_index": step_index,
                "success": False,
                "error": str(e),
                "execution_time": 0
            }
    
    def clone(self) -> 'Pipeline':
        """克隆Pipeline"""
        cloned_steps = []
        for step in self.steps:
            cloned_cell = step.cell.clone()
            cloned_step = PipelineStep(
                cell=cloned_cell,
                name=step.name,
                condition=step.condition,
                transform_input=step.transform_input,
                transform_output=step.transform_output
            )
            cloned_steps.append(cloned_step)
        
        return Pipeline(steps=cloned_steps, config=self.config.copy())


# 便捷的Pipeline构建器
class PipelineBuilder:
    """Pipeline构建器 - 提供流畅的API来构建Pipeline"""
    
    def __init__(self):
        self.steps = []
        self.config = {}
    
    def add(self, cell: Cell, name: Optional[str] = None) -> 'PipelineBuilder':
        """添加Cell"""
        self.steps.append(PipelineStep(cell, name))
        return self
    
    def add_conditional(self, cell: Cell, condition: Callable[[Dict[str, Any]], bool],
                       name: Optional[str] = None) -> 'PipelineBuilder':
        """添加条件Cell"""
        self.steps.append(PipelineStep(cell, name, condition))
        return self
    
    def sequential(self) -> 'PipelineBuilder':
        """设置为顺序执行模式"""
        self.config["execution_mode"] = "sequential"
        return self
    
    def parallel(self, max_workers: int = 4) -> 'PipelineBuilder':
        """设置为并行执行模式"""
        self.config["execution_mode"] = "parallel"
        self.config["max_workers"] = max_workers
        return self
    
    def conditional(self) -> 'PipelineBuilder':
        """设置为条件执行模式"""
        self.config["execution_mode"] = "conditional"
        return self
    
    def build(self) -> Pipeline:
        """构建Pipeline"""
        return Pipeline(steps=self.steps, config=self.config)


# 便捷函数
def create_pipeline(*cells: Cell, mode: str = "sequential") -> Pipeline:
    """快速创建Pipeline"""
    return (PipelineBuilder()
            .sequential() if mode == "sequential" 
            else PipelineBuilder().parallel() if mode == "parallel"
            else PipelineBuilder().conditional()
           ).build() 