import {
  GraphHealthSummary,
  RootCauseAnalysisResponse,
  SimulationSuite,
  GraphResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000";

const INCIDENT_ID = "INC-2024-001";

async function apiFetch(
  path: string,
  options?: RequestInit
) {
  const res = await fetch(
    `${API_BASE}${path}`,
    {
      cache: "no-store",
      ...options,
    }
  );

  if (!res.ok) {
    const text =
      await res.text();

    throw new Error(
      `API request failed: ${res.status} ${text}`
    );
  }

  return res.json();
}

export async function fetchHealthSummary(): Promise<GraphHealthSummary> {
  return apiFetch(
    "/api/v1/graph/health-summary"
  );
}

export async function fetchRootCauseAnalysis(): Promise<RootCauseAnalysisResponse> {
  return apiFetch(
    `/api/v1/incidents/${INCIDENT_ID}/analyze`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
    }
  );
}

export async function fetchSimulationSuite(): Promise<SimulationSuite> {
  return apiFetch(
    `/api/v1/simulation/suite/${INCIDENT_ID}`
  );
}

export async function fetchInfrastructureGraph(): Promise<GraphResponse> {
  return apiFetch("/api/v1/graph/");
}

export async function fetchCounterfactual(
  nodeId: string
) {
  return apiFetch(
    `/api/v1/simulation/counterfactual/${INCIDENT_ID}/${nodeId}`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
    }
  );
}

export async function fetchRemediation(
  nodeId: string
) {
  return apiFetch(
    `/api/v1/simulation/remediate/${INCIDENT_ID}/${nodeId}`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
    }
  );
}

export async function fetchIncidentSummary() {
  return apiFetch(
    `/api/v1/narrative/${INCIDENT_ID}/summary`
  );
}

export async function fetchPostmortem() {
  return apiFetch(
    `/api/v1/narrative/${INCIDENT_ID}/postmortem`
  );
}

export async function runAgentAnalysis(
  source = "datadog"
) {
  return apiFetch(
    "/api/v1/agent/analyze",
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify({
        incident_id:
          INCIDENT_ID,
        source,
        live_mode: true,
      }),
    }
  );
}

export async function fetchTelemetry(
  source = "datadog"
) {
  return apiFetch(
    `/api/v1/telemetry/incident/${INCIDENT_ID}?source=${source}`
  );
}

export async function fetchAgentAnalysis() {
  return apiFetch(
    "/api/v1/agent/latest"
  );
}