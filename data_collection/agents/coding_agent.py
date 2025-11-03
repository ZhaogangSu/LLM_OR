"""
Coding Agent: Generates executable COPT Python code from mathematical models.

Responsibilities:
- Translate mathematical formulation to COPT code
- Use correct COPT API syntax
- Generate complete, runnable code
- Ensure proper output format for answer extraction
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from core.llm_client import LLMClientPool
from core.code_executor import extract_python_code


class CodingAgent(BaseAgent):
    """
    Code generation agent
    
    Converts mathematical models into executable COPT Python code
    with proper syntax, imports, and output format.
    """
    
    def __init__(self, llm_client: LLMClientPool, config: Dict[str, Any]):
        """
        Initialize coding agent
        
        Args:
            llm_client: LLM client pool
            config: Configuration dictionary
        """
        super().__init__(llm_client, config)
        print(f"✓ {self.agent_name} initialized")
    
    def execute(self, problem: str, math_model: str, reference: str = "") -> str:
        """
        Generate COPT Python code from mathematical model
        
        Args:
            problem: Original problem description
            math_model: Mathematical formulation
            reference: COPT API documentation reference
            
        Returns:
            str: Executable Python code using COPT
            
        Example:
            >>> code = agent.execute(
            ...     problem="Minimize cost...",
            ...     math_model="Variables: x[i]...",
            ...     reference="COPT API docs..."
            ... )
            >>> print(code[:100])
            import coptpy as cp
            from coptpy import COPT
            ...
        """
        print(f"  [{self.agent_name}] Generating COPT Python code...")
        
        # Load prompts
        system_prompt = self._load_prompt('coding_agent_system')
        user_prompt = self._format_prompt(
            'coding_agent_user',
            problem=problem,
            math_model=math_model,
            reference=reference if reference else "No API reference provided."
        )
        
        # Call LLM
        raw_response = self._call_llm(system_prompt, user_prompt)
        
        # Extract Python code from response
        code = extract_python_code(raw_response)
        
        print(f"  [{self.agent_name}] ✓ Code generated ({len(code)} chars)")
        
        # Basic validation
        if not self._validate_code(code):
            print(f"  [{self.agent_name}] ⚠️  Warning: Generated code may be incomplete")
        
        return code
    
    def _validate_code(self, code: str) -> bool:
        """
        Basic validation of generated code
        
        Args:
            code: Python code string
            
        Returns:
            bool: True if code appears valid
        """
        required_elements = [
            'import coptpy',
            'COPT',
            'model',
            'solve()'
        ]
        
        code_lower = code.lower()
        
        for element in required_elements:
            if element.lower() not in code_lower:
                print(f"  ⚠️  Missing: {element}")
                return False
        
        return True
    
    def format_code(self, code: str) -> str:
        """
        Format code for better readability (optional)
        
        Args:
            code: Python code
            
        Returns:
            str: Formatted code
        """
        # Basic formatting - remove extra blank lines
        lines = code.split('\n')
        formatted_lines = []
        prev_blank = False
        
        for line in lines:
            if line.strip():
                formatted_lines.append(line)
                prev_blank = False
            elif not prev_blank:
                formatted_lines.append(line)
                prev_blank = True
        
        return '\n'.join(formatted_lines)


# Test
if __name__ == "__main__":
    from config.config_loader import get_config
    from core.llm_client import create_llm_client
    
    print("=== Coding Agent Test ===\n")
    
    # Initialize
    config = get_config()
    llm = create_llm_client(config)
    agent = CodingAgent(llm, config._config)
    
    # Test inputs
    test_problem = "Maximize profit with resource constraints"
    test_model = """
    Decision Variables:
    x1, x2 = amount of products 1 and 2
    
    Objective:
    maximize 30*x1 + 40*x2
    
    Constraints:
    2*x1 + 3*x2 <= 100 (labor hours)
    x1, x2 >= 0
    """
    
    # Execute
    try:
        code = agent.execute(
            problem=test_problem,
            math_model=test_model,
            reference=""
        )
        print("\n--- Generated Code (first 500 chars) ---")
        print(code[:500] + "..." if len(code) > 500 else code)
        print("\n✓ Coding Agent test passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
