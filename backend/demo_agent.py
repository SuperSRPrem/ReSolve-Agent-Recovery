from backend.recovery_memory import RecoveryMemory
from backend.feedback import FeedbackManager


class DemoAgent:
    def __init__(self):
        self.memory = RecoveryMemory()
        self.feedback = FeedbackManager()

    def runIncident(self, incident, firstAction, retryResult="success"):
        self.feedback.addAttempt(
            incident,
            firstAction,
            "failed"
        )

        recovery = self.memory.getRecovery(incident)

        if recovery["status"] == "NO_MATCH":
            return {
                "status": "NO_MATCH",
                "message": recovery["message"],
                "attempts": incident["actionsTried"]
            }

        choice = recovery["bestChoice"]
        action = choice["action"]

        self.feedback.addAttempt(
            incident,
            action,
            retryResult
        )

        self.feedback.recordResult(
            choice["incidentId"],
            retryResult
        )

        return {
            "status": "RECOVERED" if retryResult == "success" else "FAILED",
            "firstAction": firstAction,
            "recoveryAction": action,
            "sourceIncident": choice["incidentId"],
            "score": choice["score"],
            "steps": choice["steps"],
            "attempts": incident["actionsTried"]
        }

