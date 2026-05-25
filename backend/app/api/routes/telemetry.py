from fastapi import APIRouter, HTTPException, Query
from app.models.responses import APIResponse
from app.services.connectors.connector_factory import get_connector
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/telemetry",
    tags=["Telemetry"],
)


@router.get(
    "/incident/{incident_id}",
    response_model=APIResponse[dict],
)
async def get_incident_telemetry(
    incident_id: str,
    source: str = Query(default="datadog"),
):
    """
    Fetch normalized telemetry from monitoring providers.
    Supports:
    - datadog
    - grafana
    - newrelic
    """
    try:
        connector = get_connector(source)

        telemetry = connector.fetch_incident_context(
            incident_id
        )

        return APIResponse(
            success=True,
            message=f"Telemetry fetched from {source}",
            data=telemetry,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        logger.exception("Telemetry fetch failed")
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )