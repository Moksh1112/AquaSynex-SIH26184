'use client'

import React, { useMemo } from 'react'

export function NetworkGraph({ nodes, edges, onNodeClick }: { nodes: any[], edges: any[], onNodeClick?: (node: any) => void }) {
  const layout = useMemo(() => {
    if (!nodes || nodes.length === 0) return { nodes: [], edges: [], width: 0, height: 0 }

    const adj: Record<string, string[]> = {}
    const inDegree: Record<string, number> = {}

    nodes.forEach(n => {
      adj[n.id] = []
      inDegree[n.id] = 0
    })

    edges.forEach(e => {
      if (adj[e.source] && inDegree[e.target] !== undefined) {
        adj[e.source].push(e.target)
        inDegree[e.target]++
      }
    })

    let queue = Object.keys(inDegree).filter(id => inDegree[id] === 0)
    if (queue.length === 0) {
      queue = [nodes[0].id]
    }

    const layers: string[][] = []
    const visited = new Set<string>()

    while (queue.length > 0) {
      layers.push([...queue])
      const nextQueue: string[] = []
      for (const id of queue) {
        visited.add(id)
        for (const neighbor of adj[id] || []) {
          if (!visited.has(neighbor) && !nextQueue.includes(neighbor)) {
            nextQueue.push(neighbor)
          }
        }
      }
      queue = nextQueue
      if (queue.length === 0 && visited.size < nodes.length) {
        const unvisited = nodes.find(n => !visited.has(n.id))
        if (unvisited) queue.push(unvisited.id)
      }
    }

    const NODE_WIDTH = 180
    const NODE_HEIGHT = 100
    const LAYER_SPACING_X = 280
    const NODE_SPACING_Y = 140

    const positionedNodes: any[] = []
    let maxH = 0

    layers.forEach((layer, layerIndex) => {
      const x = layerIndex * LAYER_SPACING_X
      const startY = -((layer.length - 1) * NODE_SPACING_Y) / 2

      layer.forEach((nodeId, nodeIndex) => {
        const y = startY + nodeIndex * NODE_SPACING_Y
        const node = nodes.find(n => n.id === nodeId)
        if (node) {
          positionedNodes.push({
            ...node,
            x,
            y
          })
        }
        maxH = Math.max(maxH, Math.abs(y))
      })
    })

    const width = (layers.length - 1) * LAYER_SPACING_X + NODE_WIDTH + 100
    const height = maxH * 2 + NODE_HEIGHT + 100

    const xOffset = 50
    const yOffset = height / 2

    const finalNodes = positionedNodes.map(n => ({
      ...n,
      x: n.x + xOffset,
      y: n.y + yOffset
    }))

    const finalEdges = edges.map(e => {
      const sourceNode = finalNodes.find(n => n.id === e.source)
      const targetNode = finalNodes.find(n => n.id === e.target)
      return {
        ...e,
        sourceNode,
        targetNode
      }
    }).filter(e => e.sourceNode && e.targetNode)

    return {
      nodes: finalNodes,
      edges: finalEdges,
      width,
      height
    }
  }, [nodes, edges])

  if (layout.nodes.length === 0) {
    return <div style={{ padding: '2rem', color: '#a1a1aa' }}>No graph data available.</div>
  }

  const getNodeColor = (label: string) => {
    switch (label) {
      case 'Complaint': return '#ec4899';
      case 'Person': return '#3b82f6';
      case 'Account': return '#10b981';
      case 'Transaction': return '#8b5cf6';
      case 'Withdrawal': return '#f59e0b';
      case 'ATM': return '#ef4444';
      default: return '#64748b';
    }
  }

  return (
    <div style={{ position: 'relative', width: '100%', overflowX: 'auto', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
      <div style={{ width: Math.max(layout.width, 800), height: Math.max(layout.height, 400), position: 'relative', minHeight: 400 }}>
        <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
            </marker>
          </defs>
          {layout.edges.map((edge, i) => (
            <g key={i}>
              <line
                x1={edge.sourceNode.x + 180}
                y1={edge.sourceNode.y + 50}
                x2={edge.targetNode.x}
                y2={edge.targetNode.y + 50}
                stroke="#cbd5e1"
                strokeWidth="2"
                markerEnd="url(#arrow)"
              />
              <text
                x={(edge.sourceNode.x + 180 + edge.targetNode.x) / 2}
                y={(edge.sourceNode.y + 50 + edge.targetNode.y + 50) / 2 - 5}
                fill="#64748b"
                fontSize="10"
                textAnchor="middle"
              >
                {edge.type.replace(/_/g, ' ')}
              </text>
            </g>
          ))}
        </svg>

        {layout.nodes.map(node => (
          <div
            key={node.id}
            onClick={() => onNodeClick && onNodeClick(node)}
            style={{
              position: 'absolute',
              left: node.x,
              top: node.y,
              width: 180,
              height: 100,
              backgroundColor: 'white',
              border: `2px solid ${getNodeColor(node.label)}`,
              borderRadius: '8px',
              padding: '12px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              display: 'flex',
              flexDirection: 'column',
              cursor: onNodeClick ? 'pointer' : 'default',
              overflow: 'hidden'
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: getNodeColor(node.label), textTransform: 'uppercase', marginBottom: '4px' }}>
              {node.label}
            </div>
            <div style={{ fontSize: '12px', fontWeight: 500, color: '#1e293b', wordBreak: 'break-all' }}>
              {node.metadata?.account_number || node.metadata?.transaction_id || node.metadata?.withdrawal_id || node.metadata?.atm_id || node.metadata?.name || node.metadata?.case_id || node.id}
            </div>
            {node.metadata?.amount && (
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: 'auto' }}>
                ₹{Number(node.metadata.amount).toLocaleString()}
              </div>
            )}
            {node.metadata?.bank_name && (
              <div style={{ fontSize: '10px', color: '#64748b', marginTop: 'auto' }}>
                {node.metadata.bank_name}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
