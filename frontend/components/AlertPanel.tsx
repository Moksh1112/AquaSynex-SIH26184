'use client'

import { PageHeader } from './ui/PageHeader'
import { Badge } from './ui/Badge'
import { fetchApi } from '../lib/api'
import { useState } from 'react'
import BorderGlow from './BorderGlow'

export function AlertPanel({
  token,
  alerts,
  cases,
  loading,
  refreshAlerts,
  setView,
  setCaseId
}: {
  token: string;
  alerts: any[];
  cases: any[];
  loading: boolean;
  refreshAlerts: () => void;
  setView: (v: any) => void;
  setCaseId: (id: string) => void;
}) {
  const [actingOn, setActingOn] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('OPEN');

  const updateStatus = async (alertId: string, status: string) => {
    setActingOn(alertId);
    try {
      await fetchApi(`/alerts/${alertId}/status`, token, {
        method: 'PATCH',
        body: JSON.stringify({ status })
      });
      refreshAlerts();
    } catch (e: any) {
      console.error("Failed to update status", e);
      alert(`Failed to update alert status: ${e.message || 'Unknown error'}`);
    } finally {
      setActingOn(null);
    }
  }

  if (loading) {
    return (
      <>
        <PageHeader eyebrow="Operations / Risk response" title="Alert Center" subtitle="Loading alerts..." />
        <div style={{ padding: '2rem' }}>Loading alerts from backend...</div>
      </>
    )
  }

  const openAlerts = alerts.filter(a => a.status === 'OPEN').length;
  const acknowledgedAlerts = alerts.filter(a => a.status === 'ACKNOWLEDGED').length;
  const resolvedAlerts = alerts.filter(a => a.status === 'RESOLVED').length;

  const filteredAlerts = filter === 'ALL'
    ? alerts
    : alerts.filter(a => a.status === filter);

  // Sorting descending by ID (newest first based on DB increment)
  filteredAlerts.sort((a, b) => b.id - a.id);

  return (
    <>
      <PageHeader
        eyebrow="Operations / Risk response"
        title="Alert Center"
        subtitle="Review, confirm, and route model-generated alerts."
      />
      <section className="alert-layout" style={{ alignItems: 'start' }}>
        <BorderGlow glowColor="0 0 20" backgroundColor="#ffffff" colors={['#222222', '#333333', '#111111']} borderRadius={4} glowRadius={15}>
          <div className="panel alert-card" style={{ border: 'none', boxShadow: 'none' }}>
            <div className="eyebrow" style={{ display: 'flex', gap: '16px', padding: '24px 25px', borderBottom: '1px solid var(--line)', marginBottom: 0 }}>
            <button className={`text-button ${filter === 'ALL' ? '' : 'muted'}`} onClick={(e) => { e.preventDefault(); setFilter('ALL'); }}>ALL</button>
            <button className={`text-button ${filter === 'OPEN' ? '' : 'muted'}`} onClick={(e) => { e.preventDefault(); setFilter('OPEN'); }}>OPEN</button>
            <button className={`text-button ${filter === 'ACKNOWLEDGED' ? '' : 'muted'}`} onClick={(e) => { e.preventDefault(); setFilter('ACKNOWLEDGED'); }}>ACKNOWLEDGED</button>
            <button className={`text-button ${filter === 'RESOLVED' ? '' : 'muted'}`} onClick={(e) => { e.preventDefault(); setFilter('RESOLVED'); }}>RESOLVED</button>
          </div>

          {filteredAlerts.length === 0 ? (
             <div style={{ padding: '24px 25px', color: '#a1a1aa' }}>No {filter !== 'ALL' ? filter.toLowerCase() : ''} alerts available.</div>
          ) : (
            filteredAlerts.slice(0, 50).map(alert => (
              <div key={alert.id} style={{ borderBottom: '1px solid var(--line)' }}>
                <div className={`alert-banner ${alert.status === 'RESOLVED' ? 'resolved' : ''}`} style={{ margin: 0 }}>
                  <span>{alert.status === 'RESOLVED' ? '✓' : '!'}</span>
                  <div>
                    <Badge tone={alert.priority === 'CRITICAL' ? 'red' : 'amber'}>{alert.priority} ALERT</Badge>
                    <h2
                      style={{ cursor: 'pointer', textDecoration: 'underline', color: cases.some((c: any) => c.case_id === alert.case_id) ? 'inherit' : '#ef4444' }}
                      onClick={() => {
                        if (!cases.some((c: any) => c.case_id === alert.case_id)) {
                          window.alert(`Case ${alert.case_id} is missing from the queue or restricted.`);
                          return;
                        }
                        setCaseId(alert.case_id);
                        setView('case');
                      }}
                    >
                      {cases.some((c: any) => c.case_id === alert.case_id)
                        ? `Case ${alert.case_id} requires review`
                        : `Orphaned/Restricted Alert: Case ${alert.case_id} missing`}
                    </h2>
                    <p>Generated {new Date(alert.created_at).toLocaleString()}</p>
                  </div>
                </div>

                <div className="alert-details" style={{ margin: 0 }}>
                  <div>
                    <span className="eyebrow">Status</span>
                    <strong>{alert.status}</strong>
                  </div>
                  {alert.prediction_id && (
                    <div>
                      <span className="eyebrow">Prediction Relation</span>
                      <strong>Prediction #{alert.prediction_id}</strong>
                    </div>
                  )}
                  {alert.target_stakeholder && (
                    <div>
                      <span className="eyebrow">Target Stakeholder</span>
                      <Badge tone="blue">{alert.target_stakeholder}</Badge>
                    </div>
                  )}
                  {alert.recommended_action && (
                    <div>
                      <span className="eyebrow">Recommended Action</span>
                      <strong>{alert.recommended_action.replace(/_/g, ' ')}</strong>
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', padding: '0 24px 24px 25px' }}>
                  {alert.status === 'OPEN' && (
                    <button className="button button-primary" disabled={actingOn === alert.id} onClick={(e) => { e.preventDefault(); updateStatus(alert.id, 'ACKNOWLEDGED'); }}>
                      {actingOn === alert.id ? 'Working...' : 'Acknowledge'}
                    </button>
                  )}
                  {alert.status === 'ACKNOWLEDGED' && (
                    <button className="button button-primary" disabled={actingOn === alert.id} onClick={(e) => { e.preventDefault(); updateStatus(alert.id, 'RESOLVED'); }}>
                      {actingOn === alert.id ? 'Working...' : 'Resolve'}
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
          </div>
        </BorderGlow>

        <BorderGlow glowColor="0 0 20" backgroundColor="#ffffff" colors={['#222222', '#333333', '#111111']} borderRadius={4} glowRadius={15}>
          <div className="panel" style={{ border: 'none', boxShadow: 'none' }}>
            <div className="eyebrow">Open alerts</div>
          <h2>Queue health</h2>
          <div className="queue-number">{alerts.length}</div>
          <p className="muted">Total alerts</p>
          <div className="queue-row"><span>Awaiting review (OPEN)</span><b>{openAlerts}</b></div>
          <div className="queue-row"><span>Acknowledged</span><b>{acknowledgedAlerts}</b></div>
          <div className="queue-row"><span>Resolved</span><b>{resolvedAlerts}</b></div>
          </div>
        </BorderGlow>
      </section>
    </>
  )
}
