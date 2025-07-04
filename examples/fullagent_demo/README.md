# FuturEmbryo Full Agent Demo

一个基于FuturEmbryo框架的**全功能AI智能助手演示**，展示了生物启发式模块化AI系统的完整能力。

## 🌟 功能特性

### 核心能力
- **💬 智能对话** - 基于Claude-4的高质量对话交互
- **🧠 智能思考** - MindCell提供深度推理和反思能力
- **📚 持久记忆** - StateMemoryCell跨会话记忆系统
- **🔧 工具集成** - 完整的MCP协议支持，包括SSE和stdio两种传输方式
- **📖 知识查询** - 集成FastGPT专业知识库
- **⚙️ 配置驱动** - 完全基于YAML配置的模块化设计

### 技术特性
- **🧬 生物启发架构** - Cell-Pipeline模块化设计
- **⚡ 异步处理** - 全异步架构，高性能响应
- **🔌 标准协议** - 完整的MCP (Model Context Protocol) 支持
- **🌐 多传输方式** - 支持SSE和stdio两种MCP传输方式
- **🎯 智能上下文** - 动态构建包含历史、知识和工具的完整上下文

## 🚀 快速开始

### 前置要求
- Python 3.11+
- MCP Python SDK
- 有效的AI模型API密钥

### 安装依赖
```bash
# 使用uv安装（推荐）
cd futurembryo
uv sync

# 或使用pip安装
pip install -e .
pip install "mcp[cli]"
```

### 配置设置
1. 编辑配置文件`config.yaml`中的API配置：
```yaml
api:
  key: "your-api-key"
  base_url: "https://your-api-endpoint.com/v1"
```

### 运行演示
```bash
cd examples/fullagent_demo
python fullagent_demo.py
```

### 体验功能
- **智能对话**: "你好！"
- **记忆测试**: "我们之前聊过什么？"
- **新闻查询**: "告诉我最新的新闻"
- **技术文档**: "查询Python最佳实践"
- **MCP工具**: 自动调用外部服务获取实时信息

## ⚙️ 配置详解

### Agent配置
```yaml
agent:
  name: "FuturEmbryo Full Agent"
  model: "anthropic/claude-sonnet-4-20250514"
  temperature: 0.7
  max_tokens: 16384
  system_prompt: |
    你是FuturEmbryo框架驱动的智能助手...
```

### MindCell配置
```yaml
mind:
  enabled: true
  model_name: "gpt-4o-mini"
  thinking_mode: "reflection"
  character: "孙悟空"  # 可自定义思维性格
  max_thinking_tokens: 300
```

### 工具配置
```yaml
tools:
  defaults: true
  mcp_servers:
    # SSE类型MCP服务器
    - name: "dynamic-knowledgebase-mcp"
      type: "sse"
      url: "http://example.com:3001/sse"
      headers:
        Authorization: "Bearer your-token"
    
    # stdio类型MCP服务器
    - name: "context7"
      command: ["npx", "-y", "@upstash/context7-mcp"]
      description: "技术文档查询工具"
```

## 🏗️ 架构设计

### Cell组件
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLMCell       │    │   MindCell      │    │ StateMemoryCell │
│ (核心对话)      │    │ (智能思考)      │    │ (记忆管理)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ToolCell      │    │ FastGPTAdapter  │    │ContextBuilder   │
│ (工具调用)      │    │ (知识库)        │    │ (上下文构建)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 数据流
```
用户输入 → ContextBuilder → LLMCell → ToolCell → 外部服务
    ↑                                      ↓
StateMemoryCell ← ← ← ← ← ← ← ← ← ← ← ← 响应处理
```

### 项目结构
```
fullagent_demo/
├── fullagent_demo.py      # 主程序
├── config.yaml            # 配置文件
├── README.md              # 本文档
├── PROGRESS_SUMMARY.md    # 开发进度记录
├── memory_db/             # 自动创建的记忆数据库
└── test_*.py              # 测试脚本
```

## 🔧 MCP工具集成

### 支持的传输方式
- **SSE (Server-Sent Events)** - 适用于HTTP-based MCP服务器
- **stdio** - 适用于本地命令行MCP服务器

### 已集成工具
1. **Context7** - 技术文档查询
   - 支持主流开源项目文档
   - 实时代码示例检索

2. **Dynamic Knowledge Base** - 动态知识库
   - 最新新闻资讯查询
   - 政经动态分析

### 添加自定义工具
在`config.yaml`中添加MCP服务器配置：
```yaml
tools:
  mcp_servers:
    - name: "your-tool"
      type: "sse"  # 或 "stdio"
      url: "your-server-url"  # SSE类型需要
      command: ["your-command"]  # stdio类型需要
```

## 🧠 智能特性

### MindCell思维模式
- **反思模式** - 深度分析和自我审视
- **规划模式** - 任务分解和策略制定
- **分析模式** - 逻辑推理和数据分析

### 记忆系统
- **对话记忆** - 自动保存所有对话历史
- **语义检索** - 基于ChromaDB的向量检索
- **结构化存储** - SQLite关系数据库支持

### 上下文管理
- **历史上下文** - 最近N条对话记录
- **知识上下文** - 相关知识库内容
- **工具上下文** - 可用工具列表
- **智能筛选** - 动态选择最相关内容

## 🛠️ 开发指南

### 架构亮点
这个Demo展示了FuturEmbryo框架的设计理念：
- **🧬 生物启发** - Cell-Pipeline模块化架构
- **🔧 模块化** - 记忆、知识库、工具、思维各自独立
- **⚙️ 可配置** - 通过配置文件控制所有功能
- **🔌 可扩展** - 轻松添加新的MCP工具、知识源和思维模式
- **🎭 个性化** - 支持不同人物性格的思维和表达方式
- **🚀 生产就绪** - 完整的错误处理和日志记录

### 自定义开发
1. **扩展Cell功能** - 继承基础Cell类
2. **添加新工具** - 实现MCP协议或Function Call
3. **定制思维模式** - 修改MindCell的推理逻辑
4. **优化上下文** - 调整ContextBuilder策略

### 调试技巧
- 启用详细日志：`logging.basicConfig(level=logging.DEBUG)`
- 查看工具调用：观察MCP通信日志
- 检查记忆存储：查看`memory_db/`目录
- 分析思维过程：启用MindCell详细输出

## 🔍 故障排除

### 常见问题
1. **MCP连接失败**
   - 检查网络连接和服务器状态
   - 验证认证令牌和权限

2. **工具调用超时**
   - 增加timeout配置
   - 检查服务器响应能力

3. **记忆系统错误**
   - 清理`memory_db/`目录
   - 重新初始化数据库

4. **API调用失败**
   - 验证API密钥有效性
   - 检查模型可用性

### 日志分析
查看详细日志以诊断问题：
```bash
python fullagent_demo.py 2>&1 | tee fullagent.log
```

## 📋 更新日志

### v2.1c (2025-07-01)
- ✅ 重构MCP集成，使用官方Python SDK
- ✅ 修复SSE响应监听问题
- ✅ 支持标准化MCP协议
- ✅ 优化连接管理和错误处理
- ✅ 完善工具发现和调用机制

### v2.1b (2025-06-30)
- ✅ 完成ToolCell设计改进
- ✅ 增强LLMCell的Function Calling支持
- ✅ 建立标准OpenAI工具调用接口
- ✅ 集成MCP协议支持

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境
```bash
git clone <repository>
cd FuturEmbryo
uv sync --dev
```

### 提交规范
- feat: 新功能
- fix: 修复
- docs: 文档
- test: 测试
- refactor: 重构

## 📄 许可证

[MIT License](../../LICENSE)

## 🙏 致谢

- [MCP (Model Context Protocol)](https://github.com/modelcontextprotocol) - 工具协议标准
- [Claude](https://claude.ai) - 核心AI能力
- [ChromaDB](https://github.com/chroma-core/chroma) - 向量数据库
- [FastGPT](https://github.com/labring/FastGPT) - 知识库平台

---

**FuturEmbryo** - 生物启发式AI系统框架 🧬✨

这就是用FuturEmbryo构建完整AI Agent的最佳方式！ 🚀