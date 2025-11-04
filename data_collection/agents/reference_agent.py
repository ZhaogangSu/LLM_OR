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

from reference_agent import ReferenceAgent as KBReferenceAgent


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
    
    def __init__(self, config: Dict[str, Any]):
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
            translation_guide=kb_config.get('translation_guide')
        )
        
        self.condensed_mode = config.get('pipeline', {}).get('condensed_references', True)
        print(f"✓ ReferenceAgent wrapper initialized (condensed={self.condensed_mode})")
    
    def get_modeling_references(self, problem: str) -> str:
        """
        Get references for mathematical modeling
        
        Args:
            problem: Problem description
            
        Returns:
            str: Formatted references (Gurobi examples)
        """
        return self.kb_agent.get_modeling_references(
            problem, 
            condensed=self.condensed_mode  # Pass through
        )
    
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