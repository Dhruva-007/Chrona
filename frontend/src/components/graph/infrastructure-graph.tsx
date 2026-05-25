"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  ReactFlow,
  type Edge,
  type Node,
  type NodeMouseHandler,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";

import GraphNode from "./graph-node";
import { IncidentReplay } from "./incident-replay";
import { NodeInspector } from "./node-inspector";
import { SimulationToggle } from "./simulation-toggle";

import {
  GraphResponse,
  InfrastructureNode,
  SimulationSuite,
  TelemetryResponse,
} from "@/lib/types";

import { NodeStatus } from "./graph-types";
import { fetchCounterfactual } from "@/lib/api";

const nodeTypes = {
  infra: GraphNode,
};

interface Props {
  graph: GraphResponse;
  suite: SimulationSuite;
  telemetry: TelemetryResponse;
}

type SimulationMode =
  | "reality"
  | "counterfactual"
  | "failover";

type GraphNodeData = Record<string, unknown> & {
  name: string;
  type: string;
  status: NodeStatus;
  cpu: number;
  memory: number;
  error: number;
  latency: number;
};

interface CounterfactualResponse {
  success: boolean;
  data: {
    recovered_nodes: string[];
    still_failing_nodes: string[];
  };
}

function createPositions(
  nodes: InfrastructureNode[]
): Record<string, { x: number; y: number }> {
  const positions: Record<
    string,
    { x: number; y: number }
  > = {};

  const layers: Record<string, number> = {
    cdn: 0,
    gateway: 1,
    service: 2,
    cache: 3,
    queue: 3,
    database: 4,
    external: 5,
  };

  const grouped: Record<number, InfrastructureNode[]> = {};

  for (const node of nodes) {
    const layer = layers[node.type] ?? 2;

    if (!grouped[layer]) {
      grouped[layer] = [];
    }

    grouped[layer].push(node);
  }

  for (const [layer, layerNodes] of Object.entries(grouped)) {
    layerNodes.forEach((node, index) => {
      positions[node.id] = {
        x: Number(layer) * 420,
        y: index * 240,
      };
    });
  }

  return positions;
}

function getRealityStatus(
  node: InfrastructureNode,
  step: number
): NodeStatus {
  if (step === 0) return "healthy";

  if (step >= 1 && node.id === "postgres-primary") {
    return "critical";
  }

  if (step >= 2 && node.id === "payment-svc") {
    return "critical";
  }

  if (step >= 3 && node.id === "order-svc") {
    return "critical";
  }

  if (step >= 4 && node.id === "gateway-01") {
    return "degraded";
  }

  if (step >= 5 && node.id === "gateway-01") {
    return "critical";
  }

  return node.status as NodeStatus;
}

function getSimulationStatus(
  node: InfrastructureNode,
  mode: SimulationMode,
  step: number,
  counterfactual: CounterfactualResponse | null,
  suite: SimulationSuite
): NodeStatus {
  if (mode === "reality") {
    return getRealityStatus(node, step);
  }

  if (mode === "counterfactual" && counterfactual) {
    if (
      counterfactual.data.recovered_nodes.includes(node.id)
    ) {
      return "healthy";
    }

    if (
      counterfactual.data.still_failing_nodes.includes(
        node.id
      )
    ) {
      return "critical";
    }

    return node.status as NodeStatus;
  }

  if (mode === "failover") {
    const recovered =
      suite.data.simulations.replica_failover
        .recovered_nodes;

    if (recovered.includes(node.id)) {
      return "healthy";
    }

    return node.status as NodeStatus;
  }

  return node.status as NodeStatus;
}

export function InfrastructureGraph({
  graph,
  suite,
  telemetry,
}: Props) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const [selectedNode, setSelectedNode] =
    useState<InfrastructureNode | null>(null);

  const [mode, setMode] =
    useState<SimulationMode>("reality");

  const [counterfactual, setCounterfactual] =
    useState<CounterfactualResponse | null>(null);

  useEffect(() => {
    fetchCounterfactual("postgres-primary")
      .then(setCounterfactual)
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!isPlaying || mode !== "reality") return;

    const timer = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= 5) {
          setIsPlaying(false);
          return prev;
        }

        return prev + 1;
      });
    }, 1500);

    return () => clearInterval(timer);
  }, [isPlaying, mode]);

  const positions = useMemo(
    () => createPositions(graph.data.nodes),
    [graph.data.nodes]
  );

  const nodes: Node<GraphNodeData>[] = useMemo(() => {
    return graph.data.nodes.map((node) => ({
      id: node.id,
      type: "infra",
      position: positions[node.id],
      draggable: false,
      data: {
        name: node.name,
        type: node.type,
        status: getSimulationStatus(
          node,
          mode,
          currentStep,
          counterfactual,
          suite
        ),
        cpu: node.cpu_usage,
        memory: node.memory_usage,
        error: node.error_rate,
        latency: node.latency_ms,
      },
    }));
  }, [
    graph.data.nodes,
    positions,
    currentStep,
    mode,
    counterfactual,
    suite,
  ]);

  const edges: Edge[] = useMemo(() => {
    return graph.data.edges.map((edge, index) => ({
      id: `${edge.source}-${edge.target}-${index}`,
      source: edge.source,
      target: edge.target,
      animated: mode === "reality" && currentStep >= 2,
      style: {
        stroke:
          mode === "reality" && currentStep >= 2
            ? "#dc2626"
            : "#cbd5e1",
        strokeWidth:
          mode === "reality" && currentStep >= 2
            ? 2.5
            : 1.5,
      },
    }));
  }, [graph.data.edges, mode, currentStep]);

  const handleNodeClick: NodeMouseHandler = (
    _,
    clickedNode
  ) => {
    const infraNode = graph.data.nodes.find(
      (node) => node.id === clickedNode.id
    );

    if (infraNode) {
      setSelectedNode(infraNode);
    }
  };

  return (
    <>
      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-6 py-5">
          <h2 className="text-2xl font-semibold text-slate-900">
            Live Infrastructure Topology
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Real-time dependency graph with
            counterfactual replay simulation
          </p>
        </div>

        <div className="space-y-6 p-6">
          <SimulationToggle
            mode={mode}
            onChange={(nextMode) => {
              setMode(nextMode as SimulationMode);
              setCurrentStep(0);
              setIsPlaying(false);
            }}
          />

          {mode === "reality" && (
            <IncidentReplay
              currentStep={currentStep}
              maxSteps={5}
              isPlaying={isPlaying}
              onPlayPause={() =>
                setIsPlaying((prev) => !prev)
              }
              onReset={() => {
                setCurrentStep(0);
                setIsPlaying(false);
              }}
              onStepChange={(step) => {
                setCurrentStep(step);
                setIsPlaying(false);
              }}
            />
          )}

          <div className="h-[900px] overflow-hidden rounded-3xl border border-slate-200 bg-slate-50">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              fitView
              onNodeClick={handleNodeClick}
              proOptions={{
                hideAttribution: true,
              }}
            >
              <Background
                gap={24}
                size={1}
                color="#dbeafe"
              />

              <Controls position="top-right" />
            </ReactFlow>
          </div>
        </div>
      </div>

      <NodeInspector
        node={selectedNode}
        telemetry={telemetry}
        onClose={() => setSelectedNode(null)}
      />
    </>
  );
}