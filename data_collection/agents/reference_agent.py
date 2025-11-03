"""
Reference Agent: Retrieves relevant knowledge for modeling and coding.

This is a wrapper around the knowledge base retrievers.
The actual retrievers remain in knowledge_base/retrievers/.
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
    Wrapper for knowledge base reference agent
    
    Provides clean interface for retrieving:
    - Gurobi modeling examples
    - COPT API documentation
    - Gurobi→COPT translation guides
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize reference agent
        
        Args:
            config: Configuration dictionary with knowledge_base paths
        """
        kb_config = config.get('knowledge_base', {})
        
        self.kb_agent = KBReferenceAgent(
            copt_kb_dir=kb_config.get('copt_kb_dir'),
            gurobi_index=kb_config.get('gurobi_index')
        )
        
        print("✓ ReferenceAgent initialized")
    
    def get_modeling_references(self, problem: str) -> str:
        """
        Get references for mathematical modeling
        
        Args:
            problem: Problem description
            
        Returns:
            str: Formatted references (Gurobi examples + COPT docs)
        """
        return self.kb_agent.get_modeling_references(problem)
    
    def get_coding_references(self, math_model: str) -> str:
        """
        Get references for code generation
        
        Args:
            math_model: Mathematical formulation
            
        Returns:
            str: Formatted references (COPT docs + translation guide)
        """
        return self.kb_agent.get_coding_references(math_model)


# Test
if __name__ == "__main__":
    from config.config_loader import get_config
    
    print("=== Reference Agent Test ===\n")
    
    config = get_config()
    agent = ReferenceAgent(config._config)
    
    test_problem = "production planning with capacity constraints"
    
    print("Testing modeling references...")
    modeling_ref = agent.get_modeling_references(test_problem)
    print(f"✓ Got {len(modeling_ref)} chars of modeling references")
    
    test_model = "Variables: x[i], Objective: minimize cost, Constraints: capacity"
    
    print("\nTesting coding references...")
    coding_ref = agent.get_coding_references(test_model)
    print(f"✓ Got {len(coding_ref)} chars of coding references")
    
    print("\n✓ Reference Agent test passed!")
