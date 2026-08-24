import { BaseEdge, getBezierPath, type EdgeProps } from '@xyflow/react';

export function AnimatedEdge({ sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, style, data }: EdgeProps) {
  const [edgePath] = getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition });
  const isActive = (data as any)?.isActive;
  const isCycle = (data as any)?.isCycle;
  return (
    <>
      <BaseEdge
        path={edgePath}
        style={{
          stroke: isCycle ? '#f59e0b' : isActive ? '#6366f1' : '#334155',
          strokeWidth: isActive ? 2.5 : 1.5,
          opacity: isActive ? 1 : 0.6,
          ...style,
        }}
      />
      {isActive && (
        <path
          d={edgePath}
          fill="none"
          stroke="#818cf8"
          strokeWidth={2}
          strokeDasharray="8 6"
          opacity={0.9}
          style={{ animation: 'flowDash 1s linear infinite' } as any}
        />
      )}
    </>
  );
}
