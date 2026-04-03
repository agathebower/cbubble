"""Abstract LLM provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    success: bool
    error: str | None = None
    usage: dict | None = None


class BaseLLMProvider(ABC):
    def __init__(self, name, api_key, base_url, model, max_tokens=1024, temperature=0.3):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse: ...

    def __repr__(self):
        return f"<{self.__class__.__name__} model={self.model}>"
