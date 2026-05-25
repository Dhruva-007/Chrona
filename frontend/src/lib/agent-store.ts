"use client";

export interface AgentAnalysisResult {
  root_cause: string;
  confidence: number;
  reasoning: string[];
  recommended_actions: string[];
  ai_summary: string;
}

type Listener = () => void;

class AgentStore {
  private result: AgentAnalysisResult | null = null;
  private loading = false;
  private listeners = new Set<Listener>();

  subscribe(listener: Listener) {
    this.listeners.add(listener);
    return () => {this.listeners.delete(listener);};
  }

  private emit() {
    this.listeners.forEach((listener) => listener());
  }

  getState() {
    return {
      result: this.result,
      loading: this.loading,
    };
  }

  setLoading(value: boolean) {
    this.loading = value;
    this.emit();
  }

  setResult(result: AgentAnalysisResult | null) {
    this.result = result;
    this.loading = false;
    this.emit();
  }

  reset() {
    this.result = null;
    this.loading = false;
    this.emit();
  }
}

export const agentStore = new AgentStore();