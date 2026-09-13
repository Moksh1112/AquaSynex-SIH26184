'use client'

import { PageHeader } from './ui/PageHeader'
import { Badge } from './ui/Badge'

export function MapView({ 
  caseId, 
  predictionData, 
  loadingPrediction,
  locationsData
}: { 
  caseId: string; 
  predictionData: any; 
  loadingPrediction: boolean;
  locationsData: any[];
}) {
  return (
    <>
      <PageHeader 
        eyebrow={`${caseId} / Geospatial analysis`} 
        title="Geo Intelligence" 
        subtitle="Jurisdictional view of the transfer network and predicted locations." 
      />
      <section className="panel map-panel">
        {loadingPrediction ? (
          <div style={{ padding: '2rem' }}>Loading map data...</div>
        ) : (!locationsData || locationsData.length === 0) ? (
          <div style={{ padding: '2rem', color: '#a1a1aa' }}>No locations found.</div>
        ) : (
          <>
            <div className="map-canvas" style={{ position: 'relative', overflow: 'hidden' }}>
              <div className="map-grid" />
              
              {/* Display background ATMs */}
              {locationsData.map((loc: any, i: number) => {
                 // Fake a position based on hash or just randomly distribute them for visual purposes if they don't have normalized coordinates. 
                 // Since this is a demo, we will use index to scatter them if actual lat/lon isn't easily map-able to CSS.
                 // Assuming actual lat/lon needs projection, we'll do a simple mock projection.
                 const top = ((Math.abs(loc.latitude) % 90) / 90) * 100;
                 const left = ((Math.abs(loc.longitude) % 180) / 180) * 100;
                 
                 // Is it a prediction?
                 const isPredicted = predictionData?.predictions?.find((p: any) => p.atm_id === loc.atm_id);
                 
                 return (
                   <div 
                     key={loc.atm_id} 
                     className={`map-label`} 
                     style={{
                       position: 'absolute', 
                       top: `${top}%`, 
                       left: `${left}%`, 
                       transform: 'translate(-50%, -50%)', 
                       backgroundColor: isPredicted ? 'rgba(255,0,0,0.8)' : 'rgba(0,0,0,0.5)', 
                       padding: '5px', 
                       borderRadius: '4px',
                       zIndex: isPredicted ? 10 : 1
                     }}
                   >
                     {loc.atm_id}
                     {isPredicted && <span>{isPredicted.risk} RISK</span>}
                   </div>
                 );
              })}
              <div className="map-watermark">FININT<br />NETWORK MAP</div>
            </div>
            <div className="map-side">
              <div className="eyebrow">Prediction Candidates</div>
              <h2>{predictionData?.predictions?.length || 0} Predicted Locations</h2>
              {predictionData?.predictions?.length > 0 ? (
                predictionData.predictions.map((p: any) => (
                  <div className="jurisdiction" key={p.atm_id}>
                    <span className={`country-dot ${p.risk === 'HIGH' ? 'red' : 'amber'}`} />
                    <div>
                      <strong>{p.atm_id}</strong>
                      <small>{p.latitude}, {p.longitude}</small>
                    </div>
                    <Badge tone={p.risk === 'HIGH' ? 'red' : 'amber'}>{p.risk}</Badge>
                  </div>
                ))
              ) : (
                <div style={{ color: '#a1a1aa' }}>No predictions available for this case.</div>
              )}
            </div>
          </>
        )}
      </section>
    </> 
  )
}
