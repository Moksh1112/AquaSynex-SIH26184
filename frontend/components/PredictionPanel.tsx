'use client'

import { PageHeader } from './ui/PageHeader'
import { Badge } from './ui/Badge'

export function PredictionPanel({ 
  setView, 
  caseId, 
  predictionData, 
  loadingPrediction,
  runPrediction
}: { 
  setView: (v: string) => void; 
  caseId: string; 
  predictionData: any; 
  loadingPrediction: boolean;
  runPrediction: () => void;
}) {
  if (loadingPrediction) {
    return (
      <>
        <PageHeader eyebrow={`${caseId} / Model output`} title="Prediction Rationale" subtitle="Loading..." />
        <div style={{ padding: '2rem' }}>Loading prediction from backend...</div>
      </>
    )
  }

  if (!predictionData) {
    return (
      <>
        <PageHeader eyebrow={`${caseId} / Model output`} title="Prediction Rationale" subtitle="No prediction has been run for this case yet." />
        <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '1rem' }}>
          <p style={{ color: '#a1a1aa' }}>Run the ML model to generate risk scores, predictions, and alerts.</p>
          <button className="button button-primary" onClick={runPrediction}>Run Prediction Model</button>
        </div>
      </>
    )
  }
  
  return (
    <>
      <PageHeader 
        eyebrow={`${caseId} / Model output`} 
        title="Prediction Rationale" 
        subtitle="Transparent model explanation for the current risk score." 
        action={<button className="button button-primary" onClick={() => setView('alerts')}>View Alert(s)</button>} 
      />
      
      <div className="prediction-grid">
        <section className="panel score-panel">
          <div className="eyebrow">Predicted illicit flow</div>
          <div className="score">{predictionData.risk}</div>
          <Badge tone={predictionData.risk === 'CRITICAL' ? 'red' : 'amber'}>{predictionData.risk} RISK</Badge>
          <div className="model-foot" style={{ marginTop: 'auto' }}>
            <span>Time Window: {predictionData.time_window || 'N/A'}</span>
          </div>
        </section>
        
        <section className="panel factors">
          <div className="eyebrow">Risk Locations</div>
          <h2>Top predicted candidates</h2>
          {predictionData.predictions && predictionData.predictions.length > 0 ? (
            predictionData.predictions.slice(0, 5).map((p: any) => (
              <div className="factor" key={p.atm_id}>
                <div>
                  <span>{p.atm_id}</span>
                  <b className={p.risk === 'HIGH' ? 'text-red' : 'text-amber'}>{(p.probability * 100).toFixed(1)}%</b>
                </div>
                <div className="factor-track">
                  <i className={`fill-${p.risk === 'HIGH' ? 'red' : 'amber'}`} style={{ width: `${p.probability * 100}%` }} />
                </div>
              </div>
            ))
          ) : (
             <div style={{ color: '#a1a1aa' }}>No predictions available</div>
          )}
        </section>
      </div>
      
      <section className="panel explanation">
        <div className="eyebrow">Plain-language explanation</div>
        <h2>Backend Model Explanation</h2>
        <p>{(predictionData.explanation || []).join(' ')}</p>
        <div className="explain-tags">
          {(predictionData.explanation || []).map((exp: string, idx: number) => (
            <Badge key={idx} tone={idx % 2 === 0 ? "red" : "amber"}>{exp}</Badge>
          ))}
        </div>
      </section>
    </>
  )
}
