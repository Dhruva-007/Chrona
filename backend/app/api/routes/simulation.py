from fastapi import APIRouter, HTTPException, Query
from app.models.incident import CounterfactualResult
from app.models.responses import APIResponse
from app.services.simulation_engine import (
    simulate_node_removal,
    simulate_node_hardening,
    simulate_with_replica,
    run_full_simulation_suite,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/simulation", tags=["Simulation"])


@router.post(
    "/counterfactual/{incident_id}/{node_id}",
    response_model=APIResponse[CounterfactualResult],
)
async def run_counterfactual(
    incident_id: str,
    node_id: str,
    simulation_type: str = Query(
        default="node_removal",
        description="node_removal | node_hardening | replica_failover",
    ),
    replica_node_id: str = Query(
        default=None,
        description="Replica node ID for replica_failover simulation type",
    ),
):
    """
    Run a counterfactual simulation for a specific node.

    simulation_type options:
    - node_removal    : What if this node had not failed?
    - node_hardening  : What if this node had circuit breakers?
    - replica_failover: What if a replica existed for this node?

    IMPORTANT: Activate incident state first via:
      POST /api/v1/graph/incident/activate
    """
    try:
        if simulation_type == "node_removal":
            result = simulate_node_removal(incident_id, node_id)

        elif simulation_type == "node_hardening":
            result = simulate_node_hardening(incident_id, node_id)

        elif simulation_type == "replica_failover":
            result = simulate_with_replica(incident_id, node_id, replica_node_id)

        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unknown simulation_type '{simulation_type}'. "
                    "Use: node_removal, node_hardening, or replica_failover"
                ),
            )

        return APIResponse(
            success=True,
            message=(
                f"Counterfactual simulation complete - "
                f"Outcome: {result.outcome} "
                f"(confidence: {result.confidence:.2%})"
            ),
            data=result,
        )

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Counterfactual simulation failed: {node_id}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/suite/{incident_id}",
    response_model=APIResponse[dict],
)
async def run_simulation_suite(incident_id: str):
    """
    Run all counterfactual simulations for an incident in one call.

    Runs 4 scenarios:
    1. What if PostgreSQL had not failed?
    2. What if PostgreSQL had circuit breakers?
    3. What if PostgreSQL replica had been promoted?
    4. What if Redis had eviction fallback?

    Returns all results plus the best recommended intervention.

    IMPORTANT: Activate incident state first via:
      POST /api/v1/graph/incident/activate
    """
    try:
        results = run_full_simulation_suite(incident_id)
        sim_count = len([
            v for v in results["simulations"].values()
            if "error" not in v
        ])
        return APIResponse(
            success=True,
            message=f"Simulation suite complete - {sim_count} scenarios evaluated",
            data=results,
        )
    except Exception as exc:
        logger.exception(f"Simulation suite failed for {incident_id}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/remediate/{incident_id}/{node_id}",
    response_model=APIResponse[dict],
)
async def simulate_remediation(incident_id: str, node_id: str):
    """
    Simulate a one-click remediation action.
    Full implementation in Phase 11.
    """
    return APIResponse(
        success=True,
        message="Remediation endpoint ready - full implementation in Phase 11",
        data={"incident_id": incident_id, "node_id": node_id},
    )