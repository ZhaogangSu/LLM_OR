# OR Multi-Agent Data Collection

Automated data collection system for Operations Research problems using multi-agent framework with reasoning LLMs.

## Quick Start
```bash
# 1. Configure API keys
echo "your-api-key-1" > config/API_keys.txt
echo "your-api-key-2" >> config/API_keys.txt

# 2. Run multi-agent data collection
cd scripts
./run_data_collection.sh

# 3. Run baseline comparison
./run_baseline.sh

# 4. Check answer correctness
python -m baselines.check_answer_correctness \
    --file ../outputs/collected_data/mamo_complex/training_data.jsonl
```

## Project Structure
```
├── agents/                          # Multi-agent framework
│   ├── multi_agent_collector.py    # Main collector: orchestrates 5-stage pipeline
│   └── parallel_collection.py      # Parallel execution wrapper
├── baselines/                       # Baseline experiments
│   ├── direct_qwen_baseline.py     # Direct Qwen-Max prompting (no framework)
│   └── check_answer_correctness.py # Verify solution correctness
├── knowledge_base/                  # Knowledge retrieval system
│   ├── builders/                    # Build knowledge bases
│   │   ├── build_gurobi_kb.py      # Index Gurobi modeling examples
│   │   ├── copt_web_crawler.py     # Crawl COPT documentation
│   │   ├── extract_gurobi_patterns.py  # Extract API patterns
│   │   └── build_verified_translation.py  # Build Gurobi→COPT translation
│   ├── data/                        # Knowledge base data
│   │   ├── gurobi_modeling_examples/  # Gurobi example notebooks
│   │   ├── copt_knowledge_base/    # COPT documentation
│   │   └── *.json                  # Indexed data files
│   └── retrievers/                  # Retrieval agents
│       ├── reference_agent.py      # Provides modeling/coding references
│       ├── gurobi_retriever.py     # Search Gurobi examples
│       └── copt_retriever.py       # Search COPT documentation
├── scripts/                         # Execution scripts
│   ├── run_data_collection.sh      # Run multi-agent pipeline
│   ├── run_baseline.sh             # Run baseline experiment
│   ├── test_api.py                 # Test API connectivity
│   └── inspect_knowledge.py        # Inspect KB contents
├── outputs/                         # All outputs
│   ├── collected_data/             # Multi-agent results
│   ├── baseline_results/           # Baseline results
│   └── answer_correctness_report.json
└── config/
    └── API_keys.txt                # API keys (one per line)
```

## File Roles

### Core System

| File | Role |
|------|------|
| `multi_agent_collector.py` | Orchestrates 5 agents: Reference(modeling) → Modeling → Reference(coding) → Coding → Debugging |
| `parallel_collection.py` | Parallel execution with multiple API keys and workers |
| `reference_agent.py` | Retrieves relevant Gurobi examples and COPT docs for each stage |

### Knowledge Base

| File | Role |
|------|------|
| `build_gurobi_kb.py` | Index 51 Gurobi modeling examples into searchable JSON |
| `copt_web_crawler.py` | Crawl and extract COPT API documentation |
| `extract_gurobi_patterns.py` | Analyze Gurobi code to extract common API patterns |
| `build_verified_translation.py` | Build Gurobi→COPT API translation guide |
| `gurobi_retriever.py` | Search Gurobi examples by keywords |
| `copt_retriever.py` | Search COPT docs by semantic similarity |

### Baselines & Analysis

| File | Role |
|------|------|
| `direct_qwen_baseline.py` | Direct Qwen-Max prompting without multi-agent framework |
| `check_answer_correctness.py` | Validate solutions against ground truth |

### Utilities

| File | Role |
|------|------|
| `test_api.py` | Test API key validity and connectivity |
| `inspect_knowledge.py` | Inspect knowledge base contents |
| `run_data_collection.sh` | Main pipeline launcher |
| `run_baseline.sh` | Baseline experiment launcher |

## Multi-Agent Pipeline
```
Problem → [1] Reference Agent (modeling) → [2] Modeling Agent 
       → [3] Reference Agent (coding) → [4] Coding Agent 
       → [5] Debugging Agent → Solution
```

**Stage 1**: Retrieve relevant Gurobi examples for mathematical modeling  
**Stage 2**: Generate mathematical formulation (variables, objective, constraints)  
**Stage 3**: Retrieve COPT API docs and Gurobi→COPT translation  
**Stage 4**: Generate executable COPT Python code  
**Stage 5**: Execute code, debug errors, verify answer (max 3 attempts)

## Configuration

Edit `scripts/run_data_collection.sh` to configure:
```bash
--input_file       # Input problem file (.jsonl)
--output_dir       # Output directory
--num_workers      # Parallel workers (default: 9)
--max_problems     # Limit number of problems (optional)
--kb_dir           # Knowledge base directory
```

## Results

Current performance on MAMO Complex LP (111 problems):
- **Multi-Agent Framework**: 61.3% correctness
- **Baseline (Direct Qwen)**: Run `./scripts/run_baseline.sh` to compare

## Requirements
```bash
pip install openai tqdm beautifulsoup4 requests sentence-transformers faiss-cpu
```

COPT solver must be installed for code execution.

## License

[Your License Here]