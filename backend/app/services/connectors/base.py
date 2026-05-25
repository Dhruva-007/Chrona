from abc import ABC, abstractmethod
from typing import Any, Dict


class MonitoringConnector(ABC):
    """
    Base contract for telemetry providers.
    All providers must normalize into Chrona telemetry schema.
    """

    @abstractmethod
    def fetch_incident_context(
        self,
        incident_id: str,
    ) -> Dict[str, Any]:
        pass