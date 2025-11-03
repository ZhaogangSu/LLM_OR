"""
Abstract base class for all agents in the multi-agent framework.
Provides common functionality and enforces consistent interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from config.prompt_loader import PromptLoader
from core.llm_client import LLMClientPool


class BaseAgent(ABC):
    """
    Abstract base class for all agents
    
    All agents must implement the execute() method.
    Common functionality is provided through this base class.
    """
    
    def __init__(self, llm_client: LLMClientPool, config: Dict[str, Any]):
        """
        Initialize base agent
        
        Args:
            llm_client: LLM client pool for API calls
            config: Configuration dictionary
        """
        self.llm = llm_client
        self.config = config
        self.prompt_loader = PromptLoader(config.get('paths', {}).get('prompts_dir'))
        self.agent_name = self.__class__.__name__
        
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the agent's main task
        
        Args:
            **kwargs: Task-specific parameters
            
        Returns:
            Agent output (type varies by agent)
        """
        pass
    
    def _call_llm(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """
        Call LLM with retry logic
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            **kwargs: Additional LLM parameters
            
        Returns:
            str: LLM response
        """
        try:
            response = self.llm.call(system_prompt, user_prompt, **kwargs)
            return response
        except Exception as e:
            print(f"❌ {self.agent_name} LLM call failed: {e}")
            raise
    
    def _load_prompt(self, prompt_name: str) -> str:
        """
        Load prompt template from file
        
        Args:
            prompt_name: Name of prompt file (without .txt)
            
        Returns:
            str: Prompt content
        """
        return self.prompt_loader.load(prompt_name)
    
    def _format_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Load and format prompt with variables
        
        Args:
            prompt_name: Name of prompt file
            **kwargs: Variables to substitute
            
        Returns:
            str: Formatted prompt
        """
        return self.prompt_loader.format(prompt_name, **kwargs)
    
    def __repr__(self) -> str:
        return f"<{self.agent_name}>"


# Test
if __name__ == "__main__":
    print("BaseAgent is an abstract class and cannot be instantiated directly.")
    print("It provides the foundation for ModelingAgent, CodingAgent, etc.")
