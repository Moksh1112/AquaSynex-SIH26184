'use client'

import { PageHeader } from './ui/PageHeader'
import { Badge } from './ui/Badge'
import { FlowEntity, TrailStep, getNodeDisplayName } from '../lib/graph-transform'

export function GraphPanel({ 
  setView, 
  caseId, 
  flow,
  steps,
  loadingGraph 
}: { 
  setView: (v: string) => void; 
  caseId: string; 
  flow: FlowEntity[];
  steps: TrailStep[];
  loadingGraph: boolean;
}) {
  return (
    <>
      <PageHeader 
        eyebrow={`${caseId} / Transaction graph`} 
        title="Money Trail" 
        subtitle="Following the movement from origin to final destination." 
        action={<button className="button button-primary" onClick={() => setView('map')}>Open geo view</button>} 
      />
      <section className="panel trail-panel">
        <div className="trail-top">
          <div>
            <div className="eyebrow">Transaction chain</div>
            <h2>Transfer path</h2>
          </div>
          <div className="trail-meta">
            <span>Nodes <b>{flow.length}</b></span>
          </div>
        </div>
        
        {loadingGraph ? (
          <div style={{ padding: '2rem' }}>Loading graph...</div>
        ) : flow.length === 0 ? (
          <div style={{ padding: '2rem', color: '#a1a1aa' }}>No graph data available.</div>
        ) : (
          <>
            <div className="large-flow">
              {flow.map((item, i) => (
                <div className="large-step" key={item.id + i}>
                  <div className={`large-node ${item.tone}`}>
                    <span>{i + 1}</span>
                  </div>
                  <div className="eyebrow">{item.label}</div>
                  <h3>{item.name}</h3>
                  <strong>{item.value}</strong>
                  <Badge tone={item.tone}>
                    {item.type}
                  </Badge>
                  {i < flow.length - 1 && <div className="large-line"><i /></div>}
                </div>
              ))}
            </div>
            
            <div className="transaction-table">
              {steps.map((step, i) => {
                const fromName = getNodeDisplayName(step.fromNode);
                const toName = getNodeDisplayName(step.toNode);

                const amountDisplay = step.amount ? `₹${step.amount.toLocaleString()}` : '';

                return (
                  <div key={i}>
                    <span>Step {i+1}</span>
                    <b>{step.description}</b>
                    <span>{fromName} → {toName}</span>
                    <strong>{amountDisplay}</strong>
                  </div>
                )
              })}
            </div>
          </>
        )}
      </section>
    </>
  )
}
