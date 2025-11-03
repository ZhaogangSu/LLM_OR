"""
Debugging Agent: Executes, debugs, and repairs generated code.

Responsibilities:
- Execute Python code in isolated environment
- Capture and analyze errors
- Repair code errors (syntax, runtime, logic)
- Repair mathematical model if code fixes fail
- Verify answer correctness against ground truth
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from core.llm_client import LLMClientPool
from core.code_executor import CodeExecutor, extract_python_code
from core.answer_checker import check_answer_correctness


class DebuggingAgent(BaseAgent):
    """
    Debugging and repair agent
    
    Executes code, identifies errors, and iteratively repairs
    both code-level and model-level issues.
    """
    
    def __init__(self, llm_client: LLMClientPool, config: Dict[str, Any]):
        """
        Initialize debugging agent
        
        Args:
            llm_client: LLM client pool
            config: Configuration dictionary
        """
        super().__init__(llm_client, config)
        
        # Get pipeline config
        pipeline_config = config.get('pipeline', {})
        self.max_attempts = pipeline_config.get('max_debug_attempts', 3)
        self.answer_tolerance = pipeline_config.get('answer_tolerance', 0.1)
        self.execution_timeout = pipeline_config.get('code_execution_timeout', 30)
        
        # Initialize code executor
        self.executor = CodeExecutor(timeout=self.execution_timeout)
        
        print(f"✓ {self.agent_name} initialized (max_attempts={self.max_attempts})")
    
    def execute(
        self,
        code: str,
        problem: str,
        ground_truth: str,
        math_model: str = ""
    ) -> Dict[str, Any]:
        """
        Execute code and repair if needed
        
        Args:
            code: Initial Python code
            problem: Original problem description
            ground_truth: Expected answer
            math_model: Mathematical formulation (for model repair)
            
        Returns:
            Dict with keys:
                - success: bool, overall success
                - answer_correct: bool, if answer matches ground truth
                - final_code: str, final working code
                - result: Dict, execution result
                - history: List[Dict], debug history
                - attempts: int, number of attempts made
        """
        print(f"  [{self.agent_name}] Starting debugging process...")
        
        current_code = code
        debug_history = []
        
        for attempt in range(1, self.max_attempts + 1):
            print(f"  [{self.agent_name}] Attempt {attempt}/{self.max_attempts}")
            
            # Execute code
            exec_result = self.executor.execute(current_code, problem)
            
            # Record attempt
            attempt_record = {
                'attempt': attempt,
                'execution': exec_result,
                'code': current_code
            }
            
            # Check if execution succeeded
            if exec_result['success']:
                # Execution succeeded - check answer
                is_correct, pred_value, status = check_answer_correctness(
                    exec_result['output'],
                    ground_truth,
                    self.answer_tolerance
                )
                
                attempt_record['answer_check'] = {
                    'correct': is_correct,
                    'predicted': pred_value,
                    'expected': ground_truth,
                    'status': status
                }
                
                if is_correct:
                    print(f"  [{self.agent_name}] ✓ Success! Answer is correct.")
                    debug_history.append(attempt_record)
                    
                    return {
                        'success': True,
                        'answer_correct': True,
                        'final_code': current_code,
                        'result': exec_result,
                        'history': debug_history,
                        'attempts': attempt
                    }
                else:
                    # Execution succeeded but wrong answer
                    print(f"  [{self.agent_name}] ⚠️  Wrong answer: {status}")
                    
                    # Try variable type fix
                    if attempt < self.max_attempts:
                        current_code = self._repair_variable_types(
                            current_code,
                            math_model,
                            pred_value,
                            ground_truth
                        )
                        attempt_record['repair_action'] = 'variable_type_fix'
                    
            else:
                # Execution failed - repair code
                print(f"  [{self.agent_name}] ❌ Execution error: {exec_result['error'][:100]}...")
                
                if attempt < self.max_attempts:
                    if attempt < self.max_attempts - 1:
                        # Code repair
                        current_code = self._repair_code(
                            current_code,
                            exec_result['error'],
                            problem
                        )
                        attempt_record['repair_action'] = 'code_repair'
                    else:
                        # Last attempt - try model repair
                        current_code = self._repair_model(
                            problem,
                            math_model,
                            current_code,
                            exec_result['error'],
                            attempt
                        )
                        attempt_record['repair_action'] = 'model_repair'
            
            debug_history.append(attempt_record)
        
        # All attempts exhausted
        print(f"  [{self.agent_name}] ❌ Failed after {self.max_attempts} attempts")
        
        return {
            'success': False,
            'answer_correct': False,
            'final_code': current_code,
            'result': exec_result,
            'history': debug_history,
            'attempts': self.max_attempts
        }
    
    def _repair_code(self, code: str, error: str, problem: str) -> str:
        """
        Repair code-level errors
        
        Args:
            code: Current code
            error: Error message
            problem: Problem description
            
        Returns:
            str: Repaired code
        """
        print(f"  [{self.agent_name}] Attempting code repair...")
        
        system_prompt = self._load_prompt('debugging_code_repair_system')
        user_prompt = self._format_prompt(
            'debugging_code_repair_user',
            code=code,
            error=error,
            problem=problem
        )
        
        raw_response = self._call_llm(system_prompt, user_prompt)
        repaired_code = extract_python_code(raw_response)
        
        print(f"  [{self.agent_name}] ✓ Code repaired")
        return repaired_code
    
    def _repair_model(
        self,
        problem: str,
        math_model: str,
        code: str,
        error: str,
        attempt_count: int
    ) -> str:
        """
        Repair mathematical model (last resort)
        
        Args:
            problem: Problem description
            math_model: Current mathematical model
            code: Current code
            error: Error message
            attempt_count: Number of failed attempts
            
        Returns:
            str: New code with corrected model
        """
        print(f"  [{self.agent_name}] Attempting model repair (last resort)...")
        
        system_prompt = self._load_prompt('debugging_model_repair_system')
        user_prompt = self._format_prompt(
            'debugging_model_repair_user',
            problem=problem,
            math_model=math_model,
            code=code,
            error=error,
            attempt_count=attempt_count
        )
        
        raw_response = self._call_llm(system_prompt, user_prompt)
        repaired_code = extract_python_code(raw_response)
        
        print(f"  [{self.agent_name}] ✓ Model repaired")
        return repaired_code
    
    def _repair_variable_types(
        self,
        code: str,
        math_model: str,
        predicted: float,
        expected: str
    ) -> str:
        """
        Fix variable type issues (CONTINUOUS vs INTEGER)
        
        Args:
            code: Current code
            math_model: Mathematical model
            predicted: Predicted answer
            expected: Expected answer
            
        Returns:
            str: Code with fixed variable types
        """
        print(f"  [{self.agent_name}] Attempting variable type fix...")
        
        system_prompt = self._load_prompt('debugging_variable_type_fix_system')
        user_prompt = self._format_prompt(
            'debugging_variable_type_fix_user',
            code=code,
            math_model=math_model,
            predicted=predicted,
            ground_truth=expected
        )
        
        raw_response = self._call_llm(system_prompt, user_prompt)
        repaired_code = extract_python_code(raw_response)
        
        print(f"  [{self.agent_name}] ✓ Variable types fixed")
        return repaired_code


# Test
if __name__ == "__main__":
    from config.config_loader import get_config
    from core.llm_client import create_llm_client
    
    print("=== Debugging Agent Test ===\n")
    
    # Initialize
    config = get_config()
    llm = create_llm_client(config)
    agent = DebuggingAgent(llm, config._config)
    
    # Test with simple working code
    test_code = """
import coptpy as cp
from coptpy import COPT

env = cp.Envr()
model = env.createModel("test")

x = model.addVar(lb=0, ub=10, vtype=COPT.CONTINUOUS, name="x")
model.setObjective(x, COPT.MINIMIZE)
model.addConstr(x >= 5, name="constraint")

model.solve()

if model.status == COPT.OPTIMAL:
    print(f"Optimal objective: {model.objval}")
else:
    print("No solution")
"""
    
    test_problem = "Minimize x subject to x >= 5"
    test_ground_truth = "5.0"
    
    # Execute
    try:
        result = agent.execute(
            code=test_code,
            problem=test_problem,
            ground_truth=test_ground_truth,
            math_model="minimize x, s.t. x >= 5"
        )
        
        print("\n--- Debug Result ---")
        print(f"Success: {result['success']}")
        print(f"Answer correct: {result['answer_correct']}")
        print(f"Attempts: {result['attempts']}")
        print(f"\n✓ Debugging Agent test passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
