from .base import AttackStrategy, AttackResult
from .roleplay import RoleplayStrategy
from .encoding import EncodingStrategy
from .logic_trap import LogicTrapStrategy
from .prefix_injection import PrefixInjectionStrategy
from .hypothetical import HypotheticalStrategy
from .multi_turn import MultiTurnStrategy
from .combination import CombinationStrategy
from .persona import PersonaStrategy
from .context_manipulation import ContextManipulationStrategy
from .novel import NovelStrategy

__all__ = [
    "AttackStrategy",
    "AttackResult",
    "RoleplayStrategy",
    "EncodingStrategy",
    "LogicTrapStrategy",
    "PrefixInjectionStrategy",
    "HypotheticalStrategy",
    "MultiTurnStrategy",
    "CombinationStrategy",
    "PersonaStrategy",
    "ContextManipulationStrategy",
    "NovelStrategy",
]

# Strategy registry - all available strategies
STRATEGIES = {
    "roleplay": RoleplayStrategy,
    "encoding": EncodingStrategy,
    "logic_trap": LogicTrapStrategy,
    "prefix_injection": PrefixInjectionStrategy,
    "hypothetical": HypotheticalStrategy,
    "multi_turn": MultiTurnStrategy,
    "combination": CombinationStrategy,
    "persona": PersonaStrategy,
    "context_manipulation": ContextManipulationStrategy,
    "novel": NovelStrategy,
}


def get_strategy(name: str) -> AttackStrategy:
    """Get strategy instance by name."""
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {name}. Available: {list(STRATEGIES.keys())}")
    return STRATEGIES[name]()


def get_all_strategies() -> list[AttackStrategy]:
    """Get instances of all available strategies."""
    return [cls() for cls in STRATEGIES.values()]


def get_total_variants() -> int:
    """Get total number of variants across all strategies."""
    return sum(len(s.variants) for s in get_all_strategies())


def list_all_variants() -> dict[str, list[str]]:
    """List all variants organized by strategy."""
    return {
        name: cls().variants
        for name, cls in STRATEGIES.items()
    }
