"use client";

import { Handle, Position } from "@xyflow/react";
import { NodeStatus, STATUS_COLORS } from "./graph-types";

type GraphNodeData = {
  name: string;
  type: string;
  status: NodeStatus;
  cpu: number;
  memory: number;
  error: number;
  latency: number;
};

interface GraphNodeProps {
  data: GraphNodeData;
}

export default function GraphNode({ data }: GraphNodeProps) {
  const color = STATUS_COLORS[data.status];

  return (
    <div
      className="min-w-[220px] rounded-2xl border bg-slate-950 px-4 py-3 shadow-lg"
      style={{
        borderColor: color,
        boxShadow: `0 0 0 1px ${color}20`,
      }}
    >
      <Handle type="target" position={Position.Top} />

      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-white">{data.name}</h3>

        <div
          className="h-3 w-3 rounded-full"
          style={{ backgroundColor: color }}
        />
      </div>

      <p className="mt-2 text-xs uppercase tracking-wide text-slate-400">
        {data.type}
      </p>

      <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-slate-400">
        <div>CPU: {Math.round(data.cpu)}%</div>
        <div>Mem: {Math.round(data.memory)}%</div>
        <div>Err: {data.error.toFixed(1)}%</div>
        <div>Lat: {Math.round(data.latency)}ms</div>
      </div>

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}