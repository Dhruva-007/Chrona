from app.services.connectors.datadog_connector import DatadogConnector
from app.services.connectors.grafana_connector import GrafanaConnector
from app.services.connectors.newrelic_connector import NewRelicConnector


def get_connector(source: str):
    normalized = source.lower()

    if normalized == "datadog":
        return DatadogConnector()

    if normalized == "grafana":
        return GrafanaConnector()

    if normalized == "newrelic":
        return NewRelicConnector()

    raise ValueError(f"Unsupported monitoring source: {source}")