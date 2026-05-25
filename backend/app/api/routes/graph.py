from fastapi import APIRouter, HTTPException, Query
from app.models.graph import (
    GraphSnapshot,
    InfraNode,
    NodeStatus,
    TraversalResult,
    ImpactAnalysis,
    GraphHealthSummary,
)
from app.models.responses import APIResponse
from app.services.seed import seed_graph, get_graph_stats
from app.services import graph_service as gs
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/graph", tags=["Graph"])


# ---------------------------------------------------------------------------
# Core graph endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=APIResponse[GraphSnapshot])
async def get_full_graph(
    namespace: str = Query(default="all", description="Filter by namespace"),
    incident_active: bool = Query(default=False, description="Return incident state"),
):
    """
    Return the complete infrastructure graph snapshot.
    Set incident_active=true to get the graph with failure states applied.
    """
    try:
        if incident_active:
            snapshot = gs.get_full_snapshot(incident_id="INC-2024-001")
        else:
            snapshot = gs.get_full_snapshot()

        if namespace != "all":
            snapshot.nodes = [
                n for n in snapshot.nodes if n.namespace == namespace
            ]
            node_ids = {n.id for n in snapshot.nodes}
            snapshot.edges = [
                e for e in snapshot.edges
                if e.source in node_ids and e.target in node_ids
            ]

        return APIResponse(
            success=True,
            message=f"Graph loaded: {len(snapshot.nodes)} nodes, {len(snapshot.edges)} edges",
            data=snapshot,
        )
    except Exception as exc:
        logger.exception("Failed to fetch graph")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/health-summary", response_model=APIResponse[GraphHealthSummary])
async def get_health_summary():
    """Return aggregate health metrics across all infrastructure nodes."""
    try:
        nodes = gs.fetch_all_nodes()
        summary = gs.compute_health_summary(nodes)
        return APIResponse(
            success=True,
            message="Health summary computed",
            data=summary,
        )
    except Exception as exc:
        logger.exception("Failed to compute health summary")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/stats", response_model=APIResponse[dict])
async def get_graph_statistics():
    """Return node and edge counts from Memgraph."""
    try:
        stats = get_graph_stats()
        return APIResponse(success=True, message="Graph stats retrieved", data=stats)
    except Exception as exc:
        logger.exception("Failed to fetch graph stats")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/seed", response_model=APIResponse[dict])
async def seed_infrastructure(
    force: bool = Query(default=False, description="Wipe existing data before seeding")
):
    """
    Seed the graph database with the simulated infrastructure.
    Set force=true to clear existing data first.
    """
    try:
        result = seed_graph(force=force)
        return APIResponse(
            success=True,
            message="Infrastructure graph seeded successfully",
            data=result,
        )
    except Exception as exc:
        logger.exception("Failed to seed graph")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Node endpoints
# ---------------------------------------------------------------------------

@router.get("/node/{node_id}", response_model=APIResponse[InfraNode])
async def get_node(node_id: str):
    """Return a single node by ID."""
    try:
        node = gs.fetch_node_by_id(node_id)
        if not node:
            raise HTTPException(
                status_code=404, detail=f"Node '{node_id}' not found"
            )
        return APIResponse(success=True, message="Node found", data=node)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Failed to fetch node {node_id}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/node/{node_id}/neighbors", response_model=APIResponse[dict])
async def get_node_neighbors(node_id: str):
    """Return immediate upstream and downstream neighbors of a node."""
    try:
        result = gs.fetch_node_neighbors(node_id)
        return APIResponse(
            success=True,
            message=f"Neighbors fetched for {node_id}",
            data=result,
        )
    except Exception as exc:
        logger.exception(f"Failed to fetch neighbors for {node_id}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/node/{node_id}/status", response_model=APIResponse[InfraNode])
async def update_node_status(node_id: str, status: NodeStatus):
    """Update the status of a node."""
    try:
        from app.services.memgraph import run_query
        rows = run_query(
            "MATCH (n:InfraNode {id: $id}) SET n.status = $status RETURN n",
            {"id": node_id, "status": status.value},
        )
        if not rows:
            raise HTTPException(
                status_code=404, detail=f"Node '{node_id}' not found"
            )
        node = gs.fetch_node_by_id(node_id)
        return APIResponse(
            success=True,
            message=f"Node '{node_id}' status updated to {status.value}",
            data=node,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Failed to update node status {node_id}")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Traversal endpoints
# ---------------------------------------------------------------------------

@router.get("/traversal/{node_id}", response_model=APIResponse[TraversalResult])
async def get_node_traversal(
    node_id: str,
    target_id: str = Query(default=None, description="Optional target for path finding"),
):
    """
    Run full traversal analysis on a node.
    Returns ancestors, descendants, and optionally all paths to a target.
    """
    try:
        nodes = gs.fetch_all_nodes()
        edges = gs.fetch_all_edges()
        G = gs.build_networkx_graph(nodes, edges)

        if node_id not in G:
            raise HTTPException(
                status_code=404, detail=f"Node '{node_id}' not found in graph"
            )

        result = gs.get_traversal_result(G, node_id, target_id)
        return APIResponse(
            success=True,
            message=f"Traversal complete for {node_id}",
            data=result,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Traversal failed for {node_id}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/impact/{node_id}", response_model=APIResponse[ImpactAnalysis])
async def get_impact_analysis(node_id: str):
    """
    Compute the blast radius if this node were to fail.
    Returns directly and transitively affected nodes.
    """
    try:
        nodes = gs.fetch_all_nodes()
        edges = gs.fetch_all_edges()
        G = gs.build_networkx_graph(nodes, edges)

        if node_id not in G:
            raise HTTPException(
                status_code=404, detail=f"Node '{node_id}' not found in graph"
            )

        analysis = gs.compute_impact_analysis(G, node_id)
        return APIResponse(
            success=True,
            message=f"Impact analysis complete for {node_id}",
            data=analysis,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Impact analysis failed for {node_id}")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Incident state endpoints
# ---------------------------------------------------------------------------

@router.post("/incident/activate", response_model=APIResponse[dict])
async def activate_incident_state():
    """
    Apply failure states to the graph to simulate the demo incident.
    This sets nodes to critical/degraded with realistic metrics.
    """
    try:
        result = gs.apply_incident_state("INC-2024-001")
        return APIResponse(
            success=True,
            message="Incident state activated - graph shows failure cascade",
            data=result,
        )
    except Exception as exc:
        logger.exception("Failed to activate incident state")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/incident/reset", response_model=APIResponse[dict])
async def reset_incident_state():
    """
    Reset all nodes back to healthy baseline.
    Used after demo or remediation simulation.
    """
    try:
        result = gs.reset_to_healthy_state()
        return APIResponse(
            success=True,
            message="All nodes reset to healthy state",
            data=result,
        )
    except Exception as exc:
        logger.exception("Failed to reset incident state")
        raise HTTPException(status_code=500, detail=str(exc))