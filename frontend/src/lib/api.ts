import {
  GraphHealthSummary,
  RootCauseAnalysisResponse,
  SimulationSuite,
  GraphResponse,
} from "./types";

const API_BASE = "http://localhost:8000";
const INCIDENT_ID = "INC-2024-001";

export async function fetchHealthSummary(): Promise<GraphHealthSummary> {
  const res = await fetch(`${API_BASE}/api/v1/graph/health-summary`, {
    cache: "no-store",
  });

  if (!res.ok) throw new Error("Failed to fetch health summary");

  return res.json();
}

export async function fetchRootCauseAnalysis(): Promise<RootCauseAnalysisResponse> {
  const res = await fetch(
    `${API_BASE}/api/v1/incidents/${INCIDENT_ID}/analyze`,
    {
      method: "POST",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!res.ok) throw new Error("Failed to fetch root cause analysis");

  return res.json();
}

export async function fetchSimulationSuite(): Promise<SimulationSuite> {
  const res = await fetch(
    `${API_BASE}/api/v1/simulation/suite/${INCIDENT_ID}`,
    {
      cache: "no-store",
    }
  );

  if (!res.ok) throw new Error("Failed to fetch simulation suite");

  return res.json();
}

export async function fetchInfrastructureGraph(): Promise<GraphResponse> {
  const res = await fetch(`${API_BASE}/api/v1/graph/`, {
    cache: "no-store",
  });

  if (!res.ok) throw new Error("Failed to fetch graph");

  return res.json();
}

export async function fetchCounterfactual(nodeId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/simulation/counterfactual/${INCIDENT_ID}/${nodeId}`,
    {
      method: "POST",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!res.ok) {
    throw new Error("Failed counterfactual simulation");
  }

  return res.json();
}

export async function fetchRemediation(nodeId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/simulation/remediate/${INCIDENT_ID}/${nodeId}`,
    {
      method: "POST",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!res.ok) {
    throw new Error("Failed remediation simulation");
  }

  return res.json();
}

export async function fetchIncidentSummary() {
  const res = await fetch(
    `${API_BASE}/api/v1/narrative/${INCIDENT_ID}/summary`,
    {
      cache: "no-store",
    }
  );

  if (!res.ok) {
    throw new Error("Failed to fetch incident summary");
  }

  return res.json();
}

export async function fetchPostmortem() {
  const res = await fetch(
    `${API_BASE}/api/v1/narrative/${INCIDENT_ID}/postmortem`,
    {
      cache: "no-store",
    }
  );

  if (!res.ok) {
    throw new Error("Failed to fetch postmortem");
  }

  return res.json();
}

export async function runAgentAnalysis(
  source = "datadog"
) {
  const res = await fetch(
    `${API_BASE}/api/v1/agent/analyze`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify({
        incident_id: "INC-2024-001",
        source,
        live_mode: true,
      }),
    }
  );

  if (!res.ok) {
    throw new Error(
      "AI analysis failed"
    );
  }

  return res.json();
}

export async function fetchTelemetry(
  source = "datadog"
) {
  const res = await fetch(
    `${API_BASE}/api/v1/telemetry/incident/INC-2024-001?source=${source}`,
    {
      cache: "no-store",
    }
  );

  if (!res.ok) {
    throw new Error("Failed to fetch telemetry");
  }

  return res.json();
}

export async function fetchAgentAnalysis() {
  const res = await fetch(
    "http://localhost:8000/api/v1/agent/latest",
    {
      cache: "no-store",
    }
  );

  if (!res.ok) {
    throw new Error(
      "Failed to fetch AI analysis"
    );
  }

  return res.json();
}