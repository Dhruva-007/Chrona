"""
Chrona Counterfactual Simulation Engine

Answers "what if?" questions about infrastructure incidents using
deterministic graph surgery on NetworkX DiGraph clones.

NO LLM is used. Every outcome is computed from graph reachability analysis.

Simulation types:
  1. NODE_REMOVAL   - What if this node had not failed?
  2. NODE_HARDENING - What if this node had redundancy / circuit breaker?
  3. PATH_ANALYSIS  - What alternative dependency paths existed?

Key insight on graph direction:
  Edge A → B means "A depends on B"
  So if B fails, A is impacted (A cannot function without B)
  Healing B means A can recover IF A has no other failed dependencies

Recovery propagation:
  When we heal a node, we must also heal all nodes whose ONLY
  reason for failure was their dependency on the healed node.
  This is computed by checking: after healing X, does node Y
  still have any critical/degraded dependencies?
"""

import logging
import networkx as nx
from datetime import datetime, timezone
from typing import Optional
from enum import Enum

from app.models.incident import CounterfactualResult
from app.models.graph import NodeStatus
from app.services.graph_service import (
    fetch_all_nodes,
    fetch_all_edges,
    build_networkx_graph,
)

logger = logging.getLogger(__name__)

# Entry points - nodes from which user traffic enters the system
ENTRY_POINTS = {"cdn-01", "gateway-01"}

# Critical path nodes - recovering these = incident resolved
CRITICAL_PATH_NODES = {
    "gateway-01",
    "order-svc",
    "payment-svc",
    "user-svc",
}


class SimulationType(str, Enum):
    NODE_REMOVAL = "node_removal"
    NODE_HARDENING = "node_hardening"
    PATH_ANALYSIS = "path_analysis"


# ---------------------------------------------------------------------------
# Core recovery propagation
# ---------------------------------------------------------------------------

def _propagate_healing(
    G: nx.DiGraph,
    healed_nodes: set[str],
) -> nx.DiGraph:
    """
    After healing a set of nodes, propagate recovery through the graph.

    A node Y can recover if ALL of its dependencies (nodes it points to)
    are either healthy or also being healed.

    Edge direction: Y → Z means Y depends on Z.
    So Y's dependencies = successors of Y in the DiGraph.

    We do BFS from healed nodes upward (toward callers/predecessors)
    to find which nodes can now recover.

    This is the critical fix: without propagation, healing postgres
    does not automatically show payment-svc as recovered even though
    payment-svc only failed because postgres failed.
    """
    clone = G.copy()

    # Mark the directly healed nodes as healthy
    for node_id in healed_nodes:
        if node_id in clone:
            clone.nodes[node_id]["status"] = "healthy"
            clone.nodes[node_id]["error_rate"] = max(
                clone.nodes[node_id].get("error_rate", 0.0) * 0.05, 0.1
            )
            clone.nodes[node_id]["latency_ms"] = max(
                clone.nodes[node_id].get("latency_ms", 10.0) * 0.05, 5.0
            )

    # BFS upward: find nodes that can now recover
    # A node can recover if all its dependencies are now healthy
    changed = True
    iterations = 0
    max_iterations = 20  # prevent infinite loops

    while changed and iterations < max_iterations:
        changed = False
        iterations += 1

        for node_id in list(clone.nodes()):
            attrs = clone.nodes[node_id]
            current_status = attrs.get("status", "healthy")

            # Only try to recover failed/degraded nodes
            if current_status not in ("critical", "degraded"):
                continue

            # Check all dependencies of this node (its successors)
            dependencies = list(clone.successors(node_id))
            if not dependencies:
                # No dependencies - this node's failure is self-caused
                # Only clear it if it was in the original healed set
                continue

            # Can this node recover?
            # Yes if ALL its dependencies are now healthy
            all_deps_healthy = all(
                clone.nodes[dep].get("status", "healthy") not in ("critical",)
                for dep in dependencies
            )

            if all_deps_healthy:
                # This node can recover
                clone.nodes[node_id]["status"] = "healthy"
                clone.nodes[node_id]["error_rate"] = max(
                    attrs.get("error_rate", 0.0) * 0.1, 0.5
                )
                clone.nodes[node_id]["latency_ms"] = max(
                    attrs.get("latency_ms", 100.0) * 0.1, 20.0
                )
                changed = True
                logger.debug(f"  Cascading recovery: {node_id} recovered")

    logger.debug(f"Healing propagation completed in {iterations} iterations")
    return clone


def _propagate_hardening(
    G: nx.DiGraph,
    hardened_node_id: str,
) -> nx.DiGraph:
    """
    After hardening a node (circuit breaker), propagate partial recovery.

    Hardening = node goes from critical → degraded.
    Nodes that depended ONLY on this node for their failure can partially recover.
    Nodes with multiple failed dependencies only partially recover.
    """
    clone = G.copy()

    if hardened_node_id not in clone:
        return clone

    # Upgrade the hardened node from critical → degraded
    current_status = clone.nodes[hardened_node_id].get("status", "healthy")
    if current_status == "critical":
        clone.nodes[hardened_node_id]["status"] = "degraded"
        clone.nodes[hardened_node_id]["error_rate"] = max(
            clone.nodes[hardened_node_id].get("error_rate", 0.0) * 0.25, 5.0
        )
        clone.nodes[hardened_node_id]["latency_ms"] = max(
            clone.nodes[hardened_node_id].get("latency_ms", 1000.0) * 0.3, 200.0
        )

    # Propagate partial recovery upward
    changed = True
    iterations = 0
    max_iterations = 20

    while changed and iterations < max_iterations:
        changed = False
        iterations += 1

        for node_id in list(clone.nodes()):
            if node_id == hardened_node_id:
                continue

            attrs = clone.nodes[node_id]
            current = attrs.get("status", "healthy")

            if current not in ("critical", "degraded"):
                continue

            dependencies = list(clone.successors(node_id))
            if not dependencies:
                continue

            critical_deps = [
                dep for dep in dependencies
                if clone.nodes[dep].get("status") == "critical"
            ]
            degraded_deps = [
                dep for dep in dependencies
                if clone.nodes[dep].get("status") == "degraded"
            ]

            # If no more critical deps, can upgrade from critical → degraded
            if current == "critical" and not critical_deps:
                clone.nodes[node_id]["status"] = "degraded"
                clone.nodes[node_id]["error_rate"] = max(
                    attrs.get("error_rate", 0.0) * 0.3, 5.0
                )
                clone.nodes[node_id]["latency_ms"] = max(
                    attrs.get("latency_ms", 1000.0) * 0.35, 100.0
                )
                changed = True
                logger.debug(f"  Partial recovery: {node_id} critical→degraded")

            # If no more critical OR degraded deps, fully recover
            elif current in ("critical", "degraded") and not critical_deps and not degraded_deps:
                clone.nodes[node_id]["status"] = "healthy"
                clone.nodes[node_id]["error_rate"] = max(
                    attrs.get("error_rate", 0.0) * 0.05, 0.3
                )
                changed = True
                logger.debug(f"  Full recovery: {node_id} → healthy")

    return clone


def _propagate_reroute(
    G: nx.DiGraph,
    failed_node_id: str,
    replica_node_id: Optional[str],
) -> nx.DiGraph:
    """
    After adding a failover path, propagate recovery for nodes
    that were only blocked because of the failed node.
    """
    clone = G.copy()

    if failed_node_id not in clone:
        return clone

    # Connect callers to replica or direct dependencies
    callers = list(clone.predecessors(failed_node_id))
    dependencies = list(clone.successors(failed_node_id))

    if replica_node_id and replica_node_id in clone:
        for caller in callers:
            if not clone.has_edge(caller, replica_node_id):
                clone.add_edge(
                    caller,
                    replica_node_id,
                    type="Postgres",
                    weight=1.2,
                    latency_ms=8.0,
                    rps=500.0,
                    error_rate=0.0,
                )
        # Mark failed node as bypassed (degraded, not critical)
        clone.nodes[failed_node_id]["status"] = "degraded"
    else:
        for caller in callers:
            for dep in dependencies:
                if caller != dep and not clone.has_edge(caller, dep):
                    clone.add_edge(
                        caller, dep,
                        type="HTTP",
                        weight=2.0,
                        latency_ms=50.0,
                        rps=200.0,
                        error_rate=2.0,
                    )
        clone.nodes[failed_node_id]["status"] = "degraded"

    # Now propagate recovery for nodes that were only blocked by failed_node
    # Treat the failed node as degraded (not critical) for propagation
    changed = True
    iterations = 0
    max_iterations = 20

    while changed and iterations < max_iterations:
        changed = False
        iterations += 1

        for node_id in list(clone.nodes()):
            if node_id == failed_node_id:
                continue

            attrs = clone.nodes[node_id]
            current = attrs.get("status", "healthy")

            if current not in ("critical", "degraded"):
                continue

            # For reroute: check if this node's critical deps are cleared
            # We subtract the failed_node from consideration since it's bypassed
            dependencies_excl = [
                dep for dep in clone.successors(node_id)
                if dep != failed_node_id
            ]

            critical_deps = [
                dep for dep in dependencies_excl
                if clone.nodes[dep].get("status") == "critical"
            ]

            if current == "critical" and not critical_deps:
                clone.nodes[node_id]["status"] = "degraded"
                clone.nodes[node_id]["error_rate"] = max(
                    attrs.get("error_rate", 0.0) * 0.3, 5.0
                )
                clone.nodes[node_id]["latency_ms"] = max(
                    attrs.get("latency_ms", 1000.0) * 0.35, 100.0
                )
                changed = True

            elif current in ("critical", "degraded") and not critical_deps:
                # Check degraded deps too
                degraded_deps = [
                    dep for dep in dependencies_excl
                    if clone.nodes[dep].get("status") == "degraded"
                ]
                if not degraded_deps:
                    clone.nodes[node_id]["status"] = "healthy"
                    clone.nodes[node_id]["error_rate"] = 0.5
                    changed = True

    return clone


# ---------------------------------------------------------------------------
# Outcome comparison
# ---------------------------------------------------------------------------

def _get_failed_node_ids(G: nx.DiGraph) -> list[str]:
    """Return IDs of all nodes currently marked critical or degraded."""
    return [
        n for n, attrs in G.nodes(data=True)
        if attrs.get("status") in ("critical", "degraded")
    ]


def _compute_outcome(
    G_before: nx.DiGraph,
    G_after: nx.DiGraph,
    failed_node_ids: list[str],
    intervention_node_id: str,
) -> dict:
    """
    Compare before/after graphs to determine simulation outcome.

    A node is "recovered" if:
    - It was failed/degraded before the intervention
    - It is healthy after the intervention
    - It is not the intervention node itself

    A node is "still failing" if:
    - It was failed before AND is still failed/degraded after
    - It is not the intervention node
    """
    other_failed = [n for n in failed_node_ids if n != intervention_node_id]

    recovered = []
    still_failing = []

    for node_id in other_failed:
        status_before = G_before.nodes[node_id].get("status", "healthy")
        status_after = G_after.nodes[node_id].get("status", "healthy")

        was_failed = status_before in ("critical", "degraded")
        is_now_healthy = status_after == "healthy"
        is_still_failed = status_after in ("critical", "degraded")

        if was_failed and is_now_healthy:
            recovered.append(node_id)
        elif was_failed and is_still_failed:
            still_failing.append(node_id)

    recovery_rate = len(recovered) / len(other_failed) if other_failed else 1.0

    # Compute affected paths - show paths that now work after intervention
    affected_paths: list[list[str]] = []
    for entry in ENTRY_POINTS:
        for critical in CRITICAL_PATH_NODES:
            if entry != critical:
                try:
                    # Check if path is now unblocked
                    path_after = nx.shortest_path(G_after, entry, critical)
                    # Only include if it involves a recovered node
                    path_nodes_set = set(path_after)
                    if path_nodes_set.intersection(set(recovered)):
                        affected_paths.append(path_after)
                except nx.NetworkXNoPath:
                    pass

    # Outcome classification
    if recovery_rate >= 0.85:
        outcome = "full_recovery"
        outcome_label = (
            "Full Recovery - fixing this node would have prevented the incident"
        )
    elif recovery_rate >= 0.55:
        outcome = "partial_recovery"
        outcome_label = (
            f"Partial Recovery - {len(recovered)} of {len(other_failed)} "
            f"affected services would have recovered"
        )
    elif recovery_rate >= 0.25:
        outcome = "minimal_recovery"
        outcome_label = (
            f"Minimal Recovery - only {len(recovered)} service(s) recover; "
            f"cascading failure continues"
        )
    else:
        outcome = "no_recovery"
        outcome_label = (
            "No Recovery - this node alone is not the root cause; "
            "cascade continues regardless"
        )

    logger.info(
        f"Outcome: {outcome} | recovered={recovered} | "
        f"still_failing={still_failing} | rate={recovery_rate:.2%}"
    )

    return {
        "recovered": recovered,
        "still_failing": still_failing,
        "affected_paths": affected_paths,
        "recovery_rate": round(recovery_rate, 4),
        "outcome": outcome,
        "outcome_label": outcome_label,
    }


# ---------------------------------------------------------------------------
# Main simulation entry points
# ---------------------------------------------------------------------------

def simulate_node_removal(
    incident_id: str,
    node_id: str,
) -> CounterfactualResult:
    """
    Simulate: What would have happened if this node had NOT failed?
    Heals the node and propagates recovery through all dependents.
    """
    logger.info(f"Running node_removal: {node_id} for {incident_id}")

    nodes = fetch_all_nodes()
    edges = fetch_all_edges()
    G = build_networkx_graph(nodes, edges)

    if node_id not in G:
        raise ValueError(f"Node '{node_id}' not found in graph")

    node_name = G.nodes[node_id].get("name", node_id)
    failed_node_ids = _get_failed_node_ids(G)

    logger.info(f"Failed nodes before simulation: {failed_node_ids}")

    # Apply healing + propagate recovery
    G_after = _propagate_healing(G, healed_nodes={node_id})

    # Log after states for debugging
    for n in failed_node_ids:
        logger.info(
            f"  {n}: {G.nodes[n].get('status')} → "
            f"{G_after.nodes[n].get('status')}"
        )

    outcome = _compute_outcome(G, G_after, failed_node_ids, node_id)

    confidence = _score_simulation_confidence(
        simulation_type=SimulationType.NODE_REMOVAL,
        recovery_rate=outcome["recovery_rate"],
        node_attrs=G.nodes[node_id],
        failed_count=len(failed_node_ids),
    )

    explanation = _build_explanation(
        simulation_type=SimulationType.NODE_REMOVAL,
        node_name=node_name,
        outcome=outcome,
        confidence=confidence,
    )

    return CounterfactualResult(
        incident_id=incident_id,
        removed_node_id=node_id,
        removed_node_name=node_name,
        outcome=outcome["outcome"],
        affected_paths=outcome["affected_paths"],
        recovered_nodes=outcome["recovered"],
        still_failing_nodes=outcome["still_failing"],
        confidence=round(confidence, 4),
        explanation=explanation,
    )


def simulate_node_hardening(
    incident_id: str,
    node_id: str,
) -> CounterfactualResult:
    """
    Simulate: What if this node had circuit breakers and redundancy?
    Models graceful degradation - partial availability instead of hard failure.
    """
    logger.info(f"Running node_hardening: {node_id} for {incident_id}")

    nodes = fetch_all_nodes()
    edges = fetch_all_edges()
    G = build_networkx_graph(nodes, edges)

    if node_id not in G:
        raise ValueError(f"Node '{node_id}' not found in graph")

    node_name = G.nodes[node_id].get("name", node_id)
    failed_node_ids = _get_failed_node_ids(G)

    G_after = _propagate_hardening(G, hardened_node_id=node_id)

    for n in failed_node_ids:
        logger.info(
            f"  {n}: {G.nodes[n].get('status')} → "
            f"{G_after.nodes[n].get('status')}"
        )

    outcome = _compute_outcome(G, G_after, failed_node_ids, node_id)

    confidence = _score_simulation_confidence(
        simulation_type=SimulationType.NODE_HARDENING,
        recovery_rate=outcome["recovery_rate"],
        node_attrs=G.nodes[node_id],
        failed_count=len(failed_node_ids),
    )

    explanation = _build_explanation(
        simulation_type=SimulationType.NODE_HARDENING,
        node_name=node_name,
        outcome=outcome,
        confidence=confidence,
    )

    return CounterfactualResult(
        incident_id=incident_id,
        removed_node_id=node_id,
        removed_node_name=node_name,
        outcome=outcome["outcome"],
        affected_paths=outcome["affected_paths"],
        recovered_nodes=outcome["recovered"],
        still_failing_nodes=outcome["still_failing"],
        confidence=round(confidence, 4),
        explanation=explanation,
    )


def simulate_with_replica(
    incident_id: str,
    node_id: str,
    replica_node_id: Optional[str] = None,
) -> CounterfactualResult:
    """
    Simulate: What if a read replica or fallback existed for this node?
    """
    logger.info(
        f"Running replica_failover: {node_id} → {replica_node_id} "
        f"for {incident_id}"
    )

    nodes = fetch_all_nodes()
    edges = fetch_all_edges()
    G = build_networkx_graph(nodes, edges)

    if node_id not in G:
        raise ValueError(f"Node '{node_id}' not found in graph")

    node_name = G.nodes[node_id].get("name", node_id)
    failed_node_ids = _get_failed_node_ids(G)

    G_after = _propagate_reroute(G, node_id, replica_node_id)

    for n in failed_node_ids:
        logger.info(
            f"  {n}: {G.nodes[n].get('status')} → "
            f"{G_after.nodes[n].get('status')}"
        )

    outcome = _compute_outcome(G, G_after, failed_node_ids, node_id)

    confidence = _score_simulation_confidence(
        simulation_type=SimulationType.PATH_ANALYSIS,
        recovery_rate=outcome["recovery_rate"],
        node_attrs=G.nodes[node_id],
        failed_count=len(failed_node_ids),
    )

    replica_label = (
        G.nodes[replica_node_id].get("name", replica_node_id)
        if replica_node_id and replica_node_id in G
        else "direct dependency bypass"
    )

    explanation = _build_explanation(
        simulation_type=SimulationType.PATH_ANALYSIS,
        node_name=node_name,
        outcome=outcome,
        confidence=confidence,
        extra=f"Failover target: {replica_label}.",
    )

    return CounterfactualResult(
        incident_id=incident_id,
        removed_node_id=node_id,
        removed_node_name=node_name,
        outcome=outcome["outcome"],
        affected_paths=outcome["affected_paths"],
        recovered_nodes=outcome["recovered"],
        still_failing_nodes=outcome["still_failing"],
        confidence=round(confidence, 4),
        explanation=explanation,
    )


def run_full_simulation_suite(incident_id: str) -> dict:
    """
    Run all counterfactual scenarios and return a comprehensive report.
    """
    primary_node = "postgres-primary"

    results = {
        "incident_id": incident_id,
        "simulated_at": datetime.now(timezone.utc).isoformat(),
        "target_node": primary_node,
        "simulations": {},
    }

    scenarios = [
        (
            "node_removal",
            "What if PostgreSQL Primary had not failed?",
            lambda: simulate_node_removal(incident_id, primary_node),
        ),
        (
            "node_hardening",
            "What if PostgreSQL had circuit breakers and connection pooling limits?",
            lambda: simulate_node_hardening(incident_id, primary_node),
        ),
        (
            "replica_failover",
            "What if PostgreSQL Replica had been promoted automatically?",
            lambda: simulate_with_replica(incident_id, primary_node, "postgres-replica"),
        ),
        (
            "redis_hardening",
            "What if Redis had been configured with eviction fallback?",
            lambda: simulate_node_hardening(incident_id, "redis-cluster"),
        ),
    ]

    for key, question, runner in scenarios:
        try:
            result = runner()
            results["simulations"][key] = {
                "type": key,
                "question": question,
                "outcome": result.outcome,
                "recovered_nodes": result.recovered_nodes,
                "still_failing_nodes": result.still_failing_nodes,
                "confidence": result.confidence,
                "explanation": result.explanation,
                "affected_paths": result.affected_paths,
            }
        except Exception as exc:
            logger.error(f"Simulation '{key}' failed: {exc}")
            results["simulations"][key] = {"error": str(exc), "type": key}

    valid_sims = [
        v for v in results["simulations"].values()
        if "error" not in v
    ]
    best = max(valid_sims, key=lambda s: s.get("confidence", 0)) if valid_sims else None
    results["best_intervention"] = best

    return results


# ---------------------------------------------------------------------------
# Scoring and explanation helpers
# ---------------------------------------------------------------------------

def _score_simulation_confidence(
    simulation_type: SimulationType,
    recovery_rate: float,
    node_attrs: dict,
    failed_count: int,
) -> float:
    """Score confidence in the simulation outcome."""
    type_multiplier = {
        SimulationType.NODE_REMOVAL: 1.0,
        SimulationType.NODE_HARDENING: 0.85,
        SimulationType.PATH_ANALYSIS: 0.80,
    }.get(simulation_type, 0.8)

    status = node_attrs.get("status", "healthy")
    severity_bonus = {
        "critical": 0.10,
        "degraded": 0.05,
        "healthy": -0.05,
    }.get(status, 0.0)

    scale_bonus = min(failed_count / 15.0, 0.08)

    raw = (recovery_rate * type_multiplier) + severity_bonus + scale_bonus
    return round(min(max(raw, 0.0), 1.0), 4)


def _build_explanation(
    simulation_type: SimulationType,
    node_name: str,
    outcome: dict,
    confidence: float,
    extra: str = "",
) -> str:
    """Build a deterministic plain-English explanation of the simulation."""
    recovered_count = len(outcome["recovered"])
    failing_count = len(outcome["still_failing"])
    rate_pct = outcome["recovery_rate"] * 100

    prefix = {
        SimulationType.NODE_REMOVAL: f"If {node_name} had remained healthy",
        SimulationType.NODE_HARDENING: f"If {node_name} had circuit breakers and connection limits",
        SimulationType.PATH_ANALYSIS: f"If a failover path existed for {node_name}",
    }.get(simulation_type, f"If {node_name} was fixed")

    parts = [
        f"{prefix}, {recovered_count} service(s) would have recovered "
        f"({rate_pct:.0f}% recovery rate).",
    ]

    if outcome["still_failing"]:
        parts.append(
            f"{failing_count} service(s) would still be affected: "
            f"{', '.join(outcome['still_failing'][:3])}."
        )

    if extra:
        parts.append(extra)

    parts.append(
        f"Simulation confidence: {confidence * 100:.0f}%. "
        f"Outcome: {outcome['outcome_label']}."
    )

    return " ".join(parts)