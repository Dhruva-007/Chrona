from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class NodeStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class NodeType(str, Enum):
    SERVICE = "service"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    GATEWAY = "gateway"
    CDN = "cdn"
    LOADBALANCER = "loadbalancer"
    EXTERNAL = "external"


class EdgeType(str, Enum):
    HTTP = "HTTP"
    GRPC = "gRPC"
    TCP = "TCP"
    AMQP = "AMQP"
    REDIS = "Redis"
    POSTGRES = "Postgres"
    MONGO = "MongoDB"


class InfraNode(BaseModel):
    """Represents a node in the infrastructure graph."""
    id: str
    name: str
    type: NodeType
    status: NodeStatus = NodeStatus.HEALTHY
    namespace: str = "production"
    version: str = "1.0.0"
    replicas: int = 1
    cpu_usage: float = Field(default=0.0, ge=0.0, le=100.0)
    memory_usage: float = Field(default=0.0, ge=0.0, le=100.0)
    error_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    latency_ms: float = Field(default=0.0, ge=0.0)
    metadata: dict = Field(default_factory=dict)


class InfraEdge(BaseModel):
    """Represents a directed dependency edge between nodes."""
    source: str
    target: str
    type: EdgeType = EdgeType.HTTP
    weight: float = Field(default=1.0, ge=0.0)
    latency_ms: float = Field(default=0.0, ge=0.0)
    requests_per_second: float = Field(default=0.0, ge=0.0)
    error_rate: float = Field(default=0.0, ge=0.0, le=100.0)


class GraphSnapshot(BaseModel):
    """A point-in-time snapshot of the infrastructure graph."""
    nodes: list[InfraNode]
    edges: list[InfraEdge]
    timestamp: str
    incident_id: Optional[str] = None


class TraversalPath(BaseModel):
    """A single path through the graph."""
    nodes: list[str]
    total_latency_ms: float = 0.0
    hop_count: int = 0
    contains_failure: bool = False


class TraversalResult(BaseModel):
    """Result of a graph traversal operation."""
    source_node: str
    target_node: Optional[str] = None
    paths: list[TraversalPath] = Field(default_factory=list)
    ancestors: list[str] = Field(default_factory=list)
    descendants: list[str] = Field(default_factory=list)
    depth: int = 0


class ImpactAnalysis(BaseModel):
    """Impact analysis for a given node failure."""
    failed_node_id: str
    failed_node_name: str
    directly_affected: list[str] = Field(default_factory=list)
    transitively_affected: list[str] = Field(default_factory=list)
    total_affected_count: int = 0
    critical_path_broken: bool = False
    estimated_blast_radius_percent: float = 0.0


class GraphHealthSummary(BaseModel):
    """Overall health summary of the infrastructure graph."""
    total_nodes: int
    healthy_nodes: int
    degraded_nodes: int
    critical_nodes: int
    unknown_nodes: int
    total_edges: int
    health_score: float = Field(ge=0.0, le=100.0)
    critical_node_ids: list[str] = Field(default_factory=list)
    degraded_node_ids: list[str] = Field(default_factory=list)