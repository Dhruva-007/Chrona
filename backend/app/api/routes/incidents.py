from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.incident import (
    Incident,
    IncidentStatus,
    EventSeverity,
    RootCauseAnalysis,
)
from app.models.responses import APIResponse
from app.services.causal_engine import run_root_cause_analysis, confidence_label
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/incidents", tags=["Incidents"])

# ---------------------------------------------------------------------------
# Demo incident definition
# ---------------------------------------------------------------------------

DEMO_INCIDENT = Incident(
    id="INC-2024-001",
    title="Cascading Payment Failures - Black Friday",
    description=(
        "High error rate detected across payment and order services. "
        "Customer checkout flow degraded. Revenue impact estimated at $42,000/min."
    ),
    status=IncidentStatus.INVESTIGATING,
    severity=EventSeverity.CRITICAL,
    started_at="2024-11-29T18:32:00Z",
    affected_nodes=[
        "postgres-primary",
        "redis-cluster",
        "payment-svc",
        "order-svc",
        "inventory-svc",
        "notification-svc",
        "gateway-01",
    ],
    timeline=[],
)

DEMO_TIMELINE: list[dict] = [
    {
        "timestamp": "2024-11-29T18:32:00Z",
        "node_id": "postgres-primary",
        "node_name": "PostgreSQL Primary",
        "event_type": "cpu_spike",
        "severity": "warning",
        "message": "CPU usage spiked to 94% - connection pool exhaustion starting",
        "metrics": {"cpu_usage": 94.0, "connections": 498, "max_connections": 500},
    },
    {
        "timestamp": "2024-11-29T18:32:45Z",
        "node_id": "redis-cluster",
        "node_name": "Redis Cluster",
        "event_type": "memory_pressure",
        "severity": "warning",
        "message": "Redis memory at 91% - eviction policy triggered",
        "metrics": {"memory_usage": 91.0, "evicted_keys": 14200},
    },
    {
        "timestamp": "2024-11-29T18:33:20Z",
        "node_id": "postgres-primary",
        "node_name": "PostgreSQL Primary",
        "event_type": "connection_refused",
        "severity": "critical",
        "message": "Connection pool exhausted - new connections refused",
        "metrics": {"cpu_usage": 99.2, "connections": 500, "error_rate": 78.0},
    },
    {
        "timestamp": "2024-11-29T18:33:35Z",
        "node_id": "payment-svc",
        "node_name": "Payment Service",
        "event_type": "error_rate_spike",
        "severity": "critical",
        "message": "Payment Service error rate at 67% - DB writes failing",
        "metrics": {"error_rate": 67.0, "latency_ms": 4200.0},
    },
    {
        "timestamp": "2024-11-29T18:33:42Z",
        "node_id": "inventory-svc",
        "node_name": "Inventory Service",
        "event_type": "error_rate_spike",
        "severity": "error",
        "message": "Inventory Service DB writes failing - stock updates delayed",
        "metrics": {"error_rate": 23.0, "latency_ms": 2100.0},
    },
    {
        "timestamp": "2024-11-29T18:33:50Z",
        "node_id": "order-svc",
        "node_name": "Order Service",
        "event_type": "error_rate_spike",
        "severity": "critical",
        "message": "Order Service cascading failure - payment and DB both unavailable",
        "metrics": {"error_rate": 71.0, "latency_ms": 8900.0},
    },
    {
        "timestamp": "2024-11-29T18:33:58Z",
        "node_id": "notification-svc",
        "node_name": "Notification Service",
        "event_type": "queue_backup",
        "severity": "warning",
        "message": "Kafka consumer lag spiking - notification delivery delayed",
        "metrics": {"error_rate": 18.0, "latency_ms": 1200.0},
    },
    {
        "timestamp": "2024-11-29T18:34:10Z",
        "node_id": "gateway-01",
        "node_name": "API Gateway",
        "event_type": "timeout_storm",
        "severity": "critical",
        "message": "Gateway timeout storm - 503s returning to clients",
        "metrics": {"error_rate": 45.0, "latency_ms": 15000.0},
    },
]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=APIResponse[list[Incident]])
async def list_incidents():
    """Return all tracked incidents."""
    return APIResponse(
        success=True,
        message="1 incident found",
        data=[DEMO_INCIDENT],
    )


@router.get("/{incident_id}", response_model=APIResponse[Incident])
async def get_incident(incident_id: str):
    """Return a single incident by ID."""
    if incident_id != DEMO_INCIDENT.id:
        raise HTTPException(
            status_code=404,
            detail=f"Incident '{incident_id}' not found",
        )
    return APIResponse(success=True, message="Incident found", data=DEMO_INCIDENT)


@router.get("/{incident_id}/timeline", response_model=APIResponse[list])
async def get_incident_timeline(incident_id: str):
    """Return the ordered timeline of events for an incident."""
    if incident_id != DEMO_INCIDENT.id:
        raise HTTPException(status_code=404, detail="Incident not found")
    return APIResponse(
        success=True,
        message=f"{len(DEMO_TIMELINE)} timeline events found",
        data=DEMO_TIMELINE,
    )


@router.post(
    "/{incident_id}/analyze",
    response_model=APIResponse[RootCauseAnalysis],
)
async def analyze_root_cause(incident_id: str):
    """
    Run deterministic root cause analysis on the incident.

    This endpoint:
      1. Reads current graph state from Memgraph
      2. Scores all failed nodes across 5 signals
      3. Returns ranked root cause candidates with confidence scores
      4. Traces the full failure propagation path

    IMPORTANT: Activate the incident state first via:
      POST /api/v1/graph/incident/activate
    """
    if incident_id != DEMO_INCIDENT.id:
        raise HTTPException(status_code=404, detail="Incident not found")

    try:
        analysis = run_root_cause_analysis(incident_id=incident_id)

        label = confidence_label(analysis.primary_cause.confidence_score)
        return APIResponse(
            success=True,
            message=(
                f"Root cause identified: {analysis.primary_cause.node_name} "
                f"({label} confidence: {analysis.primary_cause.confidence_score:.2%})"
            ),
            data=analysis,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Root cause analysis failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/{incident_id}/analysis",
    response_model=APIResponse[RootCauseAnalysis],
)
async def get_cached_analysis(incident_id: str):
    """
    Re-run and return root cause analysis.
    Same as POST /analyze but accessible via GET for frontend polling.
    """
    if incident_id != DEMO_INCIDENT.id:
        raise HTTPException(status_code=404, detail="Incident not found")

    try:
        analysis = run_root_cause_analysis(incident_id=incident_id)
        return APIResponse(
            success=True,
            message="Analysis complete",
            data=analysis,
        )
    except Exception as exc:
        logger.exception("Root cause analysis failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{incident_id}/resolve", response_model=APIResponse[Incident])
async def resolve_incident(incident_id: str):
    """Mark an incident as resolved."""
    if incident_id != DEMO_INCIDENT.id:
        raise HTTPException(status_code=404, detail="Incident not found")

    DEMO_INCIDENT.status = IncidentStatus.RESOLVED
    DEMO_INCIDENT.resolved_at = datetime.now(timezone.utc).isoformat()

    return APIResponse(
        success=True,
        message="Incident resolved",
        data=DEMO_INCIDENT,
    )