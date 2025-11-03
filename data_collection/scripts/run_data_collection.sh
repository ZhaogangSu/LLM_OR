#!/bin/bash

echo "========================================"
echo "OR Multi-Agent Data Collection Pipeline"
echo "========================================"

cd "$(dirname "$0")/.." || exit

python -m agents.parallel_collection \
    --input_file ../benchmark/Mamo_complex_lp_clean.jsonl \
    --output_dir outputs/collected_data/mamo_complex \
    --api_keys config/API_keys.txt \
    --kb_dir knowledge_base/data \
    --num_workers 9 \
    --max_problems 111

echo ""
echo "Data collection complete!"
echo "Check results in: outputs/collected_data/mamo_complex"
