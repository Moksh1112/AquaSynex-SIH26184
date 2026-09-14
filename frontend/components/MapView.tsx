'use client'

import { useState, useMemo } from 'react'
import dynamic from 'next/dynamic'
import { PageHeader } from './ui/PageHeader'
import { Badge } from './ui/Badge'

const MapClient = dynamic(() => import('./MapClient'), {
  ssr: false,
  loading: () => <div style={{ padding: '2rem' }}>Loading geographic map...</div>
})

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
  const [selectedAtmId, setSelectedAtmId] = useState<string | null>(null);

  const [riskFilter, setRiskFilter] = useState<string>('ALL');
  const [timeFilter, setTimeFilter] = useState<string>('ALL');
  const [radiusFilter, setRadiusFilter] = useState<number>(0); // 0 means ALL

  const filteredCandidates = useMemo(() => {
    if (!predictionData?.predictions) return [];

    // Time filter - since prediction is for a specific time window
    if (timeFilter !== 'ALL' && predictionData.time_window !== timeFilter) {
      return [];
    }

    return predictionData.predictions.filter((p: any) => {
      if (riskFilter !== 'ALL' && p.risk !== riskFilter) return false;

      if (radiusFilter > 0) {
        // Simple distance filter from Mumbai center [19.076, 72.877]
        const dLat = p.latitude - 19.076;
        const dLon = p.longitude - 72.877;
        const distDeg = Math.sqrt(dLat*dLat + dLon*dLon);
        // roughly 1 deg = 111km
        if (distDeg * 111 > radiusFilter) return false;
      }
      return true;
    });
  }, [predictionData, riskFilter, timeFilter, radiusFilter]);

  const filteredPredictionData = {
    ...predictionData,
    predictions: filteredCandidates
  };

  return (
    <>
      <PageHeader 
        eyebrow={`${caseId} / Geospatial analysis`} 
        title="Geo Intelligence" 
        subtitle="Jurisdictional view of the transfer network and predicted locations." 
      />
      <div className="filter-row" style={{ marginBottom: '1rem', display: 'flex', gap: '1rem' }}>
         <div>
            <label style={{ marginRight: '0.5rem', color: '#a1a1aa' }}>Risk Level:</label>
            <select style={{ background: '#27272a', color: 'white', border: '1px solid #3f3f46', padding: '0.25rem' }} value={riskFilter} onChange={e => setRiskFilter(e.target.value)}>
               <option value="ALL">All Risks</option>
               <option value="HIGH">High Risk</option>
               <option value="MEDIUM">Medium Risk</option>
            </select>
         </div>
         <div>
            <label style={{ marginRight: '0.5rem', color: '#a1a1aa' }}>Time Window:</label>
            <select style={{ background: '#27272a', color: 'white', border: '1px solid #3f3f46', padding: '0.25rem' }} value={timeFilter} onChange={e => setTimeFilter(e.target.value)}>
               <option value="ALL">All Times</option>
               <option value={predictionData?.time_window || "22:00-23:00"}>Predicted: {predictionData?.time_window || "N/A"}</option>
            </select>
         </div>
         <div>
            <label style={{ marginRight: '0.5rem', color: '#a1a1aa' }}>Radius (Mumbai):</label>
            <select style={{ background: '#27272a', color: 'white', border: '1px solid #3f3f46', padding: '0.25rem' }} value={radiusFilter} onChange={e => setRadiusFilter(Number(e.target.value))}>
               <option value={0}>Anywhere</option>
               <option value={5}>Within 5 km</option>
               <option value={15}>Within 15 km</option>
               <option value={50}>Within 50 km</option>
            </select>
         </div>
      </div>
      <section className="panel map-panel" style={{ display: 'flex' }}>
        {loadingPrediction ? (
          <div style={{ padding: '2rem' }}>Loading map data...</div>
        ) : (!locationsData || locationsData.length === 0) ? (
          <div style={{ padding: '2rem', color: '#a1a1aa' }}>No locations found.</div>
        ) : (
          <>
            <div className="map-canvas" style={{ flexGrow: 1, position: 'relative', overflow: 'hidden' }}>
              <MapClient
                predictionData={filteredPredictionData}
                locationsData={locationsData}
                selectedAtmId={selectedAtmId}
              />
            </div>
            <div className="map-side" style={{ flexShrink: 0, width: '300px', overflowY: 'auto' }}>
              <div className="eyebrow">Prediction Candidates</div>
              <h2>{filteredCandidates.length} Predicted Locations</h2>
              {filteredCandidates.length > 0 ? (
                filteredCandidates.map((p: any) => (
                  <div
                    className="jurisdiction"
                    key={p.atm_id}
                    onClick={() => setSelectedAtmId(p.atm_id)}
                    style={{
                      cursor: 'pointer',
                      backgroundColor: selectedAtmId === p.atm_id ? 'rgba(255,255,255,0.1)' : 'transparent',
                      padding: '10px',
                      borderRadius: '8px',
                      marginBottom: '8px',
                      border: selectedAtmId === p.atm_id ? '1px solid rgba(255,255,255,0.2)' : '1px solid transparent'
                    }}
                  >
                    <span className={`country-dot ${p.risk === 'HIGH' ? 'red' : 'amber'}`} />
                    <div>
                      <strong>#{p.rank} {p.atm_id}</strong>
                      <small style={{ display: 'block' }}>{p.latitude}, {p.longitude}</small>
                    </div>
                    <Badge tone={p.risk === 'HIGH' ? 'red' : 'amber'}>{p.risk}</Badge>
                  </div>
                ))
              ) : (
                <div style={{ color: '#a1a1aa', marginTop: '1rem' }}>No predictions match filters.</div>
              )}
            </div>
          </>
        )}
      </section>
    </> 
  )
}
