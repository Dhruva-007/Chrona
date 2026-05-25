export const STATUS_COLORS = {
  healthy: "#10b981",
  degraded: "#f59e0b",
  critical: "#ef4444",
} as const;

export type NodeStatus = keyof typeof STATUS_COLORS;