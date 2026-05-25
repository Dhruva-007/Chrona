from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class EventSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    ACTIVE = "active"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class TimelineEvent(BaseModel):
    """A single event in the incident timeline."""
    timestamp: str
    node_id: str
    node_name: str
    event_type: str
    severity: EventSeverity
    message: str
    metrics: dict = Field(default_factory=dict)


class RootCauseCandidate(BaseModel):
    """A candidate node identified as potential root cause."""
    node_id: str
    node_name: str
    node_type: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: list[str] = Field(default_factory=list)
    downstream_impact: list[str] = Field(default_factory=list)
    time_to_first_failure_ms: Optional[float] = None


class RootCauseAnalysis(BaseModel):
    """Complete root cause analysis result."""
    incident_id: str
    primary_cause: RootCauseCandidate
    contributing_factors: list[RootCauseCandidate]
    blast_radius: list[str]
    propagation_path: list[str]
    analysis_confidence: float = Field(ge=0.0, le=1.0)
    computed_at: str


class CounterfactualResult(BaseModel):
    """Result of a counterfactual simulation."""
    incident_id: str
    removed_node_id: str
    removed_node_name: str
    outcome: str
    affected_paths: list[list[str]]
    recovered_nodes: list[str]
    still_failing_nodes: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str


class Incident(BaseModel):
    """A full production incident record."""
    id: str
    title: str
    description: str
    status: IncidentStatus = IncidentStatus.ACTIVE
    severity: EventSeverity = EventSeverity.CRITICAL
    started_at: str
    resolved_at: Optional[str] = None
    affected_nodes: list[str] = Field(default_factory=list)
    root_cause: Optional[RootCauseAnalysis] = None
    timeline: list[TimelineEvent] = Field(default_factory=list)