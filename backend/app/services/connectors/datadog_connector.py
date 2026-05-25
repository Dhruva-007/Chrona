import json
from pathlib import Path
from typing import Any, Dict

import httpx

from app.core.config import settings
from app.services.connectors.base import MonitoringConnector


class DatadogConnector(MonitoringConnector):
    """
    Datadog telemetry provider.

    Modes:
    - file  : local ingestion payload
    - live  : real Datadog API
    """

    def _headers(self) -> Dict[str, str]:
        return {
            "DD-API-KEY": settings.DATADOG_API_KEY,
            "DD-APPLICATION-KEY": settings.DATADOG_APP_KEY,
            "Content-Type": "application/json",
        }

    def _base_url(self) -> str:
        return f"https://api.{settings.DATADOG_SITE}"

    def _load_file_payload(self) -> Dict[str, Any]:
        payload_path = (
            Path(__file__)
            .resolve()
            .parents[3]
            / "telemetry"
            / "datadog_incident.json"
        )

        with open(
            payload_path,
            "r",
            encoding="utf-8",
        ) as f:
            return json.load(f)

    def _fetch_live_payload(
        self,
        incident_id: str,
    ) -> Dict[str, Any]:
        if (
            not settings.DATADOG_API_KEY
            or not settings.DATADOG_APP_KEY
        ):
            raise ValueError(
                "Datadog credentials missing"
            )

        with httpx.Client(timeout=20.0) as client:
            monitors = client.get(
                f"{self._base_url()}/api/v1/monitor",
                headers=self._headers(),
            )

            monitors.raise_for_status()

            events = client.get(
                f"{self._base_url()}/api/v1/events",
                headers=self._headers(),
                params={"priority": "normal"},
            )

            events.raise_for_status()

        monitor_data = monitors.json()
        event_data = events.json()

        alerts = []

        for monitor in monitor_data[:10]:
            alerts.append(
                {
                    "severity": "critical"
                    if monitor.get("overall_state")
                    == "Alert"
                    else "warning",
                    "service": monitor.get(
                        "name",
                        "unknown-monitor",
                    ),
                    "message": monitor.get(
                        "message",
                        "No message",
                    ),
                    "timestamp": "",
                }
            )

        logs = []

        for event in event_data.get("events", [])[:10]:
            logs.append(
                {
                    "service": "datadog-event",
                    "level": "info",
                    "message": event.get(
                        "title",
                        "No event title",
                    ),
                    "timestamp": event.get(
                        "date_happened",
                        "",
                    ),
                }
            )

        return {
            "alerts": alerts,
            "logs": logs,
            "metrics": {},
        }

    def _normalize_payload(
        self,
        incident_id: str,
        raw: Dict[str, Any],
    ) -> Dict[str, Any]:
        alerts = []

        for alert in raw.get("alerts", []):
            alerts.append(
                {
                    "source": "datadog",
                    "severity": alert.get(
                        "severity",
                        "warning",
                    ),
                    "service": alert.get(
                        "service",
                        "unknown",
                    ),
                    "message": alert.get(
                        "message",
                        "No message",
                    ),
                    "timestamp": str(
                        alert.get("timestamp", "")
                    ),
                }
            )

        logs = []

        for log in raw.get("logs", []):
            logs.append(
                {
                    "service": log.get(
                        "service",
                        "unknown",
                    ),
                    "level": log.get(
                        "level",
                        "info",
                    ),
                    "message": log.get(
                        "message",
                        "",
                    ),
                    "timestamp": str(
                        log.get("timestamp", "")
                    ),
                }
            )

        return {
            "incident_id": incident_id,
            "source": "datadog",
            "alerts": alerts,
            "logs": logs,
            "metrics": raw.get("metrics", {}),
        }

    def fetch_incident_context(
        self,
        incident_id: str,
    ) -> Dict[str, Any]:
        if settings.TELEMETRY_MODE == "live":
            try:
                raw = self._fetch_live_payload(
                    incident_id
                )
            except Exception:
                raw = self._load_file_payload()
        else:
            raw = self._load_file_payload()

        return self._normalize_payload(
            incident_id,
            raw,
        )