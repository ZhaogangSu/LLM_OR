"""
Answer validation utility for checking if code output matches ground truth.
Extracts numerical answers from execution output and validates with tolerance.
"""

import re
from typing import Optional, Tuple


def extract_answer_from_output(output: str) -> Optional[float]:
    """
    Extract numerical answer from code execution output

    Args:
        output: Stdout from code execution

    Returns:
        float: Extracted answer, or None if not found
    """
    # Patterns to match various output formats
    patterns = [
        r'(?:Optimal |Best |Final )?[Oo]bjective:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
        r'(?:Optimal |Best |Final )?[Cc]ost:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
        r'(?:Minimum |Min )?[Cc]ost:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
        r'(?:Maximum |Max )?[Pp]rofit:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
        r'(?:Total |Sum )?[Pp]rofit:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
        r'(?:Optimal |Best )?[Ss]olution:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
        r'(?:Optimal |Best )?[Vv]alue:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
        r'[Aa]nswer:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                continue

    return None


def check_answer_correctness(
    execution_output: str,
    ground_truth: str,
    tolerance: float = 0.1
) -> Tuple[bool, Optional[float], str]:
    """
    Check if execution output matches ground truth

    Args:
        execution_output: Output from code execution
        ground_truth: Expected answer (string)
        tolerance: Acceptable difference

    Returns:
        Tuple of:
            - bool: True if answer is correct
            - float: Extracted predicted value (or None)
            - str: Status message
    """
    # Parse ground truth
    try:
        gt_value = float(ground_truth)
    except ValueError:
        return {
            'correct': None,
            'predicted': None,
            'status': None
        }

    # Extract predicted value
    pred_value = extract_answer_from_output(execution_output)

    if pred_value is None:
        return {
            'correct': False,
            'predicted': None,
            'status': None
        }

    # Compare with tolerance
    error = abs(pred_value - gt_value)
    is_correct = error <= tolerance

    if is_correct:
        status = f"✓ Correct (predicted={pred_value}, expected={gt_value}, error={error:.6f})"
    else:
        status = f"✗ Incorrect (predicted={pred_value}, expected={gt_value}, error={error:.6f})"

    return {
        'correct': is_correct,
        'predicted': pred_value,
        'status': status
    }


# Standalone function for backward compatibility
def check_answer_correctness_simple(execution_output: str, ground_truth: str, tolerance: float = 0.1) -> bool:
    """
    Simple boolean check for answer correctness

    Args:
        execution_output: Output from code execution
        ground_truth: Expected answer
        tolerance: Acceptable difference

    Returns:
        bool: True if correct
    """
    is_correct, _, _ = check_answer_correctness(execution_output, ground_truth, tolerance)
    return {
        'correct': is_correct
    }


# Test
if __name__ == "__main__":
    print("=== Answer Checker Tests ===\n")

    # Test 1: Extract from various formats
    test_outputs = [
        "Optimal objective: 42.5",
        "Best cost: 123.456",
        "Maximum profit: 789.0",
        "The answer is: 55.5",
        "Optimal value: 1e3",
    ]

    print("Test 1: Extract answers from different formats")
    for output in test_outputs:
        answer = extract_answer_from_output(output)
        print(f"  '{output}' -> {answer}")

    # Test 2: Check correctness
    print("\nTest 2: Correctness checking")

    test_cases = [
        ("Optimal objective: 42.0", "42", 0.1, True),
        ("Optimal objective: 42.05", "42", 0.1, True),
        ("Optimal objective: 43.0", "42", 0.1, False),
        ("Optimal objective: 41.95", "42", 0.1, True),
    ]

    for output, gt, tol, expected in test_cases:
        is_correct, pred, status = check_answer_correctness(output, gt, tol)
        symbol = "✓" if is_correct == expected else "✗"
        print(f"  {symbol} {status}")

    print("\n✓ All tests completed")
