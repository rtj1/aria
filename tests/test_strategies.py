"""Tests for attack strategies."""

import pytest

from src.strategies import (
    get_strategy,
    get_all_strategies,
    RoleplayStrategy,
    EncodingStrategy,
    LogicTrapStrategy,
    PrefixInjectionStrategy,
    HypotheticalStrategy,
)


class TestStrategyRegistry:
    """Test strategy registry functions."""

    def test_get_all_strategies(self):
        """Should return all strategy instances."""
        strategies = get_all_strategies()
        assert len(strategies) == 5
        assert all(hasattr(s, "generate") for s in strategies)

    def test_get_strategy_by_name(self):
        """Should get strategy by name."""
        strategy = get_strategy("roleplay")
        assert isinstance(strategy, RoleplayStrategy)

    def test_get_unknown_strategy(self):
        """Should raise for unknown strategy."""
        with pytest.raises(ValueError):
            get_strategy("unknown")


class TestRoleplayStrategy:
    """Test roleplay attack strategy."""

    def test_generate_basic(self):
        """Should generate roleplay attack."""
        strategy = RoleplayStrategy()
        result = strategy.generate("do something harmful")

        assert result.strategy_name == "roleplay"
        assert result.original_behavior == "do something harmful"
        assert "do something harmful" in result.attack_prompt.lower() or "harmful" in result.attack_prompt.lower()

    def test_generate_with_variant(self):
        """Should use specified variant."""
        strategy = RoleplayStrategy()
        result = strategy.generate("test behavior", variant="author")

        assert result.variant == "author"
        assert "novel" in result.attack_prompt.lower() or "book" in result.attack_prompt.lower()

    def test_all_variants(self):
        """Should generate all variants."""
        strategy = RoleplayStrategy()
        results = strategy.generate_all_variants("test behavior")

        assert len(results) == len(strategy.variants)


class TestEncodingStrategy:
    """Test encoding attack strategy."""

    def test_base64_encoding(self):
        """Should generate base64 attack."""
        strategy = EncodingStrategy()
        result = strategy.generate("test behavior", variant="base64")

        assert result.variant == "base64"
        assert "base64" in result.attack_prompt.lower()

    def test_rot13_encoding(self):
        """Should generate ROT13 attack."""
        strategy = EncodingStrategy()
        result = strategy.generate("test behavior", variant="rot13")

        assert result.variant == "rot13"
        assert "rot13" in result.attack_prompt.lower()


class TestLogicTrapStrategy:
    """Test logic trap attack strategy."""

    def test_generate_logic_trap(self):
        """Should generate logic trap attack."""
        strategy = LogicTrapStrategy()
        result = strategy.generate("test behavior")

        assert result.strategy_name == "logic_trap"
        assert len(result.attack_prompt) > 50


class TestHypotheticalStrategy:
    """Test hypothetical attack strategy."""

    def test_thought_experiment(self):
        """Should generate thought experiment."""
        strategy = HypotheticalStrategy()
        result = strategy.generate("test behavior", variant="thought_experiment")

        assert "hypothetical" in result.attack_prompt.lower() or "thought" in result.attack_prompt.lower()
