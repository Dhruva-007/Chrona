from typing import Any, Dict

from app.models.agent import AgentAnalyzeRequest
from app.services.causal_engine import run_root_cause_analysis
from app.services.connectors.connector_factory import get_connector
from app.services.graph_service import (
    compute_health_summary,
    fetch_all_edges,
    fetch_all_nodes,
)
from app.services.llm_service import analyze_with_llm
from app.services.simulation_engine import run_full_simulation_suite
from app.services.telemetry_parser import build_telemetry_context


def _build_deterministic_context(
    incident_id: str,
) -> Dict[str, Any]:
    nodes = fetch_all_nodes()
    edges = fetch_all_edges()
    health = compute_health_summary(nodes)

    root_analysis = run_root_cause_analysis(incident_id)
    simulation = run_full_simulation_suite(incident_id)

    return {
        "root_analysis": root_analysis,
        "simulation": simulation,
        "health": health,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


def _build_agent_context(
    telemetry_context: str,
    deterministic: Dict[str, Any],
) -> str:
    root = deterministic["root_analysis"]
    health = deterministic["health"]
    simulation = deterministic["simulation"]
    primary = root.primary_cause

    return f"""
CHRONA INCIDENT ANALYSIS CONTEXT

TELEMETRY INPUT:
{telemetry_context}

DETERMINISTIC ROOT CAUSE:
Primary Cause: {primary.node_name}
Confidence: {primary.confidence_score}
Reasoning: {primary.reasoning}

BLAST RADIUS:
{root.blast_radius}

PROPAGATION PATH:
{root.propagation_path}

INFRASTRUCTURE HEALTH:
Healthy Nodes: {health.healthy_nodes}
Degraded Nodes: {health.degraded_nodes}
Critical Nodes: {health.critical_nodes}
Health Score: {health.health_score}

SIMULATION RESULTS:
{simulation}

GRAPH TOPOLOGY:
Nodes: {deterministic['node_count']}
Edges: {deterministic['edge_count']}

TASK:
Act as a senior SRE AI incident response agent.
Use telemetry plus deterministic infrastructure evidence.
Produce final diagnosis.
"""


def run_agent_analysis(
    payload: AgentAnalyzeRequest,
) -> Dict[str, Any]:
    connector = get_connector(payload.source)

    telemetry_payload = connector.fetch_incident_context(
        payload.incident_id
    )

    telemetry_context = build_telemetry_context(
        telemetry_payload
    )

    deterministic = _build_deterministic_context(
        payload.incident_id
    )

    llm_context = _build_agent_context(
        telemetry_context,
        deterministic,
    )

    llm_result = analyze_with_llm(llm_context)

    health = deterministic["health"]

    return {
        "root_cause": llm_result["root_cause"],
        "confidence": llm_result["confidence"],
        "reasoning": llm_result["reasoning"],
        "recommended_actions": llm_result["recommended_actions"],
        "ai_summary": llm_result["ai_summary"],
        "telemetry_source": payload.source,
        "infrastructure_health": {
            "total_nodes": health.total_nodes,
            "healthy_nodes": health.healthy_nodes,
            "degraded_nodes": health.degraded_nodes,
            "critical_nodes": health.critical_nodes,
            "health_score": health.health_score,
        },
    }