#!/usr/bin/env python3
"""
升级示例以使用核心框架组件
将examples中的本地组件替换为核心框架中已合并的组件
"""

import os
import sys
import shutil
from pathlib import Path

def backup_examples():
    """备份原示例"""
    examples_dir = Path("examples")
    backup_dir = Path("examples_backup")
    
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    
    shutil.copytree(examples_dir, backup_dir)
    print(f"✅ 已备份examples到 {backup_dir}")

def update_imports_in_file(file_path: Path, import_mapping: dict):
    """更新文件中的导入语句"""
    if not file_path.exists():
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 应用导入映射
        for old_import, new_import in import_mapping.items():
            content = content.replace(old_import, new_import)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 更新了 {file_path}")
            return True
        
        return False
    except Exception as e:
        print(f"❌ 更新 {file_path} 失败: {e}")
        return False

def upgrade_multiagent_collaboration():
    """升级multiagent_collaboration示例"""
    print("\n🔄 升级 multiagent_collaboration 示例...")
    
    base_dir = Path("examples/multiagent_collaboration")
    
    # 导入映射 - 将本地导入替换为核心框架导入
    import_mapping = {
        # ContextBuilder
        "from core.context_builder import ContextBuilder": "from futurembryo.core.context_builder import ContextBuilder",
        "from core.context_builder import create_context_builder": "from futurembryo.core.context_builder import create_context_builder",
        
        # MentionProcessorCell
        "from cells.mention_processor_cell import MentionProcessorCell": "from futurembryo.cells.mention_processor_cell import MentionProcessorCell",
        "from cells.mention_processor_cell import create_mention_processor": "from futurembryo.cells.mention_processor_cell import create_mention_processor",
        
        # UserMemoryCell -> UserProfileAdapter
        "from cells.user_memory_cell import UserMemoryCell": "from futurembryo.adapters.user_profile_adapter import UserProfileAdapter",
        
        # 用户数据模型
        "from cells.user_memory_cell import UserProfile": "from futurembryo.core.user_models import UserProfile",
        "from cells.user_memory_cell import UserMemoryEntry": "from futurembryo.core.user_models import UserMemoryEntry",
        "from cells.user_memory_cell import UserPreferences": "from futurembryo.core.user_models import UserPreferences",
        "from cells.user_memory_cell import UserContext": "from futurembryo.core.user_models import UserContext",
    }
    
    # 需要更新的文件列表
    files_to_update = [
        base_dir / "agents/coordinator_agent.py",
        base_dir / "agents/user_aware_agent.py", 
        base_dir / "agents/user_aware_agent_v2.py",
        base_dir / "core/dynamic_agent_factory.py",
        base_dir / "multiagent_demo_v2.py",
        base_dir / "examples/quick_start.py"
    ]
    
    updated_count = 0
    for file_path in files_to_update:
        if update_imports_in_file(file_path, import_mapping):
            updated_count += 1
    
    print(f"✅ multiagent_collaboration: 更新了 {updated_count} 个文件")
    
    # 删除本地组件文件（已合并到核心）
    local_components = [
        base_dir / "cells/mention_processor_cell.py",
        base_dir / "cells/user_memory_cell.py"
    ]
    
    removed_count = 0
    for component_file in local_components:
        if component_file.exists():
            component_file.unlink()
            print(f"🗑️ 删除本地组件: {component_file}")
            removed_count += 1
    
    print(f"✅ 删除了 {removed_count} 个已合并的本地组件")

def upgrade_multiagent_team_static():
    """升级multiagent_team_static示例"""
    print("\n🔄 升级 multiagent_team_static 示例...")
    
    base_dir = Path("examples/multiagent_team_static")
    
    # 相同的导入映射
    import_mapping = {
        "from cells.mention_processor_cell import MentionProcessorCell": "from futurembryo.cells.mention_processor_cell import MentionProcessorCell",
        "from cells.user_memory_cell import UserMemoryCell": "from futurembryo.adapters.user_profile_adapter import UserProfileAdapter",
        "from cells.user_memory_cell import UserProfile": "from futurembryo.core.user_models import UserProfile",
        "from cells.user_memory_cell import UserMemoryEntry": "from futurembryo.core.user_models import UserMemoryEntry",
        "from cells.user_memory_cell import UserPreferences": "from futurembryo.core.user_models import UserPreferences",
    }
    
    files_to_update = [
        base_dir / "agents/coordinator_agent.py",
        base_dir / "agents/user_aware_agent.py",
        base_dir / "multiagent_demo.py"
    ]
    
    updated_count = 0
    for file_path in files_to_update:
        if update_imports_in_file(file_path, import_mapping):
            updated_count += 1
    
    print(f"✅ multiagent_team_static: 更新了 {updated_count} 个文件")
    
    # 删除本地组件
    local_components = [
        base_dir / "cells/mention_processor_cell.py",
        base_dir / "cells/user_memory_cell.py"
    ]
    
    removed_count = 0
    for component_file in local_components:
        if component_file.exists():
            component_file.unlink()
            print(f"🗑️ 删除本地组件: {component_file}")
            removed_count += 1
    
    print(f"✅ 删除了 {removed_count} 个已合并的本地组件")

def create_migration_test():
    """创建迁移测试脚本"""
    test_content = '''#!/usr/bin/env python3
"""
测试升级后的示例是否正常工作
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试核心组件导入"""
    print("🔍 测试核心组件导入...")
    
    try:
        from futurembryo.core.user_models import UserProfile, UserMemoryEntry, UserPreferences, UserContext
        print("✅ 用户数据模型导入成功")
        
        from futurembryo.cells.mention_processor_cell import MentionProcessorCell
        print("✅ @引用处理器导入成功")
        
        from futurembryo.adapters.user_profile_adapter import UserProfileAdapter
        print("✅ 用户画像适配器导入成功")
        
        from futurembryo.core.context_builder import ContextBuilder
        print("✅ 上下文构建器导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_examples():
    """测试示例组件"""
    print("\\n🔍 测试示例高级组件...")
    
    try:
        # 测试dynamic_agent_factory仍然可用
        sys.path.insert(0, str(Path("examples/multiagent_collaboration")))
        from core.dynamic_agent_factory import DynamicAgentFactory
        print("✅ DynamicAgentFactory可用")
        
        from agents.coordinator_agent import CoordinatorAgent  
        print("✅ CoordinatorAgent可用")
        
        from agents.user_aware_agent_v2 import UserAwareAgent
        print("✅ UserAwareAgent可用")
        
        return True
    except Exception as e:
        print(f"❌ 示例组件测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试示例升级结果")
    print("=" * 50)
    
    tests = [
        ("核心组件导入", test_imports),
        ("示例高级组件", test_examples)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: 通过")
            else:
                print(f"❌ {test_name}: 失败")
        except Exception as e:
            print(f"❌ {test_name}: 错误 - {e}")
    
    print("=" * 50)
    print(f"📊 测试结果: {passed}/{len(tests)} 通过")
    
    if passed == len(tests):
        print("🎉 所有测试通过！示例升级成功！")
    else:
        print("⚠️ 部分测试失败，需要进一步调试")

if __name__ == "__main__":
    main()
'''
    
    with open("test_examples_upgrade.py", 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("✅ 创建了迁移测试脚本: test_examples_upgrade.py")

def main():
    """主升级函数"""
    print("🚀 开始升级examples以使用核心框架组件")
    print("=" * 60)
    
    # 询问用户是否继续
    response = input("是否继续升级示例？这将修改examples中的文件 (y/N): ").strip().lower()
    if response != 'y':
        print("❌ 升级被取消")
        return
    
    try:
        # 备份
        backup_examples()
        
        # 升级各个示例
        upgrade_multiagent_collaboration()
        upgrade_multiagent_team_static()
        
        # 创建测试脚本
        create_migration_test()
        
        print("\n" + "=" * 60)
        print("🎉 示例升级完成!")
        print("\n📋 升级总结:")
        print("✅ 所有本地组件导入已更新为核心框架组件")
        print("✅ 重复的本地组件文件已删除") 
        print("✅ 示例现在使用统一的核心组件")
        print("✅ 创建了备份: examples_backup/")
        print("✅ 创建了测试脚本: test_examples_upgrade.py")
        
        print("\n🔧 下一步:")
        print("1. 运行测试: python test_examples_upgrade.py")
        print("2. 测试示例: python examples/multiagent_collaboration/multiagent_demo_v2.py")
        print("3. 如有问题，可从 examples_backup/ 恢复")
        
    except Exception as e:
        print(f"\n❌ 升级过程中出错: {e}")
        print("💡 请检查错误并从备份恢复必要的文件")

if __name__ == "__main__":
    main()