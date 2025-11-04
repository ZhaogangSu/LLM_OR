#!/usr/bin/env python3
"""
Run direct Qwen-Max baseline for comparison.

This bypasses the multi-agent framework and uses direct prompting.
Useful for comparing performance against the multi-agent approach.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from baselines.direct_qwen_baseline import DirectQwenSolver
from config.config_loader import get_config
import json
import os


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Run direct Qwen baseline (no multi-agent framework)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-i', '--input',
        type=str,
        required=True,
        help='Input JSONL file with OR problems'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        required=True,
        help='Output directory for baseline results'
    )

    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=9,
        help='Number of parallel workers (default: 9)'
    )

    parser.add_argument(
        '-n', '--max-problems',
        type=int,
        default=None,
        help='Maximum number of problems to process (default: all)'
    )

    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()

    print("=" * 70)
    print("Direct Qwen-Max Baseline (No Multi-Agent Framework)")
    print("=" * 70)
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")
    print(f"Workers: {args.workers}")
    print("=" * 70)
    print()

    try:
        # Load config for API keys
        config = get_config()
        api_keys = config.get_api_keys()

        # Create output directory
        os.makedirs(args.output, exist_ok=True)

        # Load problems
        problems = []
        with open(args.input, 'r') as f:
            for line in f:
                problems.append(json.loads(line))
                if args.max_problems and len(problems) >= args.max_problems:
                    break

        print(f"✓ Loaded {len(problems)} problems")

        # Create baseline solver
        from baselines.direct_qwen_baseline import DirectQwenSolver
        solver = DirectQwenSolver(api_keys)

        # Process problems
        results = []
        for i, problem in enumerate(problems, 1):
            print(f"\n[{i}/{len(problems)}] Processing {problem.get('id')}...")
            result = solver.solve_problem(problem)
            results.append(result)

        # Save results
        output_file = os.path.join(args.output, 'baseline_results.jsonl')
        with open(output_file, 'w') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')

        # Calculate statistics
        total = len(results)
        successful = sum(1 for r in results if r.get('success', False))
        correct = sum(1 for r in results if r.get('answer_correct', False))

        print("\n" + "=" * 70)
        print("Baseline Results")
        print("=" * 70)
        print(f"Total: {total}")
        print(f"Successful: {successful} ({successful/total*100:.1f}%)")
        print(f"Correct: {correct} ({correct/total*100:.1f}%)")
        print(f"Output: {output_file}")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
