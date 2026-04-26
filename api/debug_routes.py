# api / debug_routes.py : This file is used for defining debug routes for testing and debugging purposes.
# These routes are not meant for production use and should be used with caution.

from fastapi import APIRouter , Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Rate limiting
from core.config import DEBUG_RATE_LIMIT_REQUESTS, DEBUG_RATE_LIMIT_WINDOW_SEC
from core.rate_limiter import enforce_rate_limit

# auth 
from core.auth import verify_api_key

from services.confidence_service import ConfidenceService

from database import get_db
from models import AgentRun, Agent_Outcomes

async def rate_limit_debug(request: Request, response: Response):
    await enforce_rate_limit(
        request,
        response,
        scope="debug",
        limit=DEBUG_RATE_LIMIT_REQUESTS,
        window_sec=DEBUG_RATE_LIMIT_WINDOW_SEC,
    )

router = APIRouter(
    prefix="/debug", 
    tags=["Observability"],
    dependencies=[Depends(verify_api_key), Depends(rate_limit_debug)],
)

@router.get("/runs")
async def get_recent_runs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Endpoint to retrieve recent agent runs for debugging purposes.
        Here the query retrieves the most recent agent runs from the db, (20 by default) 
        and returns them as a list of AgentRun objects."""
    
    query = (
        select(AgentRun)
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    runs = result.scalars().all() # scalars() is used to extract the AgentRun objects from the result set, and all() retrieves them as a list.

    return runs 


@router.get("/critic_result/{run_id}")
async def get_critic_background_result(
    run_id: int,
    user_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve persisted background critic status/result for a specific run."""

    query = select(AgentRun).where(AgentRun.run_id == run_id)
    if user_id:
        query = query.where(AgentRun.user_id == user_id)

    result = await db.execute(query)
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    payload = run.result if isinstance(run.result, dict) else {}
    metadata = payload.get("metadata") if isinstance(payload, dict) else {}
    if not isinstance(metadata, dict):
        metadata = {}

    return {
        "run_id": run.run_id,
        "user_id": run.user_id,
        "critic_mode": metadata.get("critic_mode"),
        "critic_background_status": metadata.get("critic_background_status"),
        "critic_background_result": metadata.get("critic_background_result"),
        "critic_background_error": metadata.get("critic_background_error"),
        "critic_background_latency_ms": metadata.get("critic_background_latency_ms"),
        "critic_background_completed_at": metadata.get("critic_background_completed_at"),
    }

@router.get("/slow_runs")
async def get_slow_runs( db: AsyncSession = Depends(get_db)):
    """This Endpoint serves the purpose of debugging and monitoring slow running tools by returning the latency of the agents runs"""
    query = (
        select(AgentRun)
        .where(AgentRun.latency > 1)
        .order_by(AgentRun.latency.desc())
    )

    result = await db.execute(query)

    runs = result.scalars().all() # scalars() is used to extract the AgentRun objects from the result set, and all() retrieves them as a list.
    return runs

@router.get("/outcomes")
async def get_recent_outcomes(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Endpoint to retrieve recent agent outcomes for debugging purposes.
        Here the query retrieves the most recent agent outcomes from the db, (20 by default) 
        and returns them as a list of Agent_Outcomes objects."""
    
    query = (
        select(Agent_Outcomes)
        .order_by(Agent_Outcomes.created_at.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    outcomes = result.scalars().all() # scalars() is used to extract the Agent_Outcomes objects from the result set, and all() retrieves them as a list.

    return outcomes

@router.get("/confidence")
async def get_confidence(
    user_id: str, 
    domain: str,
    task_type: str, 
    db: AsyncSession = Depends(get_db)
    ):

    """Endpoint to retrieve confidence level for a specific user, domain, and task type.
        This endpoint uses the ConfidenceService to calculate and return the confidence level based on user feedback."""
    
    service = ConfidenceService(db)

    result = await service.get_confidence(user_id, domain, task_type)

    return result

