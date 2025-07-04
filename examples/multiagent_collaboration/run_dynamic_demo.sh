#!/bin/bash

# 动态多智能体协作系统启动脚本

echo "🚀 启动动态多智能体协作系统..."

# 检查当前目录
if [ ! -f "dynamic_multiagent_demo.py" ]; then
    echo "❌ 错误: 请在 multiagent_collaboration 目录下运行此脚本"
    echo "正确路径: /Users/dajoe/joe_ai_lab/FuturEmbryo/FuturEmbryo-v2.1c_claude/examples/multiagent_collaboration/"
    exit 1
fi

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ 错误: 未找到Python环境"
    exit 1
fi

# 设置Python路径
export PYTHONPATH="/Users/dajoe/joe_ai_lab/FuturEmbryo/FuturEmbryo-v2.1c_claude:$PYTHONPATH"

echo "✅ 环境检查通过"
echo "🔧 PYTHONPATH: $PYTHONPATH"
echo ""

# 运行演示程序
echo "🎯 启动动态多智能体协作演示..."
python dynamic_multiagent_demo.py

echo ""
echo "👋 演示程序结束"