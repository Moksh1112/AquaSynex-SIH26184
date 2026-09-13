'use client'

import { PageHeader } from './ui/PageHeader'
import { Badge } from './ui/Badge'

export function Cases({ 
  setView, 
  setCaseId, 
  cases,
  loading
}: { 
  setView: (v: string) => void; 
  setCaseId: (id: string) => void; 
  cases: any[];
  loading: boolean;
}) {
  return (
    <>
      <PageHeader 
        eyebrow="Investigations / Queue" 
        title="Case Files" 
        subtitle={`${cases.length} active investigations`} 
      />
      <div className="filter-row">
        <button className="filter active">All cases <b>{cases.length}</b></button>
        <div className="search">⌕ <input placeholder="Search case ID..." /></div>
      </div>
      <section className="panel table-panel">
        {loading ? (
          <div style={{ padding: '2rem' }}>Loading cases...</div>
        ) : cases.length === 0 ? (
          <div style={{ padding: '2rem', color: '#a1a1aa' }}>No cases available.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Description</th>
                <th>Status</th>
                <th>Reported At</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {cases.map((item) => (
                <tr key={item.case_id} onClick={() => { setCaseId(item.case_id); setView('case') }} style={{ cursor: 'pointer' }}>
                  <td><strong>{item.case_id}</strong></td>
                  <td>{item.description || 'N/A'}</td>
                  <td><Badge tone="slate">{item.status}</Badge></td>
                  <td className="muted">{new Date(item.reported_at).toLocaleString()}</td>
                  <td className="arrow">→</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  )
}
