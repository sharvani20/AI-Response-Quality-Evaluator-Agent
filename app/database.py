import aiosqlite
import json
import os
from app.config import settings

DATABASE_PATH = settings.DATABASE_URL


async def get_db():
    """Get an async database connection."""
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """Initialize database tables."""
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                reference TEXT,
                relevance_score REAL NOT NULL,
                relevance_reasoning TEXT NOT NULL,
                relevance_details TEXT,
                accuracy_score REAL NOT NULL,
                accuracy_reasoning TEXT NOT NULL,
                accuracy_details TEXT,
                hallucination_score REAL NOT NULL,
                hallucination_reasoning TEXT NOT NULL,
                hallucination_details TEXT,
                flagged_claims TEXT,
                completeness_score REAL NOT NULL,
                completeness_reasoning TEXT NOT NULL,
                completeness_details TEXT,
                overall_score REAL NOT NULL,
                quality_tier TEXT NOT NULL,
                verdict_reasoning TEXT NOT NULL,
                recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS batch_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                total_items INTEGER NOT NULL,
                completed_items INTEGER DEFAULT 0,
                failed_items INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS batch_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_job_id INTEGER NOT NULL,
                evaluation_id INTEGER NOT NULL,
                FOREIGN KEY (batch_job_id) REFERENCES batch_jobs(id),
                FOREIGN KEY (evaluation_id) REFERENCES evaluations(id)
            );
        """)
        await db.commit()
    finally:
        await db.close()


async def save_evaluation(result) -> int:
    """Save an evaluation result to the database. Returns the evaluation ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO evaluations (
                question, ai_response, reference,
                relevance_score, relevance_reasoning, relevance_details,
                accuracy_score, accuracy_reasoning, accuracy_details,
                hallucination_score, hallucination_reasoning, hallucination_details, flagged_claims,
                completeness_score, completeness_reasoning, completeness_details,
                overall_score, quality_tier, verdict_reasoning, recommendations
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                result.question,
                result.ai_response,
                result.reference,
                result.relevance.score,
                result.relevance.reasoning,
                json.dumps(result.relevance.details) if result.relevance.details else None,
                result.accuracy.score,
                result.accuracy.reasoning,
                json.dumps(result.accuracy.details) if result.accuracy.details else None,
                result.hallucination.score,
                result.hallucination.reasoning,
                json.dumps(result.hallucination.details) if result.hallucination.details else None,
                json.dumps([c.model_dump() for c in result.hallucination.flagged_claims]) if result.hallucination.flagged_claims else None,
                result.completeness.score,
                result.completeness.reasoning,
                json.dumps(result.completeness.details) if result.completeness.details else None,
                result.overall_score,
                result.quality_tier.value,
                result.verdict_reasoning,
                json.dumps(result.recommendations) if result.recommendations else None,
            )
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_evaluation(eval_id: int) -> dict:
    """Get a single evaluation by ID."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM evaluations WHERE id = ?", (eval_id,))
        row = await cursor.fetchone()
        if row:
            return _row_to_dict(row)
        return None
    finally:
        await db.close()


async def get_evaluations(limit: int = 50, offset: int = 0) -> list:
    """Get paginated evaluations."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM evaluations ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        rows = await cursor.fetchall()
        return [_row_to_dict(row) for row in rows]
    finally:
        await db.close()


async def delete_evaluation(eval_id: int) -> bool:
    """Delete an evaluation by ID."""
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM evaluations WHERE id = ?", (eval_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def get_evaluation_count() -> int:
    """Get total number of evaluations."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) FROM evaluations")
        row = await cursor.fetchone()
        return row[0]
    finally:
        await db.close()


async def save_batch_job(filename: str, total_items: int) -> int:
    """Create a new batch job. Returns job ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO batch_jobs (filename, total_items, status) VALUES (?, ?, 'pending')",
            (filename, total_items)
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def update_batch_job(job_id: int, **kwargs):
    """Update batch job fields."""
    db = await get_db()
    try:
        set_clauses = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [job_id]
        await db.execute(
            f"UPDATE batch_jobs SET {set_clauses} WHERE id = ?",
            values
        )
        await db.commit()
    finally:
        await db.close()


async def save_batch_result(batch_job_id: int, evaluation_id: int):
    """Link an evaluation result to a batch job."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO batch_results (batch_job_id, evaluation_id) VALUES (?, ?)",
            (batch_job_id, evaluation_id)
        )
        await db.commit()
    finally:
        await db.close()


async def get_batch_job(job_id: int) -> dict:
    """Get a batch job by ID."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM batch_jobs WHERE id = ?", (job_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        await db.close()


async def get_batch_jobs() -> list:
    """Get all batch jobs."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM batch_jobs ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_batch_results(job_id: int) -> list:
    """Get all evaluation results for a batch job."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT e.* FROM evaluations e
               JOIN batch_results br ON e.id = br.evaluation_id
               WHERE br.batch_job_id = ?
               ORDER BY e.id""",
            (job_id,)
        )
        rows = await cursor.fetchall()
        return [_row_to_dict(row) for row in rows]
    finally:
        await db.close()


async def get_dashboard_stats() -> dict:
    """Get aggregate statistics for the dashboard."""
    db = await get_db()
    try:
        # Totals and averages
        cursor = await db.execute("""
            SELECT
                COUNT(*) as total,
                COALESCE(AVG(overall_score), 0) as avg_overall,
                COALESCE(AVG(relevance_score), 0) as avg_relevance,
                COALESCE(AVG(accuracy_score), 0) as avg_accuracy,
                COALESCE(AVG(hallucination_score), 0) as avg_hallucination,
                COALESCE(AVG(completeness_score), 0) as avg_completeness,
                COALESCE(SUM(CASE WHEN overall_score >= 7 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 0) as pass_rate
            FROM evaluations
        """)
        stats = dict(await cursor.fetchone())

        # Quality distribution
        cursor = await db.execute("""
            SELECT quality_tier, COUNT(*) as count
            FROM evaluations
            GROUP BY quality_tier
        """)
        distribution = {}
        for row in await cursor.fetchall():
            distribution[row[0]] = row[1]

        # Recent evaluations
        cursor = await db.execute("""
            SELECT id, question, overall_score, quality_tier, created_at
            FROM evaluations
            ORDER BY created_at DESC
            LIMIT 10
        """)
        recent = [dict(row) for row in await cursor.fetchall()]

        # Score distribution for charts (bucketed)
        cursor = await db.execute("""
            SELECT
                CASE
                    WHEN overall_score >= 9 THEN '9-10'
                    WHEN overall_score >= 7 THEN '7-8.9'
                    WHEN overall_score >= 5 THEN '5-6.9'
                    WHEN overall_score >= 3 THEN '3-4.9'
                    ELSE '1-2.9'
                END as bucket,
                COUNT(*) as count
            FROM evaluations
            GROUP BY bucket
            ORDER BY bucket
        """)
        score_distribution = {}
        for row in await cursor.fetchall():
            score_distribution[row[0]] = row[1]

        return {
            "total_evaluations": stats["total"],
            "average_overall_score": round(stats["avg_overall"], 2),
            "average_relevance": round(stats["avg_relevance"], 2),
            "average_accuracy": round(stats["avg_accuracy"], 2),
            "average_hallucination": round(stats["avg_hallucination"], 2),
            "average_completeness": round(stats["avg_completeness"], 2),
            "pass_rate": round(stats["pass_rate"], 1),
            "quality_distribution": distribution,
            "score_distribution": score_distribution,
            "recent_evaluations": recent,
        }
    finally:
        await db.close()


async def get_trends(limit: int = 30) -> list:
    """Get score trends for the last N evaluations."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, overall_score, relevance_score, accuracy_score,
                      hallucination_score, completeness_score, created_at
               FROM evaluations
               ORDER BY created_at DESC
               LIMIT ?""",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in reversed(rows)]
    finally:
        await db.close()


def _row_to_dict(row) -> dict:
    """Convert a database row to a dictionary with parsed JSON fields."""
    d = dict(row)
    # Parse JSON fields
    for field in ["relevance_details", "accuracy_details", "hallucination_details",
                  "completeness_details", "recommendations"]:
        if d.get(field):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                pass
    if d.get("flagged_claims"):
        try:
            d["flagged_claims"] = json.loads(d["flagged_claims"])
        except (json.JSONDecodeError, TypeError):
            pass
    return d
