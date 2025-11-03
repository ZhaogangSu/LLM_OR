"""
Pipeline orchestration for multi-agent OR problem solving.

Components:
- Collector: Orchestrates the 5-stage agent pipeline
- DataFormatter: Formats agent outputs into training data
- ParallelExecutor: Runs collection in parallel with progress tracking
"""

from .collector import DataCollector
from .data_formatter import DataFormatter
from .parallel_executor import ParallelExecutor

__all__ = [
    'DataCollector',
    'DataFormatter',
    'ParallelExecutor'
]
