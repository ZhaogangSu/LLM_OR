"""
Code execution utility for running generated Python code safely.
Executes code in isolated subprocess with timeout and error capture.
"""

import subprocess
import tempfile
import os
from typing import Dict


class CodeExecutor:
    """Execute Python code in isolated environment"""

    def __init__(self, timeout: int = 30):
        """
        Initialize code executor

        Args:
            timeout: Maximum execution time in seconds
        """
        self.timeout = timeout

    def execute(self, code: str, problem: str = "") -> Dict:
        """
        Execute Python code and capture results

        Args:
            code: Python code to execute
            problem: Problem description (for context in errors)

        Returns:
            Dict with keys:
                - success: bool, whether execution succeeded
                - output: str, stdout from execution
                - error: str, error message if failed
                - execution_time: float, time taken in seconds
        """
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Execute code in subprocess
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # Check if execution succeeded
            if result.returncode == 0:
                return {
                    'success': True,
                    'output': result.stdout,
                    'error': '',
                    'returncode': 0
                }
            else:
                # Execution failed - return error
                error_msg = result.stderr or result.stdout
                return {
                    'success': False,
                    'output': result.stdout,
                    'error': self._clean_error_message(error_msg, temp_file),
                    'returncode': result.returncode
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': f'Code execution timeout after {self.timeout} seconds',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'Execution error: {str(e)}',
                'returncode': -2
            }
        finally:
            # Cleanup temp file
            try:
                os.unlink(temp_file)
            except:
                pass

    def _clean_error_message(self, error: str, temp_file: str) -> str:
        """
        Clean error message to remove temp file paths

        Args:
            error: Raw error message
            temp_file: Temp file path to remove

        Returns:
            Cleaned error message
        """
        # Replace temp file path with generic name
        cleaned = error.replace(temp_file, 'code.py')

        # Keep only relevant parts of traceback
        lines = cleaned.split('\n')
        relevant_lines = []

        for line in lines:
            # Skip lines with temp directory paths
            if '/tmp/' in line or 'Traceback' in line:
                continue
            if line.strip():
                relevant_lines.append(line)

        return '\n'.join(relevant_lines)


def extract_python_code(text: str) -> str:
    """
    Extract Python code from markdown code blocks or raw text

    Args:
        text: Text potentially containing Python code

    Returns:
        str: Extracted Python code
    """
    import re

    # Try to extract from markdown code block
    pattern = r'```python\s*(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        # Return the first Python code block
        return matches[0].strip()

    # Try without language specifier
    pattern = r'```\s*(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        # Check if it looks like Python code
        code = matches[0].strip()
        if 'import' in code or 'def ' in code or 'model' in code:
            return code

    # If no code blocks, assume entire text is code
    return text.strip()


# Test
if __name__ == "__main__":
    executor = CodeExecutor(timeout=5)

    # Test 1: Successful execution
    code1 = """
import coptpy as cp
from coptpy import COPT

env = cp.Envr()
model = env.createModel("test")

x = model.addVar(lb=0, ub=10, vtype=COPT.CONTINUOUS, name="x")
model.setObjective(x, COPT.MINIMIZE)
model.addConstr(x >= 5, name="min_constraint")

model.solve()

if model.status == COPT.OPTIMAL:
    print(f"Optimal objective: {model.objval}")
else:
    print("No solution")
"""

    print("Test 1: Valid code")
    result = executor.execute(code1)
    print(f"Success: {result['success']}")
    print(f"Output: {result['output']}")

    # Test 2: Code with error
    code2 = """
print("Starting...")
x = 1 / 0  # This will cause error
print("This won't print")
"""

    print("\nTest 2: Code with error")
    result = executor.execute(code2)
    print(f"Success: {result['success']}")
    print(f"Error: {result['error']}")

    # Test 3: Extract code from markdown
    markdown_code = """
Here's the solution:

```python
print("Hello from markdown!")
x = 42
print(f"Answer: {x}")
```

That's the code.
"""

    print("\nTest 3: Extract from markdown")
    extracted = extract_python_code(markdown_code)
    print(f"Extracted code:\n{extracted}")
