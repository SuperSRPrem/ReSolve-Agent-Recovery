from backend.retriever import IncidentRetriever


class RecoveryMemory:
    def __init__(self, minScore=0.5):
        self.retriever = IncidentRetriever()
        self.minScore = minScore

    def getFailedActions(self, incident):
        failedActions = []

        for item in incident.get("actionsTried", []):
            if item.get("result") == "failed":
                action = item.get("action", "").lower()
                failedActions.append(action)

        return failedActions

    def getSuccessRate(self, incident):
        stats = incident.get("resolutionStats", {})

        success = stats.get("successCount", 0)
        failure = stats.get("failureCount", 0)

        total = success + failure

        if total == 0:
            return 0

        return success / total

    def getRecovery(self, currentIncident, limit=5):
        results = self.retriever.getSimilarIncidents(currentIncident, limit)
        failedActions = self.getFailedActions(currentIncident)

        choices = []

        for result in results:
            incident = result["incident"]
            similarity = result["score"]

            if similarity < self.minScore:
                continue

            if incident.get("resolutionStatus") == "deprecated":
                continue

            resolution = incident.get("resolution", {})
            action = resolution.get("action", "")

            if action.lower() in failedActions:
                continue

            successRate = self.getSuccessRate(incident)

            score = (similarity * 0.8) + (successRate * 0.2)

            choice = {
                "incidentId": incident["incidentId"],
                "title": incident["title"],
                "similarity": similarity,
                "successRate": successRate,
                "score": score,
                "action": action,
                "steps": resolution.get("steps", []),
                "rootCause": incident.get("rootCause", "")
            }

            choices.append(choice)

        choices.sort(key=lambda item: item["score"], reverse=True)

        if len(choices) == 0:
            return {
                "status": "NO_MATCH",
                "message": "No reliable recovery was found.",
                "choices": []
            }

        return {
            "status": "MATCH_FOUND",
            "message": "Recovery options found.",
            "bestChoice": choices[0],
            "choices": choices
        }
