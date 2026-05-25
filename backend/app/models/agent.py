from pydantic import BaseModel
from typing import Optional


class AgentAnalyzeRequest(BaseModel):
    incident_id: str
    source: str = "datadog"
    live_mode: bool = False


class AgentAnalyzeResponse(BaseModel):
    root_cause: str
    confidence: float
    reasoning: list[str]
    recommended_actions: list[str]
    ai_summary: str