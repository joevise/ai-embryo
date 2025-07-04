#!/bin/bash

# FuturEmbryo 多智能体静态团队 - 快速启动脚本

echo "🚀 启动 FuturEmbryo 多智能体静态团队系统..."
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

# 运行主程序
python3 multiagent_demo.py "$@"