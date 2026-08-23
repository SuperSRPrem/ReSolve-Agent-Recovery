class RecoverySession:
    """
    Stores the state of one recovery run.

    This allows the agent to pause for human approval and later
    resume from exactly where it stopped.
    """

    def __init__(self, incident, errorSignature, firstAction):
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
        verification=None
    ):
        attempt = {
            "action": action,
            "result": result,
            "errorSignature": self.errorSignature,
            "note": note
        }

        if verification is not None:
            attempt["verification"] = verification

        self.attemptHistory.append(attempt)

    def setPendingStrategy(self, strategy):
        self.pendingStrategy = strategy
        self.status = "AWAITING_APPROVAL"

    def clearPendingStrategy(self):
        self.pendingStrategy = None

        if self.status == "AWAITING_APPROVAL":
            self.status = "ACTIVE"

    def getState(self):
        return {
            "status": self.status,
            "incident": self.incident,
            "errorSignature": self.errorSignature,
            "attemptHistory": self.attemptHistory,
            "recoveryAttempts": self.recoveryAttempts,
            "pendingStrategy": self.pendingStrategy
        }