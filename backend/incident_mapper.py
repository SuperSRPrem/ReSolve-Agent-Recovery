import re


PRIORITY_TO_SEVERITY = {
    1: "low",
    2: "medium",
    3: "high",
    4: "urgent"
}

RESOLVED_STATUSES = {4, 5}  # Freshservice: 4 = Resolved, 5 = Closed

ERROR_CODE_PATTERN = re.compile(r"\b(HTTP[-_]?\d{3}|[A-Z]{2,}_[A-Z_]{2,})\b")


def extractErrorCodes(text):
    """
    Best-effort only. Freshservice tickets have no structured 'error codes'
    field like the synthetic dataset does - this pattern-matches things
    that look like HTTP-503 or DB_CONNECTION_TIMEOUT out of free text.
    Expect to miss things. Proper extraction is a job for the LLM drafting
    agent planned for a later phase, not this mapper.
    """
    if not text:
        return []

    matches = ERROR_CODE_PATTERN.findall(text)
    return sorted(set(matches))


def firstLineOf(text, maxLen=200):
    if not text:
        return ""

    stripped = text.strip()
    if not stripped:
        return ""

    return stripped.splitlines()[0][:maxLen]


def mapConversationToAction(conversation):
    body = conversation.get("body_text") or conversation.get("body") or ""

    return {
        "action": firstLineOf(body),
        "result": "unknown"
    }


def mapTicketToIncident(ticket, conversations=None):
    """
    Maps one raw Freshservice ticket (as returned by the MCP server's
    get_ticket_by_id / get_tickets tools) into the incident dict shape
    this repo already works with - see data/incidents.json for the shape.

    Several fields there - errorCodes, metrics, recentChange, rootCause,
    resolution.steps - don't exist natively on a Freshservice ticket; they
    were invented for the synthetic dataset. Where there's no real source,
    this leaves them empty/default instead of guessing at data. Filling
    rootCause and resolution.steps in properly from the ticket's free text
    is the LLM drafting agent's job (planned for a later phase), not this
    mapper's.
    """
    conversations = conversations or []

    descriptionText = ticket.get("description_text") or ticket.get("description") or ""
    status = ticket.get("status")
    isResolved = status in RESOLVED_STATUSES

    actionsTried = [mapConversationToAction(c) for c in conversations]

    resolutionAction = ""
    if isResolved and conversations:
        lastNote = conversations[-1]
        resolutionAction = firstLineOf(
            lastNote.get("body_text") or lastNote.get("body") or ""
        )

    incident = {
        "incidentId": "INC-" + str(ticket.get("id")),
        "title": ticket.get("subject", ""),
        "service": ticket.get("category") or "Unknown",
        "environment": "production",
        "severity": PRIORITY_TO_SEVERITY.get(ticket.get("priority"), "unknown"),
        "date": ticket.get("created_at", ""),
        "symptoms": [descriptionText[:500]] if descriptionText else [],
        "errorCodes": extractErrorCodes(descriptionText),
        "metrics": {},
        "recentChange": {
            "type": "unknown",
            "description": "None",
            "minutesBeforeIncident": None
        },
        "actionsTried": actionsTried,
        "rootCause": "",
        "resolution": {
            "action": resolutionAction,
            "steps": [],
            "result": "success" if isResolved else "unknown",
            "resolutionTimeMinutes": None
        },
        "resolutionStats": {
            "successCount": 0,
            "failureCount": 0
        },
        "resolutionStatus": "active"
    }

    return incident