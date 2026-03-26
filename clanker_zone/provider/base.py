from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..models import ProviderRequest, ProviderResponse


class LLMProvider(ABC):
    @abstractmethod
    def build_request(self, *, system_prompt: str, user_prompt: str, metadata: Optional[dict] = None) -> ProviderRequest:
        raise NotImplementedError

    @abstractmethod
    def resolve_api_key(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        raise NotImplementedError
