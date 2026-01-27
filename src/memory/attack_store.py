"""Attack memory using ChromaDB for similarity search."""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime
import json

import chromadb
from chromadb.config import Settings as ChromaSettings

from ..config import get_settings


@dataclass
class StoredAttack:
    """An attack stored in memory."""

    id: str
    behavior: str
    strategy: str
    variant: str
    attack_prompt: str
    response: str
    succeeded: bool
    confidence: float
    timestamp: str
    metadata: dict

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "behavior": self.behavior,
            "strategy": self.strategy,
            "variant": self.variant,
            "attack_prompt": self.attack_prompt,
            "response": self.response,
            "succeeded": self.succeeded,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class AttackMemory:
    """
    Persistent attack memory using ChromaDB.

    Stores successful and failed attacks for:
    1. Finding similar past attacks
    2. Learning from successful patterns
    3. Avoiding repeated failures
    """

    def __init__(self, persist_dir: Optional[str] = None):
        """
        Initialize attack memory.

        Args:
            persist_dir: Directory to persist ChromaDB (defaults to config)
        """
        settings = get_settings()
        persist_dir = persist_dir or settings.chroma_persist_dir

        self.client = chromadb.Client(ChromaSettings(
            persist_directory=persist_dir,
            anonymized_telemetry=False,
        ))

        # Collection for successful attacks
        self.successful = self.client.get_or_create_collection(
            name="successful_attacks",
            metadata={"description": "Attacks that bypassed safety measures"},
        )

        # Collection for failed attacks
        self.failed = self.client.get_or_create_collection(
            name="failed_attacks",
            metadata={"description": "Attacks that were blocked"},
        )

    def store(
        self,
        behavior: str,
        strategy: str,
        variant: str,
        attack_prompt: str,
        response: str,
        succeeded: bool,
        confidence: float,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Store an attack attempt.

        Args:
            behavior: Target behavior
            strategy: Strategy used
            variant: Variant used
            attack_prompt: The attack prompt
            response: Model's response
            succeeded: Whether attack succeeded
            confidence: Confidence score
            metadata: Additional metadata

        Returns:
            ID of stored attack
        """
        attack_id = f"{strategy}_{variant}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        doc_metadata = {
            "strategy": strategy,
            "variant": variant,
            "succeeded": succeeded,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "behavior_preview": behavior[:100],
            **(metadata or {}),
        }

        # Combine behavior and prompt for embedding
        document = f"BEHAVIOR: {behavior}\n\nATTACK: {attack_prompt}\n\nRESPONSE: {response[:500]}"

        collection = self.successful if succeeded else self.failed
        collection.add(
            ids=[attack_id],
            documents=[document],
            metadatas=[doc_metadata],
        )

        return attack_id

    def find_similar_successful(
        self,
        behavior: str,
        n_results: int = 5,
    ) -> list[StoredAttack]:
        """
        Find successful attacks similar to the given behavior.

        Args:
            behavior: Target behavior to match
            n_results: Number of results to return

        Returns:
            List of similar successful attacks
        """
        if self.successful.count() == 0:
            return []

        results = self.successful.query(
            query_texts=[behavior],
            n_results=min(n_results, self.successful.count()),
        )

        return self._parse_results(results)

    def find_similar_failed(
        self,
        behavior: str,
        strategy: Optional[str] = None,
        n_results: int = 5,
    ) -> list[StoredAttack]:
        """
        Find failed attacks similar to the given behavior.

        Args:
            behavior: Target behavior to match
            strategy: Filter by strategy (optional)
            n_results: Number of results to return

        Returns:
            List of similar failed attacks
        """
        if self.failed.count() == 0:
            return []

        where_filter = {"strategy": strategy} if strategy else None

        results = self.failed.query(
            query_texts=[behavior],
            n_results=min(n_results, self.failed.count()),
            where=where_filter,
        )

        return self._parse_results(results)

    def get_successful_strategies(self, behavior: str) -> list[tuple[str, str, float]]:
        """
        Get strategies that worked for similar behaviors.

        Returns:
            List of (strategy, variant, confidence) tuples
        """
        similar = self.find_similar_successful(behavior, n_results=10)

        strategies = []
        for attack in similar:
            strategies.append((
                attack.strategy,
                attack.variant,
                attack.confidence,
            ))

        return strategies

    def get_failed_strategies(self, behavior: str) -> list[tuple[str, str]]:
        """
        Get strategies that failed for similar behaviors.

        Returns:
            List of (strategy, variant) tuples to avoid
        """
        similar = self.find_similar_failed(behavior, n_results=10)

        return [(a.strategy, a.variant) for a in similar]

    def _parse_results(self, results: dict) -> list[StoredAttack]:
        """Parse ChromaDB results into StoredAttack objects."""
        attacks = []

        if not results["ids"] or not results["ids"][0]:
            return attacks

        for i, attack_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            document = results["documents"][0][i] if results["documents"] else ""

            # Parse document
            parts = document.split("\n\n")
            behavior = parts[0].replace("BEHAVIOR: ", "") if len(parts) > 0 else ""
            attack_prompt = parts[1].replace("ATTACK: ", "") if len(parts) > 1 else ""
            response = parts[2].replace("RESPONSE: ", "") if len(parts) > 2 else ""

            attacks.append(StoredAttack(
                id=attack_id,
                behavior=behavior,
                strategy=metadata.get("strategy", "unknown"),
                variant=metadata.get("variant", "unknown"),
                attack_prompt=attack_prompt,
                response=response,
                succeeded=metadata.get("succeeded", False),
                confidence=metadata.get("confidence", 0.0),
                timestamp=metadata.get("timestamp", ""),
                metadata=metadata,
            ))

        return attacks

    def get_stats(self) -> dict:
        """Get memory statistics."""
        return {
            "successful_attacks": self.successful.count(),
            "failed_attacks": self.failed.count(),
            "total_attacks": self.successful.count() + self.failed.count(),
        }

    def clear(self):
        """Clear all stored attacks."""
        self.client.delete_collection("successful_attacks")
        self.client.delete_collection("failed_attacks")

        self.successful = self.client.create_collection(
            name="successful_attacks",
            metadata={"description": "Attacks that bypassed safety measures"},
        )
        self.failed = self.client.create_collection(
            name="failed_attacks",
            metadata={"description": "Attacks that were blocked"},
        )
