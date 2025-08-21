#!/usr/bin/env python3
"""
Level 1测试运行器 - 配置真实API
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置API配置
from futurembryo import setup_futurx_api
setup_futurx_api(
    api_key="sk-tptTrlFHR14EDpg",
    base_url="https://litellm.futurx.cc"
)

# 运行Level 1测试
if __name__ == "__main__":
    import asyncio
    from level1_basic_life import Level1BasicLifeTest
    
    async def main():
        print("🔧 已配置真实API密钥")
        print("🧬 开始运行Level 1测试...")
        
        level1_test = Level1BasicLifeTest()
        success = await level1_test.run_all_tests()
        
        if success:
            print("🎉 Level 1测试完全通过！")
            return True
        else:
            print("❌ Level 1测试未完全通过")
            return False
    
    success = asyncio.run(main())
    exit(0 if success else 1)