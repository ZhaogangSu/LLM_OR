"""
Multi-agent framework for OR problem solving.
Clean, modular agents with single responsibilities.
"""

from .base_agent import BaseAgent
from .modeling_agent import ModelingAgent
from .coding_agent import CodingAgent
from .debugging_agent import DebuggingAgent
from .reference_agent import ReferenceAgent

__all__ = [
    'BaseAgent',
    'ModelingAgent',
    'CodingAgent',
    'DebuggingAgent',
    'ReferenceAgent'
]
