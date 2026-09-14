'use client'

import { PageHeader } from './ui/PageHeader'
import { Badge } from './ui/Badge'

import { useState, useEffect } from 'react'
import { fetchApi } from '../lib/api'

type IntakeStage = 'idle' | 'form' | 'processing' | 'done'

const PROCESSING_STEPS = [
  { id: 1, label: 'Intake received',       detail: 'Complaint logged in the case management system.' },
  { id: 2, label: 'Analyzing case',        detail: 'Cross-referencing account and transaction history.' },
  { id: 3, label: 'Generating prediction', detail: 'Running predictive analytics pipeline.' },
  { id: 4, label: 'Alert created',         detail: 'Investigation alert dispatched to the queue.' },
]

export function Cases({ 
  setView, 
  setCaseId, 
  cases,
  loading,
  token,
  refreshCases
}: { 
  setView: (v: string) => void; 
  setCaseId: (id: string) => void; 
  cases: any[];
  loading: boolean;
  token: string;
  refreshCases: () => void;
}) {
  const [stage, setStage] = useState<IntakeStage>('idle');
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [simData, setSimData] = useState({
    ncrp_id: `C-2026-${Math.floor(1000 + Math.random() * 9000)}`,
    description: '',
    account_number: 'V-100200300',
    fraud_amount: 50000,
    category: 'FINANCIAL_FRAUD',
    timestamp: new Date().toISOString().slice(0, 16),
  });
  const [newCaseId, setNewCaseId] = useState('');

  const openModal  = () => { setStage('form'); setCompletedSteps([]); };
  const closeModal = () => { setStage('idle'); setCompletedSteps([]); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStage('processing');
    setCompletedSteps([]);

    try {
      const payload = {
        ncrp_id:        simData.ncrp_id,
        description:    simData.description || 'Complaint submitted via NCRP portal',
        account_number: simData.account_number,
        fraud_amount:   simData.fraud_amount,
        category:       simData.category,
        timestamp:      new Date(simData.timestamp).toISOString(),
      };

      // Animate steps in sequence while the real POST is in flight
      const stepDelay = 900;
      for (let i = 1; i <= PROCESSING_STEPS.length; i++) {
        await new Promise(r => setTimeout(r, stepDelay));
        setCompletedSteps(prev => [...prev, i]);
      }

      await fetchApi('/ncrp/complaints', token, {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      setNewCaseId(simData.ncrp_id);
      setStage('done');
      refreshCases();
      // Seed a fresh ID for the next session
      setSimData(prev => ({
        ...prev,
        ncrp_id: `C-2026-${Math.floor(1000 + Math.random() * 9000)}`,
        description: '',
        timestamp: new Date().toISOString().slice(0, 16),
      }));
    } catch (err: any) {
      alert(`Intake failed: ${err.message}`);
      setStage('form');
    }
  };

  return (
    <>
      <PageHeader 
        eyebrow="Investigations / Queue" 
        title="Case Files" 
        subtitle={`${cases.length} active investigations (Sourced from NCRP Intake)`}
      />
      <div className="filter-row" style={{ display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <button className="filter active">All cases <b>{cases.length}</b></button>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="button button-primary" onClick={openModal} id="new-intake-btn">
            + New Intake
          </button>
          <div className="search">⌕ <input placeholder="Search case ID..." /></div>
        </div>
      </div>

      {/* ── MODAL OVERLAY ── */}
      {(stage !== 'idle') && (
        <div
          onClick={stage === 'form' ? closeModal : undefined}
          style={{
            position: 'fixed', inset: 0, zIndex: 1000,
            background: 'rgba(0,0,0,0.72)',
            backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            animation: 'fadeIn 0.18s ease',
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              width: '100%', maxWidth: 540,
              background: '#18181b',
              border: '1px solid #3f3f46',
              borderRadius: 14,
              padding: '2rem 2.25rem',
              boxShadow: '0 24px 80px rgba(0,0,0,0.6)',
              animation: 'slideUp 0.22s ease',
            }}
          >
            {/* ── FORM STAGE ── */}
            {stage === 'form' && (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.75rem' }}>
                  <div>
                    <div style={{ fontSize: '0.7rem', letterSpacing: '0.1em', textTransform: 'uppercase', color: '#71717a', marginBottom: '0.35rem' }}>
                      National Cybercrime Reporting Portal
                    </div>
                    <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#f4f4f5' }}>
                      New Cybercrime Complaint
                    </h2>
                  </div>
                  <button
                    onClick={closeModal}
                    style={{ background: 'none', border: 'none', color: '#71717a', fontSize: '1.2rem', cursor: 'pointer', lineHeight: 1 }}
                    aria-label="Close"
                  >✕</button>
                </div>

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>

                  {/* NCRP Reference */}
                  <label style={labelStyle}>
                    <span style={labelTextStyle}>NCRP Reference</span>
                    <input
                      value={simData.ncrp_id}
                      onChange={e => setSimData({ ...simData, ncrp_id: e.target.value })}
                      required
                      style={inputStyle}
                    />
                  </label>

                  {/* Case Description */}
                  <label style={labelStyle}>
                    <span style={labelTextStyle}>Case Description</span>
                    <textarea
                      value={simData.description}
                      onChange={e => setSimData({ ...simData, description: e.target.value })}
                      placeholder="Briefly describe the nature of the fraud…"
                      rows={2}
                      style={{ ...inputStyle, resize: 'vertical' }}
                    />
                  </label>

                  {/* Account + Amount row */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <label style={labelStyle}>
                      <span style={labelTextStyle}>Victim Account</span>
                      <input
                        value={simData.account_number}
                        onChange={e => setSimData({ ...simData, account_number: e.target.value })}
                        placeholder="V-100200300"
                        required
                        style={inputStyle}
                      />
                    </label>
                    <label style={labelStyle}>
                      <span style={labelTextStyle}>Fraud Amount (₹)</span>
                      <input
                        type="number"
                        value={simData.fraud_amount}
                        onChange={e => setSimData({ ...simData, fraud_amount: Number(e.target.value) })}
                        required
                        min={1}
                        style={inputStyle}
                      />
                    </label>
                  </div>

                  {/* Category + Time row */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <label style={labelStyle}>
                      <span style={labelTextStyle}>Crime Category</span>
                      <select
                        value={simData.category}
                        onChange={e => setSimData({ ...simData, category: e.target.value })}
                        style={{ ...inputStyle, appearance: 'auto' }}
                      >
                        <option value="FINANCIAL_FRAUD">Financial Fraud</option>
                        <option value="IDENTITY_THEFT">Identity Theft</option>
                        <option value="ATM_SKIMMING">ATM Skimming</option>
                        <option value="PHISHING">Phishing</option>
                        <option value="OTHER">Other</option>
                      </select>
                    </label>
                    <label style={labelStyle}>
                      <span style={labelTextStyle}>Incident Time</span>
                      <input
                        type="datetime-local"
                        value={simData.timestamp}
                        onChange={e => setSimData({ ...simData, timestamp: e.target.value })}
                        required
                        style={inputStyle}
                      />
                    </label>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
                    <span style={{ fontSize: '0.72rem', color: '#52525b' }}>
                      Prototype mode — local simulation only
                    </span>
                    <button
                      type="submit"
                      className="button button-primary"
                      id="submit-intake-btn"
                      style={{ padding: '0.6rem 1.4rem', fontWeight: 600 }}
                    >
                      Submit Intake →
                    </button>
                  </div>
                </form>
              </>
            )}

            {/* ── PROCESSING STAGE ── */}
            {(stage === 'processing' || stage === 'done') && (
              <div style={{ padding: '0.5rem 0' }}>
                <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', letterSpacing: '0.1em', textTransform: 'uppercase', color: '#71717a', marginBottom: '0.4rem' }}>
                    Processing Intake
                  </div>
                  <h2 style={{ margin: 0, fontSize: '1.2rem', color: '#f4f4f5' }}>
                    {stage === 'done' ? 'Case Created Successfully' : 'Please wait…'}
                  </h2>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', marginBottom: '2rem' }}>
                  {PROCESSING_STEPS.map((step, i) => {
                    const done    = completedSteps.includes(step.id);
                    const active  = !done && completedSteps.length === step.id - 1 && stage === 'processing';
                    const pending = !done && !active;

                    return (
                      <div key={step.id}>
                        <div style={{
                          display: 'flex', alignItems: 'center', gap: '0.9rem',
                          padding: '0.85rem 1rem',
                          borderRadius: 8,
                          background: done ? 'rgba(16,185,129,0.07)' : active ? 'rgba(99,102,241,0.09)' : 'transparent',
                          transition: 'background 0.3s',
                        }}>
                          {/* Icon */}
                          <div style={{
                            width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: '0.8rem',
                            background: done ? '#10b981' : active ? '#6366f1' : '#27272a',
                            color: done || active ? 'white' : '#52525b',
                            boxShadow: active ? '0 0 12px rgba(99,102,241,0.5)' : 'none',
                            transition: 'all 0.3s',
                          }}>
                            {done ? '✓' : active ? <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>◌</span> : step.id}
                          </div>
                          {/* Label */}
                          <div>
                            <div style={{ fontWeight: 600, fontSize: '0.9rem', color: done ? '#10b981' : active ? '#a5b4fc' : '#71717a' }}>
                              {step.label}
                            </div>
                            {(done || active) && (
                              <div style={{ fontSize: '0.75rem', color: '#52525b', marginTop: '0.1rem' }}>
                                {step.detail}
                              </div>
                            )}
                          </div>
                        </div>
                        {/* Connector line */}
                        {i < PROCESSING_STEPS.length - 1 && (
                          <div style={{ marginLeft: '1.85rem', width: 1, height: 8, background: done ? '#10b981' : '#27272a', transition: 'background 0.4s' }} />
                        )}
                      </div>
                    );
                  })}
                </div>

                {stage === 'done' && (
                  <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                    <button
                      className="button"
                      onClick={closeModal}
                      style={{ padding: '0.6rem 1.2rem' }}
                    >
                      Close
                    </button>
                    <button
                      className="button button-primary"
                      id="view-new-case-btn"
                      onClick={() => { setCaseId(newCaseId); setView('case'); closeModal(); }}
                      style={{ padding: '0.6rem 1.4rem', fontWeight: 600 }}
                    >
                      View Case →
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── CASES TABLE ── */}
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

      <style>{`
        @keyframes fadeIn  { from { opacity:0 }              to { opacity:1 } }
        @keyframes slideUp { from { transform:translateY(20px); opacity:0 } to { transform:translateY(0); opacity:1 } }
        @keyframes spin    { to   { transform:rotate(360deg) } }
      `}</style>
    </>
  )
}

// ── Shared style tokens ──────────────────────────────────────────────────────
const labelStyle: React.CSSProperties = {
  display: 'flex', flexDirection: 'column', gap: '0.35rem',
};
const labelTextStyle: React.CSSProperties = {
  fontSize: '0.72rem', fontWeight: 600, letterSpacing: '0.06em',
  textTransform: 'uppercase', color: '#71717a',
};
const inputStyle: React.CSSProperties = {
  background: '#27272a', color: '#f4f4f5',
  border: '1px solid #3f3f46', borderRadius: 6,
  padding: '0.55rem 0.75rem', fontSize: '0.9rem',
  width: '100%', boxSizing: 'border-box',
  outline: 'none',
};
