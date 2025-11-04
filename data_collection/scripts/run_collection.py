#!/usr/bin/env python3
"""
Main entry point for data collection pipeline.

Usage:
    python scripts/run_collection.py \
        --input benchmark/Mamo_complex_lp_clean.jsonl \
        --output outputs/mamo_complex \
        --workers 9 \
        --max-problems 111
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_loader import get_config
from pipeline import ParallelExecutor


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Run multi-agent OR data collection pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all problems with 9 workers
  python scripts/run_collection.py -i data.jsonl -o outputs/results

  # Process first 50 problems with 4 workers
  python scripts/run_collection.py -i data.jsonl -o outputs/test -w 4 -n 50

  # Use custom config file
  python scripts/run_collection.py -i data.jsonl -o outputs -c config/custom.yaml
        """
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
        help='Output directory for collected data'
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

    parser.add_argument(
        '-c', '--config',
        type=str,
        default=None,
        help='Path to config.yaml (default: config/config.yaml)'
    )

    parser.add_argument(
        '--provider',
        type=str,
        choices=['qwen', 'openai', 'deepseek', 'anthropic'],
        default=None,
        help='Override LLM provider from config'
    )

    return parser.parse_args()


def validate_args(args):
    """Validate command line arguments"""
    # Check input file exists
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)

    # Check workers is positive
    if args.workers <= 0:
        print(f"❌ Error: Workers must be positive, got: {args.workers}")
        sys.exit(1)

    # Check max_problems is positive if specified
    if args.max_problems is not None and args.max_problems <= 0:
        print(f"❌ Error: Max problems must be positive, got: {args.max_problems}")
        sys.exit(1)

    # Check config file exists if specified
    if args.config and not Path(args.config).exists():
        print(f"❌ Error: Config file not found: {args.config}")
        sys.exit(1)


def main():
    """Main entry point"""
    # Parse arguments
    args = parse_args()

    # Validate arguments
    validate_args(args)

    # Print header
    print("=" * 70)
    print("OR Multi-Agent Data Collection Pipeline")
    print("=" * 70)
    print(f"Input:       {args.input}")
    print(f"Output:      {args.output}")
    print(f"Workers:     {args.workers}")
    print(f"Max problems: {args.max_problems or 'all'}")
    if args.provider:
        print(f"LLM provider: {args.provider}")
    print("=" * 70)
    print()

    try:
        # Load config
        config = get_config(args.config)

        # Override provider if specified
        if args.provider:
            config._config['llm']['provider'] = args.provider
            print(f"✓ Using LLM provider: {args.provider}")

        # Validate config
        config.validate()

        # Create executor
        executor = ParallelExecutor(config, num_workers=args.workers)

        # Run collection
        stats = executor.execute_parallel(
            input_file=args.input,
            output_dir=args.output,
            max_problems=args.max_problems
        )

        # Print final summary
        print()
        print("=" * 70)
        print("✓ Data collection completed successfully!")
        print("=" * 70)
        print(f"Results saved to: {args.output}")
        print(f"Success rate: {stats['success_rate']*100:.1f}%")
        print(f"Correctness rate: {stats['correctness_rate']*100:.1f}%")
        print("=" * 70)

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
