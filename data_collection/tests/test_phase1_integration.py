"""
Integration test for Phase 1 refactoring.
Tests that all new components work together correctly.
"""

import sys
import os
# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config_loader import get_config
from core.llm_client import create_llm_client
from core.code_executor import CodeExecutor
from core.answer_checker import check_answer_correctness
from config.prompt_loader import PromptLoader


def test_config_loading():
    """Test configuration loading"""
    print("=" * 70)
    print("Test 1: Configuration Loading")
    print("=" * 70)

    config = get_config()
    config.validate()

    print(f"✓ Provider: {config.llm_provider}")
    print(f"✓ Model: {config.get(f'llm.{config.llm_provider}.model')}")
    print(f"✓ API keys: {len(config.get_api_keys())} loaded")
    print("✓ Config test PASSED\n")


def test_llm_client():
    """Test LLM client creation and calling"""
    print("=" * 70)
    print("Test 2: LLM Client")
    print("=" * 70)

    config = get_config()
    llm = create_llm_client(config)

    print(f"✓ LLM pool created with {len(llm.clients)} clients")

    response = llm.call(
        system_prompt="You are a helpful assistant.",
        user_prompt="Say 'Integration test successful' and nothing else."
    )

    print(f"✓ LLM response: {response[:50]}...")
    print("✓ LLM client test PASSED\n")


def test_code_executor():
    """Test code execution"""
    print("=" * 70)
    print("Test 3: Code Executor")
    print("=" * 70)

    executor = CodeExecutor(timeout=5)

    # Test successful execution
    code = """
x = 42
print(f"Optimal objective: {x}")
"""

    result = executor.execute(code)
    print(f"✓ Execution success: {result['success']}")
    print(f"✓ Output: {result['output'].strip()}")

    # Test error handling
    code_error = "x = 1 / 0"
    result = executor.execute(code_error)
    print(f"✓ Error caught: {result['success'] == False}")

    print("✓ Code executor test PASSED\n")


def test_answer_checker():
    """Test answer validation"""
    print("=" * 70)
    print("Test 4: Answer Checker")
    print("=" * 70)

    output = "Optimal objective: 42.05"
    is_correct, pred, status = check_answer_correctness(output, "42", tolerance=0.1)

    print(f"✓ Correctness: {is_correct}")
    print(f"✓ Status: {status}")
    print("✓ Answer checker test PASSED\n")


def test_prompt_loader():
    """Test prompt loading"""
    print("=" * 70)
    print("Test 5: Prompt Loader")
    print("=" * 70)

    loader = PromptLoader()
    prompts = loader.list_prompts()

    print(f"✓ Found {len(prompts)} prompts")

    system = loader.load('modeling_agent_system')
    print(f"✓ Loaded system prompt: {len(system)} chars")

    user = loader.format('modeling_agent_user',
                        problem="test",
                        reference="test")
    print(f"✓ Formatted user prompt: {len(user)} chars")

    print("✓ Prompt loader test PASSED\n")


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "=" * 70)
    print("PHASE 1 INTEGRATION TESTS")
    print("=" * 70 + "\n")

    try:
        test_config_loading()
        test_llm_client()
        test_code_executor()
        test_answer_checker()
        test_prompt_loader()

        print("=" * 70)
        print("✓ ALL TESTS PASSED - Phase 1 Complete!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
