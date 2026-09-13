'use client'

import { useMemo, useState, useEffect, useCallback } from 'react'
import { fetchApi } from '../lib/api'

import { Login } from '../components/Login'
import { Overview } from '../components/Overview'
import { Cases } from '../components/Cases'
import { CaseDetail } from '../components/CaseDetail'
import { GraphPanel } from '../components/GraphPanel'
import { PredictionPanel } from '../components/PredictionPanel'
import { MapView } from '../components/MapView'
import { AlertPanel } from '../components/AlertPanel'
import { PageHeader } from '../components/ui/PageHeader'

type View = 'overview' | 'cases' | 'case' | 'trail' | 'prediction' | 'map' | 'alerts' | 'audit'

const nav = [
  ['overview', 'Command Center', '⌂'],
  ['cases', 'Case Files', '▣'],
  ['trail', 'Money Trail', '↗'],
  ['prediction', 'Predictions', '⌁'],
  ['map', 'Geo Intelligence', '⊙'],
  ['alerts', 'Alerts', '!'],
  ['audit', 'Audit Log', '≡'],
] as const

function Audit() { 
  return (
    <>
      <PageHeader eyebrow="System / Traceability" title="Audit Log" subtitle="Currently, there is no GET /audit backend endpoint to fetch this data." />
      <div style={{ padding: '2rem', color: '#a1a1aa' }}>Audit logs will appear here once the backend API is connected.</div>
    </>
  )
}

export default function Page() {
  const [token, setToken] = useState<string>('')
  const [view, setView] = useState<View>('overview')
  const [caseId, setCaseId] = useState<string>('')
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false)
  
  // Data State
  const [backendCases, setBackendCases] = useState<any[]>([])
  const [loadingCases, setLoadingCases] = useState(false)
  
  const [caseDetails, setCaseDetails] = useState<any>(null)
  const [loadingCaseDetails, setLoadingCaseDetails] = useState(false)

  const [graphData, setGraphData] = useState<any>(null)
  const [loadingGraph, setLoadingGraph] = useState(false)
  const [computedFlow, setComputedFlow] = useState<any[]>([])
  const [computedSteps, setComputedSteps] = useState<any[]>([])
  
  const [predictionData, setPredictionData] = useState<any>(null)
  const [loadingPrediction, setLoadingPrediction] = useState(false)
  
  const [locationsData, setLocationsData] = useState<any[]>([])
  const [loadingLocations, setLoadingLocations] = useState(false)

  const [alertsData, setAlertsData] = useState<any[]>([])
  const [loadingAlerts, setLoadingAlerts] = useState(false)

  // Fetch initial data (Cases, Locations, Alerts) once authenticated
  useEffect(() => {
    if (!token) return

    setLoadingCases(true)
    fetchApi('/cases', token)
      .then(data => setBackendCases(data || []))
      .catch(() => setBackendCases([]))
      .finally(() => setLoadingCases(false))

    setLoadingLocations(true)
    fetchApi('/locations', token)
      .then(data => setLocationsData(data || []))
      .catch(() => setLocationsData([]))
      .finally(() => setLoadingLocations(false))

    fetchAlerts()
  }, [token])

  const fetchAlerts = useCallback(() => {
    if (!token) return
    setLoadingAlerts(true)
    fetchApi('/alerts', token)
      .then(data => setAlertsData(data || []))
      .catch(() => setAlertsData([]))
      .finally(() => setLoadingAlerts(false))
  }, [token])
  
  // Fetch specific case data when caseId changes
  useEffect(() => {
    if (!token || !caseId) return

    // Fetch Case Detail
    setLoadingCaseDetails(true)
    fetchApi(`/cases/${caseId}`, token)
      .then(data => setCaseDetails(data))
      .catch(() => setCaseDetails(null))
      .finally(() => setLoadingCaseDetails(false))

    // Fetch Graph
    setLoadingGraph(true)
        fetchApi(`/graph/${caseId}`, token)
      .then(data => {
          setGraphData(data)
          import('../lib/graph-transform').then(({ transformGraph }) => {
            const { flow, steps } = transformGraph(data)
            setComputedFlow(flow)
            setComputedSteps(steps)
          })
      })
      .catch(() => { setGraphData(null); setComputedFlow([]); setComputedSteps([]) })
      .finally(() => setLoadingGraph(false))

    // Do NOT automatically fetch/create Prediction here.
    // Prediction is now triggered manually via runPrediction.
    setPredictionData(null);
  }, [token, caseId])

  const runPrediction = useCallback(async () => {
    if (!token || !caseId) return;
    setLoadingPrediction(true);
    try {
      const data = await fetchApi(`/predict`, token, {
        method: 'POST',
        body: JSON.stringify({ case_id: caseId })
      });
      setPredictionData(data);
      // Refresh alerts after prediction to pick up the newly generated alert
      fetchAlerts();
    } catch (e: any) {
      console.error(e);
      alert(`Failed to run prediction: ${e.message || 'Unknown error'}`);
    } finally {
      setLoadingPrediction(false);
    }
  }, [token, caseId, fetchAlerts]);

  const activeLabel = useMemo(() => nav.find(([key]) => key === view)?.[1] ?? 'Command Center', [view])

  const activeAlertsCount = useMemo(() => {
    return alertsData.filter(a => ['OPEN', 'ACKNOWLEDGED'].includes(a.status)).length;
  }, [alertsData]);
  
  if (!token) return <Login setToken={setToken} />
  
  return (
    <main className="app-shell">
      <div 
        className={`sidebar-overlay ${isSidebarOpen ? 'open' : ''}`}
        onClick={() => setIsSidebarOpen(false)}
        aria-hidden="true"
      />
      <aside className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">◒</div>
          <div><strong>ARGUS</strong><span>FINANCIAL INTELLIGENCE</span></div>
        </div>
        <div className="workspace">
          <span className="eyebrow">Workspace</span>
          <button>
            <span className="avatar">MC</span>
            <span><strong>Major Crimes Unit</strong><small>Investigator view</small></span>
            <span>⌄</span>
          </button>
        </div>
        <nav>
          {nav.map(([key, label, icon]) => (
            <button 
              key={key} 
              className={view === key || (key === 'case' && view === 'case') ? 'active' : ''} 
              onClick={() => {
                setView(key as View)
                setIsSidebarOpen(false)
              }}
            >
              <i>{icon}</i>{label}
              {key === 'alerts' && activeAlertsCount > 0 && <b>{activeAlertsCount}</b>}
            </button>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="system-status"><span className="status-pulse" />All systems operational</div>
          <button className="user-row">
            <span className="avatar">MC</span>
            <span><strong>Maya Chen</strong><small>Senior Investigator</small></span>
            <span>•••</span>
          </button>
        </div>
      </aside>
      <div className="content">
        <header className="topbar">
          <div className="crumb">
            <button className="menu-toggle" onClick={() => setIsSidebarOpen(true)} aria-label="Open navigation">☰</button>
            <span>ARGUS</span><b>/</b>{activeLabel}
          </div>
          <div className="top-actions">
            <span className="utc"><i className="status-pulse" />LIVE · 09:42 UTC</span>
            <button aria-label="Search" disabled style={{ opacity: 0.5, cursor: 'not-allowed' }}>⌕</button>
            <button aria-label="Notifications" onClick={() => setView('alerts')}>
              ◌
              {activeAlertsCount > 0 && <b className="notification-count">{activeAlertsCount}</b>}
            </button>
            <button aria-label="Settings" disabled style={{ opacity: 0.5, cursor: 'not-allowed' }}>⚙</button>
          </div>
        </header>
        <div className="page-content">
          {view === 'overview' && (
            <Overview setView={setView} setCaseId={setCaseId} cases={backendCases} alerts={alertsData} loading={loadingCases || loadingAlerts} />
          )}
          {view === 'cases' && (
            <Cases setView={setView} setCaseId={setCaseId} cases={backendCases} loading={loadingCases} />
          )}
          {view === 'case' && (
            <CaseDetail setView={setView} caseId={caseId} caseDetails={caseDetails} loadingCase={loadingCaseDetails} flow={computedFlow} loadingGraph={loadingGraph} />
          )}
          {view === 'trail' && (
            <GraphPanel setView={setView} caseId={caseId} flow={computedFlow} steps={computedSteps} loadingGraph={loadingGraph} />
          )}
          {view === 'prediction' && (
            <PredictionPanel setView={setView} caseId={caseId} predictionData={predictionData} loadingPrediction={loadingPrediction} runPrediction={runPrediction} />
          )}
          {view === 'map' && (
            <MapView caseId={caseId} predictionData={predictionData} loadingPrediction={loadingPrediction} locationsData={locationsData} />
          )}
          {view === 'alerts' && (
            <AlertPanel token={token} alerts={alertsData} loading={loadingAlerts} refreshAlerts={fetchAlerts} />
          )}
          {view === 'audit' && <Audit />}
        </div>
      </div>
    </main>
  )
}
