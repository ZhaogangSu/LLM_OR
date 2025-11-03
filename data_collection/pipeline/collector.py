"""
Data Collector: Clean orchestrator for the multi-agent pipeline.

Responsibilities:
- Coordinate the 5-stage pipeline
- Call agents in correct order
- Return raw agent outputs

Does NOT:
- Format data (that's DataFormatter's job)
- Handle I/O (that's ParallelExecutor's job)
- Track progress (that's ParallelExecutor's job)
"""

from typing import Dict, Any
from agents import ModelingAgent, CodingAgent, DebuggingAgent, ReferenceAgent
from core.llm_client import LLMClientPool, create_llm_client
from config.config_loader import Config


class DataCollector:
    """
    Clean orchestrator for multi-agent OR problem solving

    The 5-stage pipeline:
    1. Reference Agent (modeling) - Get relevant examples
    2. Modeling Agent - Generate mathematical formulation
    3. Reference Agent (coding) - Get COPT API docs
    4. Coding Agent - Generate Python code
    5. Debugging Agent - Execute, debug, verify
    """

    def __init__(self, config: Config):
        """
        Initialize collector with all agents

        Args:
            config: Configuration object
        """
        self.config = config

        # Initialize LLM client
        self.llm = create_llm_client(config)

        # Initialize all agents
        self.reference_agent = ReferenceAgent(config._config)
        self.modeling_agent = ModelingAgent(self.llm, config._config)
        self.coding_agent = CodingAgent(self.llm, config._config)
        self.debugging_agent = DebuggingAgent(self.llm, config._config)

        print("✓ DataCollector initialized with all agents")

    def collect_single_problem(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process single OR problem through multi-agent pipeline

        Args:
            problem: Dict with keys:
                - id: Problem identifier
                - en_question: Problem description in English
                - en_answer: Ground truth answer

        Returns:
            Dict with keys:
                - problem_id: Original problem ID
                - problem: Original problem text
                - ground_truth: Expected answer
                - stage1_modeling_reference: Reference for modeling
                - stage2_math_model: Mathematical formulation
                - stage3_coding_reference: Reference for coding
                - stage4_initial_code: Generated code
                - stage5_debug_result: Debugging results with final code
                - success: Overall success boolean
                - answer_correct: Answer correctness boolean
        """
        problem_id = problem.get('id', 'unknown')
        question = problem.get('en_question', problem.get('zh_question', ''))
        ground_truth = problem.get('en_answer', problem.get('zh_answer', ''))

        print(f"\n{'='*70}")
        print(f"Processing Problem ID: {problem_id}")
        print(f"{'='*70}")

        # Stage 1: Reference Agent (Modeling)
        print("  [Stage 1/5] Reference Agent - Modeling...")
        modeling_reference = self.reference_agent.get_modeling_references(question)

        # Stage 2: Modeling Agent
        print("  [Stage 2/5] Modeling Agent...")
        math_model = self.modeling_agent.execute(
            problem=question,
            reference=modeling_reference
        )

        # Stage 3: Reference Agent (Coding)
        print("  [Stage 3/5] Reference Agent - Coding...")
        coding_reference = self.reference_agent.get_coding_references(math_model)

        # Stage 4: Coding Agent
        print("  [Stage 4/5] Coding Agent...")
        initial_code = self.coding_agent.execute(
            problem=question,
            math_model=math_model,
            reference=coding_reference
        )

        # Stage 5: Debugging Agent
        print("  [Stage 5/5] Debugging Agent...")
        debug_result = self.debugging_agent.execute(
            code=initial_code,
            problem=question,
            ground_truth=ground_truth,
            math_model=math_model
        )

        # Collect all outputs
        result = {
            'problem_id': problem_id,
            'problem': question,
            'ground_truth': ground_truth,

            # Stage outputs
            'stage1_modeling_reference': modeling_reference,
            'stage2_math_model': math_model,
            'stage3_coding_reference': coding_reference,
            'stage4_initial_code': initial_code,
            'stage5_debug_result': debug_result,

            # Success metrics
            'success': debug_result['success'],
            'answer_correct': debug_result.get('answer_correct', False)
        }

        status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
        correct = "✓ CORRECT" if result['answer_correct'] else "✗ WRONG"
        print(f"\n  Result: {status} | Answer: {correct}")

        return result


# Test
if __name__ == "__main__":
    from config.config_loader import get_config

    print("=== Data Collector Test ===\n")

    # Initialize
    config = get_config()
    collector = DataCollector(config)

    # Test problem
    test_problem = {
        'id': 'test_001',
        'en_question': """
        A company makes chairs and tables.
        Each chair takes 2 hours and earns $15 profit.
        Each table takes 4 hours and earns $30 profit.
        Total time available: 40 hours.
        How much maximum profit can be earned?
        """,
        'en_answer': '300'  # 10 tables = 10 * 30 = 300
    }

    # Run collection
    try:
        result = collector.collect_single_problem(test_problem)

        print("\n" + "="*70)
        print("Collection Complete")
        print("="*70)
        print(f"Problem ID: {result['problem_id']}")
        print(f"Success: {result['success']}")
        print(f"Answer Correct: {result['answer_correct']}")
        print(f"\nStages completed:")
        print(f"  1. Modeling reference: {len(result['stage1_modeling_reference'])} chars")
        print(f"  2. Math model: {len(result['stage2_math_model'])} chars")
        print(f"  3. Coding reference: {len(result['stage3_coding_reference'])} chars")
        print(f"  4. Initial code: {len(result['stage4_initial_code'])} chars")
        print(f"  5. Debug attempts: {result['stage5_debug_result']['attempts']}")

        print("\n✓ DataCollector test passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
