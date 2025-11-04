#!/bin/bash

echo "========================================"
echo "Direct Qwen-Max Baseline Experiment"
echo "========================================"

cd "$(dirname "$0")/.." || exit

python -m baselines.direct_qwen_baseline \
    --input_file ../benchmark/Mamo_complex_lp_clean.jsonl \
    --output_dir outputs/baseline_results/mamo_complex \
    --api_keys config/API_keys.txt \
    --num_workers 12 \
    --max_problems 111

echo ""
echo "Baseline experiment complete!"
