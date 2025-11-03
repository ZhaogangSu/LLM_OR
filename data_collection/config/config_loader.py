"""
Configuration loader for data collection system.
Loads config.yaml and provides validated access to all settings.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Configuration manager for data collection"""

    def __init__(self, config_path: str = None):
        """
        Initialize configuration from YAML file

        Args:
            config_path: Path to config.yaml (default: config/config.yaml)
        """
        if config_path is None:
            # Get data_collection root directory
            self.root_dir = Path(__file__).parent.parent.absolute()
            config_path = self.root_dir / "config" / "config.yaml"
        else:
            self.root_dir = Path(__file__).parent.parent.absolute()
            config_path = Path(config_path)

        # Load YAML
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

        # Resolve paths
        self._resolve_paths()

        print(f"✓ Configuration loaded from: {config_path}")

    def _resolve_paths(self):
        """Convert all relative paths to absolute paths"""
        paths = self._config.get('paths', {})
        kb = self._config.get('knowledge_base', {})

        # Resolve paths section
        for key, value in paths.items():
            if isinstance(value, str):
                paths[key] = str(self.root_dir / value)

        # Resolve knowledge base paths
        for key, value in kb.items():
            if isinstance(value, str):
                kb[key] = str(self.root_dir / value)

    def get(self, key_path: str, default=None) -> Any:
        """
        Get configuration value using dot notation

        Args:
            key_path: Dot-separated path (e.g., 'llm.provider')
            default: Default value if key not found

        Returns:
            Configuration value

        Example:
            >>> config.get('llm.provider')
            'qwen'
            >>> config.get('llm.qwen.model')
            'qwen-max'
        """
        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_llm_config(self) -> Dict[str, Any]:
        """Get complete LLM configuration for active provider"""
        provider = self.get('llm.provider')
        provider_config = self.get(f'llm.{provider}')

        if provider_config is None:
            raise ValueError(f"No configuration found for provider: {provider}")

        return {
            'provider': provider,
            **provider_config
        }

    def get_api_keys(self) -> list:
        """Load API keys from file"""
        api_keys_path = self.get('paths.api_keys_file')

        if not os.path.exists(api_keys_path):
            raise FileNotFoundError(f"API keys file not found: {api_keys_path}")

        with open(api_keys_path, 'r') as f:
            keys = [line.strip() for line in f if line.strip()]

        if not keys:
            raise ValueError("No API keys found in API_keys.txt")

        return keys

    def validate(self):
        """Validate that all required configuration exists"""
        required_keys = [
            'llm.provider',
            'paths.prompts_dir',
            'paths.api_keys_file',
            'knowledge_base.gurobi_index',
            'knowledge_base.copt_kb_dir',
            'pipeline.max_debug_attempts'
        ]

        missing = []
        for key in required_keys:
            if self.get(key) is None:
                missing.append(key)

        if missing:
            raise ValueError(f"Missing required config keys: {missing}")

        print("✓ Configuration validation passed")

    @property
    def llm_provider(self) -> str:
        """Get active LLM provider"""
        return self.get('llm.provider')

    @property
    def prompts_dir(self) -> str:
        """Get prompts directory path"""
        return self.get('paths.prompts_dir')

    @property
    def kb_config(self) -> Dict[str, str]:
        """Get knowledge base configuration"""
        return self._config.get('knowledge_base', {})

    @property
    def pipeline_config(self) -> Dict[str, Any]:
        """Get pipeline configuration"""
        return self._config.get('pipeline', {})


# Singleton instance for easy import
_config_instance = None

def get_config(config_path: str = None) -> Config:
    """Get or create config singleton"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance


# Usage example
if __name__ == "__main__":
    # Test configuration loading
    config = Config()
    config.validate()

    print("\n=== Configuration Test ===")
    print(f"LLM Provider: {config.llm_provider}")
    print(f"Model: {config.get('llm.qwen.model')}")
    print(f"Prompts dir: {config.prompts_dir}")
    print(f"API Keys count: {len(config.get_api_keys())}")
    print(f"\nLLM Config: {config.get_llm_config()}")
