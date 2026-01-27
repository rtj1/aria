"""Main ARIA agent for automated red-teaming."""

import asyncio
from typing import Optional
from datetime import datetime
from dataclasses import dataclass

from rich.console import Console
from rich.progress import Progress, TaskID

from ..config import get_settings
from ..targets import ClaudeTarget, TargetResponse
from ..strategies import get_strategy, get_all_strategies, AttackResult
from ..evaluation import ResponseEvaluator, EvaluationResult, MetricsTracker, AttackMetrics
from .strategy_selector import StrategySelector, StrategySelection
from .reflexion import ReflexionModule


@dataclass
class AttackAttempt:
    """Complete record of an attack attempt."""

    behavior: str
    strategy_selection: StrategySelection
    attack_result: AttackResult
    target_response: TargetResponse
    evaluation: EvaluationResult
    reflexion: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "behavior": self.behavior,
            "strategy": self.strategy_selection.strategy_name,
            "variant": self.strategy_selection.variant,
            "attack_prompt": self.attack_result.attack_prompt,
            "response": self.target_response.content[:500],
            "succeeded": self.evaluation.attack_succeeded,
            "confidence": self.evaluation.confidence,
            "latency_ms": self.target_response.latency_ms,
            "reflexion": self.reflexion,
            "timestamp": datetime.now().isoformat(),
        }


class ARIAAgent:
    """
    Automated Red-teaming & Iterative Attack Agent.

    Orchestrates the attack pipeline:
    1. Select strategy based on past results
    2. Generate attack prompt
    3. Send to target model
    4. Evaluate response
    5. Learn from results (reflexion)
    """

    def __init__(
        self,
        target_model: Optional[str] = None,
        use_llm_selection: bool = False,
        use_reflexion: bool = True,
        use_llm_evaluation: bool = True,
    ):
        """
        Initialize ARIA agent.

        Args:
            target_model: Claude model to attack (defaults to config)
            use_llm_selection: Use LLM for strategy selection
            use_reflexion: Enable learning from failures
            use_llm_evaluation: Use LLM for response evaluation
        """
        self.console = Console()
        self.target = ClaudeTarget(model=target_model)
        self.selector = StrategySelector(use_llm=use_llm_selection)
        self.evaluator = ResponseEvaluator(use_llm_evaluation=use_llm_evaluation)
        self.reflexion = ReflexionModule() if use_reflexion else None
        self.metrics = MetricsTracker()

        self._attack_history: list[AttackAttempt] = []

    async def attack(
        self,
        behavior: str,
        strategy_name: Optional[str] = None,
        variant: Optional[str] = None,
    ) -> AttackAttempt:
        """
        Execute a single attack attempt.

        Args:
            behavior: The forbidden behavior to elicit
            strategy_name: Specific strategy to use (or auto-select)
            variant: Specific variant to use (or auto-select)

        Returns:
            AttackAttempt with full results
        """
        # 1. Select strategy
        if strategy_name:
            strategy = self.selector.get_strategy(strategy_name)
            selection = StrategySelection(
                strategy_name=strategy_name,
                variant=variant or strategy.variants[0],
                reasoning="Manual selection",
                confidence=1.0,
            )
        else:
            past_results = [a.to_dict() for a in self._attack_history[-10:]]
            selection = self.selector.select(behavior, past_results)

        # 2. Generate attack prompt
        strategy = self.selector.get_strategy(selection.strategy_name)
        attack_result = strategy.generate(behavior, variant=selection.variant)

        # 3. Send to target
        response = await self.target.query(attack_result.attack_prompt)

        # 4. Evaluate response
        evaluation = self.evaluator.evaluate(
            response=response.content,
            original_behavior=behavior,
            attack_prompt=attack_result.attack_prompt,
        )

        # 5. Reflexion (learn from result)
        reflexion_text = None
        if self.reflexion and not evaluation.attack_succeeded:
            reflexion_text = self.reflexion.reflect(
                behavior=behavior,
                strategy=selection.strategy_name,
                variant=selection.variant,
                response=response.content,
                evaluation=evaluation,
            )

        # Record attempt
        attempt = AttackAttempt(
            behavior=behavior,
            strategy_selection=selection,
            attack_result=attack_result,
            target_response=response,
            evaluation=evaluation,
            reflexion=reflexion_text,
        )
        self._attack_history.append(attempt)

        # Track metrics
        self.metrics.record(AttackMetrics(
            behavior=behavior,
            strategy=selection.strategy_name,
            variant=selection.variant,
            succeeded=evaluation.attack_succeeded,
            confidence=evaluation.confidence,
            latency_ms=response.latency_ms,
            timestamp=datetime.now(),
            model=self.target.model_name,
            attack_prompt=attack_result.attack_prompt,
            response_preview=response.content[:200],
        ))

        return attempt

    async def campaign(
        self,
        behaviors: list[str],
        strategies: Optional[list[str]] = None,
        max_attempts_per_behavior: int = 5,
        stop_on_success: bool = True,
    ) -> list[AttackAttempt]:
        """
        Run a full attack campaign against multiple behaviors.

        Args:
            behaviors: List of forbidden behaviors to test
            strategies: Strategies to use (all if None)
            max_attempts_per_behavior: Max attacks per behavior
            stop_on_success: Stop attacking a behavior once successful

        Returns:
            List of all attack attempts
        """
        if strategies is None:
            strategies = [s.name for s in get_all_strategies()]

        all_attempts = []

        with Progress() as progress:
            task = progress.add_task(
                "[cyan]Running attack campaign...",
                total=len(behaviors) * max_attempts_per_behavior
            )

            for behavior in behaviors:
                behavior_attempts = 0
                succeeded = False

                for strategy_name in strategies:
                    if behavior_attempts >= max_attempts_per_behavior:
                        break
                    if stop_on_success and succeeded:
                        break

                    strategy = self.selector.get_strategy(strategy_name)

                    for variant in strategy.variants:
                        if behavior_attempts >= max_attempts_per_behavior:
                            break
                        if stop_on_success and succeeded:
                            break

                        attempt = await self.attack(
                            behavior=behavior,
                            strategy_name=strategy_name,
                            variant=variant,
                        )
                        all_attempts.append(attempt)
                        behavior_attempts += 1

                        if attempt.evaluation.attack_succeeded:
                            succeeded = True
                            self.console.print(
                                f"[green]SUCCESS[/green]: {strategy_name}/{variant} "
                                f"on '{behavior[:50]}...'"
                            )

                        progress.advance(task)

        return all_attempts

    def attack_sync(
        self,
        behavior: str,
        strategy_name: Optional[str] = None,
        variant: Optional[str] = None,
    ) -> AttackAttempt:
        """Synchronous wrapper for attack()."""
        return asyncio.run(self.attack(behavior, strategy_name, variant))

    def campaign_sync(
        self,
        behaviors: list[str],
        strategies: Optional[list[str]] = None,
        max_attempts_per_behavior: int = 5,
        stop_on_success: bool = True,
    ) -> list[AttackAttempt]:
        """Synchronous wrapper for campaign()."""
        return asyncio.run(self.campaign(
            behaviors, strategies, max_attempts_per_behavior, stop_on_success
        ))

    def get_successful_attacks(self) -> list[AttackAttempt]:
        """Get all successful attack attempts."""
        return [a for a in self._attack_history if a.evaluation.attack_succeeded]

    def print_summary(self):
        """Print campaign summary."""
        self.metrics.print_summary()

    def save_results(self, filename: Optional[str] = None):
        """Save results to file."""
        return self.metrics.save(filename)
