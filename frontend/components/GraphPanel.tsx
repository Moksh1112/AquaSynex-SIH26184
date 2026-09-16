'use client'

import { PageHeader } from './ui/PageHeader'
import { Badge } from './ui/Badge'
import { FlowEntity, TrailStep, getNodeDisplayName } from '../lib/graph-transform'

import { NetworkGraph } from './NetworkGraph'

export function GraphPanel({ 
  setView, 
  caseId, 
  flow,
  steps,
  loadingGraph,
  graphData
}: { 
  setView: (v: string) => void; 
  caseId: string; 
  flow: FlowEntity[];
  steps: TrailStep[];
  loadingGraph: boolean;
  graphData: any;
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
            <span>Entities <b>{graphData?.nodes?.length || 0}</b></span>
          </div>
        </div>
        
        {loadingGraph ? (
          <div style={{ padding: '2rem' }}>Loading graph...</div>
        ) : !graphData || !graphData.nodes || graphData.nodes.length === 0 ? (
          <div style={{ padding: '2rem', color: '#a1a1aa' }}>No graph data available.</div>
        ) : (
          <>
            <NetworkGraph nodes={graphData.nodes} edges={graphData.edges} />
            
            <div className="transaction-table" style={{ marginTop: '2rem' }}>
              <h3>Transaction Log</h3>
              {steps.map((step, i) => {
                const fromName = getNodeDisplayName(step.fromNode);
                const toName = getNodeDisplayName(step.toNode);

                const amountDisplay = step.amount ? `₹${step.amount.toLocaleString()}` : '';

                return (
                  <div key={i} style={{ padding: '1rem', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between' }}>
                    <div>
                      <div className="eyebrow">Step {i+1}</div>
                      <b>{step.description}</b>
                      <div>{fromName} → {toName}</div>
                    </div>
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
