"""
MR.GREEN — Verifier

Verifies whether the agent's response adequately addresses the user's request.
Acts as the final quality gate before returning a response.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of verifying an agent response."""
    is_valid: bool
    reason: str = ""
    confidence: float = 1.0


class Verifier:
    """
    Verifies the quality and correctness of agent responses.

    For Milestone 1: Basic validation (non-empty, reasonable length).
    Future: Will use AI to verify response quality, factual accuracy,
    and whether the response actually addresses the user's question.
    """

    async def verify_response(
        self,
        user_message: str,
        response: str,
    ) -> VerificationResult:
        """Verify that the response is valid and addresses the user's request."""
        # Basic validation
        if not response or not response.strip():
            return VerificationResult(
                is_valid=False,
                reason="Response is empty",
                confidence=1.0,
            )

        if len(response.strip()) < 2:
            return VerificationResult(
                is_valid=False,
                reason="Response is too short",
                confidence=0.9,
            )

        return VerificationResult(
            is_valid=True,
            reason="Response passes basic validation",
            confidence=0.8,
        )
