import re


# ==================================================
# FRESHSERVICE FIELD MAPPINGS
# ==================================================

PRIORITY_TO_SEVERITY = {
    1: "low",
    2: "medium",
    3: "high",
    4: "urgent"
}


RESOLVED_STATUSES = {
    4,  # Resolved
    5   # Closed
}


ERROR_CODE_PATTERN = re.compile(
    r"\b("
    r"HTTP[-_]?\d{3}"
    r"|[A-Z]{2,}_[A-Z0-9_]{2,}"
    r")\b"
)


# ==================================================
# TEXT HELPERS
# ==================================================

def extractErrorCodes(text):
    """
    Extracts error-code-like values from free text.

    Examples:

        HTTP-503
        DB_CONNECTION_TIMEOUT
        CONNECTION_REFUSED
    """

    if not text:
        return []

    matches = ERROR_CODE_PATTERN.findall(
        str(text)
    )

    return sorted(
        set(matches)
    )


def firstLineOf(text, maxLen=200):
    """
    Returns the first meaningful line of text.
    """

    if not text:
        return ""

    stripped = str(text).strip()

    if not stripped:
        return ""

    return stripped.splitlines()[0][:maxLen]


def normalizeDescription(ticket):
    """
    Freshservice may provide both:

        description
        description_text

    Prefer description_text because it removes HTML.
    """

    return (
        ticket.get("description_text")
        or ticket.get("description")
        or ""
    ).strip()


# ==================================================
# CONVERSATION MAPPING
# ==================================================

def mapConversationToAction(conversation):
    """
    Converts a Freshservice conversation into the
    ReSolve actionsTried format.

    We do not assume every conversation represents
    a successful recovery action.
    """

    body = (
        conversation.get("body_text")
        or conversation.get("body")
        or ""
    )

    return {
        "action": firstLineOf(body),
        "result": "unknown"
    }


def mapConversationsToActions(conversations):
    """
    Converts all available Freshservice conversations
    into ReSolve action history.
    """

    actions = []

    for conversation in conversations or []:

        action = mapConversationToAction(
            conversation
        )

        if action["action"]:

            actions.append(action)

    return actions


# ==================================================
# ROOT CAUSE / RESOLUTION
# ==================================================

def getResolutionAction(
    ticket,
    conversations
):
    """
    Determines the best available resolution action.

    Priority:

    1. Freshservice resolution_notes
    2. Last conversation for resolved tickets
    3. Empty value

    We do not invent a resolution action.
    """

    resolutionNotes = (
        ticket.get("resolution_notes")
        or ""
    )

    if resolutionNotes:

        return firstLineOf(
            resolutionNotes
        )

    status = ticket.get("status")

    if (
        status in RESOLVED_STATUSES
        and conversations
    ):

        lastConversation = conversations[-1]

        body = (
            lastConversation.get("body_text")
            or lastConversation.get("body")
            or ""
        )

        return firstLineOf(body)

    return ""


# ==================================================
# MAIN TICKET → INCIDENT MAPPER
# ==================================================

def mapTicketToIncident(
    ticket,
    conversations=None
):
    """
    Maps a real Freshservice ticket into the
    ReSolve incident structure.

    Only fields actually available from Freshservice
    are mapped directly.

    Missing information is intentionally left empty
    instead of being guessed.

    Later, the AI layer can enrich fields such as:

        - rootCause
        - structured symptoms
        - error codes
        - recentChange
        - recovery suggestions
        - resolution steps
    """

    conversations = conversations or []

    # ----------------------------------------------
    # Ticket basics
    # ----------------------------------------------

    ticketId = ticket.get("id")

    descriptionText = normalizeDescription(
        ticket
    )

    priority = ticket.get("priority")

    status = ticket.get("status")

    isResolved = (
        status in RESOLVED_STATUSES
    )

    # ----------------------------------------------
    # Conversation → attempted actions
    # ----------------------------------------------

    actionsTried = (
        mapConversationsToActions(
            conversations
        )
    )

    # ----------------------------------------------
    # Resolution
    # ----------------------------------------------

    resolutionAction = (
        getResolutionAction(
            ticket,
            conversations
        )
    )

    # ----------------------------------------------
    # Error codes
    # ----------------------------------------------

    combinedText = " ".join([
        str(ticket.get("subject") or ""),
        descriptionText
    ])

    errorCodes = extractErrorCodes(
        combinedText
    )

    # ----------------------------------------------
    # Build ReSolve incident
    # ----------------------------------------------

    incident = {

        "incidentId": (
            f"INC-{ticketId}"
            if ticketId is not None
            else "INC-UNKNOWN"
        ),

        "title": (
            ticket.get("subject")
            or ""
        ),

        # Freshservice category is optional.
        # Fall back to ticket type.
        "service": (
            ticket.get("category")
            or ticket.get("type")
            or "Unknown"
        ),

        # Freshservice does not provide a direct
        # environment field in this response.
        "environment": "unknown",

        "severity": (
            PRIORITY_TO_SEVERITY.get(
                priority,
                "unknown"
            )
        ),

        "date": (
            ticket.get("created_at")
            or ""
        ),

        # ------------------------------------------
        # Symptoms
        # ------------------------------------------

        "symptoms": (
            [descriptionText]
            if descriptionText
            else []
        ),

        "errorCodes": errorCodes,

        # ------------------------------------------
        # Metrics
        #
        # We currently use only real Freshservice
        # fields that may help later.
        # ------------------------------------------

        "metrics": {
            "impact": ticket.get("impact"),
            "urgency": ticket.get("urgency"),
            "xlaScore": ticket.get("xla_score"),
            "reliabilityScore": (
                ticket.get(
                    "reliability_score"
                )
            ),
            "qualityScore": (
                ticket.get(
                    "quality_score"
                )
            ),
            "effortScore": (
                ticket.get(
                    "effort_score"
                )
            ),
        },

        # ------------------------------------------
        # Recent change
        #
        # Not directly available in the ticket.
        # ------------------------------------------

        "recentChange": {
            "type": "unknown",
            "description": "",
            "minutesBeforeIncident": None
        },

        # ------------------------------------------
        # Recovery history
        # ------------------------------------------

        "actionsTried": actionsTried,

        # ------------------------------------------
        # Root cause
        #
        # Do not guess.
        # AI enrichment can fill this later.
        # ------------------------------------------

        "rootCause": "",

        # ------------------------------------------
        # Resolution
        # ------------------------------------------

        "resolution": {

            "action": resolutionAction,

            "steps": [],

            "result": (
                "success"
                if isResolved
                else "unknown"
            ),

            "resolutionTimeMinutes": None
        },

        # ------------------------------------------
        # Historical learning
        # ------------------------------------------

        "resolutionStats": {
            "successCount": 0,
            "failureCount": 0
        },

        "resolutionStatus": (
            "resolved"
            if isResolved
            else "active"
        ),

        # ------------------------------------------
        # Freshservice metadata
        #
        # Keep useful external identifiers so we can
        # later update the original ticket.
        # ------------------------------------------

        "freshservice": {

            "ticketId": ticketId,

            "status": status,

            "priority": priority,

            "source": ticket.get(
                "source"
            ),

            "type": ticket.get(
                "type"
            ),

            "requesterId": ticket.get(
                "requester_id"
            ),

            "workspaceId": ticket.get(
                "workspace_id"
            ),

            "dueBy": ticket.get(
                "due_by"
            ),

            "frDueBy": ticket.get(
                "fr_due_by"
            ),

            "updatedAt": ticket.get(
                "updated_at"
            )
        }
    }

    return incident