from fastapi import APIRouter, HTTPException, UploadFile, File
import io
from typing import Optional

from app.models import EvaluationRequest, EvaluationResult
from app.agents.orchestrator import orchestrator
from app.database import save_evaluation, get_evaluation, get_evaluations, delete_evaluation

router = APIRouter(prefix="/api", tags=["evaluation"])


@router.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """Extract readable text from an uploaded source document (.txt, .md, .pdf, .csv, .json)."""
    try:
        filename = file.filename or "document"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext == "pdf":
            try:
                import pypdf
                file_bytes = await file.read()
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                text_pages = [page.extract_text() or "" for page in reader.pages]
                text = "\n\n".join(text_pages).strip()
            except Exception as pe:
                raise HTTPException(status_code=400, detail=f"Failed to read PDF document: {str(pe)}")
        elif ext in ["txt", "md", "markdown", "csv", "json", "py", "html"]:
            file_bytes = await file.read()
            text = file_bytes.decode("utf-8", errors="ignore").strip()
        else:
            file_bytes = await file.read()
            text = file_bytes.decode("utf-8", errors="ignore").strip()

        if not text:
            raise HTTPException(status_code=400, detail="The uploaded document contains no readable text.")

        return {
            "filename": filename,
            "text": text,
            "char_count": len(text)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


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
