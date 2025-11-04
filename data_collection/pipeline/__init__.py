"""Pipeline orchestration"""
def __getattr__(name):
    if name == 'DataCollector': from .collector import DataCollector; return DataCollector
    elif name == 'DataFormatter': from .data_formatter import DataFormatter; return DataFormatter
    elif name == 'ParallelExecutor': from .parallel_executor import ParallelExecutor; return ParallelExecutor
    raise AttributeError(f"module 'pipeline' has no attribute '{name}'")
__all__ = ['DataCollector', 'DataFormatter', 'ParallelExecutor']
