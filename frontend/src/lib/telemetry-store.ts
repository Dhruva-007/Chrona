import { TelemetryResponse } from "./types";

type Listener = () => void;

class TelemetryStore {
  private telemetry:
    | TelemetryResponse
    | null = null;

  private listeners: Listener[] = [];

  setTelemetry(
    telemetry: TelemetryResponse
  ) {
    this.telemetry =
      telemetry;

    this.listeners.forEach(
      (l) => l()
    );
  }

  getTelemetry() {
    return this.telemetry;
  }

  subscribe(
    listener: Listener
  ) {
    this.listeners.push(
      listener
    );

    return () => {
      this.listeners =
        this.listeners.filter(
          (l) => l !== listener
        );
    };
  }
}

export const telemetryStore =
  new TelemetryStore();