# direct_qwen_baseline.py
"""
Direct Qwen-Max baseline - no multi-agent framework
Just prompt Qwen-Max to solve OR problems directly
"""

import json
import os
import argparse
from openai import OpenAI
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import tempfile
import re

def load_api_keys(api_file='../api_keys.txt'):
    """Load API keys from file"""
    with open(api_file, 'r') as f:
        keys = [line.strip() for line in f if line.strip()]
    print(f"✓ Loaded {len(keys)} API keys")
    return keys

def load_problems(input_file):
    """Load problems from JSONL"""
    problems = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            problems.append(json.loads(line))
    print(f"✓ Loaded {len(problems)} problems from {input_file}")
    return problems

class DirectQwenSolver:
    """Direct Qwen-Max solver without framework"""
    
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.current_key_idx = 0
    
    def _get_client(self):
        """Get OpenAI client with current API key"""
        key = self.api_keys[self.current_key_idx % len(self.api_keys)]
        self.current_key_idx += 1
        return OpenAI(
            api_key=key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    
    def _call_llm(self, system_prompt, user_prompt, max_tokens=16384):
        """Call Qwen-Max"""
        client = self._get_client()
        response = client.chat.completions.create(
            model="qwq-32b-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.5
        )
        return response.choices[0].message.content
    
    def _extract_python_code(self, text):
        """Extract Python code from markdown"""
        pattern = r'```python\s*(.*?)\s*```'
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[-1]  # Return last code block
        return text
    
    def _execute_code(self, code):
        """Execute Python code and capture output"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            os.unlink(temp_file)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'output': '', 'error': 'Timeout'}
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e)}
    
    def _check_answer(self, output, ground_truth, tolerance=0.1):
        """Check if answer is correct"""
        if not ground_truth:
            return True
        
        try:
            gt_value = float(ground_truth)
        except:
            return True
        
        # Extract objective value
        patterns = [
            r'Optimal objective:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
            r'Objective:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
            r'objval:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
            r'Optimal [Cc]ost:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
            r'Total [Cc]ost:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
            r'Minimum [Cc]ost:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
            r'Maximum [Pp]rofit:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
            r'Total [Pp]rofit:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
            r'Optimal [Pp]rofit:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
            r'Best [Oo]bjective:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
            r'Optimal [Ss]olution:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
            r'Best [Ss]olution:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                try:
                    pred_value = float(match.group(1))
                    error = abs(pred_value - gt_value)
                    return error <= tolerance
                except:
                    pass
        
        return False
    
    def solve_problem(self, problem):
        """Solve a single problem with direct prompting"""
        
        question = problem.get('en_question', problem.get('zh_question', ''))
        problem_id = problem.get('id', 'unknown')
        ground_truth = problem.get('en_answer', problem.get('zh_answer', ''))
        
        # Single comprehensive prompt
        system_prompt = """You are an expert in Operations Research optimization.

Your task: Solve the optimization problem by:
1. Understanding the problem
2. Formulating a mathematical model
3. Writing Python code using COPT to solve it

**CRITICAL REQUIREMENTS:**
- Use INTEGER variables for discrete items (servings, units, workers, machines)
- Use CONTINUOUS variables for divisible quantities (liters, kilograms, hours)
- Import: `import coptpy as cp` and `from coptpy import COPT`
- Create model: `env = cp.Envr(); model = env.createModel()`
- Solve: `model.solve()`
- Print result: `print(f"Optimal objective: {model.objval}")`

Output your complete solution including the Python code."""

        user_prompt = f"""## Problem
{question}

## Task
Solve this optimization problem:
1. Analyze and formulate the mathematical model
2. Write complete Python code using COPT
3. Make sure to print the optimal objective value

Provide your solution:"""

        try:
            # Get response
            response = self._call_llm(system_prompt, user_prompt)
            
            # Extract code
            code = self._extract_python_code(response)
            
            # Execute code
            exec_result = self._execute_code(code)
            
            # Check answer
            answer_correct = False
            if exec_result['success']:
                answer_correct = self._check_answer(exec_result['output'], ground_truth)
            
            return {
                'id': problem_id,
                'prompt': question,
                'response': response,
                'code': code,
                'execution': exec_result,
                'ground_truth': ground_truth,
                'success': exec_result['success'],
                'answer_correct': answer_correct
            }
        
        except Exception as e:
            return {
                'id': problem_id,
                'prompt': question,
                'response': None,
                'code': None,
                'execution': {'success': False, 'output': '', 'error': str(e)},
                'ground_truth': ground_truth,
                'success': False,
                'answer_correct': False
            }

def solve_wrapper(args):
    """Wrapper for parallel execution"""
    solver, problem = args
    try:
        return solver.solve_problem(problem)
    except Exception as e:
        print(f"Error solving problem {problem.get('id')}: {e}")
        return None

def main(args):
    # Load resources
    api_keys = load_api_keys(args.api_keys)
    problems = load_problems(args.input_file)
    
    # Limit problems if specified
    if args.max_problems:
        problems = problems[:args.max_problems]
        print(f"  Limited to {len(problems)} problems")
    
    # Initialize solver
    solver = DirectQwenSolver(api_keys)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"\nStarting direct Qwen-Max baseline with {args.num_workers} workers...")
    print("="*70)
    
    results = []
    
    # Prepare arguments
    solve_args = [(solver, problem) for problem in problems]
    
    # Parallel solving
    with ThreadPoolExecutor(max_workers=args.num_workers) as executor:
        futures = [executor.submit(solve_wrapper, arg) for arg in solve_args]
        
        for future in tqdm(as_completed(futures), total=len(problems), desc="Solving"):
            result = future.result()
            if result:
                results.append(result)
    
    # Save results
    output_file = os.path.join(args.output_dir, 'baseline_results.jsonl')
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    # Calculate statistics
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    correct = sum(1 for r in results if r['answer_correct'])
    
    stats = {
        'total_problems': total,
        'successful': successful,
        'failed': total - successful,
        'success_rate': successful / total if total > 0 else 0,
        'correct_answers': correct,
        'wrong_answers': successful - correct,
        'correctness_rate': correct / total if total > 0 else 0
    }
    
    stats_file = os.path.join(args.output_dir, 'baseline_stats.json')
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Print summary
    print("\n" + "="*70)
    print("BASELINE EXPERIMENT COMPLETE")
    print("="*70)
    print(f"Method: Direct Qwen-Max (No Framework)")
    print(f"Total problems: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success rate: {successful/total*100:.1f}%")
    print(f"")
    print(f"✓ Correct answers: {correct}")
    print(f"✗ Wrong answers: {successful - correct}")
    print(f"📊 Correctness rate: {correct/total*100:.1f}%")
    print(f"")
    print(f"Output saved to: {output_file}")
    print(f"Statistics saved to: {stats_file}")
    print("="*70)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', type=str, required=True)
    parser.add_argument('--output_dir', type=str, default='baseline_results/mamo_complex')
    parser.add_argument('--api_keys', type=str, default='../api_keys.txt')
    parser.add_argument('--num_workers', type=int, default=9)
    parser.add_argument('--max_problems', type=int, default=None)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    main(args)