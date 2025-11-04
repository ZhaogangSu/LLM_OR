"""
Core utilities for data collection system.
Low-level components with no business logic.
"""

def __getattr__(name):
    """Lazy import to avoid circular dependencies and module conflicts"""
    if name == 'BaseLLMClient':
        from .llm_client import BaseLLMClient
        return BaseLLMClient
    elif name == 'create_llm_client':
        from .llm_client import create_llm_client
        return create_llm_client
    elif name == 'CodeExecutor':
        from .code_executor import CodeExecutor
        return CodeExecutor
    elif name == 'check_answer_correctness':
        from .answer_checker import check_answer_correctness
        return check_answer_correctness
    raise AttributeError(f"module 'core' has no attribute '{name}'")

__all__ = [
    'BaseLLMClient',
    'create_llm_client',
    'CodeExecutor',
    'check_answer_correctness'
]