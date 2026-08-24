import React, { useMemo } from 'react';
import { ReactFlow, Background, Controls, type Node, type Edge, MarkerType } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import { GlassNode, HitlNode, WebhookNode, TicketNode } from './nodes/StateNodes';

const nodeTypes = { glass: GlassNode, hitl: HitlNode, webhook: WebhookNode, ticket: TicketNode };

export interface GraphDef {
  graph_id: string;
  label?: string;
  nodes: { name: string; label: string; description: string; type: 'glass' | 'hitl' | 'webhook' | 'ticket'; llmTag?: string }[];
  edges: { source: string; target: string; label?: string; isCycle?: boolean }[];
}

function getLayoutedElements(nodes: Node[], edges: Edge[], direction: 'TB' | 'LR' = 'TB') {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction, nodesep: 60, ranksep: 90, marginx: 60, marginy: 30 });

  const nodeWidth = 280;
  const nodeHeight = 115;

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
}

export function GraphCanvas({ graphDef, activeNode, nodeStatuses, onNodeClick }: { graphDef: GraphDef; activeNode?: string; nodeStatuses: Record<string, string>; onNodeClick?: (name: string) => void }) {
  const { nodes, edges } = useMemo(() => {
    const initialNodes: Node[] = graphDef.nodes.map((n, idx) => {
      const status = nodeStatuses[n.name] || (n.name === activeNode ? 'running' : 'idle');
      return {
        id: n.name,
        type: n.type,
        position: { x: 0, y: 0 },
        data: { label: n.label, description: n.description, step: idx + 1, status, llmTag: n.llmTag, idx, message: '' },
      } as Node;
    });

    const nodeIndex = new Map(graphDef.nodes.map((n, i) => [n.name, i]));

    const initialEdges: Edge[] = graphDef.edges.map((e, i) => {
      const isCycle = !!e.isCycle || (nodeIndex.get(e.source)! > nodeIndex.get(e.target)!);
      const isActive = activeNode === e.source;
      const isError = e.label?.toLowerCase().includes('reject') || e.label?.toLowerCase().includes('fail') || e.label?.toLowerCase().includes('amend');
      // All back edges (cycles) exit from right side, enter from right side — per user request for step 5,6
      const sourceHandle = isCycle ? 'right-source' : 'bottom';
      const targetHandle = isCycle ? 'right' : 'top';
      // Offset cycles to the right to avoid overlapping when multiple cycles go to same target
      const sourceIdx = nodeIndex.get(e.source)!;
      const cycleOffset = isCycle ? 35 + (sourceIdx % 3) * 28 : 10;
      return {
        id: `e-${e.source}-${e.target}-${i}`,
        source: e.source,
        target: e.target,
        sourceHandle,
        targetHandle,
        type: 'smoothstep',
        label: e.label,
        labelStyle: { fontSize: 10, fill: isCycle ? '#f59e0b' : isError ? '#f43f5e' : '#94a3b8', fontWeight: 600 } as any,
        labelBgStyle: { fill: '#0f172a', fillOpacity: 0.95, rx: 4, ry: 4 } as any,
        labelBgPadding: [6, 4] as any,
        style: {
          stroke: isCycle ? '#f59e0b' : isError ? '#f43f5e' : isActive ? '#6366f1' : '#475569',
          strokeWidth: isCycle ? 2.4 : isActive ? 2.2 : 1.7,
          strokeDasharray: isCycle ? '10 6' : undefined,
        } as any,
        animated: isActive && !isCycle,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
          color: isCycle ? '#f59e0b' : isError ? '#f43f5e' : isActive ? '#6366f1' : '#475569',
        },
        data: { isCycle },
        pathOptions: { offset: cycleOffset, borderRadius: 16 },
      } as Edge;
    });

    return getLayoutedElements(initialNodes, initialEdges, 'TB');
  }, [graphDef, activeNode, nodeStatuses]);

  return (
    <div className="w-full h-[680px] rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes as any}
        fitView
        fitViewOptions={{ padding: 0.3, minZoom: 0.55, maxZoom: 1.25 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        onNodeClick={(_, n) => onNodeClick?.(n.id)}
        proOptions={{ hideAttribution: true }}
        defaultEdgeOptions={{ type: 'smoothstep' }}
      >
        <Background gap={20} size={1} color="#1e293b" style={{ opacity: 0.55 }} />
        <Controls
          position="bottom-left"
          showZoom={true}
          showFitView={true}
          showInteractive={false}
        />
      </ReactFlow>
      <style>{`
        .react-flow__controls {
          background: #0f172a !important;
          border: 1px solid #334155 !important;
          border-radius: 12px !important;
          padding: 6px !important;
          display: flex !important;
          flex-direction: column !important;
          gap: 4px !important;
          box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
        }
        .react-flow__controls-button {
          background: #1e293b !important;
          border: 1px solid #334155 !important;
          color: #cbd5e1 !important;
          width: 32px !important;
          height: 32px !important;
          border-radius: 8px !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
        }
        .react-flow__controls-button:hover {
          background: #334155 !important;
          color: #f1f5f9 !important;
          border-color: #475569 !important;
        }
        .react-flow__controls-button svg {
          fill: #cbd5e1 !important;
          width: 16px !important;
          height: 16px !important;
        }
        .react-flow__attribution { display: none !important; }
        .react-flow__edge-path { stroke-linecap: round; stroke-linejoin: round; }
        .react-flow__edge-textbg { rx: 6; ry: 6; }
        .react-flow__handle { opacity: 0 !important; width: 8px !important; height: 8px !important; }
      `}</style>
    </div>
  );
}
