"""Metrics tracking for attack campaigns."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from collections import defaultdict
import json
from pathlib import Path


@dataclass
class AttackMetrics:
    """Metrics for a single attack attempt."""

    behavior: str
    strategy: str
    variant: str
    succeeded: bool
    confidence: float
    latency_ms: float
    timestamp: datetime
    model: str
    attack_prompt: str
    response_preview: str

    def to_dict(self) -> dict:
        return {
            "behavior": self.behavior,
            "strategy": self.strategy,
            "variant": self.variant,
            "succeeded": self.succeeded,
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
            "attack_prompt": self.attack_prompt[:200],
            "response_preview": self.response_preview[:200],
        }


class MetricsTracker:
    """Tracks and aggregates attack metrics."""

    def __init__(self, results_dir: Optional[Path] = None):
        self.results_dir = results_dir or Path("./experiments/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.attacks: list[AttackMetrics] = []
        self._by_strategy: dict[str, list[AttackMetrics]] = defaultdict(list)
        self._by_behavior: dict[str, list[AttackMetrics]] = defaultdict(list)
        self._by_model: dict[str, list[AttackMetrics]] = defaultdict(list)

    def record(self, metrics: AttackMetrics):
        """Record a new attack attempt."""
        self.attacks.append(metrics)
        self._by_strategy[metrics.strategy].append(metrics)
        self._by_behavior[metrics.behavior].append(metrics)
        self._by_model[metrics.model].append(metrics)

    @property
    def total_attacks(self) -> int:
        return len(self.attacks)

    @property
    def successful_attacks(self) -> int:
        return sum(1 for a in self.attacks if a.succeeded)

    @property
    def overall_asr(self) -> float:
        """Overall Attack Success Rate."""
        if not self.attacks:
            return 0.0
        return self.successful_attacks / self.total_attacks

    def asr_by_strategy(self) -> dict[str, float]:
        """ASR broken down by strategy."""
        result = {}
        for strategy, attacks in self._by_strategy.items():
            if attacks:
                succeeded = sum(1 for a in attacks if a.succeeded)
                result[strategy] = succeeded / len(attacks)
        return result

    def asr_by_variant(self, strategy: str) -> dict[str, float]:
        """ASR broken down by variant within a strategy."""
        attacks = self._by_strategy.get(strategy, [])
        by_variant: dict[str, list[AttackMetrics]] = defaultdict(list)
        for a in attacks:
            by_variant[a.variant].append(a)

        result = {}
        for variant, variant_attacks in by_variant.items():
            if variant_attacks:
                succeeded = sum(1 for a in variant_attacks if a.succeeded)
                result[variant] = succeeded / len(variant_attacks)
        return result

    def asr_by_behavior(self) -> dict[str, float]:
        """ASR broken down by target behavior."""
        result = {}
        for behavior, attacks in self._by_behavior.items():
            if attacks:
                succeeded = sum(1 for a in attacks if a.succeeded)
                result[behavior] = succeeded / len(attacks)
        return result

    def average_latency(self) -> float:
        """Average response latency in ms."""
        if not self.attacks:
            return 0.0
        return sum(a.latency_ms for a in self.attacks) / len(self.attacks)

    def get_successful_attacks(self) -> list[AttackMetrics]:
        """Get all successful attacks."""
        return [a for a in self.attacks if a.succeeded]

    def get_summary(self) -> dict:
        """Get comprehensive summary statistics."""
        return {
            "total_attacks": self.total_attacks,
            "successful_attacks": self.successful_attacks,
            "overall_asr": round(self.overall_asr, 4),
            "asr_by_strategy": {k: round(v, 4) for k, v in self.asr_by_strategy().items()},
            "average_latency_ms": round(self.average_latency(), 2),
            "strategies_tested": list(self._by_strategy.keys()),
            "behaviors_tested": len(self._by_behavior),
            "models_tested": list(self._by_model.keys()),
        }

    def save(self, filename: Optional[str] = None):
        """Save metrics to JSON file."""
        if filename is None:
            filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.results_dir / filename
        data = {
            "summary": self.get_summary(),
            "attacks": [a.to_dict() for a in self.attacks],
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return filepath

    def load(self, filepath: Path):
        """Load metrics from JSON file."""
        with open(filepath) as f:
            data = json.load(f)

        for attack_data in data.get("attacks", []):
            metrics = AttackMetrics(
                behavior=attack_data["behavior"],
                strategy=attack_data["strategy"],
                variant=attack_data["variant"],
                succeeded=attack_data["succeeded"],
                confidence=attack_data["confidence"],
                latency_ms=attack_data["latency_ms"],
                timestamp=datetime.fromisoformat(attack_data["timestamp"]),
                model=attack_data["model"],
                attack_prompt=attack_data["attack_prompt"],
                response_preview=attack_data["response_preview"],
            )
            self.record(metrics)

    def print_summary(self):
        """Print formatted summary to console."""
        from rich.console import Console
        from rich.table import Table

        console = Console()
        summary = self.get_summary()

        console.print("\n[bold]ARIA Attack Campaign Summary[/bold]\n")

        # Overall stats
        table = Table(title="Overall Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Attacks", str(summary["total_attacks"]))
        table.add_row("Successful Attacks", str(summary["successful_attacks"]))
        table.add_row("Overall ASR", f"{summary['overall_asr']:.2%}")
        table.add_row("Avg Latency", f"{summary['average_latency_ms']:.0f}ms")

        console.print(table)

        # ASR by strategy
        if summary["asr_by_strategy"]:
            strat_table = Table(title="\nASR by Strategy")
            strat_table.add_column("Strategy", style="cyan")
            strat_table.add_column("ASR", style="green")

            for strategy, asr in sorted(
                summary["asr_by_strategy"].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                strat_table.add_row(strategy, f"{asr:.2%}")

            console.print(strat_table)
