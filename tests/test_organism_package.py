"""
AI Embryo Engine — OrganismPackage 测试

覆盖: OrganismPackage 创建/加载/保存/编译
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_embryo.organism_package import OrganismPackage, PERSONA_TEMPLATES


class TestOrganismPackageCreate:
    """测试 OrganismPackage 创建"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_create_analytical_organism(self):
        """测试创建分析师类型生命体"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestAnalyst",
            purpose="深度分析和技术咨询",
            persona_config={"type": "analytical"},
        )

        assert pkg.name == "TestAnalyst"
        assert pkg.generation == 1
        assert pkg.parent_a is None
        assert pkg.parent_b is None
        assert pkg.read_soul() != ""
        assert "分析" in pkg.read_soul() or "严谨" in pkg.read_soul()
        assert pkg.read_mind() != ""
        assert pkg.read_values() != ""

    def test_create_creative_organism(self):
        """测试创建创意者类型生命体"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestCreative",
            purpose="创意内容生成",
            persona_config={"type": "creative"},
        )

        assert pkg.name == "TestCreative"
        assert pkg.read_soul() != ""
        assert "想象" in pkg.read_soul() or "创意" in pkg.read_soul()

    def test_create_executive_organism(self):
        """测试创建执行者类型生命体"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestExecutive",
            purpose="高效执行和决策",
            persona_config={"type": "executive"},
        )

        assert pkg.name == "TestExecutive"
        assert pkg.read_soul() != ""
        assert "执行" in pkg.read_soul() or "行动" in pkg.read_soul()

    def test_create_custom_organism(self):
        """测试创建自定义类型生命体"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestCustom",
            purpose="自定义AI助手",
            persona_config={"type": "custom"},
        )

        assert pkg.name == "TestCustom"
        assert pkg.read_soul() != ""

    def test_package_directory_structure(self):
        """测试包目录结构"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestStructure",
            purpose="测试结构",
            persona_config={"type": "analytical"},
        )

        base = Path(self.temp_dir)
        assert (base / "GENOME.yaml").exists()
        assert (base / "IDENTITY.md").exists()
        assert (base / "SOUL.md").exists()
        assert (base / "MIND.md").exists()
        assert (base / "VALUES.md").exists()
        assert (base / "config.yaml").exists()
        assert (base / "skills").is_dir()
        assert (base / "memory").is_dir()
        assert (base / "memory" / "episodes").is_dir()
        assert (base / "memory" / "reflections").is_dir()
        assert (base / "knowledge").is_dir()
        assert (base / "evolution").is_dir()


class TestOrganismPackageLoad:
    """测试 OrganismPackage 加载"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_load_package(self):
        """测试加载已保存的包"""
        pkg1 = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestLoad",
            purpose="测试加载",
            persona_config={"type": "analytical"},
        )
        pkg1.fitness = 0.85
        pkg1.save()

        pkg2 = OrganismPackage.load(self.temp_dir)

        assert pkg2 is not None
        assert pkg2.name == "TestLoad"
        assert pkg2.fitness == 0.85
        assert pkg2.read_soul() == pkg1.read_soul()
        assert pkg2.read_mind() == pkg1.read_mind()
        assert pkg2.read_values() == pkg1.read_values()

    def test_load_nonexistent(self):
        """测试加载不存在的包"""
        pkg = OrganismPackage.load("/nonexistent/path")
        assert pkg is None

    def test_load_with_lineage(self):
        """测试加载带族谱信息的包"""
        pkg1 = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="ParentA",
            purpose="父代A",
            persona_config={"type": "analytical"},
        )

        child_dir = Path(self.temp_dir).parent / "Child"
        pkg2 = OrganismPackage.create(
            base_dir=child_dir,
            name="Child",
            purpose="子代",
            persona_config={"type": "analytical"},
        )
        pkg2.parent_a = "ParentA"
        pkg2.parent_b = None
        pkg2.generation = 2
        pkg2.save()

        loaded = OrganismPackage.load(child_dir)
        assert loaded.parent_a == "ParentA"
        assert loaded.generation == 2


class TestOrganismPackageSave:
    """测试 OrganismPackage 保存"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_save_updates_files(self):
        """测试保存更新文件"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestSave",
            purpose="测试保存",
            persona_config={"type": "analytical"},
        )

        new_soul = "# 灵魂\n\n更新后的灵魂内容"
        pkg.write_soul(new_soul)
        pkg.save()

        pkg2 = OrganismPackage.load(self.temp_dir)
        assert pkg2.read_soul() == new_soul


class TestOrganismPackageCompile:
    """测试 system prompt 编译"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_compile_system_prompt(self):
        """测试编译 system prompt"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestCompile",
            purpose="测试编译",
            persona_config={"type": "analytical"},
        )

        prompt = pkg.compile_system_prompt()
        assert "TestCompile" in prompt
        assert "测试编译" in prompt
        assert len(prompt) > 0

    def test_compile_respects_max_chars(self):
        """测试编译遵守最大字符限制"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestTruncate",
            purpose="测试截断" * 100,
            persona_config={"type": "analytical"},
        )

        prompt = pkg.compile_system_prompt(max_chars=500)
        assert len(prompt) <= 500 + 200

    def test_compile_includes_soul(self):
        """测试编译包含灵魂"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestSoul",
            purpose="测试灵魂",
            persona_config={"type": "analytical"},
        )

        prompt = pkg.compile_system_prompt()
        assert "灵魂" in prompt or "SOUL" in prompt.upper()

    def test_compile_includes_values(self):
        """测试编译包含价值观"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestValues",
            purpose="测试价值观",
            persona_config={"type": "analytical"},
        )

        prompt = pkg.compile_system_prompt()
        assert "价值观" in prompt or "VALUES" in prompt.upper()


class TestOrganismPackageMemory:
    """测试记忆功能"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_update_memory(self):
        """测试更新记忆"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestMemory",
            purpose="测试记忆",
            persona_config={"type": "analytical"},
        )

        pkg.update_memory({"user": "你好", "assistant": "你好，有什么可以帮助你的？"})

        assert len(pkg._memory_episodes) == 1

    def test_add_reflection(self):
        """测试添加反思"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestReflection",
            purpose="测试反思",
            persona_config={"type": "analytical"},
        )

        pkg.add_reflection("# 反思\n\n这次对话表现良好。")

        assert len(pkg._memory_reflections) == 1


class TestOrganismPackageSkill:
    """测试技能功能"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_add_skill(self):
        """测试添加技能"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestSkill",
            purpose="测试技能",
            persona_config={"type": "analytical"},
        )

        pkg.add_skill({"name": "web-search", "description": "网络搜索能力"})

        assert len(pkg.list_skills()) == 1
        assert "web-search" in pkg.list_skills()

    def test_list_skills_empty(self):
        """测试空技能列表"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestNoSkills",
            purpose="没有技能",
            persona_config={"type": "analytical"},
        )

        assert len(pkg.list_skills()) == 0


class TestOrganismPackageInfo:
    """测试 to_info 方法"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_to_info(self):
        """测试转换为 info dict"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestInfo",
            purpose="测试信息",
            persona_config={"type": "analytical"},
        )
        pkg.fitness = 0.85

        info = pkg.to_info()

        assert info["name"] == "TestInfo"
        assert info["fitness"] == 0.85
        assert info["purpose"] == "测试信息"
        assert "soul_summary" in info
        assert "mind_summary" in info
        assert "values_summary" in info

    def test_get_genome_data(self):
        """测试获取基因组数据"""
        pkg = OrganismPackage.create(
            base_dir=self.temp_dir,
            name="TestGenome",
            purpose="测试基因组",
            persona_config={"type": "analytical"},
        )

        genome_data = pkg.get_genome_data()

        assert genome_data["name"] == "TestGenome"
        assert "evolution" in genome_data


class TestPersonaTemplates:
    """测试 persona 模板"""

    def test_analytical_template(self):
        """测试分析师模板"""
        template = PERSONA_TEMPLATES["analytical"]
        assert "soul" in template
        assert "mind" in template
        assert "values" in template
        assert len(template["soul"]) > 0
        assert len(template["mind"]) > 0
        assert len(template["values"]) > 0

    def test_creative_template(self):
        """测试创意者模板"""
        template = PERSONA_TEMPLATES["creative"]
        assert "soul" in template
        assert "mind" in template
        assert "values" in template

    def test_executive_template(self):
        """测试执行者模板"""
        template = PERSONA_TEMPLATES["executive"]
        assert "soul" in template
        assert "mind" in template
        assert "values" in template

    def test_custom_template(self):
        """测试自定义模板"""
        template = PERSONA_TEMPLATES["custom"]
        assert "soul" in template
        assert "mind" in template
        assert "values" in template


def run_tests():
    """运行所有测试"""
    import traceback

    test_classes = [
        TestOrganismPackageCreate,
        TestOrganismPackageLoad,
        TestOrganismPackageSave,
        TestOrganismPackageCompile,
        TestOrganismPackageMemory,
        TestOrganismPackageSkill,
        TestOrganismPackageInfo,
        TestPersonaTemplates,
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        print(f"\n{'=' * 60}")
        print(f"🧪 {test_class.__name__}")
        print(f"{'=' * 60}")

        instance = test_class()
        setup_method = getattr(instance, "setup_method", None)
        teardown_method = getattr(instance, "teardown_method", None)

        for method_name in dir(instance):
            if not method_name.startswith("test_"):
                continue

            if setup_method:
                try:
                    setup_method()
                except Exception as e:
                    print(f"  ⚠️ Setup failed: {e}")
                    continue

            try:
                getattr(instance, method_name)()
                print(f"  ✅ {method_name}")
                passed += 1
            except Exception as e:
                print(f"  ❌ {method_name}: {e}")
                traceback.print_exc()
                failed += 1
            finally:
                if teardown_method:
                    try:
                        teardown_method()
                    except Exception:
                        pass

    print(f"\n{'=' * 60}")
    print(f"📊 结果: {passed} 通过, {failed} 失败, 共 {passed + failed} 测试")
    print(f"{'=' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
