#!/usr/bin/env python3
"""
Validate collected data and check answer correctness.

This reads a training_data.jsonl file and validates:
- Answer correctness against ground truth
- Success rates
- Data format integrity
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from baselines.check_answer_correctness import check_correctness


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Validate collected data and check answer correctness',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-f', '--file',
        type=str,
        required=True,
        help='Path to training_data.jsonl or results file'
    )

    parser.add_argument(
        '-t', '--tolerance',
        type=float,
        default=0.1,
        help='Answer tolerance (default: 0.1)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='validation_report.json',
        help='Output report file (default: validation_report.json)'
    )

    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()

    if not Path(args.file).exists():
        print(f"❌ Error: File not found: {args.file}")
        return 1

    print("=" * 70)
    print("Data Validation")
    print("=" * 70)
    print(f"File: {args.file}")
    print(f"Tolerance: {args.tolerance}")
    print("=" * 70)
    print()

    try:
        # Run validation
        check_correctness(args.file, tolerance=args.tolerance)

        print(f"\n✓ Validation report saved to: {args.output}")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
