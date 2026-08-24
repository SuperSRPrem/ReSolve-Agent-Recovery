from datetime import datetime, timezone
from uuid import uuid4


class RecoverySession:
    """
    Stores the state of one recovery run.

    The session survives approval pauses and preserves the
    complete recovery history required for audit records.
    """

    def __init__(
        self,
        incident,
        errorSignature,
        firstAction
    ):
        self.runId = "RUN-" + uuid4().hex[:12].upper()

        self.createdAt = datetime.now(
            timezone.utc
        ).isoformat()

        self.incident = incident
        self.errorSignature = errorSignature

        self.attemptHistory = [
            {
                "action": firstAction,
                "result": "failed",
                "errorSignature": errorSignature,
                "note": (
                    "Initial host agent action failed before "
                    "recovery memory was consulted."
                )
            }
        ]

        self.recoveryAttempts = 0
        self.pendingStrategy = None
        self.status = "ACTIVE"

    def addAttempt(
        self,
        action,
        result,
        note="",
        verification=None,
        execution=None,
        riskTier=None,
        approval=None,
        sourceIncident=None,
        score=None
    ):
        attempt = {
            "action": action,
            "result": result,
            "errorSignature": self.errorSignature,
            "note": note
        }

        if verification is not None:
            attempt["verification"] = verification

        if execution is not None:
            attempt["execution"] = execution

        if riskTier is not None:
            attempt["riskTier"] = riskTier

        if approval is not None:
            attempt["approval"] = approval

        if sourceIncident is not None:
            attempt["sourceIncident"] = (
                sourceIncident
            )

        if score is not None:
            attempt["score"] = score

        self.attemptHistory.append(
            attempt
        )

        return attempt

    def setPendingStrategy(self, strategy):
        self.pendingStrategy = strategy
        self.status = "AWAITING_APPROVAL"

    def clearPendingStrategy(self):
        self.pendingStrategy = None

        if self.status == "AWAITING_APPROVAL":
            self.status = "ACTIVE"

    def getState(self):
        return {
            "runId": self.runId,
            "createdAt": self.createdAt,
            "status": self.status,
            "incident": self.incident,
            "errorSignature": self.errorSignature,
            "attemptHistory": self.attemptHistory,
            "recoveryAttempts": self.recoveryAttempts,
            "pendingStrategy": self.pendingStrategy
        }