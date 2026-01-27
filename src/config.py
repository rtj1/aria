"""Configuration management for ARIA."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")

    # Target Model
    target_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        env="TARGET_MODEL"
    )

    # Request settings
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    timeout_seconds: int = Field(default=60, env="TIMEOUT_SECONDS")

    # ChromaDB
    chroma_persist_dir: str = Field(
        default="./data/chroma",
        env="CHROMA_PERSIST_DIR"
    )

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Paths
    project_root: Path = Path(__file__).parent.parent
    data_dir: Path = project_root / "data"
    results_dir: Path = project_root / "experiments" / "results"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Attack strategy types
class AttackStrategy:
    ROLEPLAY = "roleplay"
    ENCODING = "encoding"
    LOGIC_TRAP = "logic_trap"
    PREFIX_INJECTION = "prefix_injection"
    HYPOTHETICAL = "hypothetical"


# Behavior categories from StrongREJECT
class BehaviorCategory:
    ILLEGAL_GOODS = "illegal_goods"
    NON_VIOLENT_CRIMES = "non_violent_crimes"
    HATE_DISCRIMINATION = "hate_discrimination"
    DISINFORMATION = "disinformation"
    VIOLENCE = "violence"
    SEXUAL_CONTENT = "sexual_content"
