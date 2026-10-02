# Stage 6 — Task Observation Engine

This package is intentionally separate from the live MOCKAPP filesystem and browser agents.
It records task observations without changing agent execution.

## Design

```text
agent/event source
      |
      v
TaskObservationSession
  |       |       |
  v       v       v
Discrete Continuous Event/Trace
collector collector collector
      \      |      /
       v     v     v
        ObservationSnapshot
               |
          BucketManager
               |
          SessionStore
               |
           ReplayAPI
               |
     MathematicalApprovalAdapter
               |
      mathematical_approval
```

The adapter is the only module that imports `mathematical_approval`.
The collector can therefore be used independently by filesystem and browser integrations.

## Missing values

Missing/invalid continuous values become `None`. Missing discrete values are allowed.
Collection continues instead of terminating the agent task.

## Persistence

Completed sessions are stored as one JSON file per session. Writes use a temporary file
and `os.replace()` so a partially-written session is not presented as complete.

## Simulation

From the package parent:

```powershell
python -c "from task_observation.simulation import generate_runs; generate_runs('observation_data', count=10)"
```

## Tests

```powershell
pytest -q tests
```
