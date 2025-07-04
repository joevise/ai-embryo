# FuturEmbryo 多智能体静态团队演示

这是一个基于FuturEmbryo框架的多智能体静态团队协作系统，展示了预定义的专业智能体如何协同工作。

## 特性

- 🧠 **智能协调员** - 自动分析任务并分配给合适的专业Agent
- 🤖 **专业智能体团队** - 5个预定义的专业Agent（研究、分析、写作、创意、规划）
- 📝 **@引用机制** - 统一的对象引用系统
- 🧠 **用户记忆学习** - 自动学习用户偏好和兴趣
- 🔄 **多Agent协作** - 支持复杂任务的多Agent协同工作

## 运行方式

### 1. 直接运行交互式演示
```bash
cd examples/multiagent_team_static
python multiagent_demo.py
```

### 2. 运行预设场景
```bash
# 个人助理场景
python multiagent_demo.py personal_assistant

# 商业分析场景
python multiagent_demo.py business_analysis

# 创意项目场景
python multiagent_demo.py creative_project
```

## 系统架构

```
multiagent_team_static/
├── multiagent_demo.py      # 主程序
├── agents/                 # 智能体实现
│   ├── user_aware_agent.py # 用户感知智能体
│   └── coordinator_agent.py # 协调智能体
├── cells/                  # Cell组件
│   ├── user_memory_cell.py # 用户记忆管理
│   └── mention_processor_cell.py # @引用处理
├── configs/                # 配置文件
│   └── demo_config.yaml    # 系统配置
└── templates/              # Agent模板
    └── agent_templates.yaml # Agent模板定义
```

## 专业智能体介绍

### 1. 研究专家 (@researcher)
- 专长：信息搜集、文献研究、趋势分析
- 适用：需要深入研究和信息收集的任务

### 2. 数据分析师 (@analyst)
- 专长：数据分析、统计建模、趋势预测
- 适用：需要数据分析和洞察的任务

### 3. 内容创作者 (@writer)
- 专长：内容创作、文案撰写、报告撰写
- 适用：需要撰写文档或创作内容的任务

### 4. 创意设计师 (@creative)
- 专长：创意构思、方案设计、营销创意
- 适用：需要创新想法和创意方案的任务

### 5. 项目规划师 (@planner)
- 专长：项目规划、任务分解、时间管理
- 适用：需要制定计划和管理项目的任务

## 使用示例

### 简单任务（单Agent）
```
用户: 帮我研究一下人工智能的发展趋势
系统: [智能协调员分析] → [分配给@researcher] → [输出研究报告]
```

### 复杂任务（多Agent协作）
```
用户: 我需要制定一个AI产品的营销方案
系统: [智能协调员分析] → [@researcher研究市场] → [@creative设计方案] → [@writer撰写文档] → [整合输出]
```

## 配置说明

### API配置
在 `configs/demo_config.yaml` 中配置API密钥和基础URL：
```yaml
api:
  key: "your-api-key"
  base_url: "https://your-api-url"
```

### Agent配置
可以在配置文件中自定义每个Agent的参数：
```yaml
agents:
  researcher:
    customizations:
      temperature: 0.7
      max_tokens: 2000
```

## 注意事项

1. 确保已安装FuturEmbryo框架
2. 配置正确的API密钥
3. Python版本需要3.8+
4. 首次运行可能需要下载模型

## 扩展开发

### 添加新的Agent
1. 在 `templates/agent_templates.yaml` 中定义新模板
2. 在 `configs/demo_config.yaml` 中添加配置
3. 重启系统即可使用新Agent

### 自定义协作流程
修改 `coordinator_agent.py` 中的工作流逻辑，实现更复杂的协作模式。

## 故障排除

### 常见问题
1. **配置文件未找到**：确保在正确目录下运行
2. **API调用失败**：检查API密钥和网络连接
3. **Agent创建失败**：检查模板配置是否正确

### 日志查看
系统会生成日志文件，可以查看详细的运行信息和错误信息。