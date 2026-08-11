import { MarkerType, type Edge, type Node } from '@xyflow/react';

import type {
  ArchitectureGraphResponse,
  GraphNode,
  GraphNodeType,
} from '../types/api';

export type ArchitectureNodeData = {
  label: string;
  nodeType: GraphNodeType;
  filePath: string;
  packageName: string;
  qualifiedClassName: string;
};

export type ArchitectureFlowNode = Node<ArchitectureNodeData, 'architecture'>;
export type ArchitectureFlowEdge = Edge;

const ROLE_ORDER: GraphNodeType[] = ['controller', 'service', 'repository', 'class'];
const NODE_WIDTH = 220;
const NODE_HEIGHT = 75;
const HORIZONTAL_STEP = 270;
const VERTICAL_STEP = 105;
const COMPONENT_GAP_X = 140;
const COMPONENT_GAP_Y = 140;
const CONNECTED_REGION_MAX_WIDTH = 1200;
const ISOLATED_MAX_COLUMNS = 5;

function transformNode(node: GraphNode, x: number, y: number): ArchitectureFlowNode {
  return {
    id: node.id,
    type: 'architecture',
    position: { x, y },
    data: {
      label: node.label,
      nodeType: node.node_type,
      filePath: node.file_path,
      packageName: node.package_name,
      qualifiedClassName: node.qualified_class_name,
    },
  };
}

function buildAdjacency(graph: ArchitectureGraphResponse): Map<string, Set<string>> {
  const adjacency = new Map(
    graph.nodes.map((node) => [node.id, new Set<string>()]),
  );

  graph.edges.forEach((edge) => {
    const sourceNeighbors = adjacency.get(edge.source);
    const targetNeighbors = adjacency.get(edge.target);
    if (!sourceNeighbors || !targetNeighbors) {
      return;
    }
    sourceNeighbors.add(edge.target);
    targetNeighbors.add(edge.source);
  });

  return adjacency;
}

function findConnectedComponents(
  connectedNodeIds: string[],
  adjacency: Map<string, Set<string>>,
): string[][] {
  const visited = new Set<string>();
  const components: string[][] = [];

  connectedNodeIds.forEach((startId) => {
    if (visited.has(startId)) {
      return;
    }

    const component: string[] = [];
    const queue = [startId];
    visited.add(startId);

    while (queue.length > 0) {
      const nodeId = queue.shift();
      if (!nodeId) {
        continue;
      }
      component.push(nodeId);

      const neighbors = [...(adjacency.get(nodeId) ?? [])].sort((left, right) =>
        left.localeCompare(right),
      );
      neighbors.forEach((neighborId) => {
        if (!visited.has(neighborId)) {
          visited.add(neighborId);
          queue.push(neighborId);
        }
      });
    }

    components.push(component.sort((left, right) => left.localeCompare(right)));
  });

  return components.sort(
    (left, right) =>
      right.length - left.length || left[0].localeCompare(right[0]),
  );
}

function layoutComponent(
  componentIds: string[],
  nodesById: Map<string, GraphNode>,
): { nodes: ArchitectureFlowNode[]; width: number; height: number } {
  const componentNodes = componentIds
    .map((id) => nodesById.get(id))
    .filter((node): node is GraphNode => node !== undefined);
  const activeRoles = ROLE_ORDER.filter((role) =>
    componentNodes.some((node) => node.node_type === role),
  );
  let largestRoleSize = 0;
  const nodes: ArchitectureFlowNode[] = [];

  activeRoles.forEach((role, column) => {
    const roleNodes = componentNodes
      .filter((node) => node.node_type === role)
      .sort((left, right) => left.id.localeCompare(right.id));
    largestRoleSize = Math.max(largestRoleSize, roleNodes.length);
    roleNodes.forEach((node, row) => {
      nodes.push(transformNode(node, column * HORIZONTAL_STEP, row * VERTICAL_STEP));
    });
  });

  return {
    nodes,
    width: (activeRoles.length - 1) * HORIZONTAL_STEP + NODE_WIDTH,
    height: (largestRoleSize - 1) * VERTICAL_STEP + NODE_HEIGHT,
  };
}

export function transformArchitectureGraph(graph: ArchitectureGraphResponse): {
  nodes: ArchitectureFlowNode[];
  edges: ArchitectureFlowEdge[];
} {
  const nodesById = new Map(graph.nodes.map((node) => [node.id, node]));
  const adjacency = buildAdjacency(graph);
  const sortedNodeIds = graph.nodes
    .map((node) => node.id)
    .sort((left, right) => left.localeCompare(right));
  const connectedNodeIds = sortedNodeIds.filter(
    (nodeId) => (adjacency.get(nodeId)?.size ?? 0) > 0,
  );
  const isolatedNodes = graph.nodes
    .filter((node) => (adjacency.get(node.id)?.size ?? 0) === 0)
    .sort(
      (left, right) =>
        ROLE_ORDER.indexOf(left.node_type) - ROLE_ORDER.indexOf(right.node_type) ||
        left.id.localeCompare(right.id),
    );
  const components = findConnectedComponents(connectedNodeIds, adjacency);
  const nodes: ArchitectureFlowNode[] = [];
  let componentX = 0;
  let componentY = 0;
  let shelfHeight = 0;

  components.forEach((componentIds) => {
    const component = layoutComponent(componentIds, nodesById);
    if (
      componentX > 0 &&
      componentX + component.width > CONNECTED_REGION_MAX_WIDTH
    ) {
      componentX = 0;
      componentY += shelfHeight + COMPONENT_GAP_Y;
      shelfHeight = 0;
    }

    component.nodes.forEach((node) => {
      nodes.push({
        ...node,
        position: {
          x: node.position.x + componentX,
          y: node.position.y + componentY,
        },
      });
    });
    componentX += component.width + COMPONENT_GAP_X;
    shelfHeight = Math.max(shelfHeight, component.height);
  });

  const connectedRegionHeight = components.length > 0 ? componentY + shelfHeight : 0;
  const isolatedStartY =
    connectedRegionHeight > 0 ? connectedRegionHeight + COMPONENT_GAP_Y : 0;
  const isolatedColumns = Math.min(
    ISOLATED_MAX_COLUMNS,
    Math.ceil(Math.sqrt(isolatedNodes.length)),
  );

  isolatedNodes.forEach((node, index) => {
    const column = isolatedColumns > 0 ? index % isolatedColumns : 0;
    const row = isolatedColumns > 0 ? Math.floor(index / isolatedColumns) : 0;
    nodes.push(
      transformNode(
        node,
        column * HORIZONTAL_STEP,
        isolatedStartY + row * VERTICAL_STEP,
      ),
    );
  });

  const edges: ArchitectureFlowEdge[] = graph.edges.map((edge, index) => ({
    id: `${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    type: 'smoothstep',
    markerEnd: { type: MarkerType.ArrowClosed },
  }));

  return { nodes, edges };
}
