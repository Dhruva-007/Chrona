from fastapi import APIRouter, HTTPException
from app.models.responses import APIResponse
from app.api.routes.incidents import DEMO_INCIDENT, DEMO_TIMELINE
from app.services.simulation_engine import run_full_simulation_suite
from app.services.causal_engine import run_root_cause_analysis
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/narrative", tags=["AI Narrative"])


def build_incident_summary(incident_id: str):
    analysis = run_root_cause_analysis(incident_id)
    suite = run_full_simulation_suite(incident_id)

    primary = analysis.primary_cause
    failover = suite["simulations"]["replica_failover"]

    affected_count = len(DEMO_INCIDENT.affected_nodes)
    recovered_count = len(failover["recovered_nodes"])
    confidence = round(failover["confidence"] * 100)

    summary = (
        f"{primary.node_name} was identified as the primary root cause "
        f"with {primary.confidence_score:.0%} confidence. "
        f"The failure triggered a cascading outage impacting "
        f"{affected_count} critical infrastructure components, including "
        f"payment, ordering, gateway, inventory, and notification services. "
        f"Counterfactual simulation indicates replica failover would have "
        f"recovered {recovered_count} services with {confidence}% confidence."
    )

    return {
        "incident_id": incident_id,
        "summary": summary,
        "root_cause": primary.node_name,
        "confidence": primary.confidence_score,
        "affected_services": affected_count,
    }


def build_postmortem(incident_id: str):
    analysis = run_root_cause_analysis(incident_id)
    suite = run_full_simulation_suite(incident_id)

    primary = analysis.primary_cause
    failover = suite["simulations"]["replica_failover"]
    node_removal = suite["simulations"]["node_removal"]

    return {
        "incident_overview": {
            "title": DEMO_INCIDENT.title,
            "description": DEMO_INCIDENT.description,
            "severity": DEMO_INCIDENT.severity,
            "status": DEMO_INCIDENT.status,
        },
        "root_cause": {
            "node": primary.node_name,
            "confidence": primary.confidence_score,
            "explanation": (
                "Primary database failure triggered cascading dependency disruption "
                "across downstream business-critical services."
            ),
        },
        "timeline": DEMO_TIMELINE,
        "impact_assessment": {
            "affected_nodes": DEMO_INCIDENT.affected_nodes,
            "count": len(DEMO_INCIDENT.affected_nodes),
        },
        "counterfactual_analysis": {
            "replica_failover": {
                "outcome": failover["outcome"],
                "confidence": failover["confidence"],
                "recovered_nodes": failover["recovered_nodes"],
                "explanation": failover["explanation"],
            },
            "node_removal": {
                "outcome": node_removal["outcome"],
                "confidence": node_removal["confidence"],
                "recovered_nodes": node_removal["recovered_nodes"],
                "still_failing_nodes": node_removal["still_failing_nodes"],
            },
        },
        "immediate_actions": [
            "Promote PostgreSQL replica immediately",
            "Stabilize database connectivity",
            "Reduce cascading retries",
            "Protect gateway traffic flow",
        ],
        "preventive_actions": [
            "Enable automatic failover",
            "Introduce circuit breakers",
            "Add connection pool safeguards",
            "Improve dependency isolation",
            "Run continuous counterfactual simulations",
        ],
        "lessons_learned": [
            "Single database dependency created excessive blast radius",
            "Replica failover would significantly reduce downtime",
            "Predictive simulation improves incident readiness",
        ],
    }


@router.get("/{incident_id}/summary", response_model=APIResponse[dict])
async def get_incident_summary(incident_id: str):
    if incident_id != DEMO_INCIDENT.id:
        raise HTTPException(status_code=404, detail="Incident not found")

    try:
        summary = build_incident_summary(incident_id)

        return APIResponse(
            success=True,
            message="Incident summary generated successfully",
            data=summary,
        )

    except Exception as exc:
        logger.exception("Summary generation failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{incident_id}/postmortem", response_model=APIResponse[dict])
async def get_postmortem(incident_id: str):
    if incident_id != DEMO_INCIDENT.id:
        raise HTTPException(status_code=404, detail="Incident not found")

    try:
        postmortem = build_postmortem(incident_id)

        return APIResponse(
            success=True,
            message="Postmortem generated successfully",
            data=postmortem,
        )

    except Exception as exc:
        logger.exception("Postmortem generation failed")
        raise HTTPException(status_code=500, detail=str(exc))