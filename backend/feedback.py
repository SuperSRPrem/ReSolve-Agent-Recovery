from backend.incident_store import IncidentStore


class FeedbackManager:
    def __init__(self):
        self.store = IncidentStore()

    def addAttempt(self, incident, action, result):
        if result not in ["success", "failed"]:
            return False

        attempt = {
            "action": action,
            "result": result
        }

        incident.setdefault("actionsTried", []).append(attempt)

        return True

    def recordResult(self, incidentId, result):
        if result not in ["success", "failed"]:
            return None

        incident = self.store.getIncident(incidentId)

        if incident is None:
            return None

        stats = incident.get("resolutionStats", {})

        success = stats.get("successCount", 0)
        failure = stats.get("failureCount", 0)

        if result == "success":
            success += 1
        else:
            failure += 1

        incident["resolutionStats"] = {
            "successCount": success,
            "failureCount": failure
        }

        self.store.saveIncidents()

        return incident["resolutionStats"]

    def setStatus(self, incidentId, status):
        if status not in ["active", "questionable", "deprecated"]:
            return False

        incident = self.store.getIncident(incidentId)

        if incident is None:
            return False

        incident["resolutionStatus"] = status
        self.store.saveIncidents()

        return True
