# ReSolve Intake + Shared Recovery Loop

## What was added

### 1. `backend/incident_intake.py`
Normalizes the manual Freshservice-like form.

Required:
- `requester_id` or `requester_email` / `email`
- `subject`
- `description`
- `priority`
- `status`

Optional fields are omitted when empty:
- source
- category / sub_category / item_category
- planned_start_date / planned_end_date / planned_effort
- tags
- urgency / impact
- group_id
- agent_id or responder_id
- department_id
- cc_emails
- workspace_id
- type
- custom_fields

### 2. `FreshserviceTicketService.createTicketFromForm(form)`
Creates a Freshservice ticket from the normalized form.

Before sending optional fields, it attempts to inspect the installed
`create_ticket` MCP schema and removes fields unsupported by that tool.
This avoids silently inventing MCP arguments.

### 3. `FreshserviceRecoveryRunner`
`firstAction` is now optional.

The runner also has:

```python
startRecoveryFromIncident(
    ticketId,
    incident,
    firstAction=None,
    conversationCount=0,
)
```

Both manual and ticket-number flows converge here.

### 4. `backend/recovery_orchestrator.py`
This is the application-facing API.

```python
orchestrator = RecoveryOrchestrator()

# Existing Freshservice ticket
result = orchestrator.startFromTicket(ticketId)

# Manual form
result = orchestrator.startFromManualForm(form)

# Shared live state
state = orchestrator.getRunState(runId)

# Approval gate
approved = orchestrator.approve(runId)
rejected = orchestrator.reject(runId)
```

The returned result includes:

```python
result["loop"] = {
    "runId": "...",
    "status": "...",
    "phase": "RECOVERY | APPROVAL_GATE | VERIFIED_RECOVERY | ESCALATION",
    "awaitingApproval": True | False,
    "pendingStrategy": {...} | None,
    "attempts": [...],
    "recoveryAttempts": 0,
    "maxAttempts": 5,
    "environmentState": {...},
    "verification": {...},
    "reason": "..."
}
```

This object is intended to power the common recovery-loop tab/page in
both intake modes.

## Recommended UI calls

### Existing ticket

```python
result = orchestrator.startFromTicket(ticket_number)

if result["status"] == "AWAITING_APPROVAL":
    # Show proposed action and Yes / No
    ...
```

### Manual ticket

Use the same names as the Freshservice form where possible:

```python
form = {
    "requester_id": requester_id,
    "subject": subject,
    "description": description,
    "source": 3,
    "status": 2,
    "priority": 1,
    "category": category,
    "planned_start_date": planned_start_date,
    "planned_end_date": planned_end_date,
    "planned_effort": planned_effort,
    "tags": tags,
    "urgency": urgency,
    "impact": impact,
    "group_id": group_id,
    "agent_id": agent_id,
    "department_id": department_id,
}
result = orchestrator.startFromManualForm(form)
```

The manual flow creates the Freshservice ticket first, obtains its ID,
then uses the existing Freshservice bridge and incident mapper. There
is no separate manual recovery algorithm.

## Approval behavior

- Low risk: auto-approved.
- Medium/high/unknown risk: `AWAITING_APPROVAL`.
- No execution happens before `approve(runId)`.
- `reject(runId)` records the rejection and continues looking for another
  evidence-backed strategy.
- Verified success resolves the Freshservice ticket.
- Exhaustion or no reliable strategy escalates the existing ticket.

## Notes on Freshservice optional fields

Freshservice's current API supports ticket properties including category,
planned dates/effort, tags, group/department/agent assignment, priority,
status and other standard ticket properties.

Attachments require multipart/form-data and CI association may use a
separate Freshservice association operation. The currently configured
MCP tool schema is checked before optional fields are sent, so fields
not exposed by that installed MCP server should be surfaced by the
application rather than silently pretending they were saved.
