from fastapi import APIRouter, HTTPException
from typing import Optional

from app.models import EvaluationRequest, EvaluationResult
from app.agents.orchestrator import orchestrator
from app.database import save_evaluation, get_evaluation, get_evaluations, delete_evaluation

router = APIRouter(prefix="/api", tags=["evaluation"])


@router.post("/evaluate")
async def evaluate_response(request: EvaluationRequest):
    """Submit a single AI response for multi-dimensional evaluation.

    Runs 4 judge agents concurrently (Relevance, Accuracy, Hallucination, Completeness)
    and aggregates results through a Verdict Agent.
    """
    try:
        result = await orchestrator.evaluate_single(request)
        eval_id = await save_evaluation(result)
        result.id = eval_id
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get("/evaluations")
async def list_evaluations(limit: int = 50, offset: int = 0):
    """List past evaluations with pagination."""
    evaluations = await get_evaluations(limit=limit, offset=offset)
    return {"evaluations": evaluations, "limit": limit, "offset": offset}


@router.get("/evaluations/{eval_id}")
async def get_evaluation_detail(eval_id: int):
    """Get detailed results for a single evaluation."""
    evaluation = await get_evaluation(eval_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation


@router.delete("/evaluations/{eval_id}")
async def remove_evaluation(eval_id: int):
    """Delete an evaluation by ID."""
    deleted = await delete_evaluation(eval_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return {"message": "Evaluation deleted", "id": eval_id}
