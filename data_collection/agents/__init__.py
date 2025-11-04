"""Multi-agent framework"""
def __getattr__(name):
    if name == 'BaseAgent': from .base_agent import BaseAgent; return BaseAgent
    elif name == 'ModelingAgent': from .modeling_agent import ModelingAgent; return ModelingAgent
    elif name == 'CodingAgent': from .coding_agent import CodingAgent; return CodingAgent
    elif name == 'DebuggingAgent': from .debugging_agent import DebuggingAgent; return DebuggingAgent
    elif name == 'ReferenceAgent': from .reference_agent import ReferenceAgent; return ReferenceAgent
    raise AttributeError(f"module 'agents' has no attribute '{name}'")
__all__ = ['BaseAgent', 'ModelingAgent', 'CodingAgent', 'DebuggingAgent', 'ReferenceAgent']
