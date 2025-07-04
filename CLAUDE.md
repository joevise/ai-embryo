# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FuturEmbryo is a Python framework for building AI agent systems using a biology-inspired architecture. It uses modular "Cells" that can be composed into "Pipelines", configured via "DNA" files, and features comprehensive memory management with both vector (ChromaDB) and relational (SQLite) storage.

## 重要设计决策记录

### ToolCell设计改进完成 (2025-06-30)
**原问题**: 当前ToolCell设计不符合预期使用模式

**✅ 已完成改进**:
1. ✅ 重构ToolCell为工具注册中心模式
2. ✅ 移除ToolCell的智能选择逻辑
3. ✅ 增强LLMCell的Function Calling支持
4. ✅ 建立标准的OpenAI工具调用接口
5. ✅ 集成MCP协议支持
6. ✅ 配置化工具管理系统

**新架构**:
- **ToolRegistry**: 工具注册中心，支持Function Call + MCP工具
- **ToolCell v2**: 纯工具提供者，暴露工具清单
- **LLMCell v2**: 智能决策者，通过Function Calling选择工具
- **ToolConfigManager**: 配置化工具管理

**文件位置**:
- `core/tool_registry.py`: 工具注册中心
- `core/tool_config.py`: 工具配置管理
- `cells/tool_cell.py`: 升级后的ToolCell（向后兼容）
- `cells/llm_cell.py`: 升级后的LLMCell（向后兼容）
- `tests/test_tool_registry_v2.py`: 测试文件
- `examples/tool_system_demo.py`: 演示程序

**升级完成 (2025-06-30)**:
✅ **统一版本**: 删除了v2版本文件，直接升级原有的 `llm_cell.py` 和 `tool_cell.py`
✅ **向后兼容**: 原有代码无需修改即可继续使用
✅ **新功能可选**: 通过配置参数启用Function Calling和MCP支持

## Common Development Commands

### Dependency Management
```bash
# Install dependencies using uv (preferred)
cd futurembryo
uv sync

# Or install manually
pip install -e .  # Install in editable mode
```

### Running Examples
```bash
# Basic examples
python examples/hello_world.py
python examples/interactive_chat.py
python examples/simple_50_line_agent.py

# Smart workflow demo (most comprehensive)
cd examples/smart_workflow
python smart_workflow_demo.py

# StateMemoryCell demo with FastGPT integration
cd examples/statememeorycell-demo
./run_demo.sh  # or python fastgpt_demo.py
```

### Running Tests
```bash
# Tests are run directly as Python scripts (no pytest configuration)
cd tests
python test_basic.py      # Basic functionality tests
python test_real_llm.py   # Tests with real LLM API (requires API key)
python test_mind_rule.py  # MindCell and rules engine tests
python test_stage2.py     # Advanced multi-stage pipeline tests

# Run a specific test by navigating to tests directory
cd tests && python test_basic.py
```

### API Configuration
Before running any examples, configure the FuturX API:
```python
from futurembryo import setup_futurx_api
setup_futurx_api(
    api_key="your-api-key",
    base_url="https://litellm.futurx.cc"
)
```

## Architecture Overview

### Core Components
1. **Cell** (`core/cell.py`): Base abstraction for all processing units
   - LLMCell: Language model integration
   - MindCell: Reasoning and decision-making
   - StateMemoryCell: Memory management with ChromaDB
   - ToolCell: External tool integration

2. **Pipeline** (`core/pipeline.py`): Orchestrates multiple cells in sequence

3. **DNA System** (`dna/`): Biology-inspired configuration
   - `embryo_dna.py`: Loads DNA configuration files
   - `genes.py`: Defines gene structures
   - `life_grower.py`: Builds systems from DNA
   - `cell_factory.py`: Dynamic cell creation

4. **Memory System**:
   - ChromaDB for vector embeddings
   - SQLite for structured data
   - Integrated in StateMemoryCell

### Key Design Patterns
- **Composition over inheritance**: Cells are composed, not subclassed
- **Runtime configuration**: Systems assembled dynamically from DNA
- **State management**: All cells track comprehensive state
- **Adapter pattern**: Integration with external systems (e.g., FastGPT)

### Project Structure
```
futurembryo/          # Main package
├── core/             # Framework core
├── cells/            # Cell implementations  
├── dna/              # DNA configuration system
├── adapters/         # External integrations
examples/             # Usage examples
tests/                # Test suite
config/               # Configuration files
memory_db/            # Database storage
```

## Smart Workflow System

The smart workflow demo showcases advanced capabilities:
- **Dynamic task analysis**: Categorizes tasks as simple/multi-step/complex
- **Role-based cells**: Creates specialized cells (researcher, analyzer, planner, etc.)
- **Automatic pipeline construction**: Builds workflows based on task complexity

Available specialized roles:
- `researcher`: Information gathering and research
- `analyzer`: Data analysis and insights
- `creative`: Creative writing and ideation
- `planner`: Task planning and organization
- `calculator`: Mathematical computations
- `writer`: Content creation and documentation
- `summarizer`: Condensing information

Special commands in interactive demos:
- `quit`: Exit system
- `clear`: Clear workflow memory  
- `history`: View execution history
- `help`: Display help

## Cell Types and Usage

### Core Cell Types
1. **LLMCell** (`cells/llm_cell.py`): Direct LLM interaction
   - Configurable model and parameters
   - Supports streaming responses
   - Example: `LLMCell(model="gpt-4", temperature=0.7)`

2. **MindCell** (`cells/mind_cell.py`): Advanced reasoning
   - Rule-based decision making
   - Multi-step reasoning chains
   - Integrates with memory systems

3. **StateMemoryCell** (`cells/state_memory_cell.py`): Persistent memory
   - ChromaDB for semantic search
   - SQLite for structured data
   - Supports multiple retrieval modes

4. **ToolCell** (`cells/tool_cell.py`): External tool integration
   - Extensible tool interface
   - Built-in tools for common operations

### DNA Configuration Example
```yaml
name: "MyAgent"
cells:
  - type: "LLMCell"
    name: "thinker"
    config:
      model: "gpt-4"
      temperature: 0.7
  - type: "StateMemoryCell"
    name: "memory"
    config:
      embedding_model: "text-embedding-ada-002"
      collection_name: "agent_memory"
pipeline:
  - "memory"
  - "thinker"
```

## Development Notes

- Python 3.12+ required
- All examples add project root to sys.path for imports
- No lint/format configuration - follow existing code style
- Tests can be run directly without pytest
- Memory databases created in local `memory_db/` folders
- Configuration via YAML/JSON with Pydantic validation
- Package uses UV for dependency management (pyproject.toml + uv.lock)