'use client';

import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default Leaflet icons in Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Component to handle auto-fitting bounds based on candidates
function FitBounds({ candidates, selectedAtmId }: { candidates: any[]; selectedAtmId: string | null }) {
  const map = useMap();

  useEffect(() => {
    if (selectedAtmId) {
      const selected = candidates.find(c => c.atm_id === selectedAtmId);
      if (selected && selected.latitude && selected.longitude) {
        map.flyTo([selected.latitude, selected.longitude], 16, { duration: 1 });
        return;
      }
    }

    if (candidates && candidates.length > 0) {
      const validCands = candidates.filter(c => typeof c.latitude === 'number' && typeof c.longitude === 'number');
      if (validCands.length > 0) {
        const bounds = L.latLngBounds(validCands.map(c => [c.latitude, c.longitude]));
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [50, 50], maxZoom: 16 });
        }
      }
    }
  }, [map, candidates, selectedAtmId]);

  return null;
}

export default function MapClient({
  predictionData,
  locationsData,
  selectedAtmId
}: {
  predictionData: any;
  locationsData: any[];
  selectedAtmId: string | null;
}) {
  const candidates = predictionData?.predictions || [];

  // Create a custom DivIcon generator for ranked predictions
  const createRankIcon = (rank: number, risk: string) => {
    const isHigh = risk === 'HIGH';
    return L.divIcon({
      className: 'custom-leaflet-icon',
      html: `<div style="
        background-color: ${isHigh ? '#ef4444' : '#f59e0b'};
        color: white;
        border: 2px solid white;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        font-size: 14px;
      ">${rank}</div>`,
      iconSize: [30, 30],
      iconAnchor: [15, 15],
      popupAnchor: [0, -15]
    });
  };

  const defaultCenter: [number, number] = [19.076, 72.877]; // Mumbai

  return (
    <MapContainer
      center={defaultCenter}
      zoom={12}
      style={{ height: '100%', width: '100%', zIndex: 1 }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {/* Plot all background ATMs if no predictions are available (fallback view) */}
      {!candidates.length && locationsData && locationsData.map((loc) => {
         if (typeof loc.latitude !== 'number' || typeof loc.longitude !== 'number') return null;
         return (
          <Marker
            key={loc.atm_id}
            position={[loc.latitude, loc.longitude]}
            opacity={0.5}
          >
            <Popup>
              <strong>{loc.atm_id}</strong><br/>
              Background Location
            </Popup>
          </Marker>
        );
      })}

      {/* Plot Candidates */}
      {candidates.map((cand: any) => {
        if (typeof cand.latitude !== 'number' || typeof cand.longitude !== 'number') {
           console.error(`Malformed coordinates for candidate ${cand.atm_id}`);
           return null;
        }

        const probPct = typeof cand.probability === 'number' ? (cand.probability * 100).toFixed(1) : 'N/A';

        return (
          <Marker
            key={cand.atm_id}
            position={[cand.latitude, cand.longitude]}
            icon={createRankIcon(cand.rank, cand.risk)}
          >
            <Popup>
              <div>
                <strong style={{ fontSize: '1.1em' }}>#{cand.rank} {cand.atm_id}</strong>
                <div style={{ margin: '4px 0' }}>Probability: <strong>{probPct}%</strong></div>
                <div>Risk: <strong style={{ color: cand.risk === 'HIGH' ? '#ef4444' : '#f59e0b' }}>{cand.risk}</strong></div>
              </div>
            </Popup>
          </Marker>
        );
      })}

      <FitBounds candidates={candidates} selectedAtmId={selectedAtmId} />
    </MapContainer>
  );
}
