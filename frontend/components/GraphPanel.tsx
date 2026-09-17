'use client'

import { PageHeader } from './ui/PageHeader'
import { Badge } from './ui/Badge'
import { FlowEntity, TrailStep, getNodeDisplayName } from '../lib/graph-transform'
import BorderGlow from './BorderGlow'
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
      <BorderGlow glowColor="0 0 20" backgroundColor="#ffffff" colors={['#222222', '#333333', '#111111']} borderRadius={4} glowRadius={15}>
        <section className="panel trail-panel" style={{ border: 'none', boxShadow: 'none' }}>
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
                    <div key={i}>
                      <div className="eyebrow" style={{ margin: 0, textAlign: 'left' }}>STEP {i+1}</div>
                      <b style={{ textAlign: 'center', color: '#111' }}>{step.description}</b>
                      <span style={{ textAlign: 'center' }}>{fromName} &rarr; {toName}</span>
                      <strong style={{ textAlign: 'right' }}>{amountDisplay}</strong>
                    </div>
                  )
                })}
              </div>
            </>
          )}
        </section>
      </BorderGlow>
    </>
  )
}
