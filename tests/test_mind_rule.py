 #!/usr/bin/env python3
"""
测试MindCell的MindRule功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from futurembryo.cells.mind_cell import MindCell

def test_mind_rule_functionality():
    """测试MindRule功能"""
    print("=== 测试MindCell的MindRule功能 ===\n")
    
    # 初始化MindCell
    mind_cell = MindCell({
        "model_name": "claude-3-5-sonnet",
        "max_thinking_tokens": 2000
    })
    
    print("1. 测试不使用MindRule的思考过程")
    print("-" * 50)
    
    context_without_rule = {
        "action": "generate_thinking",
        "user_input": "如何提高团队协作效率？",
        "thinking_mode": "chain_of_thought",
        "conversation_context": "这是一个关于团队管理的问题"
    }
    
    result_without_rule = mind_cell.process(context_without_rule)
    print(f"思考过程: {result_without_rule['thinking_process']}")
    print(f"推理步骤: {result_without_rule['reasoning_steps']}")
    print(f"结论: {result_without_rule['conclusion']}")
    print(f"应用思维规则: {result_without_rule['mind_rule_applied']}")
    print()
    
    print("2. 测试使用MindRule的思考过程")
    print("-" * 50)
    
    mind_rule = """
    思维规则：
    1. 始终从用户体验角度思考问题
    2. 优先考虑可执行性和实用性
    3. 提供具体的行动步骤
    4. 考虑潜在的风险和挑战
    5. 给出量化的评估标准
    """
    
    context_with_rule = {
        "action": "generate_thinking",
        "user_input": "如何提高团队协作效率？",
        "thinking_mode": "chain_of_thought",
        "conversation_context": "这是一个关于团队管理的问题",
        "mind_rule": mind_rule
    }
    
    result_with_rule = mind_cell.process(context_with_rule)
    print(f"思考过程: {result_with_rule['thinking_process']}")
    print(f"推理步骤: {result_with_rule['reasoning_steps']}")
    print(f"结论: {result_with_rule['conclusion']}")
    print(f"应用思维规则: {result_with_rule['mind_rule_applied']}")
    print()
    
    print("3. 测试不同思考模式下的MindRule应用")
    print("-" * 50)
    
    thinking_modes = ["step_by_step", "reflection", "planning", "analysis"]
    
    for mode in thinking_modes:
        print(f"\n测试{mode}模式:")
        context = {
            "action": "generate_thinking",
            "user_input": "如何设计一个用户友好的移动应用？",
            "thinking_mode": mode,
            "mind_rule": "始终以用户为中心，注重简洁性和易用性"
        }
        
        result = mind_cell.process(context)
        print(f"  思考模式: {result['thinking_mode']}")
        print(f"  应用思维规则: {result['mind_rule_applied']}")
        print(f"  思考过程: {result['thinking_process'][:100]}...")
    
    print("\n4. 测试特定动作下的MindRule应用")
    print("-" * 50)
    
    actions = ["analyze_problem", "plan_solution", "reflect"]
    
    for action in actions:
        print(f"\n测试{action}动作:")
        context = {
            "action": action,
            "user_input": "公司需要数字化转型",
            "mind_rule": "采用敏捷方法论，分阶段实施，重视员工培训"
        }
        
        if action == "reflect":
            context["previous_thinking"] = "之前考虑了技术方案，但忽略了人员因素"
        
        result = mind_cell.process(context)
        print(f"  动作类型: {action}")
        print(f"  应用思维规则: {result['mind_rule_applied']}")
        print(f"  置信度: {result['confidence']}")
    
    print("\n5. 测试简单模型的MindRule支持")
    print("-" * 50)
    
    # 创建一个不支持复杂思考的模型
    simple_mind_cell = MindCell({
        "model_name": "gpt-3.5-turbo",  # 不在支持思考的模型列表中
        "max_thinking_tokens": 1000
    })
    
    context_simple = {
        "action": "generate_thinking",
        "user_input": "简单问题测试",
        "thinking_mode": "chain_of_thought",
        "mind_rule": "保持简洁明了"
    }
    
    result_simple = simple_mind_cell.process(context_simple)
    print(f"简单模型思考过程: {result_simple['thinking_process']}")
    print(f"应用思维规则: {result_simple['mind_rule_applied']}")
    
    print("\n=== MindRule功能测试完成 ===")

if __name__ == "__main__":
    test_mind_rule_functionality()