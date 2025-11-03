"""
Modeling Agent: Converts natural language OR problems into mathematical formulations.

Responsibilities:
- Understand problem requirements
- Define decision variables
- Formulate objective function
- Specify constraints
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from core.llm_client import LLMClientPool


class ModelingAgent(BaseAgent):
    """
    Mathematical modeling agent
    
    Converts natural language OR problem descriptions into
    structured mathematical models with variables, objectives, and constraints.
    """
    
    def __init__(self, llm_client: LLMClientPool, config: Dict[str, Any]):
        """
        Initialize modeling agent
        
        Args:
            llm_client: LLM client pool
            config: Configuration dictionary
        """
        super().__init__(llm_client, config)
        print(f"✓ {self.agent_name} initialized")
    
    def execute(self, problem: str, reference: str = "") -> str:
        """
        Generate mathematical formulation for OR problem
        
        Args:
            problem: Natural language problem description
            reference: Optional reference examples from knowledge base
            
        Returns:
            str: Mathematical formulation with variables, objective, constraints
            
        Example:
            >>> model = agent.execute(
            ...     problem="Minimize cost of production with capacity constraints",
            ...     reference="Similar Gurobi examples..."
            ... )
            >>> print(model)
            Decision Variables:
            x[i] = amount produced at facility i
            
            Objective:
            minimize sum(cost[i] * x[i])
            
            Constraints:
            ...
        """
        print(f"  [{self.agent_name}] Generating mathematical formulation...")
        
        # Load prompts
        system_prompt = self._load_prompt('modeling_agent_system')
        user_prompt = self._format_prompt(
            'modeling_agent_user',
            problem=problem,
            reference=reference if reference else "No reference examples provided."
        )
        
        # Call LLM
        math_model = self._call_llm(system_prompt, user_prompt)
        
        print(f"  [{self.agent_name}] ✓ Mathematical formulation generated ({len(math_model)} chars)")
        
        return math_model
    
    def validate_formulation(self, formulation: str) -> bool:
        """
        Basic validation of mathematical formulation
        
        Args:
            formulation: Mathematical formulation text
            
        Returns:
            bool: True if formulation appears valid
        """
        required_sections = ['variable', 'objective', 'constraint']
        formulation_lower = formulation.lower()
        
        for section in required_sections:
            if section not in formulation_lower:
                print(f"  ⚠️  Warning: '{section}' not found in formulation")
                return False
        
        return True


# Test
if __name__ == "__main__":
    from config.config_loader import get_config
    from core.llm_client import create_llm_client
    
    print("=== Modeling Agent Test ===\n")
    
    # Initialize
    config = get_config()
    llm = create_llm_client(config)
    agent = ModelingAgent(llm, config._config)
    
    # Test problem
    test_problem = """
    A company produces two products A and B. 
    Product A requires 2 hours of labor and yields $30 profit.
    Product B requires 3 hours of labor and yields $40 profit.
    The company has 100 hours of labor available.
    Maximize total profit.
    """
    
    # Execute
    try:
        result = agent.execute(problem=test_problem, reference="")
        print("\n--- Generated Formulation ---")
        print(result[:500] + "..." if len(result) > 500 else result)
        print("\n✓ Modeling Agent test passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
