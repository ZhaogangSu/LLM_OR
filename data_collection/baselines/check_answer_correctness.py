# check_answer_correctness.py
import json
import re

def extract_objective_value(output_text):
    """Extract objective value from solver output or print statements"""
    # Try to find "Optimal objective: XXX" or "Objective: XXX"
    patterns = [
        r'Optimal objective:\s*([-+]?\d*\.?\d+)',
        r'Objective:\s*([-+]?\d*\.?\d+)',
        r'Maximum profit:\s*([-+]?\d*\.?\d+)',
        r'Minimum cost:\s*([-+]?\d*\.?\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, output_text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    
    return None

def check_correctness(jsonl_file, tolerance=0.1):
    """Check how many solutions are actually correct"""
    
    samples = []
    with open(jsonl_file, 'r') as f:
        for line in f:
            samples.append(json.loads(line))
    
    print("="*70)
    print("ANSWER CORRECTNESS ANALYSIS")
    print("="*70)
    
    correct = 0
    incorrect = 0
    no_ground_truth = 0
    cannot_extract = 0
    
    details = []
    
    for sample in samples:
        sample_id = sample['id']
        ground_truth = sample.get('ground_truth')
        
        # Skip if no ground truth
        if not ground_truth or ground_truth == "" or ground_truth == "No Best Solution":
            no_ground_truth += 1
            continue
        
        # Convert ground truth to float
        try:
            gt_value = float(ground_truth)
        except:
            print(f"⚠️  Sample {sample_id}: Cannot parse ground truth '{ground_truth}'")
            no_ground_truth += 1
            continue
        
        # Extract predicted value from execution result
        if sample['success'] and 'raw_outputs' in sample:
            exec_result = sample['raw_outputs'].get('execution_result', '')
            pred_value = extract_objective_value(exec_result)
            
            if pred_value is None:
                cannot_extract += 1
                details.append({
                    'id': sample_id,
                    'status': 'cannot_extract',
                    'ground_truth': gt_value,
                    'predicted': None
                })
                continue
            
            # Check if correct (within tolerance)
            if abs(pred_value - gt_value) <= tolerance:
                correct += 1
                details.append({
                    'id': sample_id,
                    'status': 'correct',
                    'ground_truth': gt_value,
                    'predicted': pred_value,
                    'error': abs(pred_value - gt_value)
                })
            else:
                incorrect += 1
                details.append({
                    'id': sample_id,
                    'status': 'incorrect',
                    'ground_truth': gt_value,
                    'predicted': pred_value,
                    'error': abs(pred_value - gt_value)
                })
        else:
            cannot_extract += 1
    
    total_evaluated = correct + incorrect
    
    print(f"\n📊 Results Summary:")
    print(f"  Total samples: {len(samples)}")
    print(f"  Evaluated: {total_evaluated}")
    print(f"  ✓ Correct: {correct} ({correct/total_evaluated*100:.1f}%)")
    print(f"  ✗ Incorrect: {incorrect} ({incorrect/total_evaluated*100:.1f}%)")
    print(f"  ⚠ Cannot extract: {cannot_extract}")
    print(f"  ⚠ No ground truth: {no_ground_truth}")
    print(f"")
    print(f"📈 Final Metrics:")
    print(f"  Correctness Rate: {correct/total_evaluated*100:.1f}%")
    print(f"  Execution Success Rate: {(correct+incorrect)/len(samples)*100:.1f}%")
    
    # Show incorrect examples
    if incorrect > 0:
        print(f"\n❌ Incorrect Solutions (showing first 5):")
        incorrect_samples = [d for d in details if d['status'] == 'incorrect'][:5]
        for d in incorrect_samples:
            print(f"  Sample {d['id']}:")
            print(f"    Ground truth: {d['ground_truth']}")
            print(f"    Predicted: {d['predicted']}")
            print(f"    Error: {d['error']:.2f}")
    
    # Save detailed results
    with open('answer_correctness_report.json', 'w') as f:
        json.dump({
            'summary': {
                'total': len(samples),
                'evaluated': total_evaluated,
                'correct': correct,
                'incorrect': incorrect,
                'cannot_extract': cannot_extract,
                'no_ground_truth': no_ground_truth,
                'accuracy': correct / total_evaluated if total_evaluated > 0 else 0
            },
            'details': details
        }, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: answer_correctness_report.json")
    print("="*70)

if __name__ == "__main__":
    check_correctness("collected_data/mamo_complex/training_data.jsonl")