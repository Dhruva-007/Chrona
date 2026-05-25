from typing import Any


def _get(payload: Any, key: str, default=None):
    if isinstance(payload, dict):
        return payload.get(key, default)

    return getattr(payload, key, default)


def build_telemetry_context(payload: Any) -> str:
    """
    Converts telemetry payload into LLM-friendly context.
    Works with both dict payloads and Pydantic models.
    """

    source = _get(payload, "source", "unknown")
    alerts = _get(payload, "alerts", [])
    logs = _get(payload, "logs", [])
    metrics = _get(payload, "metrics", {})

    if hasattr(source, "value"):
        source = source.value

    sections = [
        f"Telemetry Source: {source}",
        "",
        "ALERTS:",
    ]

    if alerts:
        for alert in alerts:
            if isinstance(alert, dict):
                severity = alert.get("severity", "unknown")
                service = alert.get("service", "unknown")
                message = alert.get("message", "")
            else:
                severity = getattr(alert, "severity", "unknown")
                service = getattr(alert, "service", "unknown")
                message = getattr(alert, "message", "")

                if hasattr(severity, "value"):
                    severity = severity.value

            sections.append(
                f"- [{severity.upper()}] {service}: {message}"
            )
    else:
        sections.append("- No active alerts")

    sections.extend(["", "LOGS:"])

    if logs:
        for log in logs:
            if isinstance(log, dict):
                service = log.get("service", "unknown")
                level = log.get("level", "info")
                message = log.get("message", "")
            else:
                service = getattr(log, "service", "unknown")
                level = getattr(log, "level", "info")
                message = getattr(log, "message", "")

            sections.append(
                f"- [{level.upper()}] {service}: {message}"
            )
    else:
        sections.append("- No logs")

    sections.extend(["", "METRICS:"])

    if metrics:
        for service, metric in metrics.items():
            if isinstance(metric, dict):
                cpu = metric.get("cpu_percent", 0)
                memory = metric.get("memory_percent", 0)
                latency = metric.get("latency_ms", 0)
                error_rate = metric.get("error_rate", 0)
            else:
                cpu = getattr(metric, "cpu_percent", 0)
                memory = getattr(metric, "memory_percent", 0)
                latency = getattr(metric, "latency_ms", 0)
                error_rate = getattr(metric, "error_rate", 0)

            sections.append(
                f"- {service}: CPU={cpu}%, MEM={memory}%, LAT={latency}ms, ERR={error_rate}%"
            )
    else:
        sections.append("- No metrics")

    return "\n".join(sections)