"""
Abstract LLM client interface with multiple provider implementations.
Enables easy switching between Qwen, OpenAI, DeepSeek, and Anthropic.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import time
from openai import OpenAI  # OpenAI-compatible client


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""

    def __init__(self, api_key: str, model: str, **kwargs):
        """
        Initialize LLM client

        Args:
            api_key: API key for the provider
            model: Model name
            **kwargs: Additional provider-specific config
        """
        self.api_key = api_key
        self.model = model
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_tokens = kwargs.get('max_tokens', 4000)
        self.timeout = kwargs.get('timeout', 60)
        self.max_retries = kwargs.get('max_retries', 3)

    @abstractmethod
    def call(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """
        Call the LLM with system and user prompts

        Args:
            system_prompt: System prompt (role/instructions)
            user_prompt: User prompt (actual query)
            **kwargs: Additional call-specific parameters

        Returns:
            str: LLM response text
        """
        pass

    def call_with_retry(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """
        Call LLM with exponential backoff retry logic

        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            **kwargs: Additional parameters

        Returns:
            str: LLM response

        Raises:
            Exception: If all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                return self.call(system_prompt, user_prompt, **kwargs)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"⚠️  LLM call failed (attempt {attempt+1}/{self.max_retries}): {e}")
                    print(f"   Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ All {self.max_retries} attempts failed")
                    raise


class QwenClient(BaseLLMClient):
    """Qwen (Alibaba Cloud) LLM client"""

    def __init__(self, api_key: str, model: str, base_url: str, **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def call(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Call Qwen API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=kwargs.get('temperature', self.temperature),
            max_tokens=kwargs.get('max_tokens', self.max_tokens),
            timeout=kwargs.get('timeout', self.timeout)
        )
        return str(response.choices[0].message.content)


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT client"""

    def __init__(self, api_key: str, model: str, base_url: str, **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def call(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Call OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=kwargs.get('temperature', self.temperature),
            max_tokens=kwargs.get('max_tokens', self.max_tokens),
            timeout=kwargs.get('timeout', self.timeout)
        )
        return str(response.choices[0].message.content)


class DeepSeekClient(BaseLLMClient):
    """DeepSeek LLM client"""

    def __init__(self, api_key: str, model: str, base_url: str, **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def call(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Call DeepSeek API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=kwargs.get('temperature', self.temperature),
            max_tokens=kwargs.get('max_tokens', self.max_tokens),
            timeout=kwargs.get('timeout', self.timeout)
        )
        return str(response.choices[0].message.content)


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude client"""

    def __init__(self, api_key: str, model: str, base_url: str, **kwargs):
        super().__init__(api_key, model, **kwargs)
        # Note: Anthropic uses a different SDK, but we'll use OpenAI-compatible mode if available
        # Otherwise, you'd import anthropic SDK here
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def call(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Call Anthropic API"""
        # If using native Anthropic SDK:
        # response = self.client.messages.create(
        #     model=self.model,
        #     system=system_prompt,
        #     messages=[{"role": "user", "content": user_prompt}],
        #     max_tokens=self.max_tokens,
        #     temperature=self.temperature
        # )
        # return response.content[0].text

        # Using OpenAI-compatible mode:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=kwargs.get('temperature', self.temperature),
            max_tokens=kwargs.get('max_tokens', self.max_tokens),
            timeout=kwargs.get('timeout', self.timeout)
        )
        return str(response.choices[0].message.content)


class LLMClientPool:
    """Pool of LLM clients for round-robin API key usage"""

    def __init__(self, provider: str, api_keys: List[str], config: Dict):
        """
        Initialize pool with multiple API keys

        Args:
            provider: LLM provider name
            api_keys: List of API keys
            config: Provider configuration dict
        """
        self.provider = provider
        self.clients = []
        self.current_idx = 0

        # Create client for each API key
        for api_key in api_keys:
            client = create_single_llm_client(provider, api_key, config)
            self.clients.append(client)

        print(f"✓ LLM Client Pool initialized: {provider} with {len(self.clients)} API keys")

    def get_client(self) -> BaseLLMClient:
        """Get next client in round-robin fashion"""
        client = self.clients[self.current_idx]
        self.current_idx = (self.current_idx + 1) % len(self.clients)
        return client

    def call(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Call LLM using next available client"""
        client = self.get_client()
        return client.call_with_retry(system_prompt, user_prompt, **kwargs)


def create_single_llm_client(provider: str, api_key: str, config: Dict) -> BaseLLMClient:
    """
    Factory function to create single LLM client

    Args:
        provider: Provider name (qwen, openai, deepseek, anthropic)
        api_key: API key
        config: Provider configuration

    Returns:
        BaseLLMClient instance

    Raises:
        ValueError: If provider is unknown
    """
    if provider == 'qwen':
        return QwenClient(api_key, **config)
    elif provider == 'openai':
        return OpenAIClient(api_key, **config)
    elif provider == 'deepseek':
        return DeepSeekClient(api_key, **config)
    elif provider == 'anthropic':
        return AnthropicClient(api_key, **config)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def create_llm_client(config_obj) -> LLMClientPool:
    """
    Factory function to create LLM client pool from config

    Args:
        config_obj: Config object with get_llm_config() and get_api_keys()

    Returns:
        LLMClientPool instance

    Example:
        >>> from config.config_loader import get_config
        >>> config = get_config()
        >>> llm = create_llm_client(config)
        >>> response = llm.call(system_prompt, user_prompt)
    """
    llm_config = config_obj.get_llm_config()
    api_keys = config_obj.get_api_keys()
    provider = llm_config.pop('provider')

    return LLMClientPool(provider, api_keys, llm_config)


# Test the implementation
if __name__ == "__main__":
    from config.config_loader import get_config

    # Load config
    config = get_config()

    # Create LLM client
    llm = create_llm_client(config)

    print("\n=== LLM Client Test ===")
    print(f"Provider: {llm.provider}")
    print(f"Number of clients: {len(llm.clients)}")

    # Test call
    try:
        response = llm.call(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'Hello, World!' and nothing else."
        )
        print(f"\nTest Response: {response}")
        print("\n✓ LLM client test passed!")
    except Exception as e:
        print(f"\n❌ LLM client test failed: {e}")
