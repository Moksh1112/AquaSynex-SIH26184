# SIH26184 — Demo Scenario

## Case
`C10231`

Fraud amount:
`₹4,80,000`

## Money trail
`V001 → M001 → M002 → M003`

Example relationships:
- M001 and M002 share a device
- M002 and M003 share an IP
- M003 has elevated risk
- similar historical cases cash out in the same area

## Example output
| Rank | ATM | Score | Time | Risk |
|---|---|---:|---|---|
| 1 | ATM-184 | 82% | 10–11 PM | HIGH |
| 2 | ATM-092 | 74% | 10–11 PM | HIGH |
| 3 | ATM-211 | 69% | 11–12 PM | MEDIUM |
| 4 | ATM-301 | 62% | 11–12 PM | MEDIUM |
| 5 | ATM-119 | 57% | 12–1 AM | MEDIUM |

These numbers are demonstration examples unless produced by the actual model.

## Demo
Login → open C10231 → show money trail → Predict Cash-Out → show Top-5 → highlight ATM-184 → show map → show time → show Why → show HIGH risk → Generate Alert → show audit.

## Jury line
> We are not simply detecting suspicious transactions. We are predicting where the stolen money is likely to exit next, when it may happen, why the system believes that, and what action should follow.
