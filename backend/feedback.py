from backend.incident_store import IncidentStore
from backend.outcome_tracker import OutcomeTracker


class FeedbackManager:
    def __init__(self):
        self.store = IncidentStore()
        self.outcomeTracker = OutcomeTracker(self.store)

    def addAttempt(self, incident, action, result, errorSignature=None, note=""):
        if result not in ["success", "failed"]:
            return False

        attempt = {
            "action": action,
            "result": result,
            "errorSignature": errorSignature,
            "note": note
        }

        incident.setdefault("actionsTried", []).append(attempt)

        return True

    def recordResult(self, incidentId, errorSignature, result):
        return self.outcomeTracker.recordOutcome(incidentId, errorSignature, result)

    def setStatus(self, incidentId, status):
        if status not in ["active", "questionable", "deprecated"]:
            return False

        incident = self.store.getIncident(incidentId)

        if incident is None:
            return False

        incident["resolutionStatus"] = status
        self.store.saveIncidents()

        return True