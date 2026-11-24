import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from app.models import DimensionScore, FlaggedClaim
from app.utils.groq_client import groq_client

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all judge agents."""

    @property
    @abstractmethod
    def dimension_name(self) -> str:
        """Name of the evaluation dimension."""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt that defines the agent's role and evaluation criteria."""
        pass

    def _build_user_prompt(self, question: str, ai_response: str, reference: Optional[str] = None) -> str:
        """Build the user prompt from evaluation inputs."""
        prompt = f"""Please evaluate the following AI response:

**Question Asked:**
{question}

**AI Response to Evaluate:**
{ai_response}
"""
        if reference:
            prompt += f"""
**Reference Answer / Source Document:**
{reference}
"""
        else:
            prompt += """
**Reference Answer:** Not provided. Evaluate based on the response's internal consistency and general knowledge.
"""
        prompt += """
Respond ONLY with a valid JSON object. Do not include any text outside the JSON.
"""
        return prompt

    async def evaluate(self, question: str, ai_response: str, reference: Optional[str] = None) -> DimensionScore:
        """Evaluate a response and return a dimension score.

        Args:
            question: The question that was asked.
            ai_response: The AI-generated response to evaluate.
            reference: Optional reference answer or source document.

        Returns:
            DimensionScore with score, reasoning, and details.
        """
        try:
            user_prompt = self._build_user_prompt(question, ai_response, reference)
            result = await groq_client.parse_json_response(self.system_prompt, user_prompt)
            return self._parse_result(result)
        except Exception as e:
            logger.error(f"{self.dimension_name} agent failed: {e}")
            return DimensionScore(
                dimension=self.dimension_name,
                score=5.0,
                reasoning=f"Evaluation failed due to an error: {str(e)}. A default score of 5 has been assigned.",
                details=["Agent encountered an error during evaluation."],
            )

    def _parse_result(self, result: dict) -> DimensionScore:
        """Parse the LLM JSON response into a DimensionScore."""
        score = float(result.get("score", 5))
        score = max(1.0, min(10.0, score))

        reasoning = result.get("reasoning", "No reasoning provided.")
        details = result.get("details", [])

        if isinstance(details, str):
            details = [details]

        # Handle flagged_claims for hallucination agent
        flagged_claims = None
        if "flagged_claims" in result and result["flagged_claims"]:
            flagged_claims = []
            for claim in result["flagged_claims"]:
                if isinstance(claim, dict):
                    flagged_claims.append(FlaggedClaim(
                        claim=claim.get("claim", ""),
                        status=claim.get("status", "unknown"),
                        evidence=claim.get("evidence", ""),
                    ))

        return DimensionScore(
            dimension=self.dimension_name,
            score=score,
            reasoning=reasoning,
            details=details,
            flagged_claims=flagged_claims,
        )
