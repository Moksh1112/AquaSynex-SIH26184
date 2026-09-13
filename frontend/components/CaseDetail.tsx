'use client'

import { PageHeader } from './ui/PageHeader'
import { Badge } from './ui/Badge'
import { FlowEntity } from '../lib/graph-transform'

export function CaseDetail({ 
  setView, 
  caseId, 
  caseDetails,
  loadingCase,
  flow, 
  loadingGraph 
}: { 
  setView: (v: string) => void; 
  caseId: string; 
  caseDetails: any;
  loadingCase: boolean;
  flow: FlowEntity[]; 
  loadingGraph: boolean;
}) {
  if (loadingCase) {
    return <div style={{ padding: '2rem' }}>Loading case details...</div>
  }

  if (!caseDetails) {
    return <div style={{ padding: '2rem', color: '#a1a1aa' }}>Case details unavailable.</div>
  }

  return (
    <>
      <div className="breadcrumbs" onClick={() => setView('cases')} style={{ cursor: 'pointer' }}>
        Case Files <span>/</span> {caseId}
      </div>
      <PageHeader 
        eyebrow={`Case ${caseId} / Open investigation`} 
        title={caseDetails.description || 'Investigation'} 
        subtitle={`Status: ${caseDetails.status} · Reported: ${new Date(caseDetails.reported_at).toLocaleString()}`} 
      />
      <div className="case-summary">
        <div>
          <span className="eyebrow">Status</span>
          <strong>{caseDetails.status}</strong>
        </div>
        <div>
          <span className="eyebrow">Entities in Graph</span>
          <strong>{flow.length}</strong>
        </div>
        <div>
          <span className="eyebrow">Transfer layers</span>
          <strong>{flow.length > 0 ? flow.length - 1 : 0}</strong>
        </div>
      </div>
      <div className="section-grid">
        <section className="panel span-2">
          <div className="panel-head">
            <div>
              <div className="eyebrow">Entity graph</div>
              <h2>Money movement overview</h2>
            </div>
            <button className="text-button" onClick={() => setView('trail')}>Open money trail →</button>
          </div>
          {loadingGraph ? (
            <div style={{ padding: '2rem' }}>Loading graph...</div>
          ) : flow.length === 0 ? (
            <div style={{ padding: '2rem', color: '#a1a1aa' }}>No graph data available.</div>
          ) : (
            <div className="flow">
              {flow.map((item, i) => (
                <div className="flow-step" key={item.id + i}>
                  <div className={`flow-node ${item.tone}`}>
                    <span>{i === 0 ? 'A' : i === flow.length - 1 ? '?' : '◈'}</span>
                  </div>
                  <div className="eyebrow">{item.label}</div>
                  <strong>{item.value}</strong>
                  <span>{item.name}</span>
                  {i < flow.length - 1 && <div className="flow-line" />}
                </div>
              ))}
            </div>
          )}
        </section>
        <section className="panel">
          <div className="eyebrow">Actions</div>
          <h2>Investigator Tools</h2>
          <br/>
          <button className="button button-primary full" onClick={() => setView('prediction')}>View prediction rationale</button>
          <br/><br/>
          <button className="button button-quiet full" onClick={() => setView('alerts')}>View alerts</button>
        </section>
      </div>
    </>
  )
}
