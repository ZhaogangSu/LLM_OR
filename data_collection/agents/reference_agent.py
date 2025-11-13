# agents/reference_agent.py
"""
Reference Agent Wrapper - Simplified version

This wrapper provides a clean interface to the knowledge base reference agent.
Now only requires copt_api_json (no more copt_kb_dir).
"""

from typing import Dict, Any
import sys
from pathlib import Path

# Add knowledge_base to path
kb_path = Path(__file__).parent.parent / 'knowledge_base' / 'retrievers'
sys.path.insert(0, str(kb_path))

import re

from reference_agent import ReferenceAgent as KBReferenceAgent
# from core.llm_client import create_llm_client

class ReferenceAgent:
    """
    Wrapper for knowledge base reference agent (Simplified)
    
    Provides clean interface for retrieving:
    - Gurobi modeling examples
    - COPT API essentials (JSON only)
    - Gurobi→COPT translation guide (optional)
    
    Removed:
    - General COPT documentation (copt_kb_dir)
    - Complex document searching
    """
    
    def __init__(self, config: Dict[str, Any], llm=None):
        """
        Initialize reference agent
        
        Args:
            config: Configuration dictionary with knowledge_base paths
            
        Required config keys:
            - knowledge_base.gurobi_index
            - knowledge_base.copt_api_json
            
        Optional config keys:
            - knowledge_base.translation_guide
        """
        kb_config = config.get('knowledge_base', {})
        self.kb_agent = KBReferenceAgent(
            gurobi_index=kb_config['gurobi_index'],
            copt_api_json=kb_config['copt_api_json'],
            translation_guide=kb_config.get('translation_guide'),
            llm=llm
        )
        
        # 使用传入的 LLM client
        self.llm = llm  # ← 直接使用传入的
        
        self.condensed_mode = config.get('pipeline', {}).get('condensed_references', True)
        
        print(f"✓ ReferenceAgent wrapper initialized (condensed={self.condensed_mode})")

    def _generate_search_query(self, problem: str) -> str:
        """让LLM生成检索查询"""
        system_prompt = """You are a knowledge retrieval expert. Given an optimization problem, identify what modeling patterns to search for.

Output format:
Search keywords: [keyword1, keyword2, keyword3]
Reasoning: [why these keywords]"""
        
        user_prompt = f"""Problem: {problem[:500]}

What modeling patterns should I search for?"""
        
        response = self.llm.call(system_prompt, user_prompt)
        return response
    
    def get_modeling_references(self, problem: str) -> str:
        """获取建模参考（包含检索思考过程）"""
        
        # 1. LLM生成检索意图
        search_thinking = self._generate_search_query(problem)
        
        # 2. 从thinking里提取关键词（简单正则）
        keywords_match = re.search(r'Search keywords:\s*\[(.*?)\]', search_thinking)
        if keywords_match:
            keywords_str = keywords_match.group(1)
            # 用这些关键词搜索
            search_query = keywords_str
        else:
            # 备选：直接用problem
            search_query = problem
        
        # 3. 实际检索
        examples = self.gurobi_retriever.search(search_query, top_k=2)
        
        # 4. 格式化输出（包含检索思考）
        if self.condensed_mode:
            reference = "## Retrieval Process\n\n"
            reference += search_thinking + "\n\n"
            reference += "## Retrieved Patterns\n\n"
            reference += self.gurobi_retriever.format_for_prompt(examples, condensed=True)
        else:
            # 详细模式
            reference = "## Mathematical Modeling Guidance\n\n"
            reference += "### Retrieval Strategy\n"
            reference += search_thinking + "\n\n"
            reference += "### Retrieved Examples\n"
            reference += self.gurobi_retriever.format_for_prompt(examples)
        
        return reference

    def get_coding_references(self, math_model: str) -> str:
        """
        Get references for code generation
        
        Args:
            math_model: Mathematical formulation
            
        Returns:
            str: Formatted references (COPT API essentials)
        """
        return self.kb_agent.get_coding_references(
            math_model,
            condensed=self.condensed_mode  # Pass through
        )


# Test
if __name__ == "__main__":
    from config.config_loader import get_config
    
    print("=== Reference Agent Wrapper Test ===\n")
    
    # Load config
    config = get_config()
    
    # Initialize agent
    agent = ReferenceAgent(config._config)
    
    # Test problem
    test_problem = "production planning with capacity constraints"
    
    print("Testing modeling references...")
    modeling_ref = agent.get_modeling_references(test_problem)
    print(f"✓ Got {len(modeling_ref)} chars of modeling references\n")
    
    test_model = "Variables: x[i], Objective: minimize cost, Constraints: capacity"
    
    print("Testing coding references...")
    coding_ref = agent.get_coding_references(test_model)
    print(f"✓ Got {len(coding_ref)} chars of coding references\n")
    
    print("✓ Reference Agent wrapper test passed!")