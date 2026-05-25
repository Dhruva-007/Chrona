export interface GraphHealthSummary {
  success: boolean;
  message: string;
  data: {
    total_nodes: number;
    healthy_nodes: number;
    degraded_nodes: number;
    critical_nodes: number;
    unknown_nodes: number;
    total_edges: number;
    health_score: number;
    critical_node_ids: string[];
    degraded_node_ids: string[];
  };
}

export interface RootCauseCandidate {
  node_id: string;
  node_name: string;
  node_type: string;
  confidence_score: number;
  reasoning: string[];
  downstream_impact: string[];
  time_to_first_failure_ms?: number;
}

export interface RootCauseAnalysisResponse {
  success: boolean;
  message: string;
  data: {
    incident_id: string;
    primary_cause: RootCauseCandidate;
    contributing_factors: RootCauseCandidate[];
    blast_radius: string[];
    propagation_path: string[];
    analysis_confidence: number;
    computed_at: string;
  };
}

export interface SimulationResult {
  type: string;
  question: string;
  outcome: string;
  recovered_nodes: string[];
  still_failing_nodes: string[];
  confidence: number;
  explanation: string;
}

export interface SimulationSuite {
  success: boolean;
  message: string;
  data: {
    incident_id: string;
    simulations: {
      node_removal: SimulationResult;
      node_hardening: SimulationResult;
      replica_failover: SimulationResult;
    };
  };
}

export interface InfrastructureNode {
  id: string;
  name: string;
  type: string;
  status: "healthy" | "degraded" | "critical";
  namespace: string;
  version: string;
  replicas: number;
  cpu_usage: number;
  memory_usage: number;
  error_rate: number;
  latency_ms: number;
}

export interface InfrastructureEdge {
  source: string;
  target: string;
  type: string;
  latency_ms: number;
  requests_per_second: number;
  error_rate: number;
}

export interface GraphResponse {
  success: boolean;
  message: string;
  data: {
    nodes: InfrastructureNode[];
    edges: InfrastructureEdge[];
    timestamp: string;
    incident_id: string | null;
  };
}

export interface IncidentSummaryResponse {
  success: boolean;
  data: {
    incident_id: string;
    summary: string;
    root_cause: string;
    confidence: number;
    affected_services: number;
  };
}

export interface PostmortemResponse {
  success: boolean;
  data: {
    incident_overview: {
      title: string;
      description: string;
      severity: string;
      status: string;
    };
    root_cause: {
      node: string;
      confidence: number;
      explanation: string;
    };
    timeline: Array<{
      timestamp: string;
      node_name: string;
      message: string;
      severity: string;
    }>;
    immediate_actions: string[];
    preventive_actions: string[];
    lessons_learned: string[];
  };
}

export interface TelemetryAlert {
  source: string;
  severity: string;
  service: string;
  message: string;
  timestamp: string;
}

export interface TelemetryLog {
  service: string;
  level: string;
  message: string;
  timestamp: string;
}

export interface TelemetryResponse {
  success: boolean;
  message: string;
  data: {
    incident_id: string;
    source: string;
    alerts: TelemetryAlert[];
    logs: TelemetryLog[];
    metrics: Record<
      string,
      {
        cpu_percent: number;
        memory_percent: number;
        latency_ms: number;
        error_rate: number;
        active_connections?: number;
      }
    >;
  };
}