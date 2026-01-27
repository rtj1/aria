"""Base class for target LLM APIs."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class TargetResponse:
    """Response from a target LLM."""

    content: str
    model: str
    refused: bool
    refusal_reason: Optional[str]
    latency_ms: float
    timestamp: datetime
    raw_response: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "model": self.model,
            "refused": self.refused,
            "refusal_reason": self.refusal_reason,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat(),
        }


class TargetLLM(ABC):
    """Abstract base class for target LLM APIs."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier."""
        pass

    @abstractmethod
    async def query(self, prompt: str, system_prompt: Optional[str] = None) -> TargetResponse:
        """
        Send a prompt to the target LLM and get response.

        Args:
            prompt: The user message/attack prompt
            system_prompt: Optional system prompt

        Returns:
            TargetResponse with content and metadata
        """
        pass

    @abstractmethod
    def detect_refusal(self, response: str) -> tuple[bool, Optional[str]]:
        """
        Detect if the model refused to respond.

        Args:
            response: The model's response text

        Returns:
            Tuple of (refused: bool, reason: Optional[str])
        """
        pass
