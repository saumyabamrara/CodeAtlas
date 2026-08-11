import { Handle, Position, type NodeProps } from '@xyflow/react';

import type { ArchitectureFlowNode } from '../utils/graphTransform';

export function ArchitectureNode({ data, selected }: NodeProps<ArchitectureFlowNode>) {
  return (
    <div className={`architecture-node ${data.nodeType} ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Left} />
      <strong>{data.label}</strong>
      <span>{data.nodeType}</span>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
