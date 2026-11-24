import asyncio
import csv
import io
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from app.models import EvaluationRequest
from app.agents.orchestrator import orchestrator
from app.database import (
    save_batch_job, update_batch_job, save_batch_result,
    save_evaluation, get_batch_job, get_batch_jobs, get_batch_results,
)
from app.utils.csv_parser import parse_csv
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/batch", tags=["batch"])


@router.post("/upload")
async def upload_batch(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a CSV file for batch evaluation.

    CSV must have columns: question, ai_response, reference_answer (optional).
    Processing runs as a background task with rate limiting.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    rows, errors = parse_csv(text)

    if errors and not rows:
        raise HTTPException(status_code=400, detail={"errors": errors})

    # Create batch job
    job_id = await save_batch_job(filename=file.filename, total_items=len(rows))

    # Start background processing
    background_tasks.add_task(process_batch, job_id, rows)

    return {
        "job_id": job_id,
        "filename": file.filename,
        "total_items": len(rows),
        "status": "processing",
        "warnings": errors if errors else None,
    }


@router.get("/jobs")
async def list_batch_jobs():
    """List all batch evaluation jobs."""
    jobs = await get_batch_jobs()
    return {"jobs": jobs}


@router.get("/jobs/{job_id}")
async def get_batch_job_status(job_id: int):
    """Get batch job status and results."""
    job = await get_batch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")

    results = await get_batch_results(job_id)

    return {
        "job": job,
        "results": results,
    }


@router.get("/jobs/{job_id}/download")
async def download_batch_results(job_id: int):
    """Download batch evaluation results as CSV."""
    job = await get_batch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")

    results = await get_batch_results(job_id)

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "question", "ai_response", "reference",
        "overall_score", "quality_tier",
        "relevance_score", "accuracy_score",
        "hallucination_score", "completeness_score",
        "verdict_reasoning",
    ])

    for r in results:
        writer.writerow([
            r.get("question", ""),
            r.get("ai_response", ""),
            r.get("reference", ""),
            r.get("overall_score", ""),
            r.get("quality_tier", ""),
            r.get("relevance_score", ""),
            r.get("accuracy_score", ""),
            r.get("hallucination_score", ""),
            r.get("completeness_score", ""),
            r.get("verdict_reasoning", ""),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=batch_{job_id}_results.csv"},
    )


async def process_batch(job_id: int, rows: list):
    """Background task to process batch evaluation items."""
    logger.info(f"Starting batch job {job_id} with {len(rows)} items")
    await update_batch_job(job_id, status="processing")

    completed = 0
    failed = 0

    for i, row in enumerate(rows):
        try:
            request = EvaluationRequest(
                question=row["question"],
                ai_response=row["ai_response"],
                reference=row.get("reference"),
            )
            result = await orchestrator.evaluate_single(request)
            eval_id = await save_evaluation(result)
            await save_batch_result(job_id, eval_id)
            completed += 1
            logger.info(f"Batch {job_id}: Completed {completed}/{len(rows)}")
        except Exception as e:
            failed += 1
            logger.error(f"Batch {job_id}: Item {i + 1} failed: {e}")

        # Update progress
        await update_batch_job(job_id, completed_items=completed, failed_items=failed)

        # Rate limiting — wait between evaluations
        if i < len(rows) - 1:
            await asyncio.sleep(settings.BATCH_DELAY_SECONDS)

    # Mark job as completed
    final_status = "completed" if failed == 0 else "completed"
    await update_batch_job(job_id, status=final_status, completed_items=completed, failed_items=failed)
    logger.info(f"Batch job {job_id} finished: {completed} completed, {failed} failed")
