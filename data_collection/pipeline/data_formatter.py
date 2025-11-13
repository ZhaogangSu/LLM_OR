"""
Data Formatter: Converts raw agent outputs into training data format.
Updated to support function calling format with tool use.
"""

from typing import Dict, Any
import json


class DataFormatter:
    """
    Formats agent outputs into training data with tool calling support
    """

    def format_training_sample(self, collector_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format collector output into training sample with tool calling format
        
        Args:
            collector_output: Raw output from DataCollector
            
        Returns:
            Formatted training sample
        """
        # Load system prompt
        from config.prompt_loader import PromptLoader
        prompt_loader = PromptLoader()
        system_prompt = prompt_loader.load('training_system')
        
        # Build response with tool calling pattern
        response_parts = []
        
        # Stage 1: Think about what to retrieve for modeling
        response_parts.append("<think>")
        response_parts.append("Let me search for relevant modeling patterns for this optimization problem.")
        response_parts.append("</think>\n")
        
        # Stage 1: Observation from RAG (modeling)
        response_parts.append("<observation>")
        response_parts.append("[RETRIEVED] Modeling patterns:")
        response_parts.append(collector_output['stage1_modeling_reference'])
        response_parts.append("</observation>\n")
        
        # Stage 2: Think about mathematical modeling
        response_parts.append("<think>")
        response_parts.append("Now I'll formulate the mathematical model based on the problem structure.")
        response_parts.append("</think>\n")
        
        # Stage 2: Mathematical model output
        response_parts.append("<model_agent>")
        response_parts.append(collector_output['stage2_math_model'])
        response_parts.append("</model_agent>\n")
        
        # Stage 3: Think about what API documentation needed
        response_parts.append("<think>")
        response_parts.append("I need to retrieve COPT API documentation for implementing this model.")
        response_parts.append("</think>\n")
        
        # Stage 3: Observation from RAG (API)
        response_parts.append("<observation>")
        response_parts.append("[RETRIEVED] COPT API documentation:")
        response_parts.append(collector_output['stage3_coding_reference'])
        response_parts.append("</observation>\n")
        
        # Stage 4: Code generation (use <code> tag, not <code_agent>)
        response_parts.append("<code>")
        response_parts.append(f"```python\n{collector_output['stage4_initial_code']}\n```")
        response_parts.append("</code>\n")
        
        # Stage 5: Code execution observations and debugging
        debug_result = collector_output['stage5_debug_result']
        
        for i, attempt in enumerate(debug_result.get('history', []), 1):
            # Execution observation
            response_parts.append("<observation>")
            
            if attempt['execution']['success']:
                response_parts.append("[EXECUTED] Code exited with status 0.")
                response_parts.append("[STDOUT:BEGIN]")
                # Clean output, remove extra whitespace
                output = attempt['execution']['output'].strip()
                response_parts.append(output)
                response_parts.append("[STDOUT:END]")
            else:
                response_parts.append("[EXECUTED] Code exited with non-zero status.")
                response_parts.append("[STDERR:BEGIN]")
                error = attempt['execution'].get('error', 'Unknown error').strip()
                response_parts.append(error[:500])  # Limit error length
                response_parts.append("[STDERR:END]")
            
            response_parts.append("</observation>\n")
            
            # If there's debugging reasoning (wrong answer or error)
            if attempt.get('reasoning'):
                response_parts.append("<think>")
                response_parts.append("## Debugging Analysis")
                response_parts.append(str(attempt['reasoning']))
                response_parts.append("</think>\n")
                
                # If there's repaired code
                if attempt.get('repaired_code'):
                    response_parts.append("<code>")
                    response_parts.append(f"```python\n{attempt['repaired_code']}\n```")
                    response_parts.append("</code>\n")
        
        # Final code (only if successful)
        if debug_result['success']:
            # Don't add final_code separately if it's same as last repaired_code
            # Just ensure the last code in sequence is the working one
            pass
        
        # DON'T include <answer> tag - let model learn to extract from observation
        # The answer will be extracted from execution output during inference
        
        # Combine response
        full_response = '\n'.join(response_parts)
        
        # Create training sample in new format
        training_sample = {
            'system': system_prompt,
            'input': collector_output['problem'],
            'completion': full_response,
            
            # Keep original fields for analysis
            'problem_id': collector_output['problem_id'],
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


# Test
if __name__ == "__main__":
    print("=== Data Formatter Test (Tool Calling Format) ===\n")
    
    # Mock collector output
    mock_output = {
        'problem_id': 'test_001',
        'problem': 'Optimize resource allocation...',
        'ground_truth': '42',
        'stage1_modeling_reference': 'Pattern: Linear Programming with capacity constraints',
        'stage2_math_model': 'Variables: x (INTEGER)\nObjective: minimize cost\nConstraints: x >= 42',
        'stage3_coding_reference': 'model.addVar(vtype=COPT.INTEGER)\nmodel.setObjective(expr, COPT.MINIMIZE)',
        'stage4_initial_code': 'import coptpy as cp\nmodel = cp.Envr().createModel()\nx = model.addVar(lb=0, vtype=cp.COPT.INTEGER)\nmodel.setObjective(x, cp.COPT.MINIMIZE)\nmodel.addConstr(x >= 42)\nmodel.solve()\nprint(f"Optimal objective: {model.objval}")',
        'stage5_debug_result': {
            'success': True,
            'answer_correct': True,
            'final_code': 'import coptpy as cp\nmodel = cp.Envr().createModel()\nx = model.addVar(lb=0, vtype=cp.COPT.INTEGER)\nmodel.setObjective(x, cp.COPT.MINIMIZE)\nmodel.addConstr(x >= 42)\nmodel.solve()\nprint(f"Optimal objective: {model.objval}")',
            'attempts': 1,
            'history': [{
                'attempt': 1,
                'execution': {'success': True, 'output': 'Optimal objective: 42.0'},
                'answer_check': {'correct': True, 'status': 'Correct'},
                'reasoning': None,
                'repaired_code': None
            }]
        },
        'success': True,
        'answer_correct': True
    }
    
    # Test formatting
    formatter = DataFormatter()
    training_sample = formatter.format_training_sample(mock_output)
    
    print(f"✓ Keys: {list(training_sample.keys())}")
    print(f"✓ Has system: {bool(training_sample.get('system'))}")
    print(f"✓ Completion length: {len(training_sample['completion'])} chars")
    print(f"\n✓ Sample completion preview:")
    print(training_sample['completion'][:500])
    print("\n✓ Data Formatter test passed!")