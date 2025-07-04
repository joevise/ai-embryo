# FuturEmbryo 多智能体协作系统

基于FuturEmbryo核心框架的用户中心@机制驱动多智能体协作平台。实现了"一切皆可@引用"的统一协作体验。

## ✨ 核心特性

- **🧠 用户记忆学习**: 自动学习用户偏好、兴趣和交互习惯，提供个性化服务
- **📝 @引用机制**: 统一的对象引用系统，支持@用户画像、@智能体、@产出物等
- **🤖 多智能体协作**: 专业化Agent协同工作，包括研究员、分析师、写作者等
- **⚙️ 配置驱动**: 基于DNA配置系统，用户只需修改YAML即可定制全部功能
- **🔗 完全兼容**: 基于FuturEmbryo核心框架，与现有项目完全兼容

## 🏗️ 架构设计

```
MultiAgent System (基于FuturEmbryo)
├── 📦 扩展的Cell组件
│   ├── UserMemoryCell (扩展StateMemoryCell - 用户记忆管理)
│   └── MentionProcessorCell (新Cell类型 - @引用处理)
│
├── 🤖 用户感知Agent (基于Pipeline)
│   ├── ResearcherAgent (研究员 - 信息收集和分析)
│   ├── AnalystAgent (分析师 - 数据分析和洞察)
│   ├── WriterAgent (写作者 - 内容创作和整理)
│   ├── CreativeAgent (创意专家 - 创新设计和方案)
│   └── PlannerAgent (规划师 - 项目规划和管理)
│
├── 🎯 智能协作机制
│   ├── @引用解析引擎
│   ├── 用户上下文感知
│   └── 产出物自动注册
│
└── 📋 DNA配置系统
    ├── demo_config.yaml (主配置)
    ├── agent_templates.yaml (Agent模板)
    └── workflow_templates.yaml (工作流模板)
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 确保已安装FuturEmbryo
cd futurembryo
uv sync

# 设置API密钥
export FUTURX_API_KEY="your-api-key"
```

### 2. 运行演示

```bash
# 运行完整演示
cd examples/multiagent_collaboration
python multiagent_demo.py

# 运行快速开始示例
python examples/quick_start.py

# 运行特定场景
python multiagent_demo.py personal_assistant
python multiagent_demo.py business_analysis
python multiagent_demo.py creative_project
```

### 3. 自定义配置

编辑 `configs/demo_config.yaml` 定制您的AI协作系统：

```yaml
# 自定义用户记忆系统
user_memory:
  auto_learning: true
  explicit_memory_keywords: ["记住", "重要", "关注"]

# 自定义Agent配置  
agents:
  my_researcher:
    template: "researcher_template"
    customizations:
      focus_areas: ["你的专业领域"]
      output_style: "@user-preferences.detail_level"
```

## 💡 使用示例

### 基础对话和学习
```python
# 用户告诉系统兴趣，系统自动学习
"我对AI投资很感兴趣，特别是多智能体技术，请记住这个"
# 系统会自动更新@user-profile，记录到@user-memory

# 查看学到的用户信息
"显示我的@user-profile"
# 系统会展示学习到的用户画像
```

### 智能体协作
```python
# 指定智能体进行专业任务
"@researcher 研究AI发展趋势，重点关注投资机会"
# 系统会：
# 1. 激活@researcher Agent
# 2. 结合@user-profile的投资兴趣
# 3. 生成个性化研究报告
# 4. 自动注册为@research-report-xxx

# 基于产出物继续协作  
"@analyst 基于@research-report-xxx 进行投资可行性分析"
# 系统会：
# 1. 加载之前的研究报告
# 2. 激活@analyst Agent
# 3. 结合用户风险偏好生成分析

# 最终整理成报告
"@writer 基于以上分析写一份投资建议报告"
```

### 工作流自动化
```python
# 启动预定义工作流
"@research-workflow 帮我全面分析AI市场投资机会"
# 系统会自动执行：
# researcher → analyst → writer → 最终报告
```

## 📂 项目结构

```
examples/multiagent_collaboration/
├── 📁 cells/                    # 扩展的Cell组件
│   ├── user_memory_cell.py      # 用户记忆Cell
│   └── mention_processor_cell.py # @引用处理Cell
│
├── 🤖 agents/                   # 智能体实现
│   └── user_aware_agent.py      # 用户感知Agent基类
│
├── ⚙️ configs/                  # 配置文件
│   └── demo_config.yaml         # 主配置文件
│
├── 📚 templates/                # 模板定义
│   └── agent_templates.yaml     # Agent模板
│
├── 🎯 examples/                 # 使用示例
│   └── quick_start.py           # 快速开始示例
│
├── 📖 docs/                     # 详细文档
│   └── ARCHITECTURE.md          # 架构设计文档
│
├── 🚀 multiagent_demo.py        # 主演示程序
└── 📋 README.md                 # 本文件
```

## 🎯 核心功能详解

### 1. 用户记忆学习系统

```python
# 自动学习用户兴趣
"我对技术创新很感兴趣" → 更新@user-profile.interests

# 学习用户偏好
"请简洁一些" → 学习@user-preferences.communication_style = "concise"

# 显式记忆存储
"记住我的投资风格是稳健型" → 保存到@user-memory
```

### 2. @引用系统

| 引用类型 | 示例 | 功能 |
|---------|------|------|
| 用户信息 | `@user-profile` | 获取用户画像 |
| 用户记忆 | `@user-memory` | 获取重要记忆 |
| 用户偏好 | `@user-preferences` | 获取交互偏好 |
| 智能体 | `@researcher` | 激活研究员 |
| 产出物 | `@report-123` | 引用生成的报告 |

### 3. 多智能体协作

- **🔍 Researcher**: 信息收集、趋势分析、报告撰写
- **📊 Analyst**: 数据分析、模式识别、洞察发现  
- **✍️ Writer**: 内容创作、文档编写、信息整理
- **💡 Creative**: 创意生成、方案设计、头脑风暴
- **📋 Planner**: 任务分解、项目规划、时间管理

## 🛠️ 自定义和扩展

### 创建自定义Agent

```python
# 1. 定义Agent配置
custom_agent_config = {
    "name": "投资顾问",
    "role": "analyst", 
    "capabilities": ["投资分析", "风险评估"],
    "personality": ["专业", "谨慎"],
    "llm_config": {
        "model": "gpt-4",
        "temperature": 0.2,
        "system_prompt": "你是专业的投资顾问..."
    }
}

# 2. 创建Agent实例
advisor = UserAwareAgent("investment_advisor", custom_agent_config)

# 3. 使用自定义Agent
result = advisor.process_user_input("分析当前市场投资机会")
```

### 扩展配置模板

在 `templates/agent_templates.yaml` 中添加新模板：

```yaml
investment_advisor_template:
  name: "投资顾问"
  role: "analyst"
  capabilities: ["投资分析", "风险评估", "市场研究"]
  personality: ["专业", "客观", "谨慎"]
  llm_config:
    model: "gpt-4"
    temperature: 0.2
    system_prompt: |
      你是一个专业的投资顾问...
```

## 📊 监控和调试

### 系统状态查看

```python
# 查看当前状态
"status"  # 显示用户信息、对话统计、产出物等

# 查看帮助
"help"    # 显示使用帮助和可用功能
```

### 调试配置

在 `configs/demo_config.yaml` 中启用调试：

```yaml
demo:
  debug:
    enabled: true
    log_level: "DEBUG"
    log_user_learning: true
    log_mention_processing: true
```

## 🎉 特色亮点

1. **🧠 智能学习**: 系统会自动学习用户的兴趣、偏好和交互习惯
2. **📝 统一引用**: 通过@机制统一引用用户信息、智能体和产出物
3. **🎨 个性化**: 根据用户画像自动调整Agent的回复风格和内容深度
4. **🔄 产出物循环**: AI生成的内容自动注册为可@引用的对象，支持递归协作
5. **⚙️ 配置驱动**: 所有功能通过配置文件控制，用户无需编程即可定制

## 🤝 与FuturEmbryo的关系

本项目完全基于FuturEmbryo核心框架构建：

- **复用核心组件**: Cell、Pipeline、StateMemoryCell、LLMCell等
- **扩展而非替换**: 在现有基础上增加用户感知和@引用能力
- **保持兼容性**: 与现有FuturEmbryo项目完全兼容
- **继承设计理念**: 延续生物学启发的架构设计思想

## 📚 文档和支持

- [架构设计文档](docs/ARCHITECTURE.md) - 详细的系统架构说明
- [快速开始示例](examples/quick_start.py) - 基础使用方法
- [配置文件说明](configs/demo_config.yaml) - 完整配置选项
- [Agent模板](templates/agent_templates.yaml) - 预定义Agent模板

## 🌟 下一步计划

- [ ] 工作流可视化界面
- [ ] 更多专业化Agent模板
- [ ] 支持更多@引用对象类型
- [ ] 集成更多外部工具和数据源
- [ ] 性能优化和扩展性改进

---

**🎯 这个项目展示了如何基于FuturEmbryo框架构建复杂的多智能体协作系统，同时保持简单易用的用户体验。通过@机制，用户可以像使用社交媒体一样轻松地与AI系统协作！**