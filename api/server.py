"""FastAPI server for ARIA red-teaming agent."""

from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, "..")

from src.agent import ARIAAgent
from src.strategies import STRATEGIES
from src.memory import AttackMemory


# Global agent instance
agent: Optional[ARIAAgent] = None
memory: Optional[AttackMemory] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent on startup."""
    global agent, memory
    agent = ARIAAgent(
        use_llm_selection=False,
        use_reflexion=True,
        use_llm_evaluation=True,
    )
    memory = AttackMemory()
    yield
    # Cleanup
    if agent:
        agent.save_results()


app = FastAPI(
    title="ARIA - Automated Red-teaming Agent",
    description="API for automated LLM red-teaming and jailbreak testing",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models

class AttackRequest(BaseModel):
    """Request to execute a single attack."""
    behavior: str = Field(..., description="The forbidden behavior to elicit")
    strategy: Optional[str] = Field(None, description="Specific strategy to use")
    variant: Optional[str] = Field(None, description="Specific variant to use")


class CampaignRequest(BaseModel):
    """Request to run an attack campaign."""
    behaviors: list[str] = Field(..., description="List of behaviors to test")
    strategies: Optional[list[str]] = Field(None, description="Strategies to use")
    max_attempts: int = Field(5, description="Max attempts per behavior")
    stop_on_success: bool = Field(True, description="Stop after first success")


class AttackResponse(BaseModel):
    """Response from an attack attempt."""
    behavior: str
    strategy: str
    variant: str
    succeeded: bool
    confidence: float
    response_preview: str
    reflexion: Optional[str]


class CampaignStatus(BaseModel):
    """Status of a running campaign."""
    campaign_id: str
    status: str
    total_attacks: int
    successful_attacks: int
    current_behavior: Optional[str]


# Endpoints

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ARIA Red-teaming Agent",
        "version": "0.1.0",
    }


@app.get("/strategies")
async def list_strategies():
    """List available attack strategies."""
    strategies = []
    for name, cls in STRATEGIES.items():
        instance = cls()
        strategies.append({
            "name": name,
            "description": instance.description,
            "variants": instance.variants,
        })
    return {"strategies": strategies}


@app.post("/attack", response_model=AttackResponse)
async def execute_attack(request: AttackRequest):
    """Execute a single attack attempt."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        attempt = await agent.attack(
            behavior=request.behavior,
            strategy_name=request.strategy,
            variant=request.variant,
        )

        # Store in memory
        if memory:
            memory.store(
                behavior=attempt.behavior,
                strategy=attempt.strategy_selection.strategy_name,
                variant=attempt.strategy_selection.variant,
                attack_prompt=attempt.attack_result.attack_prompt,
                response=attempt.target_response.content,
                succeeded=attempt.evaluation.attack_succeeded,
                confidence=attempt.evaluation.confidence,
            )

        return AttackResponse(
            behavior=attempt.behavior,
            strategy=attempt.strategy_selection.strategy_name,
            variant=attempt.strategy_selection.variant,
            succeeded=attempt.evaluation.attack_succeeded,
            confidence=attempt.evaluation.confidence,
            response_preview=attempt.target_response.content[:300],
            reflexion=attempt.reflexion,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/campaign")
async def start_campaign(
    request: CampaignRequest,
    background_tasks: BackgroundTasks
):
    """Start an attack campaign (runs in background)."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # For now, run synchronously (could be improved with background tasks)
    try:
        attempts = await agent.campaign(
            behaviors=request.behaviors,
            strategies=request.strategies,
            max_attempts_per_behavior=request.max_attempts,
            stop_on_success=request.stop_on_success,
        )

        # Store all attempts in memory
        if memory:
            for attempt in attempts:
                memory.store(
                    behavior=attempt.behavior,
                    strategy=attempt.strategy_selection.strategy_name,
                    variant=attempt.strategy_selection.variant,
                    attack_prompt=attempt.attack_result.attack_prompt,
                    response=attempt.target_response.content,
                    succeeded=attempt.evaluation.attack_succeeded,
                    confidence=attempt.evaluation.confidence,
                )

        return {
            "status": "completed",
            "total_attacks": len(attempts),
            "successful_attacks": sum(1 for a in attempts if a.evaluation.attack_succeeded),
            "results": [
                {
                    "behavior": a.behavior[:50],
                    "strategy": a.strategy_selection.strategy_name,
                    "succeeded": a.evaluation.attack_succeeded,
                }
                for a in attempts
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Get current campaign metrics."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    return agent.metrics.get_summary()


@app.get("/metrics/by-strategy")
async def get_metrics_by_strategy():
    """Get ASR broken down by strategy."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    return {
        "asr_by_strategy": agent.metrics.asr_by_strategy(),
    }


@app.get("/successful-attacks")
async def get_successful_attacks():
    """Get all successful attacks."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    attacks = agent.get_successful_attacks()
    return {
        "count": len(attacks),
        "attacks": [
            {
                "behavior": a.behavior[:100],
                "strategy": a.strategy_selection.strategy_name,
                "variant": a.strategy_selection.variant,
                "attack_prompt": a.attack_result.attack_prompt[:300],
                "response_preview": a.target_response.content[:200],
            }
            for a in attacks
        ],
    }


@app.get("/memory/stats")
async def get_memory_stats():
    """Get attack memory statistics."""
    if not memory:
        raise HTTPException(status_code=503, detail="Memory not initialized")

    return memory.get_stats()


@app.get("/memory/similar/{behavior}")
async def find_similar_attacks(behavior: str, successful_only: bool = True):
    """Find attacks similar to the given behavior."""
    if not memory:
        raise HTTPException(status_code=503, detail="Memory not initialized")

    if successful_only:
        attacks = memory.find_similar_successful(behavior, n_results=5)
    else:
        attacks = memory.find_similar_failed(behavior, n_results=5)

    return {
        "query": behavior,
        "similar_attacks": [a.to_dict() for a in attacks],
    }


@app.post("/save")
async def save_results():
    """Save current results to file."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    filepath = agent.save_results()
    return {"saved_to": str(filepath)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
