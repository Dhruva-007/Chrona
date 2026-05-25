"""
Graph Service - all graph operations for Chrona.

Responsibilities:
  - Cypher query execution for graph traversal
  - Converting Memgraph results to NetworkX DiGraph
  - Ancestor/descendant analysis
  - Blast radius calculation
  - Incident state injection into graph
  - Health summary computation
"""

import logging
import networkx as nx
from datetime import datetime, timezone
from typing import Optional

from app.services.memgraph import run_query
from app.models.graph import (
    InfraNode,
    InfraEdge,
    GraphSnapshot,
    TraversalResult,
    TraversalPath,
    ImpactAnalysis,
    GraphHealthSummary,
    NodeStatus,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Private mappers - defined first so all functions below can use them
# ---------------------------------------------------------------------------

def _map_node(raw: dict) -> InfraNode:
    """Map a raw Memgraph node property dict to an InfraNode model."""
    return InfraNode(
        id=raw["id"],
        name=raw["name"],
        type=raw["type"],
        status=raw.get("status", "healthy"),
        namespace=raw.get("namespace", "production"),
        version=raw.get("version", "1.0.0"),
        replicas=int(raw.get("replicas", 1)),
        cpu_usage=float(raw.get("cpu_usage", 0.0)),
        memory_usage=float(raw.get("memory_usage", 0.0)),
        error_rate=float(raw.get("error_rate", 0.0)),
        latency_ms=float(raw.get("latency_ms", 0.0)),
    )


def _map_edge(raw: dict) -> InfraEdge:
    """Map a raw Memgraph edge property dict to an InfraEdge model."""
    return InfraEdge(
        source=raw["source"],
        target=raw["target"],
        type=raw.get("type", "HTTP"),
        weight=float(raw.get("weight", 1.0)),
        latency_ms=float(raw.get("latency_ms", 0.0)),
        requests_per_second=float(raw.get("rps", 0.0)),
        error_rate=float(raw.get("error_rate", 0.0)),
    )


# ---------------------------------------------------------------------------
# Raw data fetchers
# ---------------------------------------------------------------------------

def fetch_all_nodes() -> list[InfraNode]:
    """Fetch all InfraNode records from Memgraph."""
    rows = run_query("MATCH (n:InfraNode) RETURN n")
    return [_map_node(r["n"]) for r in rows]


def fetch_all_edges() -> list[InfraEdge]:
    """Fetch all DEPENDS_ON edges from Memgraph."""
    rows = run_query(
        """
        MATCH (a:InfraNode)-[r:DEPENDS_ON]->(b:InfraNode)
        RETURN a.id        AS source,
               b.id        AS target,
               r.type      AS type,
               r.weight    AS weight,
               r.latency_ms AS latency_ms,
               r.rps       AS rps,
               r.error_rate AS error_rate
        """
    )
    return [_map_edge(r) for r in rows]


def fetch_node_by_id(node_id: str) -> Optional[InfraNode]:
    """Fetch a single node by its ID."""
    rows = run_query(
        "MATCH (n:InfraNode {id: $id}) RETURN n",
        {"id": node_id},
    )
    if not rows:
        return None
    return _map_node(rows[0]["n"])


def fetch_node_neighbors(node_id: str) -> dict:
    """
    Fetch immediate upstream (callers) and downstream (callees)
    neighbors of a node.
    """
    upstream = run_query(
        """
        MATCH (up:InfraNode)-[r:DEPENDS_ON]->(n:InfraNode {id: $id})
        RETURN up.id     AS id,
               up.name   AS name,
               up.status AS status,
               r.type    AS edge_type
        """,
        {"id": node_id},
    )
    downstream = run_query(
        """
        MATCH (n:InfraNode {id: $id})-[r:DEPENDS_ON]->(dn:InfraNode)
        RETURN dn.id     AS id,
               dn.name   AS name,
               dn.status AS status,
               r.type    AS edge_type
        """,
        {"id": node_id},
    )
    return {
        "node_id": node_id,
        "upstream": upstream,
        "downstream": downstream,
    }


# ---------------------------------------------------------------------------
# Full snapshot builder
# ---------------------------------------------------------------------------

def get_full_snapshot(incident_id: Optional[str] = None) -> GraphSnapshot:
    """
    Build a complete GraphSnapshot from current Memgraph state.
    Optionally tag with an incident ID.
    """
    nodes = fetch_all_nodes()
    edges = fetch_all_edges()
    return GraphSnapshot(
        nodes=nodes,
        edges=edges,
        timestamp=datetime.now(timezone.utc).isoformat(),
        incident_id=incident_id,
    )


# ---------------------------------------------------------------------------
# NetworkX bridge - core of causal analysis
# ---------------------------------------------------------------------------

def build_networkx_graph(
    nodes: Optional[list[InfraNode]] = None,
    edges: Optional[list[InfraEdge]] = None,
) -> nx.DiGraph:
    """
    Convert Memgraph data into a NetworkX DiGraph.

    Edge direction: A → B means "A depends on B"
    So if B fails, A is impacted.

    Node attributes: name, type, status, namespace,
                     cpu_usage, memory_usage, error_rate,
                     latency_ms, replicas
    Edge attributes: type, weight, latency_ms, rps, error_rate
    """
    if nodes is None:
        nodes = fetch_all_nodes()
    if edges is None:
        edges = fetch_all_edges()

    G = nx.DiGraph()

    for node in nodes:
        G.add_node(
            node.id,
            name=node.name,
            type=node.type.value,
            status=node.status.value,
            namespace=node.namespace,
            cpu_usage=node.cpu_usage,
            memory_usage=node.memory_usage,
            error_rate=node.error_rate,
            latency_ms=node.latency_ms,
            replicas=node.replicas,
            version=node.version,
        )

    for edge in edges:
        G.add_edge(
            edge.source,
            edge.target,
            type=edge.type.value,
            weight=edge.weight,
            latency_ms=edge.latency_ms,
            rps=edge.requests_per_second,
            error_rate=edge.error_rate,
        )

    logger.info(
        f"NetworkX graph built: {G.number_of_nodes()} nodes, "
        f"{G.number_of_edges()} edges"
    )
    return G


# ---------------------------------------------------------------------------
# Graph traversal operations
# ---------------------------------------------------------------------------

def get_ancestors(G: nx.DiGraph, node_id: str) -> list[str]:
    """
    Return all nodes that node_id depends on (directly or transitively).
    Edge A→B means A depends on B, so descendants in DiGraph = dependencies.
    """
    if node_id not in G:
        return []
    return list(nx.descendants(G, node_id))


def get_dependents(G: nx.DiGraph, node_id: str) -> list[str]:
    """
    Return all nodes that depend on node_id (will be impacted if it fails).
    These are the ancestors in the DiGraph (nodes that have paths TO node_id).
    """
    if node_id not in G:
        return []
    return list(nx.ancestors(G, node_id))


def get_shortest_path(
    G: nx.DiGraph, source: str, target: str
) -> Optional[list[str]]:
    """Return the shortest dependency path between two nodes."""
    try:
        return nx.shortest_path(G, source=source, target=target)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def get_all_paths(
    G: nx.DiGraph, source: str, target: str, cutoff: int = 6
) -> list[list[str]]:
    """
    Return all simple paths between source and target.
    cutoff prevents combinatorial explosion on large graphs.
    """
    try:
        return list(
            nx.all_simple_paths(G, source=source, target=target, cutoff=cutoff)
        )
    except (nx.NodeNotFound, nx.NetworkXError):
        return []


def get_traversal_result(
    G: nx.DiGraph,
    node_id: str,
    target_id: Optional[str] = None,
) -> TraversalResult:
    """
    Full traversal analysis for a node.
    Returns ancestors, dependents, and optionally paths to a target.
    """
    ancestors = get_ancestors(G, node_id)
    dependents = get_dependents(G, node_id)
    paths: list[TraversalPath] = []

    if target_id:
        raw_paths = get_all_paths(G, node_id, target_id)
        for path in raw_paths:
            total_latency = sum(
                G.edges[path[i], path[i + 1]].get("latency_ms", 0.0)
                for i in range(len(path) - 1)
            )
            has_failure = any(
                G.nodes[n].get("status") in ("critical", "degraded")
                for n in path
            )
            paths.append(
                TraversalPath(
                    nodes=path,
                    total_latency_ms=total_latency,
                    hop_count=len(path) - 1,
                    contains_failure=has_failure,
                )
            )

    return TraversalResult(
        source_node=node_id,
        target_node=target_id,
        paths=paths,
        ancestors=ancestors,
        descendants=dependents,
        depth=len(ancestors),
    )


# ---------------------------------------------------------------------------
# Impact analysis
# ---------------------------------------------------------------------------

def compute_impact_analysis(
    G: nx.DiGraph, failed_node_id: str
) -> ImpactAnalysis:
    """
    Compute the blast radius of a node failure.

    Directly affected  = immediate callers (1 hop upstream in dependency graph).
    Transitively affected = all upstream dependents beyond 1 hop.
    Blast radius % = total affected / total nodes * 100.
    """
    if failed_node_id not in G:
        return ImpactAnalysis(
            failed_node_id=failed_node_id,
            failed_node_name=failed_node_id,
        )

    node_name = G.nodes[failed_node_id].get("name", failed_node_id)

    directly_affected: list[str] = list(G.predecessors(failed_node_id))
    all_dependents: list[str] = get_dependents(G, failed_node_id)
    transitively_affected: list[str] = [
        n for n in all_dependents if n not in directly_affected
    ]

    total_affected = len(set(directly_affected + transitively_affected))
    total_nodes = G.number_of_nodes()
    blast_radius_pct = (
        (total_affected / total_nodes * 100) if total_nodes > 0 else 0.0
    )

    critical_nodes = {"gateway-01", "cdn-01"}
    critical_path_broken = bool(
        critical_nodes.intersection(set(all_dependents))
    )

    return ImpactAnalysis(
        failed_node_id=failed_node_id,
        failed_node_name=node_name,
        directly_affected=directly_affected,
        transitively_affected=transitively_affected,
        total_affected_count=total_affected,
        critical_path_broken=critical_path_broken,
        estimated_blast_radius_percent=round(blast_radius_pct, 2),
    )


# ---------------------------------------------------------------------------
# Health summary
# ---------------------------------------------------------------------------

def compute_health_summary(nodes: list[InfraNode]) -> GraphHealthSummary:
    """Compute overall infrastructure health from node statuses."""
    total = len(nodes)
    healthy = sum(1 for n in nodes if n.status == NodeStatus.HEALTHY)
    degraded = sum(1 for n in nodes if n.status == NodeStatus.DEGRADED)
    critical = sum(1 for n in nodes if n.status == NodeStatus.CRITICAL)
    unknown = sum(1 for n in nodes if n.status == NodeStatus.UNKNOWN)
    health_score = (healthy / total * 100) if total > 0 else 100.0
    edges = fetch_all_edges()

    return GraphHealthSummary(
        total_nodes=total,
        healthy_nodes=healthy,
        degraded_nodes=degraded,
        critical_nodes=critical,
        unknown_nodes=unknown,
        total_edges=len(edges),
        health_score=round(health_score, 2),
        critical_node_ids=[n.id for n in nodes if n.status == NodeStatus.CRITICAL],
        degraded_node_ids=[n.id for n in nodes if n.status == NodeStatus.DEGRADED],
    )


# ---------------------------------------------------------------------------
# Incident state injection
# ---------------------------------------------------------------------------

INCIDENT_FAILURE_STATES: dict[str, dict] = {
    "postgres-primary": {
        "status": "critical",
        "cpu_usage": 99.2,
        "memory_usage": 95.0,
        "error_rate": 78.0,
        "latency_ms": 8500.0,
    },
    "redis-cluster": {
        "status": "degraded",
        "cpu_usage": 88.0,
        "memory_usage": 91.0,
        "error_rate": 12.0,
        "latency_ms": 450.0,
    },
    "payment-svc": {
        "status": "critical",
        "cpu_usage": 95.0,
        "memory_usage": 88.0,
        "error_rate": 67.0,
        "latency_ms": 4200.0,
    },
    "order-svc": {
        "status": "critical",
        "cpu_usage": 92.0,
        "memory_usage": 85.0,
        "error_rate": 71.0,
        "latency_ms": 8900.0,
    },
    "gateway-01": {
        "status": "degraded",
        "cpu_usage": 78.0,
        "memory_usage": 72.0,
        "error_rate": 45.0,
        "latency_ms": 15000.0,
    },
    "inventory-svc": {
        "status": "degraded",
        "cpu_usage": 70.0,
        "memory_usage": 68.0,
        "error_rate": 23.0,
        "latency_ms": 2100.0,
    },
    "notification-svc": {
        "status": "degraded",
        "cpu_usage": 55.0,
        "memory_usage": 60.0,
        "error_rate": 18.0,
        "latency_ms": 1200.0,
    },
}

HEALTHY_STATES: dict[str, dict] = {
    "postgres-primary": {
        "status": "healthy",
        "cpu_usage": 48.0,
        "memory_usage": 71.0,
        "error_rate": 0.0,
        "latency_ms": 4.0,
    },
    "redis-cluster": {
        "status": "healthy",
        "cpu_usage": 25.0,
        "memory_usage": 58.0,
        "error_rate": 0.0,
        "latency_ms": 1.0,
    },
    "payment-svc": {
        "status": "healthy",
        "cpu_usage": 41.0,
        "memory_usage": 55.0,
        "error_rate": 0.3,
        "latency_ms": 230.0,
    },
    "order-svc": {
        "status": "healthy",
        "cpu_usage": 55.1,
        "memory_usage": 62.0,
        "error_rate": 0.5,
        "latency_ms": 120.0,
    },
    "gateway-01": {
        "status": "healthy",
        "cpu_usage": 34.2,
        "memory_usage": 41.0,
        "error_rate": 0.1,
        "latency_ms": 12.0,
    },
    "inventory-svc": {
        "status": "healthy",
        "cpu_usage": 30.0,
        "memory_usage": 44.0,
        "error_rate": 0.1,
        "latency_ms": 67.0,
    },
    "notification-svc": {
        "status": "healthy",
        "cpu_usage": 18.0,
        "memory_usage": 29.0,
        "error_rate": 0.2,
        "latency_ms": 88.0,
    },
}


def apply_incident_state(incident_id: str) -> dict:
    """
    Apply failure states to simulate an active incident.
    Updates node statuses and metrics in Memgraph.
    """
    cypher = """
    MATCH (n:InfraNode {id: $id})
    SET n.status       = $status,
        n.cpu_usage    = $cpu_usage,
        n.memory_usage = $memory_usage,
        n.error_rate   = $error_rate,
        n.latency_ms   = $latency_ms
    """
    updated = []
    for node_id, state in INCIDENT_FAILURE_STATES.items():
        run_query(cypher, {"id": node_id, **state})
        updated.append(node_id)

    logger.info(f"Incident state applied to {len(updated)} nodes")
    return {
        "incident_id": incident_id,
        "nodes_updated": updated,
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "status": "incident_active",
    }


def reset_to_healthy_state() -> dict:
    """Reset all nodes back to healthy baseline."""
    cypher = """
    MATCH (n:InfraNode {id: $id})
    SET n.status       = $status,
        n.cpu_usage    = $cpu_usage,
        n.memory_usage = $memory_usage,
        n.error_rate   = $error_rate,
        n.latency_ms   = $latency_ms
    """
    reset = []
    for node_id, state in HEALTHY_STATES.items():
        run_query(cypher, {"id": node_id, **state})
        reset.append(node_id)

    logger.info(f"Reset {len(reset)} nodes to healthy state")
    return {
        "nodes_reset": reset,
        "reset_at": datetime.now(timezone.utc).isoformat(),
        "status": "healthy",
    }