from typing import Any, Dict
import httpx

from app.core.config import settings
from app.services.connectors.base import MonitoringConnector


class GrafanaConnector(MonitoringConnector):
    """
    Grafana telemetry connector.
    Supports:
    - file fallback MVP
    - live Grafana API
    """

    def _headers(self):
        return {
            "Authorization": f"Bearer {settings.GRAFANA_API_KEY}",
            "Content-Type": "application/json",
        }

    def _fetch_live_payload(
        self,
        incident_id: str,
    ) -> Dict[str, Any]:
        if (
            not settings.GRAFANA_URL
            or not settings.GRAFANA_API_KEY
        ):
            raise ValueError(
                "Grafana credentials missing"
            )

        with httpx.Client(timeout=20.0) as client:
            alerts = client.get(
                f"{settings.GRAFANA_URL}/api/alertmanager/grafana/api/v2/alerts",
                headers=self._headers(),
            )

            alerts.raise_for_status()

        alert_data = alerts.json()

        normalized_alerts = []

        for item in alert_data[:10]:
            labels = item.get("labels", {})

            normalized_alerts.append(
                {
                    "severity": labels.get(
                        "severity",
                        "warning",
                    ),
                    "service": labels.get(
                        "service",
                        "grafana-service",
                    ),
                    "message": item.get(
                        "annotations",
                        {}
                    ).get(
                        "summary",
                        "Grafana alert",
                    ),
                    "timestamp": item.get(
                        "startsAt",
                        "",
                    ),
                }
            )

        return {
            "alerts": normalized_alerts,
            "logs": [],
            "metrics": {},
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
                raw = {
                    "alerts": [],
                    "logs": [],
                    "metrics": {},
                }
        else:
            raw = {
                "alerts": [],
                "logs": [],
                "metrics": {},
            }

        return {
            "incident_id": incident_id,
            "source": "grafana",
            "alerts": raw["alerts"],
            "logs": raw["logs"],
            "metrics": raw["metrics"],
        }