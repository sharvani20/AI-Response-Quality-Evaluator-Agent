from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class QualityTier(str, Enum):
    """Quality tier classification based on overall score."""
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"
    FAILING = "Failing"


class FlaggedClaim(BaseModel):
    """A specific claim flagged by the hallucination detector."""
    claim: str
    status: str = Field(description="supported, unsupported, or fabricated")
    evidence: str = Field(default="", description="Evidence from reference or reason for flag")


class DimensionScore(BaseModel):
    """Score and reasoning for a single evaluation dimension."""
    dimension: str
    score: float = Field(ge=1, le=10)
    reasoning: str
    details: Optional[List[str]] = None
    flagged_claims: Optional[List[FlaggedClaim]] = None


class EvaluationRequest(BaseModel):
    """Request body for submitting a single evaluation."""
    question: str = Field(min_length=1, description="The question that was asked")
    ai_response: str = Field(min_length=1, description="The AI-generated response to evaluate")
    reference: Optional[str] = Field(default=None, description="Reference answer or source document")


class EvaluationResult(BaseModel):
    """Complete evaluation result with all dimension scores."""
    id: Optional[int] = None
    question: str
    ai_response: str
    reference: Optional[str] = None
    relevance: DimensionScore
    accuracy: DimensionScore
    hallucination: DimensionScore
    completeness: DimensionScore
    overall_score: float
    quality_tier: QualityTier
    verdict_reasoning: str
    recommendations: Optional[List[str]] = None
    created_at: Optional[str] = None


class BatchJobStatus(str, Enum):
    """Status of a batch evaluation job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchJob(BaseModel):
    """Batch evaluation job metadata."""
    id: Optional[int] = None
    filename: str
    total_items: int
    completed_items: int = 0
    failed_items: int = 0
    status: BatchJobStatus = BatchJobStatus.PENDING
    created_at: Optional[str] = None


class BatchResultItem(BaseModel):
    """Single item result within a batch job."""
    batch_job_id: int
    evaluation_id: int
    question: str
    overall_score: float
    quality_tier: QualityTier
    relevance_score: float
    accuracy_score: float
    hallucination_score: float
    completeness_score: float


class DashboardStats(BaseModel):
    """Aggregate dashboard statistics."""
    total_evaluations: int
    average_overall_score: float
    average_relevance: float
    average_accuracy: float
    average_hallucination: float
    average_completeness: float
    pass_rate: float = Field(description="Percentage of evaluations scoring >= 7")
    quality_distribution: dict
    recent_evaluations: List[dict]
