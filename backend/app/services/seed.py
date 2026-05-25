"""
Seed the Memgraph database with a realistic simulated microservice
infrastructure for Chrona demos. This represents a typical e-commerce
platform with 15 services across 3 namespaces.
"""

import logging
from datetime import datetime, timezone
from app.services.memgraph import run_query

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Infrastructure definition
# ---------------------------------------------------------------------------

NODES: list[dict] = [
    # API Gateway layer
    {
        "id": "gateway-01",
        "name": "API Gateway",
        "type": "gateway",
        "namespace": "production",
        "version": "2.4.1",
        "replicas": 3,
        "cpu_usage": 34.2,
        "memory_usage": 41.0,
        "error_rate": 0.1,
        "latency_ms": 12.0,
        "status": "healthy",
    },
    {
        "id": "cdn-01",
        "name": "CloudFront CDN",
        "type": "cdn",
        "namespace": "production",
        "version": "1.0.0",
        "replicas": 1,
        "cpu_usage": 5.0,
        "memory_usage": 8.0,
        "error_rate": 0.0,
        "latency_ms": 2.0,
        "status": "healthy",
    },
    # Core services
    {
        "id": "user-svc",
        "name": "User Service",
        "type": "service",
        "namespace": "production",
        "version": "3.1.0",
        "replicas": 2,
        "cpu_usage": 22.5,
        "memory_usage": 38.0,
        "error_rate": 0.2,
        "latency_ms": 45.0,
        "status": "healthy",
    },
    {
        "id": "order-svc",
        "name": "Order Service",
        "type": "service",
        "namespace": "production",
        "version": "2.8.3",
        "replicas": 3,
        "cpu_usage": 55.1,
        "memory_usage": 62.0,
        "error_rate": 0.5,
        "latency_ms": 120.0,
        "status": "healthy",
    },
    {
        "id": "payment-svc",
        "name": "Payment Service",
        "type": "service",
        "namespace": "production",
        "version": "1.9.7",
        "replicas": 2,
        "cpu_usage": 41.0,
        "memory_usage": 55.0,
        "error_rate": 0.3,
        "latency_ms": 230.0,
        "status": "healthy",
    },
    {
        "id": "inventory-svc",
        "name": "Inventory Service",
        "type": "service",
        "namespace": "production",
        "version": "2.2.1",
        "replicas": 2,
        "cpu_usage": 30.0,
        "memory_usage": 44.0,
        "error_rate": 0.1,
        "latency_ms": 67.0,
        "status": "healthy",
    },
    {
        "id": "notification-svc",
        "name": "Notification Service",
        "type": "service",
        "namespace": "production",
        "version": "1.5.2",
        "replicas": 2,
        "cpu_usage": 18.0,
        "memory_usage": 29.0,
        "error_rate": 0.2,
        "latency_ms": 88.0,
        "status": "healthy",
    },
    {
        "id": "search-svc",
        "name": "Search Service",
        "type": "service",
        "namespace": "production",
        "version": "4.0.2",
        "replicas": 3,
        "cpu_usage": 70.0,
        "memory_usage": 78.0,
        "error_rate": 0.4,
        "latency_ms": 95.0,
        "status": "healthy",
    },
    {
        "id": "recommendation-svc",
        "name": "Recommendation Service",
        "type": "service",
        "namespace": "production",
        "version": "2.1.0",
        "replicas": 2,
        "cpu_usage": 60.0,
        "memory_usage": 72.0,
        "error_rate": 0.3,
        "latency_ms": 180.0,
        "status": "healthy",
    },
    # Data layer
    {
        "id": "postgres-primary",
        "name": "PostgreSQL Primary",
        "type": "database",
        "namespace": "data",
        "version": "15.3",
        "replicas": 1,
        "cpu_usage": 48.0,
        "memory_usage": 71.0,
        "error_rate": 0.0,
        "latency_ms": 4.0,
        "status": "healthy",
    },
    {
        "id": "postgres-replica",
        "name": "PostgreSQL Replica",
        "type": "database",
        "namespace": "data",
        "version": "15.3",
        "replicas": 1,
        "cpu_usage": 35.0,
        "memory_usage": 65.0,
        "error_rate": 0.0,
        "latency_ms": 5.0,
        "status": "healthy",
    },
    {
        "id": "redis-cluster",
        "name": "Redis Cluster",
        "type": "cache",
        "namespace": "data",
        "version": "7.2.0",
        "replicas": 3,
        "cpu_usage": 25.0,
        "memory_usage": 58.0,
        "error_rate": 0.0,
        "latency_ms": 1.0,
        "status": "healthy",
    },
    {
        "id": "kafka-cluster",
        "name": "Kafka Cluster",
        "type": "queue",
        "namespace": "data",
        "version": "3.6.0",
        "replicas": 3,
        "cpu_usage": 42.0,
        "memory_usage": 55.0,
        "error_rate": 0.0,
        "latency_ms": 8.0,
        "status": "healthy",
    },
    {
        "id": "elasticsearch",
        "name": "Elasticsearch",
        "type": "database",
        "namespace": "data",
        "version": "8.11.0",
        "replicas": 3,
        "cpu_usage": 65.0,
        "memory_usage": 80.0,
        "error_rate": 0.0,
        "latency_ms": 15.0,
        "status": "healthy",
    },
    # External
    {
        "id": "stripe-api",
        "name": "Stripe API",
        "type": "external",
        "namespace": "external",
        "version": "2024-01-01",
        "replicas": 1,
        "cpu_usage": 0.0,
        "memory_usage": 0.0,
        "error_rate": 0.1,
        "latency_ms": 320.0,
        "status": "healthy",
    },
]

EDGES: list[dict] = [
    # CDN → Gateway
    {"source": "cdn-01", "target": "gateway-01", "type": "HTTP",
     "weight": 1.0, "latency_ms": 2.0, "rps": 8500.0, "error_rate": 0.0},

    # Gateway → Services
    {"source": "gateway-01", "target": "user-svc", "type": "HTTP",
     "weight": 1.0, "latency_ms": 12.0, "rps": 1200.0, "error_rate": 0.1},
    {"source": "gateway-01", "target": "order-svc", "type": "HTTP",
     "weight": 1.0, "latency_ms": 18.0, "rps": 850.0, "error_rate": 0.2},
    {"source": "gateway-01", "target": "search-svc", "type": "HTTP",
     "weight": 1.0, "latency_ms": 10.0, "rps": 3200.0, "error_rate": 0.1},
    {"source": "gateway-01", "target": "recommendation-svc", "type": "HTTP",
     "weight": 1.0, "latency_ms": 15.0, "rps": 600.0, "error_rate": 0.1},

    # Order Service dependencies
    {"source": "order-svc", "target": "payment-svc", "type": "gRPC",
     "weight": 1.0, "latency_ms": 45.0, "rps": 420.0, "error_rate": 0.3},
    {"source": "order-svc", "target": "inventory-svc", "type": "gRPC",
     "weight": 1.0, "latency_ms": 30.0, "rps": 780.0, "error_rate": 0.1},
    {"source": "order-svc", "target": "notification-svc", "type": "AMQP",
     "weight": 0.5, "latency_ms": 5.0, "rps": 420.0, "error_rate": 0.0},
    {"source": "order-svc", "target": "postgres-primary", "type": "Postgres",
     "weight": 1.0, "latency_ms": 8.0, "rps": 1600.0, "error_rate": 0.0},
    {"source": "order-svc", "target": "redis-cluster", "type": "Redis",
     "weight": 1.0, "latency_ms": 1.0, "rps": 4200.0, "error_rate": 0.0},

    # Payment Service dependencies
    {"source": "payment-svc", "target": "stripe-api", "type": "HTTP",
     "weight": 1.0, "latency_ms": 320.0, "rps": 420.0, "error_rate": 0.1},
    {"source": "payment-svc", "target": "postgres-primary", "type": "Postgres",
     "weight": 1.0, "latency_ms": 4.0, "rps": 840.0, "error_rate": 0.0},
    {"source": "payment-svc", "target": "redis-cluster", "type": "Redis",
     "weight": 1.0, "latency_ms": 1.0, "rps": 1800.0, "error_rate": 0.0},

    # User Service dependencies
    {"source": "user-svc", "target": "postgres-primary", "type": "Postgres",
     "weight": 1.0, "latency_ms": 4.0, "rps": 2400.0, "error_rate": 0.0},
    {"source": "user-svc", "target": "redis-cluster", "type": "Redis",
     "weight": 1.0, "latency_ms": 1.0, "rps": 6000.0, "error_rate": 0.0},

    # Inventory Service dependencies
    {"source": "inventory-svc", "target": "postgres-primary", "type": "Postgres",
     "weight": 1.0, "latency_ms": 4.0, "rps": 1100.0, "error_rate": 0.0},
    {"source": "inventory-svc", "target": "kafka-cluster", "type": "AMQP",
     "weight": 1.0, "latency_ms": 8.0, "rps": 340.0, "error_rate": 0.0},

    # Notification Service dependencies
    {"source": "notification-svc", "target": "kafka-cluster", "type": "AMQP",
     "weight": 1.0, "latency_ms": 8.0, "rps": 420.0, "error_rate": 0.0},

    # Search Service dependencies
    {"source": "search-svc", "target": "elasticsearch", "type": "HTTP",
     "weight": 1.0, "latency_ms": 15.0, "rps": 3200.0, "error_rate": 0.0},
    {"source": "search-svc", "target": "redis-cluster", "type": "Redis",
     "weight": 1.0, "latency_ms": 1.0, "rps": 2800.0, "error_rate": 0.0},

    # Recommendation Service dependencies
    {"source": "recommendation-svc", "target": "redis-cluster", "type": "Redis",
     "weight": 1.0, "latency_ms": 1.0, "rps": 1400.0, "error_rate": 0.0},
    {"source": "recommendation-svc", "target": "elasticsearch", "type": "HTTP",
     "weight": 1.0, "latency_ms": 15.0, "rps": 600.0, "error_rate": 0.0},

    # PostgreSQL replication
    {"source": "postgres-primary", "target": "postgres-replica", "type": "TCP",
     "weight": 1.0, "latency_ms": 2.0, "rps": 500.0, "error_rate": 0.0},
]


def clear_graph() -> None:
    """Wipe all nodes and edges from Memgraph."""
    run_query("MATCH (n) DETACH DELETE n")
    logger.info("Graph cleared.")


def seed_nodes() -> None:
    """Insert all infrastructure nodes into Memgraph."""
    cypher = """
    MERGE (n:InfraNode {id: $id})
    SET n.name          = $name,
        n.type          = $type,
        n.namespace     = $namespace,
        n.version       = $version,
        n.replicas      = $replicas,
        n.cpu_usage     = $cpu_usage,
        n.memory_usage  = $memory_usage,
        n.error_rate    = $error_rate,
        n.latency_ms    = $latency_ms,
        n.status        = $status
    """
    for node in NODES:
        run_query(cypher, node)
    logger.info(f"Seeded {len(NODES)} nodes.")


def seed_edges() -> None:
    """Insert all dependency edges into Memgraph."""
    cypher = """
    MATCH (a:InfraNode {id: $source})
    MATCH (b:InfraNode {id: $target})
    MERGE (a)-[r:DEPENDS_ON {type: $type}]->(b)
    SET r.weight     = $weight,
        r.latency_ms = $latency_ms,
        r.rps        = $rps,
        r.error_rate = $error_rate
    """
    for edge in EDGES:
        run_query(cypher, edge)
    logger.info(f"Seeded {len(EDGES)} edges.")


def seed_graph(force: bool = False) -> dict:
    """
    Seed the full infrastructure graph.
    If force=True, wipe existing data first.
    Returns a summary dict.
    """
    seeded_at = datetime.now(timezone.utc).isoformat()

    if force:
        clear_graph()

    seed_nodes()
    seed_edges()

    logger.info("Infrastructure graph seeded successfully.")
    return {
        "nodes_seeded": len(NODES),
        "edges_seeded": len(EDGES),
        "seeded_at": seeded_at,
        "status": "success",
    }


def get_graph_stats() -> dict:
    """Return basic graph statistics from Memgraph."""
    node_count = run_query("MATCH (n:InfraNode) RETURN count(n) AS count")
    edge_count = run_query("MATCH ()-[r:DEPENDS_ON]->() RETURN count(r) AS count")
    return {
        "node_count": node_count[0]["count"] if node_count else 0,
        "edge_count": edge_count[0]["count"] if edge_count else 0,
    }