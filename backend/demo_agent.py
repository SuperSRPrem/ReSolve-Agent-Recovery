from backend.recovery_memory import RecoveryMemory
from backend.feedback import FeedbackManager
from backend.outcome_tracker import computeErrorSignature


class DemoAgent:
    def __init__(self):
        self.memory = RecoveryMemory()
        self.feedback = FeedbackManager()

    def runIncident(self, incident, firstAction, retryResult="success"):
        errorSignature = computeErrorSignature(incident)

        attemptHistory = [{
            "action": firstAction,
            "result": "failed",
            "errorSignature": errorSignature,
            "note": "Initial host agent action failed before recovery memory was consulted."
        }]

        self.feedback.addAttempt(incident, firstAction, "failed", errorSignature)

        recovery = self.memory.getRecovery(incident, attemptHistory)

        if recovery["status"] == "NO_MATCH":
            return {
                "status": "NO_MATCH",
                "message": recovery["message"],
                "errorSignature": errorSignature,
                "attempts": attemptHistory
            }

        choice = recovery["bestChoice"]
        action = choice["action"]

        attemptHistory.append({
            "action": action,
            "result": retryResult,
            "errorSignature": errorSignature,
            "note": (
                "Recovery succeeded."
                if retryResult == "success"
                else "Recovery action did not resolve the error signature."
            )
        })

        self.feedback.addAttempt(incident, action, retryResult, errorSignature)
        self.feedback.recordResult(choice["incidentId"], errorSignature, retryResult)

        return {
            "status": "RECOVERED" if retryResult == "success" else "FAILED",
            "firstAction": firstAction,
            "recoveryAction": action,
            "sourceIncident": choice["incidentId"],
            "score": choice["score"],
            "similarity": choice["similarity"],
            "successRate": choice["successRate"],
            "successRateIsConditioned": choice["successRateIsConditioned"],
            "riskTier": choice["riskTier"],
            "steps": choice["steps"],
            "errorSignature": errorSignature,
            "attempts": attemptHistory
        }