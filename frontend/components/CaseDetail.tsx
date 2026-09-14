'use client'

import { useState, useEffect, useCallback } from 'react'
import { PageHeader } from './ui/PageHeader'
import { Badge } from './ui/Badge'
import { FlowEntity } from '../lib/graph-transform'
import { fetchApi } from '../lib/api'

export function CaseDetail({ 
  token,
  setView, 
  caseId, 
  caseDetails,
  loadingCase,
  flow, 
  loadingGraph 
}: { 
  token: string;
  setView: (v: string) => void; 
  caseId: string; 
  caseDetails: any;
  loadingCase: boolean;
  flow: FlowEntity[]; 
  loadingGraph: boolean;
}) {
  const [evidence, setEvidence] = useState<any[]>([]);
  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const [newEvidence, setNewEvidence] = useState({ title: '', type: 'TRANSACTION_LOG', source: '' });
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const fetchEvidence = useCallback(async () => {
    if (!token || !caseId) return;
    setLoadingEvidence(true);
    try {
      const data = await fetchApi(`/evidence/${caseId}`, token);
      setEvidence(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingEvidence(false);
    }
  }, [token, caseId]);

  useEffect(() => {
    fetchEvidence();
  }, [fetchEvidence]);

  const handleAddEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEvidence.title) return;
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('case_id', caseId);
      formData.append('evidence_type', newEvidence.type);
      formData.append('title', newEvidence.title);
      if (newEvidence.source) formData.append('source', newEvidence.source);
      if (file) formData.append('file', file);

      await fetchApi('/evidence/', token, {
        method: 'POST',
        body: formData
      });

      setNewEvidence({ title: '', type: 'TRANSACTION_LOG', source: '' });
      setFile(null);
      // Let the form element clear the file input
      const fileInput = document.getElementById('evidence-file') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

      fetchEvidence();
    } catch (err: any) {
      let msg = err.message || 'Unknown error occurred';
      alert(`Evidence upload failed: ${msg}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (evidenceId: number, originalFilename: string) => {
    try {
      const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${BASE_URL}/evidence/file/${evidenceId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        let msg = 'Failed to download';
        try { const d = await response.json(); msg = d.detail || msg; } catch(e){}
        alert(`Download failed: ${msg}`);
        return;
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = originalFilename || `evidence_${evidenceId}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e: any) {
      alert(`Download failed: ${e.message}`);
    }
  };

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

          <hr style={{ borderColor: '#27272a', margin: '2rem 0' }} />

          <div className="panel-head">
             <div>
               <div className="eyebrow">Documentation</div>
               <h2>Evidence Records</h2>
             </div>
          </div>
          <div style={{ marginBottom: '1.5rem' }}>
             {loadingEvidence ? (
               <div style={{ color: '#a1a1aa' }}>Loading evidence...</div>
             ) : evidence.length === 0 ? (
               <div style={{ color: '#a1a1aa' }}>No evidence attached to this case.</div>
             ) : (
               <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {evidence.map(ev => (
                     <div key={ev.id} style={{ padding: '1rem', background: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                           <strong style={{ color: '#f4f4f5' }}>{ev.title}</strong>
                           <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                              {!ev.original_filename && <Badge tone="neutral">Metadata Only</Badge>}
                              {ev.original_filename && (
                                <button
                                  onClick={() => handleDownload(ev.id, ev.original_filename)}
                                  className="button button-quiet"
                                  style={{ padding: '4px 8px', fontSize: '0.85rem' }}
                                >
                                  Download File
                                </button>
                              )}
                              <Badge tone="slate">{ev.evidence_type}</Badge>
                           </div>
                        </div>
                        <div style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>
                           Source: {ev.source || 'Unknown'} • Uploaded by: {ev.created_by} • {new Date(ev.created_at).toLocaleString()}
                        </div>
                        {ev.original_filename && (
                           <div style={{ color: '#a1a1aa', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                              File: {ev.original_filename} {ev.file_size ? `(${Math.round(ev.file_size / 1024)} KB)` : ''}
                           </div>
                        )}
                     </div>
                  ))}
               </div>
             )}
          </div>

          <div style={{ background: '#18181b', padding: '1rem', border: '1px solid #27272a', borderRadius: '8px' }}>
             <h3 style={{ margin: '0 0 1rem 0', fontSize: '1rem', color: '#f4f4f5' }}>Attach New Evidence</h3>
             <form onSubmit={handleAddEvidence} style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <input
                   placeholder="Title (e.g. Subpoena Docs)"
                   value={newEvidence.title}
                   onChange={e => setNewEvidence({...newEvidence, title: e.target.value})}
                   style={{ flexGrow: 1, minWidth: '200px', background: '#27272a', color: 'white', border: '1px solid #3f3f46', padding: '0.5rem', borderRadius: '4px' }}
                   required
                />
                <input
                   placeholder="Source (e.g. HDFC Bank)"
                   value={newEvidence.source}
                   onChange={e => setNewEvidence({...newEvidence, source: e.target.value})}
                   style={{ flexGrow: 1, minWidth: '200px', background: '#27272a', color: 'white', border: '1px solid #3f3f46', padding: '0.5rem', borderRadius: '4px' }}
                />
                <select
                   value={newEvidence.type}
                   onChange={e => setNewEvidence({...newEvidence, type: e.target.value})}
                   style={{ background: '#27272a', color: 'white', border: '1px solid #3f3f46', padding: '0.5rem', borderRadius: '4px' }}
                >
                   <option value="TRANSACTION_LOG">Transaction Log</option>
                   <option value="POLICE_REPORT">Police Report</option>
                   <option value="VIDEO">Video / CCTV</option>
                   <option value="OTHER">Other</option>
                </select>
                <div style={{ width: '100%', display: 'flex', gap: '1rem', alignItems: 'center' }}>
                  <input
                     id="evidence-file"
                     type="file"
                     onChange={e => setFile(e.target.files?.[0] || null)}
                     style={{ background: '#27272a', color: 'white', border: '1px solid #3f3f46', padding: '0.4rem', borderRadius: '4px', flexGrow: 1 }}
                  />
                  <button type="submit" className="button button-primary" disabled={uploading}>
                    {uploading ? 'Uploading...' : 'Attach'}
                  </button>
                </div>
             </form>
          </div>
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
