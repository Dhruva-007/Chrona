"""
Chrona Deterministic Causal Engine

Performs root cause analysis using pure graph theory and metric analysis.
NO LLM is used here. Every score is computed deterministically.

Algorithm overview:
  1. Build NetworkX DiGraph from current Memgraph state
  2. Identify all failed/degraded nodes (candidates)
  3. Score each candidate across 5 independent signals
  4. Rank candidates by weighted confidence score
  5. Trace the propagation path from root cause to blast radius
  6. Return structured RootCauseAnalysis with full reasoning

Scoring signals:
  - Temporal priority    (25%) : earliest structural failure
  - Topological centrality (25%) : downstream blast radius size
  - Metric severity      (20%) : error rate + latency + cpu deviation
  - Propagation match    (20%) : cascade pattern alignment
  - Dependency depth     (10%) : infrastructure layer position
"""

import logging
import networkx as nx
from datetime import datetime, timezone
from typing import Optional

from app.models.incident import (
    RootCauseAnalysis,
    RootCauseCandidate,
    TimelineEvent,
    EventSeverity,
)
from app.models.graph import InfraNode, InfraEdge, NodeStatus
from app.services.graph_service import (
    fetch_all_nodes,
    fetch_all_edges,
    build_networkx_graph,
    get_dependents,
    compute_impact_analysis,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scoring weights - must sum to 1.0
# ---------------------------------------------------------------------------

WEIGHT_TEMPORAL = 0.25
WEIGHT_CENTRALITY = 0.25
WEIGHT_METRIC_SEVERITY = 0.20
WEIGHT_PROPAGATION = 0.20
WEIGHT_DEPTH = 0.10

# Baseline healthy metrics for deviation scoring
BASELINE_CPU = 40.0
BASELINE_MEMORY = 50.0
BASELINE_ERROR_RATE = 0.5
BASELINE_LATENCY = 100.0

# Node type depth scores - deeper in stack = more likely root cause
NODE_TYPE_DEPTH: dict[str, float] = {
    "database": 1.0,
    "cache": 0.9,
    "queue": 0.85,
    "external": 0.7,
    "service": 0.5,
    "gateway": 0.2,
    "loadbalancer": 0.15,
    "cdn": 0.1,
}

# Timeline for the demo incident (ordered by timestamp)
# Maps node_id → relative failure order index (lower = earlier failure)
DEMO_TIMELINE_ORDER: dict[str, int] = {
    "postgres-primary": 0,   # Failed first
    "redis-cluster": 1,      # Failed second
    "payment-svc": 2,        # Cascaded third
    "inventory-svc": 3,      # Cascaded fourth
    "order-svc": 4,          # Cascaded fifth
    "notification-svc": 5,   # Cascaded sixth
    "gateway-01": 6,         # Impacted last
}


# ---------------------------------------------------------------------------
# Individual scoring functions
# ---------------------------------------------------------------------------

def _score_temporal_priority(
    node_id: str,
    failed_node_ids: list[str],
    timeline_order: dict[str, int],
) -> float:
    """
    Score based on how early this node appeared in the failure timeline.
    Earlier = higher score. Nodes not in timeline get 0.0.

    Returns value in [0.0, 1.0].
    """
    if node_id not in timeline_order:
        return 0.0

    order = timeline_order[node_id]
    max_order = max(timeline_order.values()) if timeline_order else 1

    # Invert: order 0 (first) → score 1.0, last → score 0.0
    score = 1.0 - (order / (max_order + 1))
    return round(score, 4)


def _score_topological_centrality(
    node_id: str,
    G: nx.DiGraph,
) -> float:
    """
    Score based on how many nodes are impacted if this node fails.
    Uses in-degree centrality on the reversed graph (who depends on me).

    Returns value in [0.0, 1.0].
    """
    if node_id not in G:
        return 0.0

    dependents = get_dependents(G, node_id)
    total_other_nodes = G.number_of_nodes() - 1

    if total_other_nodes <= 0:
        return 0.0

    score = len(dependents) / total_other_nodes
    return round(min(score, 1.0), 4)


def _score_metric_severity(node: InfraNode) -> float:
    """
    Score based on how far the node's metrics deviate from healthy baselines.
    Combines error_rate, latency, cpu, and memory into a single severity score.

    Returns value in [0.0, 1.0].
    """
    # Each sub-score is clamped to [0, 1]
    error_score = min(node.error_rate / 100.0, 1.0)

    latency_score = min(
        max(node.latency_ms - BASELINE_LATENCY, 0.0) / 10000.0, 1.0
    )

    cpu_score = min(
        max(node.cpu_usage - BASELINE_CPU, 0.0) / 60.0, 1.0
    )

    memory_score = min(
        max(node.memory_usage - BASELINE_MEMORY, 0.0) / 50.0, 1.0
    )

    # Status multiplier - critical nodes get full weight
    status_multiplier = {
        NodeStatus.CRITICAL: 1.0,
        NodeStatus.DEGRADED: 0.6,
        NodeStatus.HEALTHY: 0.1,
        NodeStatus.UNKNOWN: 0.3,
    }.get(node.status, 0.3)

    raw = (
        error_score * 0.40 +
        latency_score * 0.30 +
        cpu_score * 0.20 +
        memory_score * 0.10
    ) * status_multiplier

    return round(min(raw, 1.0), 4)


def _score_propagation_match(
    node_id: str,
    G: nx.DiGraph,
    failed_node_ids: list[str],
) -> float:
    """
    Score based on how well this node's dependency graph explains the
    observed failure set. A perfect root cause would have ALL other
    failed nodes as its dependents.

    Returns value in [0.0, 1.0].
    """
    if node_id not in G or len(failed_node_ids) <= 1:
        return 0.0

    dependents = set(get_dependents(G, node_id))
    other_failed = set(failed_node_ids) - {node_id}

    if not other_failed:
        return 0.0

    # What fraction of other failures can be explained by this node?
    explained = dependents.intersection(other_failed)
    score = len(explained) / len(other_failed)
    return round(score, 4)


def _score_dependency_depth(node: InfraNode) -> float:
    """
    Score based on the node's infrastructure layer.
    Databases and caches at the bottom of the stack are more likely
    root causes than gateways at the top.

    Returns value in [0.0, 1.0].
    """
    return NODE_TYPE_DEPTH.get(node.type.value, 0.5)


# ---------------------------------------------------------------------------
# Candidate builder
# ---------------------------------------------------------------------------

def _build_candidate(
    node: InfraNode,
    G: nx.DiGraph,
    failed_node_ids: list[str],
    timeline_order: dict[str, int],
) -> RootCauseCandidate:
    """
    Compute all 5 scores and produce a RootCauseCandidate with
    reasoning strings for each signal.
    """
    temporal = _score_temporal_priority(node.id, failed_node_ids, timeline_order)
    centrality = _score_topological_centrality(node.id, G)
    severity = _score_metric_severity(node)
    propagation = _score_propagation_match(node.id, G, failed_node_ids)
    depth = _score_dependency_depth(node)

    confidence = (
        temporal * WEIGHT_TEMPORAL +
        centrality * WEIGHT_CENTRALITY +
        severity * WEIGHT_METRIC_SEVERITY +
        propagation * WEIGHT_PROPAGATION +
        depth * WEIGHT_DEPTH
    )

    dependents = get_dependents(G, node.id)
    downstream_failed = [n for n in dependents if n in failed_node_ids]

    reasoning: list[str] = []

    if temporal > 0.7:
        reasoning.append(
            f"Temporal: {node.name} was among the first nodes to show "
            f"stress (priority score: {temporal:.2f})"
        )
    elif temporal > 0.3:
        reasoning.append(
            f"Temporal: {node.name} showed stress mid-cascade "
            f"(priority score: {temporal:.2f})"
        )

    if centrality > 0.3:
        reasoning.append(
            f"Centrality: Failure here directly impacts "
            f"{int(centrality * (G.number_of_nodes() - 1))} downstream nodes "
            f"({centrality * 100:.1f}% of infrastructure)"
        )

    if severity > 0.5:
        reasoning.append(
            f"Severity: Error rate {node.error_rate:.1f}%, "
            f"latency {node.latency_ms:.0f}ms, "
            f"CPU {node.cpu_usage:.1f}% - "
            f"significantly above healthy baseline"
        )

    if propagation > 0.5:
        reasoning.append(
            f"Propagation: {propagation * 100:.0f}% of observed failures "
            f"are downstream dependents of {node.name}"
        )

    reasoning.append(
        f"Layer: {node.type.value.capitalize()} layer "
        f"(depth score: {depth:.2f}) - "
        f"{'foundational infrastructure component' if depth > 0.7 else 'application layer component'}"
    )

    return RootCauseCandidate(
        node_id=node.id,
        node_name=node.name,
        node_type=node.type.value,
        confidence_score=round(min(confidence, 1.0), 4),
        reasoning=reasoning,
        downstream_impact=downstream_failed,
        time_to_first_failure_ms=_estimate_failure_time(node.id, timeline_order),
    )


def _estimate_failure_time(
    node_id: str, timeline_order: dict[str, int]
) -> Optional[float]:
    """
    Estimate relative time to first failure in milliseconds.
    Based on timeline order position × 45 seconds per step.
    """
    if node_id not in timeline_order:
        return None
    return float(timeline_order[node_id] * 45000)


# ---------------------------------------------------------------------------
# Propagation path tracer
# ---------------------------------------------------------------------------

def _trace_propagation_path(
    root_cause_id: str,
    G: nx.DiGraph,
    failed_node_ids: list[str],
    timeline_order: dict[str, int],
) -> list[str]:
    """
    Trace the exact path that failure propagated from root cause outward.
    Returns an ordered list of node IDs showing the cascade sequence.

    Strategy:
      1. Start at root cause
      2. BFS through dependents
      3. Only include nodes that are in the failed set
      4. Order by timeline position where available
    """
    if root_cause_id not in G:
        return [root_cause_id]

    failed_set = set(failed_node_ids)
    path: list[str] = [root_cause_id]
    visited = {root_cause_id}
    queue = [root_cause_id]

    while queue:
        current = queue.pop(0)
        # Predecessors in DiGraph = nodes that CALL current = dependents
        callers = [
            n for n in G.predecessors(current)
            if n in failed_set and n not in visited
        ]
        # Sort by timeline order if available
        callers.sort(key=lambda n: timeline_order.get(n, 999))
        for caller in callers:
            visited.add(caller)
            path.append(caller)
            queue.append(caller)

    return path


# ---------------------------------------------------------------------------
# Main analysis entry point
# ---------------------------------------------------------------------------

def run_root_cause_analysis(
    incident_id: str,
    timeline_events: Optional[list[dict]] = None,
    timeline_order: Optional[dict[str, int]] = None,
) -> RootCauseAnalysis:
    """
    Execute full deterministic root cause analysis for an incident.

    Steps:
      1. Load current graph state from Memgraph
      2. Build NetworkX DiGraph
      3. Identify all failed / degraded nodes
      4. Score each candidate across 5 signals
      5. Rank by confidence score
      6. Trace propagation path
      7. Compute blast radius
      8. Return complete RootCauseAnalysis

    Args:
        incident_id: The incident identifier
        timeline_events: Optional list of timeline event dicts
        timeline_order: Optional override for node failure ordering.
                        Defaults to DEMO_TIMELINE_ORDER.

    Returns:
        RootCauseAnalysis with primary cause, contributing factors,
        propagation path, and blast radius.
    """
    logger.info(f"Starting root cause analysis for incident {incident_id}")

    # Step 1: Load graph
    nodes = fetch_all_nodes()
    edges = fetch_all_edges()
    G = build_networkx_graph(nodes, edges)

    # Step 2: Identify failed nodes
    node_map: dict[str, InfraNode] = {n.id: n for n in nodes}
    failed_nodes = [
        n for n in nodes
        if n.status in (NodeStatus.CRITICAL, NodeStatus.DEGRADED)
    ]

    if not failed_nodes:
        logger.warning("No failed nodes found - analysis on healthy graph")
        failed_nodes = nodes  # Analyze all if none are marked failed

    failed_node_ids = [n.id for n in failed_nodes]
    logger.info(f"Analyzing {len(failed_nodes)} failed/degraded nodes")

    # Step 3: Use provided or default timeline ordering
    active_timeline = timeline_order or DEMO_TIMELINE_ORDER

    # Step 4: Score all candidates
    candidates: list[RootCauseCandidate] = []
    for node in failed_nodes:
        candidate = _build_candidate(
            node=node,
            G=G,
            failed_node_ids=failed_node_ids,
            timeline_order=active_timeline,
        )
        candidates.append(candidate)
        logger.debug(
            f"  {node.name}: confidence={candidate.confidence_score:.4f}"
        )

    # Step 5: Rank by confidence score descending
    candidates.sort(key=lambda c: c.confidence_score, reverse=True)

    if not candidates:
        raise ValueError("Could not identify any root cause candidates")

    primary = candidates[0]
    contributing = candidates[1:4]  # Top 3 contributing factors

    # Step 6: Trace propagation path
    propagation_path = _trace_propagation_path(
        root_cause_id=primary.node_id,
        G=G,
        failed_node_ids=failed_node_ids,
        timeline_order=active_timeline,
    )

    # Step 7: Compute blast radius
    impact = compute_impact_analysis(G, primary.node_id)
    blast_radius = list(set(
        impact.directly_affected + impact.transitively_affected
    ))

    # Step 8: Overall analysis confidence
    # High if primary is clearly separated from second place
    if len(candidates) >= 2:
        score_gap = primary.confidence_score - candidates[1].confidence_score
        analysis_confidence = min(
            primary.confidence_score + (score_gap * 0.5), 1.0
        )
    else:
        analysis_confidence = primary.confidence_score

    logger.info(
        f"Root cause identified: {primary.node_name} "
        f"(confidence: {primary.confidence_score:.2%})"
    )

    return RootCauseAnalysis(
        incident_id=incident_id,
        primary_cause=primary,
        contributing_factors=contributing,
        blast_radius=blast_radius,
        propagation_path=propagation_path,
        analysis_confidence=round(analysis_confidence, 4),
        computed_at=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Confidence label helper
# ---------------------------------------------------------------------------

def confidence_label(score: float) -> str:
    """Convert a numeric confidence score to a human-readable label."""
    if score >= 0.85:
        return "Very High"
    elif score >= 0.70:
        return "High"
    elif score >= 0.50:
        return "Medium"
    elif score >= 0.30:
        return "Low"
    else:
        return "Very Low"