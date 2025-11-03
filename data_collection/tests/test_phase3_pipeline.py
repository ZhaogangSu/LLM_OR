"""
Integration test for Phase 3 pipeline.
Tests collector, formatter, and parallel executor.
"""

import sys
import json
import os
sys.path.insert(0, '..')

from config.config_loader import get_config
from pipeline import DataCollector, DataFormatter, ParallelExecutor


def test_collector():
    """Test data collector"""
    print("=" * 70)
    print("Test 1: Data Collector")
    print("=" * 70)

    config = get_config()
    collector = DataCollector(config)

    test_problem = {
        'id': 'test_001',
        'en_question': 'Minimize x subject to x >= 3',
        'en_answer': '3'
    }

    result = collector.collect_single_problem(test_problem)

    assert 'stage1_modeling_reference' in result
    assert 'stage2_math_model' in result
    assert 'stage3_coding_reference' in result
    assert 'stage4_initial_code' in result
    assert 'stage5_debug_result' in result
    assert 'success' in result

    print("✓ Collector returns all expected stages")
    print("✓ Collector test PASSED\n")


def test_formatter():
    """Test data formatter"""
    print("=" * 70)
    print("Test 2: Data Formatter")
    print("=" * 70)

    # Mock collector output
    mock_output = {
        'problem_id': 'test_001',
        'problem': 'Test problem',
        'ground_truth': '42',
        'stage1_modeling_reference': 'ref1',
        'stage2_math_model': 'model',
        'stage3_coding_reference': 'ref2',
        'stage4_initial_code': 'code',
        'stage5_debug_result': {
            'success': True,
            'answer_correct': True,
            'final_code': 'final_code',
            'attempts': 1,
            'history': []
        },
        'success': True,
        'answer_correct': True
    }

    formatter = DataFormatter()
    sample = formatter.format_training_sample(mock_output)

    assert 'problem' in sample
    assert 'response' in sample
    assert 'success' in sample
    assert '<think_stage' in sample['response']

    print("✓ Formatter creates proper training sample")
    print("✓ Formatter includes think tags")
    print("✓ Formatter test PASSED\n")


def test_parallel_executor_init():
    """Test parallel executor initialization"""
    print("=" * 70)
    print("Test 3: Parallel Executor (Init)")
    print("=" * 70)

    config = get_config()
    executor = ParallelExecutor(config, num_workers=2)

    assert executor.collector is not None
    assert executor.formatter is not None
    assert executor.num_workers == 2

    print("✓ Executor initializes collector")
    print("✓ Executor initializes formatter")
    print("✓ Executor test PASSED\n")


def test_full_pipeline_minimal():
    """Test minimal full pipeline (1 problem)"""
    print("=" * 70)
    print("Test 4: Full Pipeline (1 problem)")
    print("=" * 70)

    # Create test file
    test_file = 'test_input.jsonl'
    test_output_dir = 'test_output_phase3'

    test_problem = {
        'id': 'minimal_test',
        'en_question': 'Minimize cost = x where x >= 5',
        'en_answer': '5'
    }

    with open(test_file, 'w') as f:
        json.dump(test_problem, f)
        f.write('\n')

    print(f"✓ Created test file: {test_file}")

    # Run collection
    config = get_config()
    executor = ParallelExecutor(config, num_workers=1)

    try:
        stats = executor.execute_parallel(
            input_file=test_file,
            output_dir=test_output_dir,
            max_problems=1
        )

        assert stats['total_problems'] == 1
        assert os.path.exists(os.path.join(test_output_dir, 'training_data.jsonl'))
        assert os.path.exists(os.path.join(test_output_dir, 'statistics.json'))

        print("\n✓ Pipeline processed 1 problem")
        print("✓ Output files created")
        print("✓ Statistics collected")
        print("✓ Full pipeline test PASSED\n")

    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        # Note: Keep test_output_phase3 for inspection


def run_all_tests():
    """Run all Phase 3 tests"""
    print("\n" + "=" * 70)
    print("PHASE 3 PIPELINE INTEGRATION TESTS")
    print("=" * 70 + "\n")

    try:
        test_collector()
        test_formatter()
        test_parallel_executor_init()
        test_full_pipeline_minimal()

        print("=" * 70)
        print("✓ ALL PHASE 3 TESTS PASSED!")
        print("=" * 70)
        print("\nPipeline is ready for production use!")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
