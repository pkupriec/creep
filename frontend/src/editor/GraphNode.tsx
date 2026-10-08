import { useLayoutEffect } from 'react';
import { Handle, Position, useUpdateNodeInternals, type NodeProps, type Node } from '@xyflow/react';
export type CanvasNode = Node<{
    label: string;
    kind: string;
    ports: string[];
    scope: string;
}, 'graph'>;
export function GraphNode({ id, data, selected }: NodeProps<CanvasNode>) {
    const updateInternals = useUpdateNodeInternals();
    const ports = data.ports.join('|');
    useLayoutEffect(() => { updateInternals(id); }, [id, ports, updateInternals]);
    return <div className={`graph-node ${selected ? 'selected' : ''}`}>
    <small>{data.kind}{data.scope ? ` · ${data.scope}` : ''}</small><strong>{data.label}</strong>
    {data.ports.map((port, index) => <div className="node-port" key={port}>
      <Handle type="target" position={Position.Left} id={port} style={{ top: 70 + index * 24 }}/><span>{port}</span>
    </div>)}
    {data.kind !== 'output' && <Handle type="source" position={Position.Right} id="out"/>}
  </div>;
}
