# SIH26184 — Frontend Master Prompt

You are the lead frontend/product designer for SIH26184.

Build a serious **cybercrime investigation command center**, not a generic AI/fintech dashboard.

## Core UX
Complaint → Money Trail → Predict → Top-5 → Map → Time → Why → Risk → Alert.

## Screens
1. Command Center: active cases, high-risk cases, alerts, GIS map.
2. Case Investigation: complaint, amount, transaction timeline, money-flow graph.
3. Predictive Intelligence: primary prediction, Top-5, risk, time.
4. GIS Map: ATM markers, candidate locations, predicted location, H3 risk areas.
5. Explanation: investigator-friendly reasons/SHAP.
6. Alert Center: case, location, probability, time, risk, status.
7. Audit Logs: user, role, action, case, timestamp.

## Visual direction
Professional, serious, intelligence/operations-oriented, map-centric, clean, high information density, restrained color. No childish emojis, excessive gradients, marketing landing-page sections, or unnecessary decoration.

## API
POST `/predict`
Request:
`{"case_id":"C10231"}`

Response contains:
case_id, risk, time_window, predictions[{rank,atm_id,probability,latitude,longitude,risk}], explanation[].

Build an API service layer so mock JSON can later be replaced by the real backend without component redesign.

## Tech
React, TypeScript if already configured, existing CSS/Tailwind if present, Leaflet or Mapbox.

Do not introduce a new framework or unnecessary dependencies.

## Agent rules
Inspect the repository first. Reuse existing stack. Plan before changing. Implement incrementally. Test. Report changed files and run commands.

Priority:
1 case investigation
2 prediction
3 map
4 Top-5
5 explanation
6 alert
7 dashboard overview
8 audit
9 polish
