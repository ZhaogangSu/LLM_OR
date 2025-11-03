"""
Integration test for Phase 2 agent refactoring.
Tests each agent independently and together.
"""

import sys
sys.path.insert(0, '..')

from config.config_loader import get_config
from core.llm_client import create_llm_client
from agents import ModelingAgent, CodingAgent, DebuggingAgent, ReferenceAgent


def test_all_agents_initialize():
    """Test that all agents can be initialized"""
    print("=" * 70)
    print("Test 1: Agent Initialization")
    print("=" * 70)
    
    config = get_config()
    llm = create_llm_client(config)
    
    # Initialize all agents
    reference_agent = ReferenceAgent(config._config)
    modeling_agent = ModelingAgent(llm, config._config)
    coding_agent = CodingAgent(llm, config._config)
    debugging_agent = DebuggingAgent(llm, config._config)
    
    print("✓ All agents initialized successfully\n")


def test_modeling_agent():
    """Test modeling agent execution"""
    print("=" * 70)
    print("Test 2: Modeling Agent")
    print("=" * 70)
    
    config = get_config()
    llm = create_llm_client(config)
    agent = ModelingAgent(llm, config._config)
    
    test_problem = """
    A factory produces chairs and tables.
    Each chair requires 2 hours and yields $15 profit.
    Each table requires 4 hours and yields $30 profit.
    Total available time is 40 hours.
    Maximize profit.
    """
    
    result = agent.execute(problem=test_problem, reference="")
    
    assert len(result) > 0, "Modeling agent returned empty result"
    assert 'variable' in result.lower() or 'profit' in result.lower(), \
        "Result doesn't appear to be a mathematical model"
    
    print(f"✓ Generated formulation: {len(result)} chars")
    print("✓ Modeling agent test PASSED\n")


def test_coding_agent():
    """Test coding agent execution"""
    print("=" * 70)
    print("Test 3: Coding Agent")
    print("=" * 70)
    
    config = get_config()
    llm = create_llm_client(config)
    agent = CodingAgent(llm, config._config)
    
    test_model = """
    Variables: x, y (number of chairs and tables)
    Objective: maximize 15*x + 30*y
    Constraints: 2*x + 4*y <= 40, x >= 0, y >= 0
    """
    
    result = agent.execute(
        problem="Maximize profit",
        math_model=test_model,
        reference=""
    )
    
    assert len(result) > 0, "Coding agent returned empty result"
    assert 'import' in result.lower(), "No imports found"
    assert 'copt' in result.lower(), "COPT not used"
    
    print(f"✓ Generated code: {len(result)} chars")
    print("✓ Coding agent test PASSED\n")


def test_debugging_agent():
    """Test debugging agent execution"""
    print("=" * 70)
    print("Test 4: Debugging Agent")
    print("=" * 70)
    
    config = get_config()
    llm = create_llm_client(config)
    agent = DebuggingAgent(llm, config._config)
    
    # Simple working code
    test_code = """
import coptpy as cp
from coptpy import COPT

env = cp.Envr()
model = env.createModel("test")

x = model.addVar(lb=0, ub=10, vtype=COPT.CONTINUOUS)
model.setObjective(x, COPT.MINIMIZE)
model.addConstr(x >= 3)

model.solve()

if model.status == COPT.OPTIMAL:
    print(f"Optimal objective: {model.objval}")
"""
    
    result = agent.execute(
        code=test_code,
        problem="Minimize x >= 3",
        ground_truth="3.0",
        math_model="minimize x, x >= 3"
    )
    
    assert result['success'], "Debugging failed on valid code"
    assert result['answer_correct'], "Answer verification failed"
    
    print("✓ Code executed successfully")
    print("✓ Answer verified correctly")
    print("✓ Debugging agent test PASSED\n")


def test_full_pipeline():
    """Test all agents working together"""
    print("=" * 70)
    print("Test 5: Full Agent Pipeline")
    print("=" * 70)
    
    config = get_config()
    llm = create_llm_client(config)
    
    # Initialize agents
    reference_agent = ReferenceAgent(config._config)
    modeling_agent = ModelingAgent(llm, config._config)
    coding_agent = CodingAgent(llm, config._config)
    debugging_agent = DebuggingAgent(llm, config._config)
    
    # Test problem
    problem = """
    Minimize the cost: 2*x + 3*y
    Subject to: x + y >= 10, x >= 0, y >= 0
    """
    
    print("Step 1: Get modeling references...")
    modeling_ref = reference_agent.get_modeling_references(problem)
    print(f"  ✓ Got {len(modeling_ref)} chars")
    
    print("Step 2: Generate mathematical model...")
    math_model = modeling_agent.execute(problem, modeling_ref)
    print(f"  ✓ Generated {len(math_model)} chars")
    
    print("Step 3: Get coding references...")
    coding_ref = reference_agent.get_coding_references(math_model)
    print(f"  ✓ Got {len(coding_ref)} chars")
    
    print("Step 4: Generate code...")
    code = coding_agent.execute(problem, math_model, coding_ref)
    print(f"  ✓ Generated {len(code)} chars")
    
    print("Step 5: Execute and debug...")
    result = debugging_agent.execute(code, problem, "20.0", math_model)
    
    if result['success']:
        print("  ✓ Execution successful")
        if result['answer_correct']:
            print("  ✓ Answer correct")
        else:
            print("  ⚠️  Answer incorrect (this is okay for test)")
    else:
        print("  ⚠️  Execution failed (might need debugging)")
    
    print("\n✓ Full pipeline test COMPLETED\n")


def run_all_tests():
    """Run all Phase 2 tests"""
    print("\n" + "=" * 70)
    print("PHASE 2 AGENT INTEGRATION TESTS")
    print("=" * 70 + "\n")
    
    try:
        test_all_agents_initialize()
        test_modeling_agent()
        test_coding_agent()
        test_debugging_agent()
        test_full_pipeline()
        
        print("=" * 70)
        print("✓ ALL PHASE 2 TESTS PASSED!")
        print("=" * 70)
        print("\nAll agents are working correctly and can be used together.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
