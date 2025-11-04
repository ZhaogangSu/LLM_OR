"""
Data Formatter: Converts raw agent outputs into training data format.

Responsibilities:
- Format agent outputs with <think> tags
- Structure data for LLM training
- Add metadata (success, correctness, etc.)

Does NOT:
- Run agents (that's Collector's job)
- Save files (that's ParallelExecutor's job)
"""

from typing import Dict, Any


class DataFormatter:
    """
    Formats agent outputs into training data

    Training data format:
    {
        "problem": "...",
        "response": "<think>...</think>...",
        "success": true,
        "answer_correct": true,
        "metadata": {...}
    }
    """

    def format_training_sample(self, collector_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format collector output into training sample

        Args:
            collector_output: Raw output from DataCollector

        Returns:
            Formatted training sample with <think> tags
        """
        # Build response with thinking process
        response_parts = []

        # Stage 1: Modeling reference
        response_parts.append("<think_stage name='reference_modeling' agent='reference'>")
        response_parts.append(collector_output['stage1_modeling_reference'])
        response_parts.append("</think_stage>\n")

        # Stage 2: Mathematical modeling
        response_parts.append("<think_stage name='mathematical_modeling' agent='modeling'>")
        response_parts.append(collector_output['stage2_math_model'])
        response_parts.append("</think_stage>\n")

        # Stage 3: Coding reference
        response_parts.append("<think_stage name='reference_coding' agent='reference'>")
        response_parts.append(collector_output['stage3_coding_reference'])
        response_parts.append("</think_stage>\n")

        # Stage 4: Code generation
        response_parts.append("<think_stage name='code_generation' agent='coding'>")
        response_parts.append(f"```python\n{collector_output['stage4_initial_code']}\n```")
        response_parts.append("</think_stage>\n")

        # Stage 5: Debugging process
        debug_result = collector_output['stage5_debug_result']
        for i, attempt in enumerate(debug_result.get('history', []), 1):
            response_parts.append(f"<think_stage name='debugging' agent='debugging' attempt='{i}'>")

            # Execution result
            if attempt['execution']['success']:
                response_parts.append("✓ Code execution successful!")
            else:
                error_msg = str(attempt['execution'].get('error', 'Unknown error'))[:200]
                response_parts.append(f"✗ Execution failed: {error_msg}")

            # Answer check
            if 'answer_check' in attempt:
                answer_check = attempt['answer_check']
                if answer_check['correct']:
                    response_parts.append(f"\n✓ Answer verified: {answer_check['status']}")
                else:
                    response_parts.append(f"\n✗ Wrong answer: {answer_check['status']}")

            # Include LLM reasoning if available
            if attempt.get('reasoning'):
                response_parts.append("\n\n## Debugging Analysis\n")
                response_parts.append(str(attempt['reasoning']))

            # Show repaired code if available
            if attempt.get('repaired_code'):
                response_parts.append("\n\n## Repaired Code\n")
                response_parts.append(f"```python\n{attempt['repaired_code']}\n```")

            response_parts.append("</think_stage>\n")
        
        # Final answer
        response_parts.append("\n<final_code>")
        response_parts.append(f"```python\n{debug_result['final_code']}\n```")
        response_parts.append("</final_code>\n")

        if debug_result['success']:
            response_parts.append(f"\n<answer>{collector_output['ground_truth']}</answer>")

        # Combine response
        full_response = '\n'.join(response_parts)

        # Create training sample
        training_sample = {
            'problem_id': collector_output['problem_id'],
            'problem': collector_output['problem'],
            'response': full_response,
            'success': collector_output['success'],
            'answer_correct': collector_output['answer_correct'],
            'ground_truth': collector_output['ground_truth'],
            'metadata': {
                'modeling_ref_length': len(collector_output['stage1_modeling_reference']),
                'math_model_length': len(collector_output['stage2_math_model']),
                'coding_ref_length': len(collector_output['stage3_coding_reference']),
                'initial_code_length': len(collector_output['stage4_initial_code']),
                'debug_attempts': debug_result['attempts'],
                'final_code_length': len(debug_result['final_code'])
            }
        }

        return training_sample

    def format_simple_response(self, collector_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format simple response without detailed thinking tags

        Args:
            collector_output: Raw output from DataCollector

        Returns:
            Simplified format for baseline comparisons
        """
        debug_result = collector_output['stage5_debug_result']

        return {
            'problem_id': collector_output['problem_id'],
            'problem': collector_output['problem'],
            'math_model': collector_output['stage2_math_model'],
            'code': debug_result['final_code'],
            'success': collector_output['success'],
            'answer_correct': collector_output['answer_correct'],
            'ground_truth': collector_output['ground_truth']
        }


# Test
if __name__ == "__main__":
    print("=== Data Formatter Test ===\n")

    # Mock collector output
    mock_output = {
        'problem_id': 'test_001',
        'problem': 'Test problem',
        'ground_truth': '42',
        'stage1_modeling_reference': 'Reference for modeling...',
        'stage2_math_model': 'Variables: x, Objective: min x, Constraints: x >= 42',
        'stage3_coding_reference': 'COPT API reference...',
        'stage4_initial_code': 'import coptpy\n# code here',
        'stage5_debug_result': {
            'success': True,
            'answer_correct': True,
            'final_code': 'import coptpy\n# final code',
            'attempts': 1,
            'history': [{
                'attempt': 1,
                'execution': {'success': True, 'output': 'Optimal objective: 42'},
                'answer_check': {'correct': True, 'status': 'Correct'}
            }]
        },
        'success': True,
        'answer_correct': True
    }

    # Test formatting
    formatter = DataFormatter()

    print("Test 1: Training sample format")
    training_sample = formatter.format_training_sample(mock_output)
    print(f"  ✓ Problem ID: {training_sample['problem_id']}")
    print(f"  ✓ Response length: {len(training_sample['response'])} chars")
    print(f"  ✓ Success: {training_sample['success']}")
    print(f"  ✓ Metadata: {list(training_sample['metadata'].keys())}")

    print("\nTest 2: Simple format")
    simple = formatter.format_simple_response(mock_output)
    print(f"  ✓ Keys: {list(simple.keys())}")

    print("\n✓ Data Formatter test passed!")
