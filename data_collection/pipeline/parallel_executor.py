"""
Parallel Executor: Manages parallel execution of data collection.

Responsibilities:
- Parallel execution with multiple workers
- Progress tracking
- File I/O (load problems, save results)
- Statistics collection and reporting

Does NOT:
- Orchestrate agents (that's Collector's job)
- Format data (that's DataFormatter's job)
"""

import json
import os
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pathlib import Path

from .collector import DataCollector
from .data_formatter import DataFormatter
from config.config_loader import Config


class ParallelExecutor:
    """
    Parallel execution manager for data collection

    Handles:
    - Loading problems from file
    - Parallel execution with progress bar
    - Saving results
    - Statistics collection
    """

    def __init__(self, config: Config, num_workers: int = 9):
        """
        Initialize parallel executor

        Args:
            config: Configuration object
            num_workers: Number of parallel workers
        """
        self.config = config
        self.num_workers = num_workers

        # Create collector and formatter
        self.collector = DataCollector(config)
        self.formatter = DataFormatter()

        print(f"✓ ParallelExecutor initialized with {num_workers} workers")

    def load_problems(self, input_file: str, max_problems: int = None) -> List[Dict]:
        """
        Load problems from JSONL file

        Args:
            input_file: Path to JSONL file
            max_problems: Maximum number to load (None = all)

        Returns:
            List of problem dictionaries
        """
        problems = []

        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                problems.append(json.loads(line))
                if max_problems and len(problems) >= max_problems:
                    break

        print(f"✓ Loaded {len(problems)} problems from {input_file}")
        return problems

    def _process_single(self, problem: Dict) -> Dict:
        """
        Process single problem (wrapper for parallel execution)

        Args:
            problem: Problem dictionary

        Returns:
            Formatted training sample or None if failed
        """
        try:
            # Collect data
            raw_output = self.collector.collect_single_problem(problem)

            # Format as training sample
            training_sample = self.formatter.format_training_sample(raw_output)

            return training_sample

        except Exception as e:
            print(f"\n❌ Failed to process problem {problem.get('id')}: {e}")
            return None

    def execute_parallel(
        self,
        input_file: str,
        output_dir: str,
        max_problems: int = None
    ) -> Dict[str, Any]:
        """
        Execute data collection in parallel

        Args:
            input_file: Input JSONL file with problems
            output_dir: Output directory for results
            max_problems: Limit number of problems (None = all)

        Returns:
            Dict with statistics and results
        """
        # Load problems
        problems = self.load_problems(input_file, max_problems)

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Parallel execution with progress bar
        print(f"\n{'='*70}")
        print(f"Starting parallel collection: {len(problems)} problems, {self.num_workers} workers")
        print(f"{'='*70}\n")

        training_samples = []
        failed_samples = []

        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(self._process_single, problem): problem
                for problem in problems
            }

            # Process with progress bar
            with tqdm(total=len(problems), desc="Processing") as pbar:
                for future in as_completed(futures):
                    result = future.result()

                    if result is not None:
                        training_samples.append(result)
                    else:
                        problem = futures[future]
                        failed_samples.append(problem.get('id', 'unknown'))

                    pbar.update(1)

        # Save results
        output_file = os.path.join(output_dir, 'training_data.jsonl')
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in training_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')

        # Collect statistics
        total = len(problems)
        successful = len(training_samples)
        failed = len(failed_samples)
        correct = sum(1 for s in training_samples if s.get('answer_correct', False))

        stats = {
            'total_problems': total,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total if total > 0 else 0,
            'correct_answers': correct,
            'correctness_rate': correct / total if total > 0 else 0,
            'output_file': output_file,
            'failed_ids': failed_samples
        }

        # Save statistics
        stats_file = os.path.join(output_dir, 'statistics.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)

        # Print summary
        self._print_summary(stats)

        return stats

    def _print_summary(self, stats: Dict[str, Any]):
        """Print execution summary"""
        print("\n" + "="*70)
        print("DATA COLLECTION COMPLETE")
        print("="*70)
        print(f"Total problems:    {stats['total_problems']}")
        print(f"Successful:        {stats['successful']} ({stats['success_rate']*100:.1f}%)")
        print(f"Failed:            {stats['failed']}")
        print(f"Correct answers:   {stats['correct_answers']} ({stats['correctness_rate']*100:.1f}%)")
        print(f"\nOutput saved to:   {stats['output_file']}")
        print("="*70)


# Test
if __name__ == "__main__":
    from config.config_loader import get_config

    print("=== Parallel Executor Test ===\n")

    # For testing, create a small test file
    test_file = 'test_problems.jsonl'
    test_problems = [
        {
            'id': 'test_001',
            'en_question': 'Minimize x subject to x >= 5',
            'en_answer': '5'
        },
        {
            'id': 'test_002',
            'en_question': 'Maximize 2*x + 3*y subject to x + y <= 10, x >= 0, y >= 0',
            'en_answer': '30'
        }
    ]

    with open(test_file, 'w') as f:
        for prob in test_problems:
            f.write(json.dumps(prob) + '\n')

    print(f"✓ Created test file: {test_file}")

    # Initialize executor
    config = get_config()
    executor = ParallelExecutor(config, num_workers=2)

    # Run collection (comment out if don't want to actually run)
    # stats = executor.execute_parallel(
    #     input_file=test_file,
    #     output_dir='test_output',
    #     max_problems=2
    # )

    print("\n✓ Parallel Executor test passed (initialization)")
    print("  (Uncomment execution block to test full pipeline)")

    # Cleanup
    import os
    if os.path.exists(test_file):
        os.remove(test_file)
