"""Base class for attack strategies."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class AttackResult:
    """Result of an attack attempt."""

    original_behavior: str
    strategy_name: str
    attack_prompt: str
    variant: str
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "original_behavior": self.original_behavior,
            "strategy_name": self.strategy_name,
            "attack_prompt": self.attack_prompt,
            "variant": self.variant,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class AttackStrategy(ABC):
    """Abstract base class for attack strategies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the strategy."""
        pass

    @property
    @abstractmethod
    def variants(self) -> list[str]:
        """List of available variants for this strategy."""
        pass

    @abstractmethod
    def generate(
        self,
        behavior: str,
        variant: Optional[str] = None,
        **kwargs
    ) -> AttackResult:
        """
        Generate an attack prompt for the given behavior.

        Args:
            behavior: The forbidden behavior to elicit
            variant: Specific variant to use (random if None)
            **kwargs: Additional strategy-specific parameters

        Returns:
            AttackResult containing the generated attack prompt
        """
        pass

    def generate_all_variants(self, behavior: str, **kwargs) -> list[AttackResult]:
        """Generate attacks using all variants."""
        return [
            self.generate(behavior, variant=v, **kwargs)
            for v in self.variants
        ]
