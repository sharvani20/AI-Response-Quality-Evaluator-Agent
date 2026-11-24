import asyncio
import logging
from typing import Optional

from app.models import EvaluationRequest, EvaluationResult, DimensionScore
from app.agents.relevance_agent import relevance_agent
from app.agents.accuracy_agent import accuracy_agent
from app.agents.hallucination_agent import hallucination_agent
from app.agents.completeness_agent import completeness_agent
from app.agents.verdict_agent import verdict_agent

logger = logging.getLogger(__name__)


class Orchestrator:
    """Coordinates all judge agents for a single evaluation."""

    async def evaluate_single(self, request: EvaluationRequest) -> EvaluationResult:
        """Run all judge agents concurrently and assemble the final result.

        Args:
            request: The evaluation request with question, ai_response, and optional reference.

        Returns:
            Complete EvaluationResult with all dimension scores and verdict.
        """
        logger.info(f"Starting evaluation for question: {request.question[:80]}...")

        # Run all 4 judge agents concurrently
        results = await asyncio.gather(
            self._safe_evaluate(relevance_agent, request),
            self._safe_evaluate(accuracy_agent, request),
            self._safe_evaluate(hallucination_agent, request),
            self._safe_evaluate(completeness_agent, request),
            return_exceptions=False,
        )

        rel_score, acc_score, hal_score, comp_score = results

        # Pass to verdict agent for aggregation
        verdict = await verdict_agent.aggregate(
            relevance=rel_score,
            accuracy=acc_score,
            hallucination=hal_score,
            completeness=comp_score,
        )

        # Assemble final result
        evaluation = EvaluationResult(
            question=request.question,
            ai_response=request.ai_response,
            reference=request.reference,
            relevance=rel_score,
            accuracy=acc_score,
            hallucination=hal_score,
            completeness=comp_score,
            overall_score=verdict["overall_score"],
            quality_tier=verdict["quality_tier"],
            verdict_reasoning=verdict["verdict_reasoning"],
            recommendations=verdict.get("recommendations", []),
        )

        logger.info(f"Evaluation complete. Score: {evaluation.overall_score}/10 ({evaluation.quality_tier.value})")
        return evaluation

    async def _safe_evaluate(self, agent, request: EvaluationRequest) -> DimensionScore:
        """Safely run an agent evaluation with error handling.

        If an agent fails, return a default score of 5 with error details.
        """
        try:
            return await agent.evaluate(
                question=request.question,
                ai_response=request.ai_response,
                reference=request.reference,
            )
        except Exception as e:
            logger.error(f"{agent.dimension_name} agent failed: {e}")
            return DimensionScore(
                dimension=agent.dimension_name,
                score=5.0,
                reasoning=f"Agent evaluation failed: {str(e)}. Default score assigned.",
                details=["Error occurred during evaluation."],
            )


orchestrator = Orchestrator()
