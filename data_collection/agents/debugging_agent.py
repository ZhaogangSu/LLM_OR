# agents/debugging_agent.py
"""
Debugging Agent: Executes, debugs, and repairs generated code.

UPDATED: Uses external prompt files for easier maintenance
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from core.llm_client import LLMClientPool
from core.code_executor import CodeExecutor, extract_python_code
from core.answer_checker import check_answer_correctness

def extract_reasoning_and_code(raw_response: str) -> Dict[str, str]:
    """Extract both reasoning and code from LLM response"""
    
    # Ensure raw_response is a string
    if not isinstance(raw_response, str):
        return {
            'reasoning': "Error: Invalid response type",
            'code': ""
        }
    
    # Extract code block
    try:
        code = extract_python_code(raw_response)
        if not isinstance(code, str):
            code = str(code) if code else ""
    except Exception as e:
        code = ""
    
    # Extract reasoning
    import re
    code_pattern = r'```python.*?```'
    match = re.search(code_pattern, raw_response, re.DOTALL)
    
    if match:
        reasoning = raw_response[:match.start()].strip()
    else:
        reasoning = raw_response.strip()
    
    if not reasoning:
        reasoning = "Applied automated repair."
    
    return {
        'reasoning': reasoning,
        'code': code
    }

class ErrorType:
    """Error type classification"""
    INCOMPLETE_CODE = "incomplete_code"
    SYNTAX_ERROR = "syntax_error"
    API_ERROR = "api_error"
    IMPORT_ERROR = "import_error"
    LOGIC_ERROR = "logic_error"
    VARIABLE_TYPE_ERROR = "variable_type"


class DebuggingAgent(BaseAgent):
    """
    Improved debugging and repair agent with smart error classification
    Uses external prompt files for easy maintenance
    """
    
    def __init__(self, llm_client: LLMClientPool, config: Dict[str, Any]):
        """Initialize debugging agent"""
        super().__init__(llm_client, config)
        
        # Get pipeline config
        pipeline_config = config.get('pipeline', {})
        self.max_attempts = pipeline_config.get('max_debug_attempts', 3)
        self.answer_tolerance = pipeline_config.get('answer_tolerance', 0.1)
        self.execution_timeout = pipeline_config.get('code_execution_timeout', 30)
        
        # Get knowledge base config for API reference
        self.kb_config = config.get('knowledge_base', {})
        
        # Initialize code executor
        self.executor = CodeExecutor(timeout=self.execution_timeout)
        
        print(f"✓ {self.agent_name} initialized (max_attempts={self.max_attempts})")
    
    def execute(
        self,
        code: str,
        problem: str,
        ground_truth: str,
        math_model: str = "",
        coding_reference: str = ""
    ) -> Dict[str, Any]:
        """Execute and debug code, capturing LLM reasoning"""
        
        print(f"  [{self.agent_name}] Starting debugging process...")
        
        current_code = code
        debug_history = []
        
        for attempt in range(1, self.max_attempts + 1):
            print(f"  [{self.agent_name}] Attempt {attempt}/{self.max_attempts}")
            
            # Execute code
            exec_result = self.executor.execute(current_code)
            # print(f"DEBUG: exec_result type = {type(exec_result)}")
            # print(f"DEBUG: exec_result = {exec_result}")
            
            # Create attempt record
            attempt_record = {
                'attempt': attempt,
                'execution': exec_result,
                'reasoning': None,  # ← NEW: Will store LLM reasoning
                'repaired_code': None  # ← NEW: Will store repaired code
            }
            
            if exec_result['success']:
                # Check answer
                answer_check = check_answer_correctness(
                    exec_result['output'],
                    ground_truth,
                    tolerance=self.answer_tolerance
                )
                # print(f"DEBUG: answer_check type = {type(answer_check)}")
                # print(f"DEBUG: answer_check = {answer_check}")
                attempt_record['answer_check'] = answer_check
                
                if answer_check['correct']:
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
                    # Wrong answer
                    print(f"  [{self.agent_name}] ⚠️  Wrong answer: {answer_check['status']}")
                    
                    if attempt < self.max_attempts:
                        pred_value = answer_check.get('predicted')
                        error_type = self._classify_error(
                            exec_result['output'],
                            f"Wrong answer: expected {ground_truth}, got {pred_value}",
                            current_code,
                            is_execution_error=False
                        )
                        
                        # Get repair with reasoning ← CHANGED
                        repair_result = self._smart_repair(
                            error_type=error_type,
                            code=current_code,
                            error=f"Wrong answer: expected {ground_truth}, got {pred_value}",
                            problem=problem,
                            math_model=math_model,
                            coding_reference=coding_reference,
                            predicted=pred_value,
                            expected=ground_truth
                        )
                        
                        # Validate repair_result
                        if not isinstance(repair_result, dict):
                            repair_result = {'reasoning': 'Repair error', 'code': current_code}

                        if 'code' not in repair_result:
                            repair_result['code'] = current_code
                        if 'reasoning' not in repair_result:
                            repair_result['reasoning'] = 'No reasoning available'
                        
                        # Store reasoning and code ← NEW
                        attempt_record['reasoning'] = repair_result['reasoning']
                        attempt_record['repaired_code'] = repair_result['code']
                        attempt_record['repair_action'] = f'smart_repair_{error_type}'
                        
                        # Update current code for next attempt
                        current_code = repair_result['code']
            else:
                # Execution failed
                print(f"  [{self.agent_name}] ❌ Execution error")
                
                if attempt < self.max_attempts:
                    error_type = self._classify_error(
                        exec_result['output'],
                        exec_result['error'],
                        current_code,
                        is_execution_error=True
                    )
                    
                    # Get repair with reasoning ← CHANGED
                    repair_result = self._smart_repair(
                        error_type=error_type,
                        code=current_code,
                        error=exec_result['error'],
                        problem=problem,
                        math_model=math_model,
                        coding_reference=coding_reference
                    )
                    
                    # Validate repair_result
                    if not isinstance(repair_result, dict):
                        repair_result = {'reasoning': 'Repair error', 'code': current_code}

                    if 'code' not in repair_result:
                        repair_result['code'] = current_code
                    if 'reasoning' not in repair_result:
                        repair_result['reasoning'] = 'No reasoning available'
                    
                    # Store reasoning and code ← NEW
                    attempt_record['reasoning'] = repair_result['reasoning']
                    attempt_record['repaired_code'] = repair_result['code']
                    attempt_record['repair_action'] = f'smart_repair_{error_type}'
                    
                    # Update current code
                    current_code = repair_result['code']
            
            debug_history.append(attempt_record)
        
        # All attempts failed
        return {
            'success': False,
            'answer_correct': False,
            'final_code': current_code,
            'result': exec_result,
            'history': debug_history,
            'attempts': self.max_attempts
        }

    def _classify_error(
        self,
        output: str,
        error: str,
        code: str,
        is_execution_error: bool
    ) -> str:
        """
        Classify the type of error to apply appropriate fix
        
        Returns:
            Error type from ErrorType class
        """
        error_lower = error.lower()
        code_lower = code.lower()
        
        # 1. Incomplete code (most common for short code)
        if len(code) < 200:
            return ErrorType.INCOMPLETE_CODE
        
        if 'name' in error_lower and 'is not defined' in error_lower:
            if 'model' in error_lower or 'env' in error_lower:
                return ErrorType.INCOMPLETE_CODE
        
        # 2. Import errors (wrong solver)
        if 'no module named' in error_lower:
            if 'pulp' in error_lower or 'gurobipy' in error_lower:
                return ErrorType.IMPORT_ERROR
            return ErrorType.IMPORT_ERROR
        
        # 3. COPT API errors
        if is_execution_error:
            if 'attributeerror' in error_lower:
                if 'env()' in code_lower or 'cp.env' in code_lower:
                    return ErrorType.API_ERROR
                if any(wrong_api in code_lower for wrong_api in [
                    '.optimize()', '.objval', 'grb.', 'gurobipy'
                ]):
                    return ErrorType.API_ERROR
        
        # 4. Syntax errors
        if 'syntaxerror' in error_lower or 'invalid syntax' in error_lower:
            return ErrorType.SYNTAX_ERROR
        
        # 5. Variable type error (wrong answer with fractional solution)
        if not is_execution_error:
            if 'could not extract' not in error_lower:
                return ErrorType.VARIABLE_TYPE_ERROR
        
        # 6. Default: logic error
        return ErrorType.LOGIC_ERROR
    
    def _repair_variable_types(
        self,
        code: str,
        math_model: str,
        predicted: float,
        expected: str
    ) -> Dict[str, str]:  # ← Changed return type
        """Fix variable type issues - returns reasoning + code"""
        system_prompt = self._load_prompt('debugging_variable_type_system')
        user_prompt = self._format_prompt(
            'debugging_variable_type_user',
            math_model=math_model,
            code=code,
            predicted=str(predicted) if predicted else "unknown",
            expected=expected
        )
        
        raw_response = self._call_llm(system_prompt, user_prompt)
        result = extract_reasoning_and_code(raw_response)  # ← NEW
        
        print(f"  [{self.agent_name}] ✓ Fixed variable types")
        return result  # ← Returns dict with reasoning + code
    
    def _repair_logic_error(
        self,
        code: str,
        error: str,
        problem: str,
        math_model: str
    ) -> Dict[str, str]:  # ← Changed return type
        """Repair logical errors - returns reasoning + code"""
        system_prompt = self._load_prompt('debugging_logic_error_system')
        user_prompt = self._format_prompt(
            'debugging_logic_error_user',
            problem=problem,
            math_model=math_model,
            code=code,
            error=error
        )
        
        raw_response = self._call_llm(system_prompt, user_prompt)
        result = extract_reasoning_and_code(raw_response)  # ← NEW
        
        print(f"  [{self.agent_name}] ✓ Fixed logic")
        return result
    
    def _repair_syntax_error(
        self,
        code: str,
        error: str
    ) -> Dict[str, str]:  # ← Changed return type
        """Repair syntax errors - returns reasoning + code"""
        system_prompt = self._load_prompt('debugging_syntax_error_system')
        user_prompt = self._format_prompt(
            'debugging_syntax_error_user',
            code=code,
            error=error
        )
        
        raw_response = self._call_llm(system_prompt, user_prompt)
        result = extract_reasoning_and_code(raw_response)
        
        print(f"  [{self.agent_name}] ✓ Fixed syntax")
        return result
    
    def _repair_api_error(
        self,
        code: str,
        error: str,
        coding_reference: str
    ) -> Dict[str, str]:  # ← Changed return type
        """Repair API errors - returns reasoning + code"""
        system_prompt = self._load_prompt('debugging_api_error_system')
        user_prompt = self._format_prompt(
            'debugging_api_error_user',
            coding_reference=coding_reference,
            code=code,
            error=error
        )
        
        raw_response = self._call_llm(system_prompt, user_prompt)
        result = extract_reasoning_and_code(raw_response)
        
        print(f"  [{self.agent_name}] ✓ Fixed API usage")
        return result
    
    def _repair_import_error(
        self,
        code: str,
        error: str,
        problem: str,
        math_model: str,
        coding_reference: str
    ) -> Dict[str, str]:  # ← Changed return type
        """Repair import errors - returns reasoning + code"""
        system_prompt = self._load_prompt('debugging_import_error_system')
        user_prompt = self._format_prompt(
            'debugging_import_error_user',
            problem=problem,
            math_model=math_model,
            coding_reference=coding_reference,
            code=code,
            error=error
        )
        
        raw_response = self._call_llm(system_prompt, user_prompt)
        result = extract_reasoning_and_code(raw_response)
        
        print(f"  [{self.agent_name}] ✓ Fixed imports")
        return result
    
    def _repair_incomplete_code(
        self,
        code: str,
        error: str,
        problem: str,
        math_model: str,
        coding_reference: str
    ) -> Dict[str, str]:  # ← Changed return type
        """Repair incomplete code - returns reasoning + code"""
        system_prompt = self._load_prompt('debugging_incomplete_code_system')
        user_prompt = self._format_prompt(
            'debugging_incomplete_code_user',
            problem=problem,
            math_model=math_model,
            coding_reference=coding_reference,
            code=code,
            error=error
        )
        
        raw_response = self._call_llm(system_prompt, user_prompt)
        # print(f"DEBUG: raw_response type = {type(raw_response)}")  # ADD THIS
        result = extract_reasoning_and_code(raw_response)
        # print(f"DEBUG: result type = {type(result)}, keys = {result.keys() if isinstance(result, dict) else 'NOT A DICT'}")  # ADD THIS
        
        print(f"  [{self.agent_name}] ✓ Generated complete code")
        return result

    def _smart_repair(
        self,
        error_type: str,
        code: str,
        error: str,
        problem: str = "",
        math_model: str = "",
        coding_reference: str = "",
        predicted: float = None,
        expected: str = ""
    ) -> Dict[str, str]:  # ← Changed return type
        """
        Apply appropriate repair based on error type
        
        Returns:
            Dict with 'reasoning' and 'code' keys
        """
        print(f"  [{self.agent_name}] Applying {error_type} repair strategy...")
        
        if error_type == ErrorType.INCOMPLETE_CODE:
            return self._repair_incomplete_code(code, error, problem, math_model, coding_reference)
        
        elif error_type == ErrorType.IMPORT_ERROR:
            return self._repair_import_error(code, error, problem, math_model, coding_reference)
        
        elif error_type == ErrorType.API_ERROR:
            return self._repair_api_error(code, error, coding_reference)
        
        elif error_type == ErrorType.SYNTAX_ERROR:
            return self._repair_syntax_error(code, error)
        
        elif error_type == ErrorType.VARIABLE_TYPE_ERROR:
            return self._repair_variable_types(code, math_model, predicted, expected)
        
        elif error_type == ErrorType.LOGIC_ERROR:
            return self._repair_logic_error(code, error, problem, math_model)
        
        else:
            # Fallback: return code unchanged with generic message
            return {
                'reasoning': f"Unknown error type: {error_type}. No repair applied.",
                'code': code
            }

# Test
if __name__ == "__main__":
    print("Debugging Agent with External Prompts")
    print("="*70)
    print("\nError Types:")
    for attr in dir(ErrorType):
        if not attr.startswith('_'):
            print(f"  - {getattr(ErrorType, attr)}")
    print("\nPrompt Files Required:")
    prompts = [
        'debugging_incomplete_code_system.txt',
        'debugging_incomplete_code_user.txt',
        'debugging_import_error_system.txt',
        'debugging_import_error_user.txt',
        'debugging_api_error_system.txt',
        'debugging_api_error_user.txt',
        'debugging_syntax_error_system.txt',
        'debugging_syntax_error_user.txt',
        'debugging_variable_type_system.txt',
        'debugging_variable_type_user.txt',
        'debugging_logic_error_system.txt',
        'debugging_logic_error_user.txt',
    ]
    for p in prompts:
        print(f"  - config/prompts/{p}")
    print("="*70)