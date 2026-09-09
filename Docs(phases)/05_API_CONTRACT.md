# SIH26184 — API Contract

## POST /predict

### Request
```json
{"case_id":"C10231"}
```

### Response
```json
{
  "case_id":"C10231",
  "risk":"HIGH",
  "time_window":"22:00-23:00",
  "predictions":[
    {
      "rank":1,
      "atm_id":"ATM-184",
      "probability":0.82,
      "latitude":19.076,
      "longitude":72.877,
      "risk":"HIGH"
    }
  ],
  "explanation":[
    "High recent transaction velocity",
    "Similar historical cash-out behaviour",
    "High-risk connected account",
    "Short transfer-to-withdrawal interval"
  ]
}
```

Optional endpoints:
- GET `/cases`
- GET `/cases/{case_id}`
- GET `/predictions/{case_id}`
- GET `/alerts`
- POST `/alerts`
- GET `/graph/{case_id}`
- GET `/audit`

Do not break `/predict` without updating frontend and this document.
