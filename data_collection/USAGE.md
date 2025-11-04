# Usage Guide

This guide provides detailed examples of using the data collection system.

## Basic Usage

### 1. First-Time Setup

```bash
# 1. Configure API keys
echo "sk-your-qwen-key" > config/API_keys.txt

# 2. Test configuration
python -c "from config.config_loader import get_config; get_config().validate(); print('✓ Config OK')"

# 3. Test LLM connection
python -m core.llm_client
```

### 2. Run Small Test

```bash
# Process 5 problems to test the system
python scripts/run_collection.py \
    -i ../benchmark/Mamo_easy_lp_clean.jsonl \
    -o outputs/test \
    -n 5 \
    -w 2
```

### 3. Process Full Dataset

```bash
# Process all problems with 9 workers
python scripts/run_collection.py \
    -i ../benchmark/Mamo_complex_lp_clean.jsonl \
    -o outputs/mamo_complex \
    -w 9
```

---

## Advanced Usage

### Switching LLM Providers

#### Option 1: Edit config file (persistent)

Edit `config/config.yaml`:
```yaml
llm:
  provider: "openai"  # or "deepseek", "anthropic"
```

Then run normally:
```bash
python scripts/run_collection.py -i input.jsonl -o outputs
```

#### Option 2: Command line (temporary)

```bash
python scripts/run_collection.py \
    -i input.jsonl \
    -o outputs \
    --provider openai
```

### Custom Configuration

Create custom config:
```bash
cp config/config.yaml config/custom.yaml
# Edit custom.yaml
```

Use custom config:
```bash
python scripts/run_collection.py \
    -i input.jsonl \
    -o outputs \
    -c config/custom.yaml
```

### Parallel Processing Tips

**Rule of thumb**: 1 worker per API key

```bash
# If you have 3 API keys:
python scripts/run_collection.py -i input.jsonl -o outputs -w 3

# If you have 12 API keys:
python scripts/run_collection.py -i input.jsonl -o outputs -w 12
```

---

## Output Files

### Training Data Format

File: `outputs/collected_data/training_data.jsonl`

Each line is a JSON object:
```json
{
  "problem_id": "test_001",
  "problem": "Minimize cost...",
  "response": "<think_stage name='reference_modeling'>...</think_stage>...",
  "success": true,
  "answer_correct": true,
  "ground_truth": "42",
  "metadata": {
    "modeling_ref_length": 1234,
    "debug_attempts": 2
  }
}
```

### Statistics File

File: `outputs/collected_data/statistics.json`

```json
{
  "total_problems": 111,
  "successful": 68,
  "failed": 43,
  "success_rate": 0.613,
  "correct_answers": 68,
  "correctness_rate": 0.613,
  "output_file": "outputs/.../training_data.jsonl"
}
```

---

## Common Workflows

### Workflow 1: Benchmark Evaluation

```bash
# 1. Collect data
python scripts/run_collection.py \
    -i ../benchmark/NL4Opt_clean.jsonl \
    -o outputs/nl4opt

# 2. Run baseline
python scripts/run_baseline.py \
    -i ../benchmark/NL4Opt_clean.jsonl \
    -o outputs/nl4opt_baseline

# 3. Validate both
python scripts/validate_results.py -f outputs/nl4opt/training_data.jsonl
python scripts/validate_results.py -f outputs/nl4opt_baseline/baseline_results.jsonl

# 4. Compare results
# Check statistics.json in each output directory
```

### Workflow 2: Iterative Development

```bash
# 1. Test on small set
python scripts/run_collection.py -i input.jsonl -o outputs/test -n 10

# 2. Check results
cat outputs/test/statistics.json

# 3. Modify prompts if needed
vim config/prompts/modeling_agent_system.txt

# 4. Re-run test
python scripts/run_collection.py -i input.jsonl -o outputs/test2 -n 10

# 5. Compare
diff outputs/test/statistics.json outputs/test2/statistics.json
```

### Workflow 3: Production Run

```bash
# 1. Validate setup
python tests/test_phase3_pipeline.py

# 2. Run full collection
python scripts/run_collection.py \
    -i ../benchmark/all_problems.jsonl \
    -o outputs/production \
    -w 12

# 3. Validate results
python scripts/validate_results.py -f outputs/production/training_data.jsonl

# 4. Backup results
tar -czf production_$(date +%Y%m%d).tar.gz outputs/production/
```

---

## Performance Tuning

### Optimize for Speed

```yaml
# config/config.yaml
pipeline:
  code_execution_timeout: 15  # Reduce from 30
  max_debug_attempts: 2       # Reduce from 3

llm:
  qwen:
    max_tokens: 3000          # Reduce from 4000
    timeout: 30               # Reduce from 60
```

### Optimize for Quality

```yaml
pipeline:
  code_execution_timeout: 60  # Increase
  max_debug_attempts: 5       # Increase

llm:
  qwen:
    max_tokens: 8000          # Increase
    temperature: 0.5          # More deterministic
```

---

## Troubleshooting

### Problem: Low success rate

**Diagnostics**:
```bash
# Check detailed errors
grep -r "❌" outputs/collected_data/

# Inspect failed problems
python -c "
import json
with open('outputs/collected_data/training_data.jsonl') as f:
    for line in f:
        data = json.loads(line)
        if not data['success']:
            print(f\"Failed: {data['problem_id']}\")
"
```

**Solutions**:
- Review and improve prompts
- Increase `max_debug_attempts`
- Check if COPT is installed correctly

### Problem: Rate limit errors

**Solutions**:
- Add more API keys to `config/API_keys.txt`
- Reduce `--workers`
- Add delays in config

---

## Best Practices

1. **Start Small**: Always test with `-n 10` before full runs
2. **Monitor Progress**: Watch the progress bar and error messages
3. **Version Prompts**: Use git to track prompt changes
4. **Backup Data**: Save outputs before re-running
5. **Validate Results**: Always run validation after collection
6. **Document Changes**: Note config changes in commit messages

---

## FAQ

**Q: Can I pause and resume?**
A: No auto-resume yet. Best to use `-n` for incremental runs.

**Q: How to use multiple providers?**
A: Run separately with different `--provider` flags.

**Q: Can I modify prompts during execution?**
A: Changes take effect immediately but better to restart for consistency.

**Q: What if my API key expires mid-run?**
A: Add the new key to `API_keys.txt` and restart.

---

For more help, see README.md or raise an issue on GitHub.
