from typing import Any, Dict
import httpx

from app.core.config import settings
from app.services.connectors.base import MonitoringConnector


class NewRelicConnector(MonitoringConnector):
    """
    New Relic telemetry connector.
    """

    def _headers(self):
        return {
            "Api-Key": settings.NEWRELIC_API_KEY,
            "Content-Type": "application/json",
        }

    def _query(self):
        return {
            "query": """
            {
              actor {
                account(id: %s) {
                  alerts {
                    violations {
                      conditionName
                    }
                  }
                }
              }
            }
            """
            % settings.NEWRELIC_ACCOUNT_ID
        }

    def _fetch_live_payload(
        self,
        incident_id: str,
    ) -> Dict[str, Any]:
        if (
            not settings.NEWRELIC_API_KEY
            or not settings.NEWRELIC_ACCOUNT_ID
        ):
            raise ValueError(
                "New Relic credentials missing"
            )

        with httpx.Client(timeout=20.0) as client:
            res = client.post(
                "https://api.newrelic.com/graphql",
                headers=self._headers(),
                json=self._query(),
            )

            res.raise_for_status()

        payload = res.json()

        alerts = []

        violations = (
            payload.get("data", {})
            .get("actor", {})
            .get("account", {})
            .get("alerts", {})
            .get("violations", [])
        )

        for item in violations[:10]:
            alerts.append(
                {
                    "severity": "critical",
                    "service": item.get(
                        "conditionName",
                        "newrelic-alert",
                    ),
                    "message": "New Relic incident detected",
                    "timestamp": "",
                }
            )

        return {
            "alerts": alerts,
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
            "source": "newrelic",
            "alerts": raw["alerts"],
            "logs": raw["logs"],
            "metrics": raw["metrics"],
        }