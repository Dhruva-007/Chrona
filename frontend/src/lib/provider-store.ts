type Provider =
  | "datadog"
  | "grafana"
  | "newrelic";

type Listener = () => void;

class ProviderStore {
  private provider: Provider = "datadog";
  private listeners: Listener[] = [];

  getProvider() {
    return this.provider;
  }

  setProvider(provider: Provider) {
    this.provider = provider;
    this.listeners.forEach((l) => l());
  }

  subscribe(listener: Listener) {
    this.listeners.push(listener);

    return () => {
      this.listeners =
        this.listeners.filter(
          (l) => l !== listener
        );
    };
  }
}

export const providerStore =
  new ProviderStore();

export type { Provider };