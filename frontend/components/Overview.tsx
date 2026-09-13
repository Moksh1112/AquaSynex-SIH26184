'use client'

import { PageHeader } from './ui/PageHeader'
import { Stat } from './ui/Stat'
import { Badge } from './ui/Badge'

export function Overview({ 
  setView, 
  setCaseId, 
  cases, 
  alerts,
  loading 
}: { 
  setView: (v: string) => void; 
  setCaseId: (id: string) => void; 
  cases: any[]; 
  alerts: any[];
  loading: boolean;
}) {
  if (loading) {
    return <div style={{ padding: '2rem' }}>Loading dashboard data...</div>
  }

  const openAlerts = alerts.filter(a => a.status === 'OPEN').length;

  return (
    <>
      <PageHeader 
        eyebrow="Operational picture" 
        title="Command Center" 
        subtitle="Real-time intelligence across active financial crime investigations." 
        action={<button className="button button-primary" onClick={() => setView('cases')}>Open case queue <span>→</span></button>} 
      />
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)' }}>
        <Stat label="Active cases" value={cases.length.toString()} detail="Active investigations" />
        <Stat label="Open Alerts" value={openAlerts.toString()} detail={`${alerts.length} total alerts`} tone={openAlerts > 0 ? "red" : "slate"} />
      </div>
      <div className="section-grid">
        <section className="panel span-2">
          <div className="panel-head">
            <div>
              <div className="eyebrow">Priority queue</div>
              <h2>Cases needing attention</h2>
            </div>
            <button className="text-button" onClick={() => setView('cases')}>View all cases →</button>
          </div>
          <div className="case-list">
            {cases.length === 0 ? (
               <div style={{ padding: '1rem', color: '#a1a1aa' }}>No cases available.</div>
            ) : cases.slice(0, 5).map((item) => (
              <button className="case-row" key={item.case_id} onClick={() => { setCaseId(item.case_id); setView('case') }}>
                <div className="risk-mark" data-tone="slate" />
                <div className="case-main">
                  <strong>{item.description || 'Investigation'}</strong>
                  <span>{item.case_id}</span>
                </div>
                <Badge tone="slate">{item.status}</Badge>
                <div className="case-amount">
                  <small>{new Date(item.reported_at).toLocaleDateString()}</small>
                </div>
                <span className="arrow">→</span>
              </button>
            ))}
          </div>
        </section>
        
        <section className="panel span-2">
          <div className="panel-head">
            <div>
              <div className="eyebrow">Activity stream</div>
              <h2>Recent Alerts</h2>
            </div>
            <button className="text-button" onClick={() => setView('alerts')}>View all alerts →</button>
          </div>
          <div className="timeline">
            {alerts.length === 0 ? (
               <div style={{ padding: '1rem', color: '#a1a1aa' }}>No alerts available.</div>
            ) : alerts.slice(0, 4).map(alert => (
              <span key={alert.id}>
                <i className={`dot ${alert.status === 'OPEN' ? 'red' : 'blue'}`} />
                <b>{alert.priority} Alert</b>
                <small>Case {alert.case_id} · {alert.status}</small>
              </span>
            ))}
          </div>
        </section>
      </div>
    </>
  )
}
