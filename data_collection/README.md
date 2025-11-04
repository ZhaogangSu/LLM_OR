# OR Multi-Agent Data Collection System

Production-ready data collection system for Operations Research problems using multi-agent framework with reasoning LLMs.

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install openai anthropic pyyaml python-dotenv tqdm beautifulsoup4 requests lxml faiss-cpu pytest coptpy

# Install COPT solver (required)
# Follow instructions at: https://www.copt.com
```

### 2. Configuration

```bash
# Add your API keys
echo "your-api-key-1" > config/API_keys.txt
echo "your-api-key-2" >> config/API_keys.txt

# Configure LLM provider (optional - defaults to Qwen)
# Edit config/config.yaml to switch providers:
# llm:
#   provider: "qwen"  # or "openai", "deepseek", "anthropic"
```

### 3. Run Data Collection

```bash
# Process problems with default settings
python scripts/run_collection.py \
    --input ../benchmark/Mamo_complex_lp_clean.jsonl \
    --output outputs/mamo_complex

# With custom settings
python scripts/run_collection.py \
    --input ../benchmark/NL4Opt_clean.jsonl \
    --output outputs/nl4opt \
    --workers 4 \
    --max-problems 50
```

### 4. Run Baseline Comparison

```bash
python scripts/run_baseline.py \
    --input ../benchmark/Mamo_complex_lp_clean.jsonl \
    --output outputs/baseline_mamo
```

### 5. Validate Results

```bash
python scripts/validate_results.py \
    --file outputs/mamo_complex/training_data.jsonl
```

---

## 📁 Project Structure

```
data_collection/
├── config/                          # Configuration management
│   ├── config.yaml                  # Main configuration file
│   ├── config_loader.py             # Config loader utility
│   ├── prompt_loader.py             # Prompt loader utility
│   ├── API_keys.txt                 # API keys (one per line)
│   └── prompts/                     # Externalized prompts
│       ├── modeling_agent_*.txt     # Modeling prompts
│       ├── coding_agent_*.txt       # Coding prompts
│       └── debugging_*.txt          # Debugging prompts
│
├── core/                            # Core utilities
│   ├── llm_client.py                # Abstract LLM client (multi-provider)
│   ├── code_executor.py             # Code execution utility
│   └── answer_checker.py            # Answer validation utility
│
├── agents/                          # Multi-agent framework
│   ├── base_agent.py                # Abstract base agent
│   ├── modeling_agent.py            # Mathematical modeling
│   ├── coding_agent.py              # Code generation
│   ├── debugging_agent.py           # Debugging & repair
│   └── reference_agent.py           # Knowledge retrieval
│
├── pipeline/                        # Pipeline orchestration
│   ├── collector.py                 # Multi-agent orchestrator
│   ├── data_formatter.py            # Training data formatter
│   └── parallel_executor.py         # Parallel execution manager
│
├── scripts/                         # Entry points
│   ├── run_collection.py            # Main collection pipeline
│   ├── run_baseline.py              # Baseline comparison
│   └── validate_results.py          # Results validation
│
├── baselines/                       # Baseline experiments
│   ├── direct_qwen_baseline.py      # Direct prompting baseline
│   └── check_answer_correctness.py  # Answer validation
│
├── knowledge_base/                  # Knowledge retrieval (out of scope)
│   └── retrievers/                  # Gurobi & COPT knowledge base
│
├── tests/                           # Test suite
│   ├── test_phase1_integration.py   # Phase 1 tests
│   ├── test_phase2_agents.py        # Phase 2 tests
│   └── test_phase3_pipeline.py      # Phase 3 tests
│
└── outputs/                         # All outputs
    ├── collected_data/              # Training data
    └── baseline_results/            # Baseline results
```

---

## 🏗️ Architecture

### Multi-Agent Pipeline

The system uses a 5-stage pipeline:

```
Problem → [1] Reference Agent (modeling) → [2] Modeling Agent
       → [3] Reference Agent (coding)   → [4] Coding Agent
       → [5] Debugging Agent            → Solution
```

**Stage 1**: Retrieve relevant Gurobi examples for mathematical modeling
**Stage 2**: Generate mathematical formulation (variables, objective, constraints)
**Stage 3**: Retrieve COPT API docs and Gurobi→COPT translation
**Stage 4**: Generate executable COPT Python code
**Stage 5**: Execute code, debug errors, verify answer (max 3 attempts)

### Key Components

**Core Layer**: Low-level utilities
- `llm_client.py`: Abstract LLM interface (supports Qwen/OpenAI/DeepSeek/Anthropic)
- `code_executor.py`: Safe code execution with timeout
- `answer_checker.py`: Answer validation with tolerance

**Agent Layer**: Business logic
- `ModelingAgent`: Converts problems → mathematical models
- `CodingAgent`: Converts models → COPT Python code
- `DebuggingAgent`: Executes, debugs, and repairs code
- `ReferenceAgent`: Retrieves knowledge from Gurobi/COPT databases

**Pipeline Layer**: Orchestration
- `DataCollector`: Orchestrates the 5-stage agent pipeline
- `DataFormatter`: Formats outputs into training data
- `ParallelExecutor`: Manages parallel execution with progress tracking

---

## ⚙️ Configuration

### Switch LLM Provider

Edit `config/config.yaml`:

```yaml
llm:
  provider: "openai"  # Change from "qwen" to "openai"
```

Supported providers: `qwen`, `openai`, `deepseek`, `anthropic`

### Modify Prompts

Edit files in `config/prompts/`:
- No code changes needed
- Changes take effect immediately
- Easy to version control and A/B test

### Adjust Pipeline Settings

Edit `config/config.yaml`:

```yaml
pipeline:
  max_debug_attempts: 3      # Max debugging attempts
  answer_tolerance: 0.1      # Answer validation tolerance
  parallel_workers: 9        # Parallel workers
  code_execution_timeout: 30 # Code timeout (seconds)
```

---

## 📊 Results

### Current Performance on MAMO Complex LP (111 problems):

| Method | Success Rate | Correctness Rate |
|--------|--------------|------------------|
| Multi-Agent Framework | 61.3% | 61.3% |
| Direct Qwen Baseline | TBD | TBD |

---

## 🧪 Testing

```bash
# Run all tests
cd data_collection
python -m pytest tests/ -v

# Run specific test suite
python tests/test_phase1_integration.py
python tests/test_phase2_agents.py
python tests/test_phase3_pipeline.py
```

---

## 📖 Usage Examples

### Example 1: Process 10 problems for testing

```bash
python scripts/run_collection.py \
    -i ../benchmark/Mamo_easy_lp_clean.jsonl \
    -o outputs/test_run \
    -w 2 \
    -n 10
```

### Example 2: Use different LLM provider

```bash
python scripts/run_collection.py \
    -i ../benchmark/NL4Opt_clean.jsonl \
    -o outputs/nl4opt_gpt4 \
    --provider openai
```

### Example 3: Validate results with custom tolerance

```bash
python scripts/validate_results.py \
    -f outputs/mamo_complex/training_data.jsonl \
    -t 0.5 \
    -o validation_report.json
```

---

## 🔧 Development

### Adding a New Agent

1. Create new agent file in `agents/`
2. Inherit from `BaseAgent`
3. Implement `execute()` method
4. Use `self._call_llm()` for LLM calls
5. Use `self._load_prompt()` for prompts

Example:

```python
from agents.base_agent import BaseAgent

class MyNewAgent(BaseAgent):
    def execute(self, **kwargs):
        system = self._load_prompt('my_agent_system')
        user = self._format_prompt('my_agent_user', **kwargs)
        return self._call_llm(system, user)
```

### Adding a New LLM Provider

1. Edit `core/llm_client.py`
2. Create new class inheriting `BaseLLMClient`
3. Implement `call()` method
4. Add to factory function `create_single_llm_client()`
5. Add config section to `config/config.yaml`

---

## 🐛 Troubleshooting

### Issue: LLM API timeout

**Solution**:
- Check API keys are valid
- Check network connection
- Increase timeout in `config/config.yaml`
- Reduce `--workers` to lower rate limit pressure

### Issue: COPT not found

**Solution**:
```bash
pip install coptpy
# Or follow COPT installation guide
```

### Issue: Wrong answers

**Solution**:
- Check problem format matches expected input
- Review generated code in output files
- Adjust `answer_tolerance` if needed
- Check if ground truth answers are correct

---

## 📄 License

[Your License Here]

---

## 🤝 Contributing

[Your Contributing Guidelines Here]

---

## 📧 Contact

[Your Contact Information Here]
