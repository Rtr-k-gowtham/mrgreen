"""
MR.GREEN — Health Check Route

GET /health — Returns system health status including AI provider connectivity.
"""

from fastapi import APIRouter, Depends

from app.ai.provider import AIProvider
from app.api.dependencies import get_ai_provider

router = APIRouter()


@router.get("/health")
async def health_check(
    ai_provider: AIProvider = Depends(get_ai_provider),
) -> dict:
    """
    System health check.

    Returns the overall health status and checks:
    - API is running
    - AI provider (Ollama) is reachable
    - Model is available
    """
    ai_health = await ai_provider.health_check()

    overall_status = "healthy" if ai_health.get("status") == "healthy" else "degraded"

    return {
        "status": overall_status,
        "service": "MR.GREEN",
        "components": {
            "api": {"status": "healthy"},
            "ai": ai_health,
        },
    }
