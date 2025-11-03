# parallel_collection.py
import json
import os
from agents.multi_agent_collector import MultiAgentCollector
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import argparse

def load_api_keys(key_file="API_keys.txt"):
    """Load API keys from file"""
    with open(key_file, 'r') as f:
        keys = [line.strip() for line in f if line.strip()]
    print(f"✓ Loaded {len(keys)} API keys")
    return keys

def load_problems(data_file):
    """Load OR problems from JSONL file"""
    problems = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            problems.append(json.loads(line))
    print(f"✓ Loaded {len(problems)} problems from {data_file}")
    return problems

def collect_single_wrapper(args):
    """Wrapper for parallel execution"""
    collector, problem = args
    try:
        result = collector.collect_single_problem(problem)
        training_sample = collector.format_as_training_sample(result)
        return training_sample
    except Exception as e:
        print(f"❌ Failed to process problem {problem.get('id')}: {e}")
        return None

def main(args):
    # Load resources
    api_keys = load_api_keys(args.api_keys)
    problems = load_problems(args.input_file)
    
    # Limit number of problems if specified
    if args.max_problems:
        problems = problems[:args.max_problems]
        print(f"  Limited to {len(problems)} problems")
    
    # Initialize collector
    collector = MultiAgentCollector(api_keys, kb_dir=args.kb_dir)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Parallel collection
    print(f"\nStarting parallel data collection with {args.num_workers} workers...")
    print("="*70)
    
    training_samples = []
    failed_count = 0
    
    # Prepare arguments for parallel execution
    collect_args = [(collector, problem) for problem in problems]
    
    with ThreadPoolExecutor(max_workers=args.num_workers) as executor:
        # Submit all tasks
        futures = [executor.submit(collect_single_wrapper, arg) for arg in collect_args]
        
        # Process results with progress bar
        for future in tqdm(as_completed(futures), total=len(problems), desc="Collecting"):
            result = future.result()
            if result:
                training_samples.append(result)
            else:
                failed_count += 1
    
    # Save results
    output_file = os.path.join(args.output_dir, 'training_data.jsonl')
    with open(output_file, 'w', encoding='utf-8') as f:
        for sample in training_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    
    # Calculate detailed statistics
    total_problems = len(problems)
    successful = len(training_samples)
    failed = failed_count
    
    # Calculate correctness (only for successful samples)
    correct = sum(1 for sample in training_samples 
                  if sample.get('raw_outputs', {}).get('answer_correct', False))
    wrong = successful - correct
    
    # Save statistics
    stats = {
        'total_problems': total_problems,
        'successful': successful,
        'failed': failed,
        'success_rate': successful / total_problems if total_problems > 0 else 0,
        'correct_answers': correct,
        'wrong_answers': wrong,
        'correctness_rate': correct / total_problems if total_problems > 0 else 0,
        'output_file': output_file,
        'problem_breakdown': [
            {
                'id': sample.get('id'),
                'success': sample.get('success', False),
                'answer_correct': sample.get('raw_outputs', {}).get('answer_correct', False)
            }
            for sample in training_samples
        ]
    }
    
    stats_file = os.path.join(args.output_dir, 'collection_stats.json')
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Print summary
    print("\n" + "="*70)
    print("DATA COLLECTION COMPLETE")
    print("="*70)
    print(f"Total problems: {total_problems}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/total_problems*100:.1f}%")
    print(f"")
    print(f"✓ Correct answers: {correct}")
    print(f"✗ Wrong answers: {wrong}")
    print(f"📊 Correctness rate: {correct/total_problems*100:.1f}%")
    print(f"")
    print(f"Output saved to: {output_file}")
    print(f"Statistics saved to: {stats_file}")
    print("="*70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parallel multi-agent data collection")
    parser.add_argument("--input_file", type=str, required=True,
                       help="Input JSONL file with OR problems")
    parser.add_argument("--output_dir", type=str, default="collected_data",
                       help="Output directory for training data")
    parser.add_argument("--api_keys", type=str, default="API_keys.txt",
                       help="File containing API keys")
    parser.add_argument("--kb_dir", type=str, default="copt_knowledge_base",
                       help="COPT knowledge base directory")
    parser.add_argument("--num_workers", type=int, default=9,
                       help="Number of parallel workers")
    parser.add_argument("--max_problems", type=int, default=None,
                       help="Limit number of problems to process")
    
    args = parser.parse_args()
    main(args)