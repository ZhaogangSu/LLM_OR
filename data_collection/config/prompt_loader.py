"""
Prompt loader utility for loading prompts from text files.
"""

import os
from pathlib import Path
from typing import Dict


class PromptLoader:
    """Load and manage prompts from text files"""

    def __init__(self, prompts_dir: str = None):
        """
        Initialize prompt loader

        Args:
            prompts_dir: Directory containing prompt files
        """
        if prompts_dir is None:
            # Default to config/prompts
            root_dir = Path(__file__).parent.parent.absolute()
            prompts_dir = root_dir / "config" / "prompts"

        self.prompts_dir = Path(prompts_dir)
        self._cache = {}

        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")

        print(f"✓ Prompt loader initialized: {self.prompts_dir}")

    def load(self, prompt_name: str) -> str:
        """
        Load prompt from file with caching

        Args:
            prompt_name: Name of prompt file (without .txt)

        Returns:
            str: Prompt content

        Example:
            >>> loader.load('modeling_agent_system')
            'You are an expert in Operations Research...'
        """
        if prompt_name in self._cache:
            return self._cache[prompt_name]

        prompt_file = self.prompts_dir / f"{prompt_name}.txt"

        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        self._cache[prompt_name] = content
        return content

    def format(self, prompt_name: str, **kwargs) -> str:
        """
        Load and format prompt with variables

        Args:
            prompt_name: Name of prompt file
            **kwargs: Variables to substitute in prompt

        Returns:
            str: Formatted prompt

        Example:
            >>> loader.format('modeling_agent_user',
            ...               problem="Maximize profit...",
            ...               reference="Example 1...")
        """
        template = self.load(prompt_name)
        return template.format(**kwargs)

    def list_prompts(self) -> list:
        """List all available prompts"""
        prompts = []
        for file in self.prompts_dir.glob("*.txt"):
            prompts.append(file.stem)
        return sorted(prompts)


# Test
if __name__ == "__main__":
    loader = PromptLoader()

    print("=== Available Prompts ===")
    for prompt in loader.list_prompts():
        print(f"  - {prompt}")

    print("\n=== Load and Format Test ===")
    try:
        system = loader.load('modeling_agent_system')
        print(f"System prompt length: {len(system)} chars")

        user = loader.format(
            'modeling_agent_user',
            problem="Test problem",
            reference="Test reference"
        )
        print(f"Formatted user prompt length: {len(user)} chars")
        print("\n✓ Prompt loader test passed")
    except Exception as e:
        print(f"❌ Test failed: {e}")
