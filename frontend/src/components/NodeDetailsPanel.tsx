import type { ArchitectureNodeData } from '../utils/graphTransform';

interface NodeDetailsPanelProps {
  node: ArchitectureNodeData;
  onClose: () => void;
}

export function NodeDetailsPanel({ node, onClose }: NodeDetailsPanelProps) {
  return (
    <aside className="node-details" aria-label="Selected class details">
      <div className="node-details-heading">
        <div>
          <p className="section-kicker">Selected node</p>
          <h3>{node.label}</h3>
        </div>
        <button type="button" onClick={onClose} aria-label="Close node details">×</button>
      </div>
      <dl>
        <div><dt>Class</dt><dd>{node.label}</dd></div>
        <div><dt>Role</dt><dd><span className={`role-badge ${node.nodeType}`}>{node.nodeType}</span></dd></div>
        <div><dt>Package</dt><dd><code>{node.packageName || '(default package)'}</code></dd></div>
        <div><dt>Qualified name</dt><dd><code>{node.qualifiedClassName}</code></dd></div>
        <div><dt>File</dt><dd><code>{node.filePath}</code></dd></div>
      </dl>
    </aside>
  );
}
