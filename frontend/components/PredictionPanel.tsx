import { useState, useEffect } from 'react'
import { PageHeader } from './ui/PageHeader'
import { Badge } from './ui/Badge'
import BorderGlow from './BorderGlow'

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
  const [selectedAtmId, setSelectedAtmId] = useState<string | null>(null);

  useEffect(() => {
    if (predictionData?.predictions?.length > 0 && !selectedAtmId) {
      setSelectedAtmId(predictionData.predictions[0].atm_id);
    }
  }, [predictionData, selectedAtmId]);

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

  const isUnknown = predictionData.risk === 'UNKNOWN';
  const selectedCandidate = predictionData.predictions?.find((p: any) => p.atm_id === selectedAtmId) || predictionData.predictions?.[0];

  let likelihoodText = '';
  if (predictionData.risk === 'LOW') likelihoodText = 'low';
  else if (predictionData.risk === 'MEDIUM') likelihoodText = 'moderate';
  else if (predictionData.risk === 'HIGH' || predictionData.risk === 'CRITICAL') likelihoodText = 'high';
  else likelihoodText = 'unknown';

  let dynamicSentence = '';
  if (isUnknown) {
    dynamicSentence = 'Insufficient data to generate a reliable likelihood of suspicious cash-out activity.';
  } else {
    dynamicSentence = "Strong historical, transactional and spatial signals indicate elevated cash-out risk.";
  }

  return (
    <>
      <PageHeader
        eyebrow={`${caseId} / Model output`}
        title="Prediction Rationale"
        subtitle={isUnknown ? "Insufficient data to generate prediction." : "Model explanation for the current risk score."}
        action={!isUnknown ? <button className="button button-primary" onClick={() => setView('alerts')}>View Alert(s)</button> : undefined}
      />

      <div className="prediction-grid">
        <BorderGlow glowColor="0 0 20" backgroundColor="#ffffff" colors={['#222222', '#333333', '#111111']} borderRadius={4} glowRadius={15} style={{ height: '100%' }}>
          <section className="panel score-panel" style={{ border: 'none', boxShadow: 'none', height: '100%', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
              <div className="score" style={{ fontSize: '3rem', fontWeight: 800, lineHeight: 1, margin: 0, color: '#111111', opacity: 1 }}>{isUnknown ? 'N/A' : predictionData.risk}</div>
              <div>
                <Badge tone={isUnknown ? 'neutral' : (predictionData.risk === 'CRITICAL' ? 'red' : 'amber')}>
                  {isUnknown ? 'INSUFFICIENT DATA' : `${predictionData.risk} RISK`}
                </Badge>
              </div>
            </div>

            <p style={{ fontSize: '0.95rem', color: '#a1a1aa', lineHeight: 1.5, marginBottom: '2rem', flex: 1 }}>
              {dynamicSentence}
            </p>

            <div className="model-foot" style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid #27272a', fontSize: '0.85rem', color: '#71717a' }}>
              <span>Time Window: {predictionData.time_window || 'N/A'}</span>
            </div>
          </section>
        </BorderGlow>

        <BorderGlow glowColor="0 0 20" backgroundColor="#ffffff" colors={['#222222', '#333333', '#111111']} borderRadius={4} glowRadius={15} style={{ height: '100%' }}>
          <section className="panel factors" style={{ border: 'none', boxShadow: 'none', height: '100%' }}>
            <div className="eyebrow">Risk Locations</div>
            <h2>Top predicted candidates</h2>
            {predictionData.predictions && predictionData.predictions.length > 0 ? (
              predictionData.predictions.slice(0, 5).map((p: any) => (
                <div
                  className="factor"
                  key={p.atm_id}
                  onClick={() => setSelectedAtmId(p.atm_id)}
                  style={{
                    cursor: 'pointer',
                    backgroundColor: selectedAtmId === p.atm_id ? 'rgba(255,255,255,0.05)' : 'transparent',
                    padding: '0.5rem',
                    borderRadius: '4px'
                  }}
                >
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
              <div style={{ color: '#a1a1aa' }}>{isUnknown ? 'Prediction aborted due to lack of historical data.' : 'No predictions available'}</div>
            )}
          </section>
        </BorderGlow>
      </div>



      {selectedCandidate && selectedCandidate.response && (
        <BorderGlow glowColor="0 0 20" backgroundColor="#ffffff" colors={['#222222', '#333333', '#111111']} borderRadius={4} glowRadius={15} style={{ marginTop: '1.5rem' }}>
          <section className="panel response" style={{ border: 'none', boxShadow: 'none' }}>
            <div className="eyebrow">Response Intelligence ({selectedCandidate.atm_id})</div>
            <h2>Actionable Intelligence</h2>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginTop: '1rem' }}>
              <div>
                <div style={{ color: '#a1a1aa', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Nearest Police Station</div>
                <div style={{ fontWeight: 500, fontSize: '1.125rem' }}>{selectedCandidate.response.nearest_station_name || 'N/A'}</div>
              </div>
              <div>
                <div style={{ color: '#a1a1aa', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Distance</div>
                <div style={{ fontWeight: 500, fontSize: '1.125rem' }}>
                  {selectedCandidate.response.distance_km ? `${selectedCandidate.response.distance_km} km` : 'N/A'}
                </div>
              </div>
              <div>
                <div style={{ color: '#a1a1aa', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Jurisdiction</div>
                <div style={{ fontWeight: 500, fontSize: '1.125rem' }}>{selectedCandidate.response.jurisdiction || 'N/A'}</div>
              </div>
              <div>
                <div style={{ color: '#a1a1aa', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Recommended Action</div>
                <div style={{ fontWeight: 500, color: '#60a5fa' }}>{selectedCandidate.response.recommended_action}</div>
              </div>
            </div>
          </section>
        </BorderGlow>
      )}
    </>
  )
}
