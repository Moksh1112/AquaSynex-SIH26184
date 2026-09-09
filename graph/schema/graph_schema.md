# Graph Schema
Nodes:
- Complaint
- Account
- Transaction
- Device
- IP
- ATM

Relationships:
- Account -[:TRANSFERRED_TO]-> Account
- Account -[:USED]-> Device
- Account -[:USED]-> IP
- Account -[:PERFORMED]-> Transaction
- Account -[:WITHDREW_AT]-> ATM
