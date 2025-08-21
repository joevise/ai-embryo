#!/usr/bin/env python3
"""
Level 7: 杂交生成能力测试

测试目标：验证数字生命体的融合创新和杂交生成能力
- 生命体基因融合
- 杂交后代生成
- 创新能力涌现
- 生命进化验证
"""

import asyncio
import sys
from pathlib import Path

# 添加测试工具路径
sys.path.append(str(Path(__file__).parent))

from test_config import TestLevel, get_test_config, get_api_config
from utils.test_utils import TestRunner, validate_life_form_basic, test_basic_interaction
from utils.test_utils import assert_success_rate, assert_response_time, assert_metric_threshold


class Level7HybridTest:
    """Level 7 杂交生成能力测试类"""
    
    def __init__(self):
        self.test_config = get_test_config(TestLevel.LEVEL_7_HYBRID)
        self.runner = TestRunner("Level 7: 杂交生成能力")
        self.parent_life_forms = {}
        self.hybrid_life_forms = {}
    
    async def run_all_tests(self):
        """运行所有Level 7测试"""
        
        print("🧬 Level 7: 杂交生成能力测试")
        print("=" * 50)
        print("测试范围: 基因融合, 杂交生成, 创新涌现, 生命进化")
        print("新增功能: 生命体杂交, DNA融合, 能力继承与创新")
        print()
        
        # 初始化测试环境
        try:
            api_config = get_api_config()
            await self.runner.initialize_environment(api_config)
        except Exception as e:
            print(f"⚠️  API配置失败，使用演示模式: {e}")
            await self.runner.initialize_environment()
        
        # 执行测试
        await self.test_parent_life_creation()
        await self.test_genetic_fusion()
        await self.test_hybrid_generation()
        await self.test_capability_inheritance()
        await self.test_innovation_emergence()
        
        # 清理
        self.runner.cleanup()
        
        # 输出结果
        self.runner.print_summary()
        return self.runner.get_success_rate() >= 0.55  # 要求55%通过率
    
    async def test_parent_life_creation(self):
        """测试父代生命体创建"""
        
        async with self.runner.run_test("父代生命体创建") as result:
            print("🧬 测试父代生命体创建...")
            
            # 创建具有不同特色的父代生命体
            parent_specs = [
                {
                    "name": "analytical_parent",
                    "goal": "创建一个专业的数据分析专家",
                    "constraints": {
                        "cell_types": ["LLMCell", "MindCell", "StateMemoryCell", "ToolCell"],
                        "specialization": "analytical_thinking",
                        "personality": "logical_precise",
                        "strength": "data_analysis"
                    }
                },
                {
                    "name": "creative_parent",
                    "goal": "创建一个富有创意的内容创作者",
                    "constraints": {
                        "cell_types": ["LLMCell", "MindCell", "StateMemoryCell"],
                        "specialization": "creative_thinking",
                        "personality": "imaginative_innovative",
                        "strength": "content_creation"
                    }
                },
                {
                    "name": "collaborative_parent",
                    "goal": "创建一个善于协作的团队协调者",
                    "constraints": {
                        "cell_types": ["LLMCell", "MindCell", "StateMemoryCell"],
                        "specialization": "collaboration",
                        "personality": "empathetic_communicative",
                        "strength": "team_coordination"
                    }
                }
            ]
            
            creation_results = []
            
            for spec in parent_specs:
                try:
                    parent_life = await self.runner.environment.create_basic_life(
                        goal=spec["goal"],
                        constraints=spec["constraints"]
                    )
                    
                    self.parent_life_forms[spec["name"]] = parent_life
                    
                    # 验证父代特征
                    validations = validate_life_form_basic(parent_life)
                    parent_status = parent_life.get_status()
                    
                    # 测试父代特色能力
                    specialty_test = await self._test_parent_specialty(parent_life, spec["constraints"]["strength"])
                    
                    creation_results.append({
                        "name": spec["name"],
                        "created": True,
                        "basic_validations": sum(validations.values()),
                        "specialty_score": specialty_test["score"],
                        "cell_count": len(parent_life.cells),
                        "specialization": spec["constraints"]["specialization"]
                    })
                    
                    print(f"   ✅ {spec['name']}: 创建成功")
                    print(f"      专业能力: {specialty_test['score']:.2f}")
                    print(f"      Cell架构: {len(parent_life.cells)}个Cell")
                    
                    result.add_artifact(f"parent_{spec['name']}", parent_life)
                    
                except Exception as e:
                    print(f"   ❌ {spec['name']}: 创建失败 - {e}")
                    creation_results.append({
                        "name": spec["name"],
                        "created": False,
                        "error": str(e)
                    })
            
            # 验证父代创建成功率
            successful_parents = sum(1 for r in creation_results if r.get("created", False))
            parent_creation_rate = successful_parents / len(parent_specs)
            
            print(f"   📊 父代创建成功率: {parent_creation_rate*100:.1f}%")
            print(f"   🧬 成功创建: {successful_parents}/{len(parent_specs)}个父代")
            
            # 验证父代多样性
            specializations = set(r.get("specialization") for r in creation_results if r.get("created"))
            diversity_score = len(specializations) / len(parent_specs)
            
            print(f"   🌈 父代多样性: {diversity_score*100:.1f}%")
            
            # 验证创建标准
            expected_rate = self.test_config.success_criteria.get("parent_creation", 0.8)
            assert_success_rate(parent_creation_rate, expected_rate, "父代生命体创建")
            
            result.mark_success({
                "parent_creation_rate": parent_creation_rate,
                "successful_parents": successful_parents,
                "diversity_score": diversity_score,
                "total_parents": len(parent_specs)
            })
    
    async def _test_parent_specialty(self, parent_life, strength_type):
        """测试父代的专业能力"""
        specialty_tasks = {
            "data_analysis": "分析这组数据的趋势和特点: [1, 5, 3, 8, 6, 9, 4, 7]",
            "content_creation": "创作一个关于春天的短诗",
            "team_coordination": "制定一个5人团队的项目分工计划"
        }
        
        task = specialty_tasks.get(strength_type, "展示你的专业能力")
        
        try:
            specialty_result = await parent_life.think(task)
            if specialty_result.get("success", False):
                response = specialty_result.get("data", {}).get("response", "")
                score = self._assess_specialty_performance(response, strength_type)
                return {"score": score, "response_length": len(response)}
            else:
                return {"score": 0.0, "error": specialty_result.get("error", "")}
        except Exception as e:
            return {"score": 0.0, "error": str(e)}
    
    def _assess_specialty_performance(self, response: str, strength_type: str) -> float:
        """评估专业能力表现"""
        if not response:
            return 0.0
        
        score = 0.0
        
        if strength_type == "data_analysis":
            analysis_indicators = ["趋势", "增长", "下降", "平均", "最大", "最小", "分析", "数据"]
            score = sum(0.125 for indicator in analysis_indicators if indicator in response)
            
        elif strength_type == "content_creation":
            creative_indicators = ["春天", "花", "绿", "生机", "温暖", "阳光", "诗意", "美好"]
            score = sum(0.125 for indicator in creative_indicators if indicator in response)
            if len(response.split('\n')) > 2:  # 多行诗歌
                score += 0.2
                
        elif strength_type == "team_coordination":
            coordination_indicators = ["分工", "责任", "协调", "沟通", "计划", "时间", "任务", "团队"]
            score = sum(0.125 for indicator in coordination_indicators if indicator in response)
        
        return min(score, 1.0)
    
    async def test_genetic_fusion(self):
        """测试基因融合机制"""
        
        async with self.runner.run_test("基因融合机制") as result:
            print("\n🧬 测试基因融合...")
            
            if len(self.parent_life_forms) < 2:
                raise RuntimeError("需要至少2个父代生命体进行基因融合测试")
            
            # 选择两个父代进行融合
            parent_names = list(self.parent_life_forms.keys())
            parent1_name = parent_names[0]
            parent2_name = parent_names[1]
            
            parent1 = self.parent_life_forms[parent1_name]
            parent2 = self.parent_life_forms[parent2_name]
            
            print(f"   🧬 父代1: {parent1_name}")
            print(f"   🧬 父代2: {parent2_name}")
            
            fusion_results = []
            
            try:
                # 获取父代的DNA信息
                parent1_dna = parent1.dna
                parent2_dna = parent2.dna
                
                print(f"   📊 父代1 DNA: {parent1_dna.name}")
                print(f"   📊 父代2 DNA: {parent2_dna.name}")
                
                # 分析父代基因特征
                parent1_features = self._extract_genetic_features(parent1)
                parent2_features = self._extract_genetic_features(parent2)
                
                print(f"   🧬 父代1特征: {list(parent1_features.keys())}")
                print(f"   🧬 父代2特征: {list(parent2_features.keys())}")
                
                # 模拟基因融合过程
                fusion_strategy = self._design_fusion_strategy(parent1_features, parent2_features)
                
                fusion_results.append({
                    "parent1": parent1_name,
                    "parent2": parent2_name,
                    "parent1_features": parent1_features,
                    "parent2_features": parent2_features,
                    "fusion_strategy": fusion_strategy,
                    "fusion_feasible": len(fusion_strategy) > 0
                })
                
                print(f"   🔬 融合策略: {len(fusion_strategy)}个融合点")
                for strategy in fusion_strategy:
                    print(f"      {strategy}")
                
                # 验证融合可行性
                fusion_feasible = len(fusion_strategy) >= 2  # 至少要有2个融合点
                
                if fusion_feasible:
                    result.mark_success({
                        "fusion_feasible": True,
                        "fusion_points": len(fusion_strategy),
                        "parent1_features": len(parent1_features),
                        "parent2_features": len(parent2_features)
                    })
                else:
                    raise AssertionError("基因融合策略不足")
                
            except Exception as e:
                print(f"   ❌ 基因融合分析失败: {e}")
                fusion_results.append({
                    "parent1": parent1_name,
                    "parent2": parent2_name,
                    "error": str(e),
                    "fusion_feasible": False
                })
                raise
    
    def _extract_genetic_features(self, life_form) -> dict:
        """提取生命体的基因特征"""
        features = {}
        
        # Cell架构特征
        cell_types = [cell.__class__.__name__ for cell in life_form.cells]
        features["cell_architecture"] = cell_types
        
        # 状态特征
        status = life_form.get_status()
        if "personality" in status:
            features["personality"] = status["personality"]
        
        # DNA特征
        if hasattr(life_form, 'dna'):
            features["dna_name"] = life_form.dna.name
            if hasattr(life_form.dna, 'config'):
                features["dna_config"] = life_form.dna.config
        
        # 生命名片特征
        if hasattr(life_form, 'life_card_data'):
            card_data = life_form.life_card_data
            if "capabilities" in card_data:
                features["capabilities"] = card_data["capabilities"]
        
        return features
    
    def _design_fusion_strategy(self, features1: dict, features2: dict) -> list:
        """设计基因融合策略"""
        strategies = []
        
        # Cell架构融合
        if "cell_architecture" in features1 and "cell_architecture" in features2:
            cells1 = set(features1["cell_architecture"])
            cells2 = set(features2["cell_architecture"])
            common_cells = cells1 & cells2
            unique_cells1 = cells1 - cells2
            unique_cells2 = cells2 - cells1
            
            if common_cells:
                strategies.append(f"保留共同Cell: {list(common_cells)}")
            if unique_cells1:
                strategies.append(f"继承父代1独有Cell: {list(unique_cells1)}")
            if unique_cells2:
                strategies.append(f"继承父代2独有Cell: {list(unique_cells2)}")
        
        # 能力融合
        if "capabilities" in features1 and "capabilities" in features2:
            strategies.append("融合父代能力特征")
        
        # 个性融合
        if "personality" in features1 and "personality" in features2:
            strategies.append("混合个性特征")
        
        return strategies
    
    async def test_hybrid_generation(self):
        """测试杂交后代生成"""
        
        async with self.runner.run_test("杂交后代生成") as result:
            print("\n🌟 测试杂交后代生成...")
            
            if len(self.parent_life_forms) < 2:
                raise RuntimeError("需要至少2个父代生命体进行杂交测试")
            
            # 进行杂交生成
            parent_names = list(self.parent_life_forms.keys())
            hybridization_pairs = [
                (parent_names[0], parent_names[1]),
                (parent_names[1], parent_names[2] if len(parent_names) > 2 else parent_names[0])
            ]
            
            hybrid_generation_results = []
            
            for i, (parent1_name, parent2_name) in enumerate(hybridization_pairs):
                try:
                    parent1 = self.parent_life_forms[parent1_name]
                    parent2 = self.parent_life_forms[parent2_name]
                    
                    print(f"   🧬 杂交{i+1}: {parent1_name} × {parent2_name}")
                    
                    # 设计杂交后代目标
                    hybrid_goal = f"创建融合{parent1_name}和{parent2_name}优势的杂交后代"
                    
                    # 构建杂交约束
                    parent1_features = self._extract_genetic_features(parent1)
                    parent2_features = self._extract_genetic_features(parent2)
                    
                    hybrid_constraints = {
                        "hybridization": True,
                        "parent1_genes": parent1_features,
                        "parent2_genes": parent2_features,
                        "inheritance_strategy": "best_of_both",
                        "innovation_allowed": True
                    }
                    
                    # 生成杂交后代
                    hybrid_life = await self.runner.environment.create_basic_life(
                        goal=hybrid_goal,
                        constraints=hybrid_constraints
                    )
                    
                    hybrid_name = f"hybrid_{i+1}_{parent1_name[:4]}_{parent2_name[:4]}"
                    self.hybrid_life_forms[hybrid_name] = hybrid_life
                    
                    # 验证杂交后代
                    hybrid_validations = validate_life_form_basic(hybrid_life)
                    hybrid_features = self._extract_genetic_features(hybrid_life)
                    
                    # 分析继承性
                    inheritance_analysis = self._analyze_inheritance(
                        parent1_features, parent2_features, hybrid_features
                    )
                    
                    hybrid_generation_results.append({
                        "hybrid_name": hybrid_name,
                        "parent1": parent1_name,
                        "parent2": parent2_name,
                        "generation_success": True,
                        "basic_validations": sum(hybrid_validations.values()),
                        "inheritance_score": inheritance_analysis["score"],
                        "innovation_detected": inheritance_analysis["innovation"],
                        "cell_count": len(hybrid_life.cells)
                    })
                    
                    print(f"   ✅ {hybrid_name}: 生成成功")
                    print(f"      继承分数: {inheritance_analysis['score']:.2f}")
                    print(f"      创新检测: {'✅' if inheritance_analysis['innovation'] else '❌'}")
                    print(f"      Cell数量: {len(hybrid_life.cells)}")
                    
                    result.add_artifact(f"hybrid_{hybrid_name}", hybrid_life)
                    
                except Exception as e:
                    print(f"   ❌ 杂交{i+1}失败: {e}")
                    hybrid_generation_results.append({
                        "hybrid_name": f"hybrid_{i+1}_failed",
                        "parent1": parent1_name,
                        "parent2": parent2_name,
                        "generation_success": False,
                        "error": str(e)
                    })
            
            # 计算杂交成功率
            successful_hybrids = sum(1 for r in hybrid_generation_results if r.get("generation_success", False))
            hybrid_success_rate = successful_hybrids / len(hybridization_pairs)
            
            # 计算平均继承分数
            inheritance_scores = [r.get("inheritance_score", 0) for r in hybrid_generation_results if r.get("generation_success")]
            avg_inheritance = sum(inheritance_scores) / len(inheritance_scores) if inheritance_scores else 0
            
            # 计算创新率
            innovations = sum(1 for r in hybrid_generation_results if r.get("innovation_detected", False))
            innovation_rate = innovations / len(hybridization_pairs)
            
            print(f"   📊 杂交成功率: {hybrid_success_rate*100:.1f}%")
            print(f"   🧬 平均继承分数: {avg_inheritance:.2f}")
            print(f"   🌟 创新率: {innovation_rate*100:.1f}%")
            
            # 验证杂交生成效果
            expected_rate = self.test_config.success_criteria.get("hybrid_generation", 0.6)
            assert_success_rate(hybrid_success_rate, expected_rate, "杂交后代生成")
            
            result.mark_success({
                "hybrid_success_rate": hybrid_success_rate,
                "avg_inheritance_score": avg_inheritance,
                "innovation_rate": innovation_rate,
                "successful_hybrids": successful_hybrids,
                "total_attempts": len(hybridization_pairs)
            })
    
    def _analyze_inheritance(self, parent1_features: dict, parent2_features: dict, hybrid_features: dict) -> dict:
        """分析继承情况"""
        inheritance_score = 0.0
        innovation_detected = False
        
        # 检查Cell架构继承
        if "cell_architecture" in hybrid_features:
            hybrid_cells = set(hybrid_features["cell_architecture"])
            parent1_cells = set(parent1_features.get("cell_architecture", []))
            parent2_cells = set(parent2_features.get("cell_architecture", []))
            
            # 计算继承度
            inherited_from_p1 = len(hybrid_cells & parent1_cells)
            inherited_from_p2 = len(hybrid_cells & parent2_cells)
            total_parent_cells = len(parent1_cells | parent2_cells)
            
            if total_parent_cells > 0:
                inheritance_score += 0.4 * (inherited_from_p1 + inherited_from_p2) / total_parent_cells
            
            # 检查创新（新组合或新Cell）
            unique_hybrid_cells = hybrid_cells - parent1_cells - parent2_cells
            if unique_hybrid_cells or len(hybrid_cells) > max(len(parent1_cells), len(parent2_cells)):
                innovation_detected = True
                inheritance_score += 0.2
        
        # 检查能力继承
        if "capabilities" in hybrid_features:
            inheritance_score += 0.2  # 有能力定义就加分
            
            # 简单检查是否融合了父代能力
            if ("capabilities" in parent1_features or "capabilities" in parent2_features):
                inheritance_score += 0.2
        
        return {
            "score": min(inheritance_score, 1.0),
            "innovation": innovation_detected
        }
    
    async def test_capability_inheritance(self):
        """测试能力继承验证"""
        
        async with self.runner.run_test("能力继承验证") as result:
            print("\n🔗 测试能力继承...")
            
            if not self.hybrid_life_forms:
                raise RuntimeError("需要先生成杂交后代")
            
            capability_tests = []
            
            # 为每个杂交后代测试继承的能力
            for hybrid_name, hybrid_life in self.hybrid_life_forms.items():
                print(f"   🧬 测试 {hybrid_name} 的能力继承...")
                
                try:
                    # 测试分析能力（来自analytical_parent）
                    analysis_task = "分析这个数据序列的模式: [2, 4, 8, 16, 32]"
                    analysis_result = await hybrid_life.think(analysis_task)
                    analysis_success = analysis_result.get("success", False)
                    analysis_quality = 0
                    
                    if analysis_success:
                        response = analysis_result.get("data", {}).get("response", "")
                        analysis_indicators = ["倍数", "指数", "增长", "模式", "规律", "2的幂"]
                        analysis_quality = sum(0.2 for indicator in analysis_indicators if indicator in response)
                    
                    # 测试创意能力（来自creative_parent）
                    creative_task = "为一个科技公司想一个有创意的口号"
                    creative_result = await hybrid_life.think(creative_task)
                    creative_success = creative_result.get("success", False)
                    creative_quality = 0
                    
                    if creative_success:
                        response = creative_result.get("data", {}).get("response", "")
                        creative_indicators = ["创新", "未来", "科技", "梦想", "突破", "智能"]
                        creative_quality = sum(0.2 for indicator in creative_indicators if indicator in response)
                        if len(response) > 20:  # 有一定长度
                            creative_quality += 0.2
                    
                    # 测试协调能力（来自collaborative_parent）
                    coordination_task = "如何协调两个有冲突观点的团队成员"
                    coordination_result = await hybrid_life.think(coordination_task)
                    coordination_success = coordination_result.get("success", False)
                    coordination_quality = 0
                    
                    if coordination_success:
                        response = coordination_result.get("data", {}).get("response", "")
                        coordination_indicators = ["沟通", "理解", "妥协", "合作", "平衡", "协调"]
                        coordination_quality = sum(0.2 for indicator in coordination_indicators if indicator in response)
                    
                    # 计算综合继承能力
                    inherited_capabilities = {
                        "analysis": analysis_quality,
                        "creativity": creative_quality,
                        "coordination": coordination_quality
                    }
                    
                    avg_capability = sum(inherited_capabilities.values()) / len(inherited_capabilities)
                    capability_diversity = len([c for c in inherited_capabilities.values() if c > 0.3])
                    
                    capability_tests.append({
                        "hybrid_name": hybrid_name,
                        "analysis_capability": analysis_quality,
                        "creative_capability": creative_quality,
                        "coordination_capability": coordination_quality,
                        "avg_capability": avg_capability,
                        "capability_diversity": capability_diversity,
                        "inheritance_success": avg_capability > 0.3
                    })
                    
                    print(f"      📊 分析能力: {analysis_quality:.2f}")
                    print(f"      🎨 创意能力: {creative_quality:.2f}")
                    print(f"      🤝 协调能力: {coordination_quality:.2f}")
                    print(f"      📈 平均能力: {avg_capability:.2f}")
                    print(f"      🌈 能力多样性: {capability_diversity}/3")
                    
                except Exception as e:
                    print(f"      ❌ 能力测试失败: {e}")
                    capability_tests.append({
                        "hybrid_name": hybrid_name,
                        "error": str(e),
                        "inheritance_success": False
                    })
            
            # 计算整体继承效果
            successful_inheritance = sum(1 for test in capability_tests if test.get("inheritance_success", False))
            inheritance_success_rate = successful_inheritance / len(capability_tests) if capability_tests else 0
            
            # 计算平均能力水平
            valid_tests = [test for test in capability_tests if "avg_capability" in test]
            avg_capability_level = sum(test["avg_capability"] for test in valid_tests) / len(valid_tests) if valid_tests else 0
            
            # 计算能力多样性
            total_diversity = sum(test.get("capability_diversity", 0) for test in valid_tests)
            avg_diversity = total_diversity / len(valid_tests) if valid_tests else 0
            
            print(f"   📊 继承成功率: {inheritance_success_rate*100:.1f}%")
            print(f"   💪 平均能力水平: {avg_capability_level:.2f}")
            print(f"   🌈 平均能力多样性: {avg_diversity:.1f}/3")
            
            # 验证能力继承效果
            expected_rate = self.test_config.success_criteria.get("capability_inheritance", 0.5)
            assert_success_rate(inheritance_success_rate, expected_rate, "能力继承验证")
            
            result.mark_success({
                "inheritance_success_rate": inheritance_success_rate,
                "avg_capability_level": avg_capability_level,
                "avg_diversity": avg_diversity,
                "successful_inheritance": successful_inheritance,
                "total_hybrids": len(capability_tests)
            })
    
    async def test_innovation_emergence(self):
        """测试创新涌现能力"""
        
        async with self.runner.run_test("创新涌现验证") as result:
            print("\n🌟 测试创新涌现...")
            
            if not self.hybrid_life_forms:
                raise RuntimeError("需要先生成杂交后代")
            
            innovation_tests = []
            
            # 为杂交后代设计创新挑战任务
            innovation_challenges = [
                {
                    "task": "设计一个结合AI和艺术的创新产品概念",
                    "innovation_indicators": ["融合", "创新", "突破", "独特", "前所未有", "颠覆"],
                    "complexity_level": "high"
                },
                {
                    "task": "提出一个解决团队协作和数据分析结合的新方法",
                    "innovation_indicators": ["整合", "新方法", "创造性", "革新", "突破性", "独创"],
                    "complexity_level": "medium"
                },
                {
                    "task": "创造一个新的学习模式，结合个人学习和团队合作",
                    "innovation_indicators": ["创造", "新模式", "原创", "创新性", "突破", "发明"],
                    "complexity_level": "high"
                }
            ]
            
            for hybrid_name, hybrid_life in self.hybrid_life_forms.items():
                print(f"   🌟 测试 {hybrid_name} 的创新能力...")
                
                hybrid_innovation_scores = []
                
                for i, challenge in enumerate(innovation_challenges):
                    try:
                        # 执行创新挑战
                        innovation_result = await hybrid_life.think(
                            challenge["task"],
                            context={"innovation_challenge": True, "require_creativity": True}
                        )
                        
                        if innovation_result.get("success", False):
                            response = innovation_result.get("data", {}).get("response", "")
                            
                            # 评估创新性
                            innovation_score = self._assess_innovation_quality(
                                response, challenge["innovation_indicators"], challenge["complexity_level"]
                            )
                            
                            # 检测是否超越父代能力
                            transcendence_detected = await self._detect_transcendence(
                                hybrid_life, response, challenge["task"]
                            )
                            
                            hybrid_innovation_scores.append({
                                "challenge": i + 1,
                                "innovation_score": innovation_score,
                                "transcendence": transcendence_detected,
                                "response_length": len(response)
                            })
                            
                            print(f"      🎯 挑战{i+1}: 创新分数{innovation_score:.2f}, 超越性{'✅' if transcendence_detected else '❌'}")
                            
                        else:
                            print(f"      ❌ 挑战{i+1}: 执行失败")
                            hybrid_innovation_scores.append({
                                "challenge": i + 1,
                                "innovation_score": 0,
                                "transcendence": False,
                                "error": innovation_result.get("error", "")
                            })
                            
                    except Exception as e:
                        print(f"      ❌ 挑战{i+1}: 异常 - {e}")
                        hybrid_innovation_scores.append({
                            "challenge": i + 1,
                            "innovation_score": 0,
                            "transcendence": False,
                            "error": str(e)
                        })
                
                # 计算该杂交后代的创新能力
                valid_scores = [s for s in hybrid_innovation_scores if "error" not in s]
                avg_innovation = sum(s["innovation_score"] for s in valid_scores) / len(valid_scores) if valid_scores else 0
                transcendence_count = sum(1 for s in valid_scores if s["transcendence"])
                
                innovation_tests.append({
                    "hybrid_name": hybrid_name,
                    "avg_innovation_score": avg_innovation,
                    "transcendence_count": transcendence_count,
                    "successful_challenges": len(valid_scores),
                    "total_challenges": len(innovation_challenges),
                    "innovation_emergence": avg_innovation > 0.6  # 高创新阈值
                })
                
                print(f"      📊 平均创新分数: {avg_innovation:.2f}")
                print(f"      🚀 超越性表现: {transcendence_count}/{len(innovation_challenges)}")
            
            # 计算整体创新涌现效果
            emergent_hybrids = sum(1 for test in innovation_tests if test.get("innovation_emergence", False))
            emergence_rate = emergent_hybrids / len(innovation_tests) if innovation_tests else 0
            
            # 计算平均创新水平
            avg_innovation_level = sum(test["avg_innovation_score"] for test in innovation_tests) / len(innovation_tests) if innovation_tests else 0
            
            # 计算总体超越性
            total_transcendence = sum(test["transcendence_count"] for test in innovation_tests)
            max_possible_transcendence = len(innovation_tests) * len(innovation_challenges)
            transcendence_rate = total_transcendence / max_possible_transcendence if max_possible_transcendence > 0 else 0
            
            print(f"   📊 创新涌现率: {emergence_rate*100:.1f}%")
            print(f"   🌟 平均创新水平: {avg_innovation_level:.2f}")
            print(f"   🚀 超越性率: {transcendence_rate*100:.1f}%")
            
            # 验证创新涌现效果
            expected_rate = self.test_config.success_criteria.get("innovation_emergence", 0.4)
            assert_success_rate(emergence_rate, expected_rate, "创新涌现验证")
            
            result.mark_success({
                "emergence_rate": emergence_rate,
                "avg_innovation_level": avg_innovation_level,
                "transcendence_rate": transcendence_rate,
                "emergent_hybrids": emergent_hybrids,
                "total_hybrids": len(innovation_tests)
            })
    
    def _assess_innovation_quality(self, response: str, innovation_indicators: list, complexity_level: str) -> float:
        """评估创新质量"""
        if not response:
            return 0.0
        
        innovation_score = 0.0
        
        # 检查创新指标词汇
        indicator_score = sum(0.1 for indicator in innovation_indicators if indicator in response)
        innovation_score += min(indicator_score, 0.4)
        
        # 检查内容丰富度
        if len(response) > 200:
            innovation_score += 0.2
        
        # 检查结构化思考
        if any(marker in response for marker in ["1.", "首先", "其次", "具体", "例如"]):
            innovation_score += 0.2
        
        # 根据复杂度级别调整
        if complexity_level == "high":
            # 高复杂度任务要求更高的创新性
            if len(response.split()) > 100:  # 足够详细
                innovation_score += 0.2
        elif complexity_level == "medium":
            if len(response.split()) > 50:
                innovation_score += 0.1
        
        return min(innovation_score, 1.0)
    
    async def _detect_transcendence(self, hybrid_life, response: str, task: str) -> bool:
        """检测是否超越了父代能力"""
        # 简化的超越性检测
        # 实际实现中可以对比父代在相同任务上的表现
        
        transcendence_indicators = [
            len(response) > 300,  # 详细程度
            "结合" in response or "融合" in response,  # 融合思维
            response.count("创新") > 1 or response.count("新") > 2,  # 创新词汇频率
            any(word in response for word in ["突破", "颠覆", "革命性", "前所未有"])  # 突破性表达
        ]
        
        return sum(transcendence_indicators) >= 2  # 至少满足2个超越指标


async def main():
    """主函数"""
    
    # 创建并运行Level 7测试
    level7_test = Level7HybridTest()
    
    try:
        success = await level7_test.run_all_tests()
        
        if success:
            print("\n🎉 Level 7 测试完全通过！")
            print("✅ 杂交生成能力验证成功")
            print("✅ FuturEmbryo v2.1c 全部测试完成！")
            return True
        else:
            print("\n❌ Level 7 测试未完全通过")
            print("🔧 请修复问题后重新测试")
            return False
            
    except Exception as e:
        print(f"\n💥 Level 7 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import time
    start_time = time.time()
    
    print("🌱 FuturEmbryo v2.1c 渐进式测试")
    print("🧬 Level 7: 杂交生成能力测试")
    print("=" * 60)
    
    success = asyncio.run(main())
    
    end_time = time.time()
    print(f"\n⏱️  总耗时: {end_time - start_time:.2f}秒")
    
    if success:
        print("🎉 Level 7 通过！FuturEmbryo v2.1c 测试套件全部完成！")
        print("🌟 数字生命体协作框架验证成功！")
        exit(0)
    else:
        print("❌ Level 7 失败，需要修复问题")
        exit(1)