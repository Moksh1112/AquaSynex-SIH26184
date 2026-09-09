# SIH26184 — Vibe Coding Rules

1. Never ask an agent to build the entire system in one shot.
2. Inspect the repository before modifying it.
3. Preserve the API contract.
4. Reuse existing dependencies.
5. Make one small change at a time.
6. Run a test after each milestone.
7. Ask the agent to explain changed code and data flow.
8. Use mock JSON so frontend/backend can work in parallel.
9. Commit frequently.
10. Reject unnecessary microservices and advanced infrastructure.
11. Do not let AI silently replace working modules.
12. Human team members must understand what each module receives, returns, and why it exists.

Preferred prompt pattern:
"Inspect the current repository and implement only [specific module]. Do not change unrelated modules or the API contract. First give a short plan, then implement, test, and report files changed, commands to run, assumptions, and integration points."
