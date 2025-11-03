# multi_agent_collector.py
import json
import os
from typing import Dict, List
from openai import OpenAI
import time
from knowledge_base.retrievers.reference_agent import ReferenceAgent
import traceback
import re


def extract_python_code(text: str) -> str:
    """
    Extract Python code from markdown code blocks
    
    Args:
        text: Text potentially containing ```python ... ``` blocks
    
    Returns:
        Clean Python code without markdown formatting
    """
    # Pattern to match ```python...``` or ```...```
    pattern = r'```(?:python)?\s*\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        # Return the first code block found
        return matches[0].strip()
    else:
        # If no code blocks found, return original text
        # (might already be clean code)
        return text.strip()


def check_answer_correctness(execution_output: str, ground_truth: str, tolerance: float = 0.1) -> bool:
    """
    Check if the solution matches ground truth
    """
    import re
    
    # Skip if no ground truth
    if not ground_truth or ground_truth == "" or ground_truth == "No Best Solution":
        return True
    
    # Try to parse ground truth
    try:
        gt_value = float(ground_truth)
    except:
        return True
    
    # Pattern with scientific notation support
    # Added many common print formats that LLMs might use
    patterns = [
        r'Optimal objective:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
        r'Objective:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
        r'objval:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
        r'Optimal [Cc]ost:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',       # ADD THIS
        r'Total [Cc]ost:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',         # ADD THIS
        r'Minimum [Cc]ost:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',       # ADD THIS
        r'Maximum [Pp]rofit:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
        r'Total [Pp]rofit:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
        r'Optimal [Pp]rofit:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',     # ADD THIS
        r'Best [Oo]bjective:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
        r'Optimal [Ss]olution:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',   # ADD THIS
        r'Best [Ss]olution:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',      # ADD THIS
    ]
    
    for pattern in patterns:
        match = re.search(pattern, execution_output, re.IGNORECASE)
        if match:
            try:
                pred_value = float(match.group(1))
                # Check if within tolerance
                error = abs(pred_value - gt_value)
                print(f"    📊 Answer check: predicted={pred_value}, expected={gt_value}, error={error:.6f}")
                
                if error <= tolerance:
                    return True
                else:
                    print(f"    ❌ Answer mismatch: {pred_value} != {gt_value} (tolerance={tolerance})")
                    return False
            except:
                pass
    
    # Cannot extract value
    print(f"    ⚠️  Could not extract objective value from output")
    return False


class MultiAgentCollector:
    """
    Multi-agent system for collecting OR problem-solving data
    Uses separate LLM calls for each agent with thinking process
    """
    
    def __init__(self, api_keys: List[str], kb_dir="copt_knowledge_base"):
        """
        Initialize with multiple API keys for parallel processing
        
        Args:
            api_keys: List of OpenAI-compatible API keys
            kb_dir: Path to COPT knowledge base
        """
        self.api_keys = api_keys
        self.current_key_idx = 0
        self.reference_agent = ReferenceAgent(kb_dir)
        print(f"✓ Multi-Agent Collector initialized with {len(api_keys)} API keys")
    
    def _get_next_client(self) -> OpenAI:
        """Round-robin through API keys"""
        client = OpenAI(
            api_key=self.api_keys[self.current_key_idx],
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"  # Qwen endpoint
        )
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        return client
    
    def _call_llm(self, system_prompt: str, user_prompt: str, 
                 model: str = "qwen-max", 
                  max_retries: int = 3) -> str:
        """
        Call LLM with retry logic
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            model: Model name
            max_retries: Maximum retry attempts
            
        Returns:
            LLM response text
        """
        for attempt in range(max_retries):
            try:
                client = self._get_next_client()
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )
                return str(response.choices[0].message.content)
            except Exception as e:
                print(f"⚠️  LLM call failed (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
    
    def collect_single_problem(self, problem: Dict) -> Dict:
        """
        Collect data for a single OR problem through multi-agent pipeline
        
        Args:
            problem: Dict with 'id', 'en_question', 'en_answer', etc.
            
        Returns:
            Complete data sample with all agent thinking processes
        """
        problem_id = problem.get('id', 'unknown')
        question = problem.get('en_question', problem.get('zh_question', ''))
        ground_truth = problem.get('en_answer', problem.get('zh_answer', ''))
        
        print(f"\n{'='*70}")
        print(f"Processing Problem ID: {problem_id}")
        print(f"{'='*70}")
        
        # Track all agent outputs
        agent_outputs = {
            'problem_id': problem_id,
            'original_problem': question,
            'ground_truth': ground_truth,
        }
        
        try:
            # Stage 1: Reference Agent for Modeling
            print("  [1/5] Reference Agent (Modeling)...")
            modeling_ref = self.reference_agent.get_modeling_references(question)
            agent_outputs['modeling_reference'] = modeling_ref
            
            # Stage 2: Modeling Agent
            print("  [2/5] Modeling Agent...")
            math_model = self._modeling_agent(question, modeling_ref)
            agent_outputs['math_model'] = math_model
            
            # Stage 3: Reference Agent for Coding
            print("  [3/5] Reference Agent (Coding)...")
            coding_ref = self.reference_agent.get_coding_references(math_model)
            agent_outputs['coding_reference'] = coding_ref
            
            # Stage 4: Coding Agent
            print("  [4/5] Coding Agent...")
            initial_code = self._coding_agent(question, math_model, coding_ref)
            agent_outputs['initial_code'] = initial_code
            
            # Stage 5: Debugging Agent (with execution)
            print("  [5/5] Debugging Agent...")
            debug_results = self._debugging_agent(
                initial_code, 
                question,
                ground_truth,
                math_model
            )
            
            agent_outputs['debug_history'] = debug_results['history']
            agent_outputs['final_code'] = debug_results['final_code']
            agent_outputs['execution_result'] = debug_results['result']
            agent_outputs['success'] = debug_results['success']
            agent_outputs['answer_correct'] = debug_results.get('answer_correct', False)  # Add this            

            print(f"✓ Problem {problem_id} completed: {'SUCCESS' if debug_results['success'] else 'FAILED'}")
            
        except Exception as e:
            print(f"❌ Error processing problem {problem_id}: {e}")
            print(traceback.format_exc())
            agent_outputs['error'] = str(e)
            agent_outputs['success'] = False
        
        return agent_outputs

    def _modeling_agent(self, problem: str, modeling_reference: str) -> str:
        """Modeling agent generates mathematical formulation"""
        system_prompt = """You are an expert in Operations Research mathematical modeling.

    **CRITICAL: Variable Type Rules**

    Use INTEGER variables when:
    - ✅ "servings of food" → INTEGER (cannot serve 0.37 portions in practice)
    - ✅ "number of workers" → INTEGER (cannot hire 2.5 people)
    - ✅ "machines to purchase" → INTEGER (cannot buy 1.3 machines)
    - ✅ "projects to select" → BINARY (yes/no decision)

    Use CONTINUOUS variables when:
    - ✅ "kilograms of material" → CONTINUOUS (can use 2.7 kg)
    - ✅ "liters of liquid" → CONTINUOUS (can use 3.14 liters)
    - ✅ "hours of work" → CONTINUOUS (can work 4.5 hours)

    **Default Rule**: When problem mentions "servings", "units", "items" → Use INTEGER unless explicitly stated otherwise.

    **Example 1: Diet Problem**
    Problem: "Choose servings of Steak, Chicken, Rice..."
    Variable Type: INTEGER (whole servings)
    Reasoning: In meal planning, fractional servings are impractical

    **Example 2: Blending Problem**  
    Problem: "Mix x liters of solution A with y liters of solution B..."
    Variable Type: CONTINUOUS (liquids are divisible)
    Reasoning: Can mix any fractional amount

    Output your mathematical model with explicit variable types."""

        user_prompt = f"""## Problem
    {problem}

    ## Modeling Guidance
    {modeling_reference}

    ## Task
    1. **Analyze variable types carefully**: For each variable, state:
    - What it represents
    - Why it should be INTEGER or CONTINUOUS
    - Check against the rules above

    2. Build complete mathematical model:
    - Decision variables with EXPLICIT types
    - Objective function
    - Constraints

    **IMPORTANT**: If problem mentions "servings", "units", or "how many", default to INTEGER unless you have strong reason not to."""

        return self._call_llm(system_prompt, user_prompt)

    def _coding_agent(self, problem: str, math_model: str, reference: str) -> str:
        """Code generation agent"""
        system_prompt = """You are an expert in COPT Python programming for solving optimization problems.

    Your task: Given a mathematical model and COPT documentation, generate executable Python code.

    Requirements:
    - Use COPT Python API (import coptpy as cp, from coptpy import COPT)
    - Create environment: env = cp.Envr()
    - Create model: model = env.createModel("problem_name")
    - Define variables with model.addVar() or model.addVars()
    - Use vtype = COPT.BINARY, COPT.INTEGER, or COPT.CONTINUOUS
    - Add constraints with model.addConstr() or model.addConstrs()
    - Set objective with model.setObjective(expr, COPT.MINIMIZE or COPT.MAXIMIZE)
    - Solve with model.solve()
    - Print results:
    
    **CRITICAL OUTPUT FORMAT:**
    The code MUST print the objective value in this EXACT format:
    if model.status == COPT.OPTIMAL:
        print(f"Optimal objective: {model.objval}")
        # Optional: print variable values
    else:
        print("No optimal solution found")

    **IMPORTANT**: 
    - Always use "Optimal objective:" (not "Optimal Cost" or "Total Profit")
    - This ensures consistent answer verification
    - Use lowercase `model.objval` (not `model.ObjVal`)

    Output ONLY Python code, no markdown fences, no explanations."""


        user_prompt = f"""
    ## Original Problem
    {problem}

    ## Mathematical Model
    {math_model}

    ## COPT Python API Reference
    {reference}

    Generate the complete COPT Python code to solve this problem.
    """

        raw_code = self._call_llm(system_prompt, user_prompt)
        return extract_python_code(raw_code)

    def _debugging_agent(self, code: str, problem: str, ground_truth: str, math_model: str, max_attempts: int = 3) -> Dict:       
        """
        Debugging agent with code execution, answer verification, and iterative fixing
        
        Args:
            code: Initial code
            problem: Problem description
            ground_truth: Expected answer for verification
            max_attempts: Maximum debug attempts
        
        Returns:
            Dict with 'history', 'final_code', 'result', 'success', 'answer_correct'
        """
        debug_history = []
        current_code = code
        
        for attempt in range(max_attempts):
            print(f"    Attempt {attempt+1}/{max_attempts}: Executing code...")
            
            # Execute code
            exec_result = self._execute_code(current_code, problem)
            
            # Check answer correctness if execution succeeded
            answer_correct = False
            if exec_result['success']:
                answer_correct = check_answer_correctness(
                    exec_result['output'], 
                    ground_truth
                )
                
                if answer_correct:
                    print(f"    ✓ Code executed successfully and answer is CORRECT!")
                else:
                    print(f"    ⚠️  Code executed but answer is INCORRECT (expected: {ground_truth})")
                    # Treat incorrect answer as a failure
                    exec_result['success'] = False
                    exec_result['error'] = f"Answer verification failed. Expected: {ground_truth}"
            
            debug_history.append({
                'attempt': attempt + 1,
                'code': current_code,
                'execution': exec_result,
                'answer_correct': answer_correct
            })
            
            # Check if successful AND correct
            if exec_result['success'] and answer_correct:
                return {
                    'history': debug_history,
                    'final_code': current_code,
                    'result': exec_result['output'],
                    'success': True,
                    'answer_correct': True
                }
            
            # If failed and not last attempt, try to fix
            if attempt < max_attempts - 1:
                print(f"    ⚠️  Attempting to fix...")
                # Check if this is a variable type issue
                if 'Answer verification failed' in exec_result.get('error', ''):
                    # First attempt: fix with variable type consideration
                    if attempt == 0:
                        current_code = self._fix_with_variable_type_check(
                            current_code, 
                            exec_result['error'],
                            ground_truth,
                            math_model  # Pass math model for context
                        )
                    else:
                        current_code = self._fix_code_with_answer(
                            current_code, 
                            exec_result['error'],
                            ground_truth
                        )
                else:
                    current_code = self._fix_code(current_code, exec_result['error'])
        # All attempts failed
        print(f"    ❌ All {max_attempts} attempts failed")
        return {
            'history': debug_history,
            'final_code': current_code,
            'result': None,
            'success': False,
            'answer_correct': False
        }
    def _execute_code(self, code: str, problem: str) -> Dict:
        """
        Execute Python code in sandbox
        
        Returns:
            Dict with 'success', 'output', 'error'
        """
        import subprocess
        import tempfile
        
        try:
            # Write code to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute with timeout
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'output': result.stdout,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'output': result.stdout,
                    'error': result.stderr
                }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': None,
                'error': 'Execution timeout (30s)'
            }
        except Exception as e:
            return {
                'success': False,
                'output': None,
                'error': str(e)
            }
    
    def _fix_code(self, code: str, error: str) -> str:
        """Use LLM to fix buggy code"""
        system_prompt = """You are an expert debugger for COPT Python code.

Your task: Fix the buggy code based on the error message.

Common issues:
- Missing imports (import coptpy as cp, from coptpy import COPT)
- Wrong variable types (use COPT.BINARY, COPT.INTEGER, COPT.CONTINUOUS)
- Syntax errors in addConstr() or setObjective()
- Index errors in variable arrays

Output ONLY the corrected code, no explanations."""

        user_prompt = f"""## Buggy Code
```python
{code}
```

## Error Message
{error}

Fix the code to resolve this error."""

        raw_code = self._call_llm(system_prompt, user_prompt)
        return extract_python_code(raw_code)


# Around line 250, update _fix_code_with_answer:

    def _fix_code_with_answer(self, code: str, error: str, ground_truth: str) -> str:
        """Use LLM to fix code when answer is incorrect"""
        system_prompt = """You are an expert debugger for COPT Python code.

    Your task: Fix the code because it's producing the wrong answer.

    The code runs without errors, but the objective value is incorrect. Common issues:
    - Wrong objective function (minimize vs maximize)
    - Missing or incorrect constraints
    - Wrong coefficients in objective or constraints
    - Logic errors in model formulation

    Output ONLY the complete Python code, no explanations, no markdown fences."""

        user_prompt = f"""## Current Code
    ```python
    {code}
    ```

    ## Issue
    {error}

    The expected answer is: {ground_truth}

    Fix the code to produce the correct answer. Output ONLY clean Python code."""

        raw_fix = self._call_llm(system_prompt, user_prompt)
        return extract_python_code(raw_fix)

    def _fix_with_variable_type_check(self, code: str, error: str, ground_truth: str, math_model: str) -> str:
        """Fix code by reconsidering variable types"""
        
        system_prompt = """You are a debugging expert for optimization problems.

    The code runs but produces wrong answer. Common cause: **Wrong variable type**.

    Check if variables should be INTEGER instead of CONTINUOUS:
    - Problem mentions "servings", "units", "items" → likely INTEGER
    - Current code uses CONTINUOUS → try changing to INTEGER
    - Sometimes fractional solutions (like 6.37 servings) indicate wrong variable type

    Fix strategy:
    1. Check if CONTINUOUS variables should be INTEGER
    2. Change `vtype=COPT.CONTINUOUS` to `vtype=COPT.INTEGER`
    3. Keep everything else the same

    Output ONLY the corrected code."""

        user_prompt = f"""## Current Code
    ```python
    {code}
    ```

    ## Mathematical Model
    {math_model}

    ## Problem
    Answer is incorrect: got something like 53.9 but expected {ground_truth}

    **Diagnosis**: Check if this is a variable type issue.
    - If code has fractional solution (e.g., 6.37 servings), variable type is likely wrong
    - Try changing CONTINUOUS to INTEGER

    Output the fixed code."""

        return self._call_llm(system_prompt, user_prompt)

    def format_as_training_sample(self, agent_outputs: Dict) -> Dict:
        """
        Format agent outputs into training data format with <think> tags
        
        Args:
            agent_outputs: Raw agent outputs
            
        Returns:
            Formatted training sample
        """
        # Build response with all thinking processes
        response_parts = []
        
        # Modeling reference thinking
        response_parts.append("<think by reference agent for modeling>")
        response_parts.append(agent_outputs.get('modeling_reference', ''))
        response_parts.append("</think>\n")
        
        # Modeling thinking
        response_parts.append("<think by modeling agent>")
        response_parts.append(agent_outputs.get('math_model', ''))
        response_parts.append("</think>\n")
        
        # Coding reference thinking
        response_parts.append("<think by reference agent for coding>")
        response_parts.append(agent_outputs.get('coding_reference', ''))
        response_parts.append("</think>\n")
        
        # Coding thinking
        response_parts.append("<think by coding agent>")
        response_parts.append(f"```python\n{agent_outputs.get('initial_code', '')}\n```")
        response_parts.append("</think>\n")
        
        # Debugging thinking (all attempts)
        for i, debug_step in enumerate(agent_outputs.get('debug_history', []), 1):
            response_parts.append(f"<think by debugging agent - attempt {i}>")
            
            if debug_step['execution']['success']:
                response_parts.append("Code execution successful!")
                response_parts.append(f"Output: {debug_step['execution']['output']}")
            else:
                response_parts.append(f"Execution error: {debug_step['execution']['error']}")
                if i < len(agent_outputs['debug_history']):
                    response_parts.append("Attempting to fix the code...")
            
            response_parts.append("</think>\n")
        
        # Final result
        if agent_outputs.get('success'):
            response_parts.append(f"<final_result>\n{agent_outputs['execution_result']}\n</final_result>")
        else:
            response_parts.append("<final_result>Failed to solve after maximum attempts</final_result>")
        
        return {
            'id': agent_outputs['problem_id'],
            'prompt': agent_outputs['original_problem'],
            'response': '\n'.join(response_parts),
            'ground_truth': agent_outputs['ground_truth'],
            'success': agent_outputs.get('success', False),
            'raw_outputs': agent_outputs  # Keep for debugging
        }


# Test with single problem
if __name__ == "__main__":
    # Load API keys
    with open("API_keys.txt", 'r') as f:
        api_keys = [line.strip() for line in f if line.strip()]
    
    print(f"Loaded {len(api_keys)} API keys")
    
    # Initialize collector
    collector = MultiAgentCollector(api_keys)
    
    # Test problem
    test_problem = {
        'id': 'test_001',
        'en_question': """
Imagine you are a dietitian and you have been tasked with creating a meal plan for a bodybuilder. You have six food items to choose from: Steak, Tofu, Chicken, Broccoli, Rice, and Spinach. Each food provides certain amounts of protein, carbohydrates, and calories, and each has its own cost.\n\nHere's the nutritional value and cost of each food:\n\n- Steak: It gives you 14 grams of protein, 23 grams of carbohydrates, and 63 calories for $4.\n- Tofu: It offers 2 grams of protein, 13 grams of carbohydrates, and 162 calories for $6.\n- Chicken: It packs a punch with 17 grams of protein, 13 grams of carbohydrates, and gives you 260 calories for $6.\n- Broccoli: It provides 3 grams of protein, a mere 1 gram of carbohydrates, and 55 calories for $8.\n- Rice: It gives a hearty 15 grams of protein, 23 grams of carbohydrates, and 231 calories for $8.\n- Spinach: It provides 2 grams of protein, 8 grams of carbohydrates, and a huge 297 calories for just $5.\n\nYour goal is to ensure that the bodybuilder gets at least 83 grams of protein, 192 grams of carbohydrates, and 2089 calories from whatever combination of these foods you choose. The challenge is to keep the cost as low as possible while meeting these nutritional targets. \n\nWhat is the minimum cost to meet these nutritional requirements with the available food options?
        """,
        'en_answer': '57'
    }
    
    # Collect data
    print("\nStarting data collection for test problem...")
    result = collector.collect_single_problem(test_problem)
    
    # Format as training sample
    training_sample = collector.format_as_training_sample(result)
    
    # Save result
    os.makedirs('test_output', exist_ok=True)
    with open('test_output/test_sample.json', 'w') as f:
        json.dump(training_sample, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*70)
    print("Test collection complete!")
    print(f"Success: {training_sample['success']}")
    print(f"Output saved to: test_output/test_sample.json")
    print("="*70)