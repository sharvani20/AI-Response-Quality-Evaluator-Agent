from fastapi import APIRouter

from app.database import get_dashboard_stats, get_trends

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def dashboard_stats():
    """Get aggregate dashboard statistics.

    Returns total evaluations, average scores per dimension,
    pass/fail rate, quality distribution, and recent evaluations.
    """
    stats = await get_dashboard_stats()
    return stats


@router.get("/trends")
async def score_trends(limit: int = 30):
    """Get score trends for the last N evaluations.

    Returns chronological score data for trend charts.
    """
    trends = await get_trends(limit=limit)
    return {"trends": trends}
