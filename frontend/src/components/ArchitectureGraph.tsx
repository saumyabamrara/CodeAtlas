import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type NodeMouseHandler,
} from '@xyflow/react';

import '@xyflow/react/dist/style.css';

import type { ArchitectureGraphResponse, GraphNodeType } from '../types/api';
import {
  transformArchitectureGraph,
  type ArchitectureFlowNode,
  type ArchitectureNodeData,
} from '../utils/graphTransform';
import { ArchitectureNode } from './ArchitectureNode';
import { NodeDetailsPanel } from './NodeDetailsPanel';

interface ArchitectureGraphProps {
  graph: ArchitectureGraphResponse;
}

const nodeTypes = { architecture: ArchitectureNode };
const minimapColors: Record<GraphNodeType, string> = {
  controller: '#70a5ff',
  service: '#c792ea',
  repository: '#5ee2a0',
  class: '#8d9bab',
};

export function ArchitectureGraph({ graph }: ArchitectureGraphProps) {
  const transformed = useMemo(() => transformArchitectureGraph(graph), [graph]);
  const [nodes, setNodes, onNodesChange] = useNodesState(transformed.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(transformed.edges);
  const [selectedNode, setSelectedNode] = useState<ArchitectureNodeData | null>(null);

  useEffect(() => {
    setNodes(transformed.nodes);
    setEdges(transformed.edges);
    setSelectedNode(null);
  }, [setEdges, setNodes, transformed]);

  const handleNodeClick: NodeMouseHandler<ArchitectureFlowNode> = useCallback(
    (_event, node) => setSelectedNode(node.data),
    [],
  );

  if (graph.nodes.length === 0) {
    return (
      <section className="graph-empty panel">
        <span className="empty-icon">{`< >`}</span>
        <h2>Architecture relationships were not found for this repository.</h2>
        <p>The backend returned a valid graph with no production classes to display.</p>
      </section>
    );
  }

  return (
    <section className="graph-panel" aria-label="Interactive architecture graph">
      <div className="graph-toolbar">
        <div>
          <p className="section-kicker">Production architecture</p>
          <h2>Class dependency graph</h2>
        </div>
        <span>{graph.nodes.length} nodes · {graph.edges.length} edges</span>
      </div>
      <div className="graph-workspace">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          onPaneClick={() => setSelectedNode(null)}
          nodesConnectable={false}
          edgesReconnectable={false}
          deleteKeyCode={null}
          fitView
          fitViewOptions={{ padding: 0.08 }}
          minZoom={0.25}
          maxZoom={1.75}
        >
          <MiniMap
            pannable
            zoomable
            nodeColor={(node) => minimapColors[node.data.nodeType as GraphNodeType]}
            maskColor="rgba(6, 10, 15, 0.72)"
          />
          <Controls showInteractive={false} />
          <Background variant={BackgroundVariant.Dots} gap={22} size={1.2} />
        </ReactFlow>
        {selectedNode ? (
          <NodeDetailsPanel node={selectedNode} onClose={() => setSelectedNode(null)} />
        ) : null}
      </div>
    </section>
  );
}
