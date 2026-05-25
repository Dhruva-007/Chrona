from fastapi import APIRouter, HTTPException
from app.models.responses import APIResponse
from app.models.agent import (
    AgentAnalyzeRequest,
    AgentAnalyzeResponse,
)
from app.services.agent_service import run_agent_analysis
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agent",
    tags=["AI Agent"],
)


@router.post(
    "/analyze",
    response_model=APIResponse[AgentAnalyzeResponse],
)
async def analyze_incident(
    payload: AgentAnalyzeRequest,
):
    """
    Run AI incident investigation.
    """
    try:
        result = run_agent_analysis(payload)

        return APIResponse(
            success=True,
            message="AI agent analysis complete",
            data=result,
        )

    except Exception as exc:
        logger.exception("AI agent analysis failed")
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )