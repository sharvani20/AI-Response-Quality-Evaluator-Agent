import json
import logging
from typing import Optional

from app.models import DimensionScore, QualityTier
from app.utils.groq_client import groq_client
from app.config import settings

logger = logging.getLogger(__name__)


class VerdictAgent:
    """Aggregates individual dimension scores into an overall quality verdict."""

    def _get_quality_tier(self, score: float) -> QualityTier:
        """Determine quality tier from overall score."""
        if score >= 9.0:
            return QualityTier.EXCELLENT
        elif score >= 7.0:
            return QualityTier.GOOD
        elif score >= 5.0:
            return QualityTier.FAIR
        elif score >= 3.0:
            return QualityTier.POOR
        else:
            return QualityTier.FAILING

    async def aggregate(
        self,
        relevance: DimensionScore,
        accuracy: DimensionScore,
        hallucination: DimensionScore,
        completeness: DimensionScore,
    ) -> dict:
        """Aggregate dimension scores into an overall verdict.

        Args:
            relevance: Score from the Relevance Judge Agent.
            accuracy: Score from the Accuracy Judge Agent.
            hallucination: Score from the Hallucination Detection Agent.
            completeness: Score from the Completeness Judge Agent.

        Returns:
            Dictionary with overall_score, quality_tier, verdict_reasoning, recommendations.
        """
        # Calculate weighted score
        overall_score = round(
            relevance.score * settings.WEIGHT_RELEVANCE
            + accuracy.score * settings.WEIGHT_ACCURACY
            + hallucination.score * settings.WEIGHT_HALLUCINATION
            + completeness.score * settings.WEIGHT_COMPLETENESS,
            2,
        )

        quality_tier = self._get_quality_tier(overall_score)

        # Use LLM to synthesize reasoning
        try:
            verdict_data = await self._synthesize_verdict(
                relevance, accuracy, hallucination, completeness,
                overall_score, quality_tier
            )
            verdict_reasoning = verdict_data.get("verdict_reasoning", "")
            recommendations = verdict_data.get("recommendations", [])
        except Exception as e:
            logger.error(f"Verdict synthesis failed: {e}")
            verdict_reasoning = (
                f"Overall score: {overall_score}/10 ({quality_tier.value}). "
                f"Relevance: {relevance.score}/10, Accuracy: {accuracy.score}/10, "
                f"Hallucination: {hallucination.score}/10, Completeness: {completeness.score}/10."
            )
            recommendations = []

        return {
            "overall_score": overall_score,
            "quality_tier": quality_tier,
            "verdict_reasoning": verdict_reasoning,
            "recommendations": recommendations,
        }

    async def _synthesize_verdict(
        self,
        relevance: DimensionScore,
        accuracy: DimensionScore,
        hallucination: DimensionScore,
        completeness: DimensionScore,
        overall_score: float,
        quality_tier: QualityTier,
    ) -> dict:
        """Use LLM to synthesize a consolidated verdict from all dimension scores."""
        system_prompt = """You are a Verdict Synthesis Agent. Your job is to consolidate individual evaluation dimension scores into a clear, actionable overall verdict.

You will receive scores and reasoning from 4 evaluation dimensions. Synthesize them into:
1. A consolidated reasoning paragraph that explains the overall quality
2. Specific, actionable recommendations for improvement

Output Format:
{
    "verdict_reasoning": "<2-3 sentence consolidated verdict explaining overall quality, highlighting strengths and weaknesses>",
    "recommendations": ["<specific actionable recommendation 1>", "<specific actionable recommendation 2>", ...]
}

Keep recommendations practical and specific. If the response scored well (8+), focus on minor refinements. If it scored poorly (<5), focus on critical fixes."""

        user_prompt = f"""## Evaluation Results

**Overall Score: {overall_score}/10 — {quality_tier.value}**

### Relevance ({relevance.score}/10)
{relevance.reasoning}

### Accuracy ({accuracy.score}/10)
{accuracy.reasoning}

### Hallucination Risk ({hallucination.score}/10, where 10 = no hallucination)
{hallucination.reasoning}

### Completeness ({completeness.score}/10)
{completeness.reasoning}

Please synthesize these into a consolidated verdict with actionable recommendations. Respond ONLY with valid JSON."""

        return await groq_client.parse_json_response(system_prompt, user_prompt)


verdict_agent = VerdictAgent()
