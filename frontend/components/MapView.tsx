'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { PageHeader } from './ui/PageHeader'
import { Badge } from './ui/Badge'
import { fetchApi } from '../lib/api'

const MapClient = dynamic(() => import('./MapClient'), {
  ssr: false,
  loading: () => <div style={{ padding: '2rem' }}>Loading geographic map...</div>
})

export function MapView({
  token,
  caseId,
  predictionData,
  loadingPrediction,
  locationsData
}: {
  token: string;
  caseId: string;
  predictionData: any;
  loadingPrediction: boolean;
  locationsData: any[];
}) {
  const [selectedAtmId, setSelectedAtmId] = useState<string | null>(null);

  const [riskFilter, setRiskFilter] = useState<string>('');
  const [timeFilter, setTimeFilter] = useState<string>('');
  const [radiusFilter, setRadiusFilter] = useState<number>(0); // 0 means ALL
  const [categoryFilter, setCategoryFilter] = useState<string>('');

  const [mapMode, setMapMode] = useState<'CASE' | 'GLOBAL'>('CASE');
  const [heatmapData, setHeatmapData] = useState<any[]>([]);
  const [loadingHeatmap, setLoadingHeatmap] = useState<boolean>(false);

  useEffect(() => {
    if (!token || mapMode === 'CASE') return;

    setLoadingHeatmap(true);
    let url = '/locations/heatmap?';
    const params = new URLSearchParams();

    if (riskFilter) params.append('risk_level', riskFilter);
    if (categoryFilter) params.append('crime_category', categoryFilter);

    // Simplistic time filter logic for frontend demo bounds
    if (timeFilter && timeFilter !== 'ALL') {
      const now = new Date();
      if (timeFilter === 'LAST_24H') {
         params.append('start_time', new Date(now.getTime() - 24*60*60*1000).toISOString());
      } else if (timeFilter === 'LAST_7D') {
         params.append('start_time', new Date(now.getTime() - 7*24*60*60*1000).toISOString());
      }
    }

    if (radiusFilter > 0) {
      params.append('latitude', '19.076');
      params.append('longitude', '72.877');
      params.append('radius_km', radiusFilter.toString());
    }

    fetchApi(`/locations/heatmap?${params.toString()}`, token)
      .then(data => setHeatmapData(data || []))
      .catch(e => console.error("Failed to fetch heatmap", e))
      .finally(() => setLoadingHeatmap(false));
  }, [token, mapMode, riskFilter, timeFilter, radiusFilter, categoryFilter]);

  const activePredictionData = mapMode === 'CASE' ? predictionData : {
    ...predictionData,
    predictions: heatmapData.map(h => ({
      atm_id: h.atm_id,
      latitude: h.lat,
      longitude: h.lng,
      probability: h.weight,
      risk: h.risk_level || 'HIGH',
      rank: 1
    }))
  };

  const currentLocations = mapMode === 'CASE'
    ? (predictionData?.predictions || [])
    : heatmapData;


  return (
    <>
      <PageHeader
        eyebrow={`${caseId} / Geospatial analysis`}
        title="Geo Intelligence"
        subtitle="Jurisdictional view of the transfer network and predicted locations. Data is fetched directly from backend PostGIS filters."
      />
      <div className="filter-row" style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
         <div>
            <label style={{ marginRight: '0.5rem', color: '#a1a1aa' }}>Map Mode:</label>
            <select style={{ background: '#27272a', color: 'white', border: '1px solid #3f3f46', padding: '0.25rem', fontWeight: 'bold' }} value={mapMode} onChange={e => setMapMode(e.target.value as any)}>
               {caseId && <option value="CASE">Case Intelligence Mode</option>}
               <option value="GLOBAL">Global Risk Mode</option>
            </select>
         </div>
         {mapMode === 'GLOBAL' && (
           <>
             <div>
                <label style={{ marginRight: '0.5rem', color: '#a1a1aa' }}>Risk Level:</label>
                <select style={{ background: '#27272a', color: 'white', border: '1px solid #3f3f46', padding: '0.25rem' }} value={riskFilter} onChange={e => setRiskFilter(e.target.value)}>
                   <option value="">All Risks</option>
                   <option value="HIGH">High Risk</option>
                   <option value="MEDIUM">Medium Risk</option>
                </select>
             </div>
             <div>
                <label style={{ marginRight: '0.5rem', color: '#a1a1aa' }}>Time Window:</label>
                <select style={{ background: '#27272a', color: 'white', border: '1px solid #3f3f46', padding: '0.25rem' }} value={timeFilter} onChange={e => setTimeFilter(e.target.value)}>
                   <option value="">All Times</option>
                   <option value="LAST_24H">Last 24 Hours</option>
                   <option value="LAST_7D">Last 7 Days</option>
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
             <div>
                <label style={{ marginRight: '0.5rem', color: '#a1a1aa' }}>Crime Category:</label>
                <select style={{ background: '#27272a', color: 'white', border: '1px solid #3f3f46', padding: '0.25rem' }} value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}>
                   <option value="">All Categories</option>
                   <option value="FINANCIAL_FRAUD">Financial Fraud</option>
                   <option value="IDENTITY_THEFT">Identity Theft</option>
                   <option value="CYBER_TERRORISM">Cyber Terrorism</option>
                </select>
             </div>
           </>
         )}
      </div>
      <section className="panel map-panel" style={{ display: 'flex' }}>
        {mapMode === 'GLOBAL' && loadingHeatmap ? (
          <div style={{ padding: '2rem' }}>Loading heatmap data from backend...</div>
        ) : mapMode === 'CASE' && loadingPrediction ? (
          <div style={{ padding: '2rem' }}>Loading case prediction from backend...</div>
        ) : (!currentLocations || currentLocations.length === 0) ? (
          <div style={{ padding: '2rem', color: '#a1a1aa' }}>No locations available for this view.</div>
        ) : (
          <>
            <div className="map-canvas" style={{ flexGrow: 1, position: 'relative', overflow: 'hidden' }}>
              <MapClient
                predictionData={activePredictionData}
                locationsData={locationsData}
                selectedAtmId={selectedAtmId}
              />
            </div>
            <div className="map-side" style={{ flexShrink: 0, width: '300px', overflowY: 'auto' }}>
              <div className="eyebrow">{mapMode === 'CASE' ? 'Case Intelligence' : 'Global Risk View'}</div>
              <h2>{currentLocations.length} Matching Locations</h2>
              {currentLocations.length > 0 ? (
                currentLocations.map((h: any, idx: number) => (
                  <div
                    className="jurisdiction"
                    key={`${h.atm_id}-${idx}`}
                    onClick={() => setSelectedAtmId(h.atm_id)}
                    style={{
                      cursor: 'pointer',
                      backgroundColor: selectedAtmId === h.atm_id ? 'rgba(255,255,255,0.1)' : 'transparent',
                      padding: '10px',
                      borderRadius: '8px',
                      marginBottom: '8px',
                      border: selectedAtmId === h.atm_id ? '1px solid rgba(255,255,255,0.2)' : '1px solid transparent'
                    }}
                  >
                    <span className={`country-dot ${h.risk_level === 'HIGH' ? 'red' : 'amber'}`} />
                    <div>
                      <strong>{h.atm_id}</strong>
                      <small style={{ display: 'block' }}>{h.lat}, {h.lng}</small>
                      <small style={{ display: 'block', color: '#71717a' }}>{h.crime_category}</small>
                    </div>
                    <Badge tone={h.risk_level === 'HIGH' ? 'red' : 'amber'}>{h.risk_level || 'N/A'}</Badge>
                  </div>
                ))
              ) : (
                <div style={{ color: '#a1a1aa', marginTop: '1rem' }}>No matching heatmap data.</div>
              )}
            </div>
          </>
        )}
      </section>
    </>
  )
}
