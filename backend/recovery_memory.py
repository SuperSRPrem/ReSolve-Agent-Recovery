from backend.retriever import IncidentRetriever
from backend.outcome_tracker import OutcomeTracker, computeErrorSignature


RISK_SCORES = {
    "low": 1.0,
    "medium": 0.6,
    "high": 0.2
}


def getRiskTier(action):
    """
    PLACEHOLDER - real risk tagging is build-order step 4, not built yet.
    Everything currently returns "low", so riskScore contributes a flat
    0.15 to every strategy's score right now and isn't discriminating
    anything. Swap the inside of this function, not the formula, once
    step 4 lands.
    """
    return "low"


class RecoveryMemory:
    def __init__(self, minScore=0.5):
        self.retriever = IncidentRetriever()
        self.outcomeTracker = OutcomeTracker(self.retriever.store)
        self.minScore = minScore

    def getFailedActions(self, attemptHistory):
        return [
            attempt["action"].lower()
            for attempt in attemptHistory
            if attempt.get("result") == "failed"
        ]

    def getRecovery(self, currentIncident, attemptHistory=None, limit=5):
        """
        attemptHistory: explicit list of {"action", "result", ...} dicts
        for this incident run so far - not read off currentIncident. This
        is the "incident state + attempt history, not just the incident
        record" separation: the current incident describes the problem,
        attemptHistory describes what's already been tried and failed
        during this specific recovery run.
        """
        attemptHistory = attemptHistory or []

        results = self.retriever.getSimilarIncidents(currentIncident, limit)
        failedActions = self.getFailedActions(attemptHistory)
        errorSignature = computeErrorSignature(currentIncident)

        strategies = []

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

            successRate, isConditioned = self.outcomeTracker.getSuccessRate(
                incident, errorSignature
            )

            riskTier = getRiskTier(action)
            riskScore = RISK_SCORES.get(riskTier, 0.6)

            score = (
                (similarity * 0.45) +
                (successRate * 0.40) +
                (riskScore * 0.15)
            )

            strategy = {
                "incidentId": incident["incidentId"],
                "title": incident["title"],
                "similarity": similarity,
                "successRate": successRate,
                "successRateIsConditioned": isConditioned,
                "riskTier": riskTier,
                "score": score,
                "action": action,
                "steps": resolution.get("steps", []),
                "rootCause": incident.get("rootCause", "")
            }

            strategies.append(strategy)

        strategies.sort(key=lambda item: item["score"], reverse=True)

        if len(strategies) == 0:
            return {
                "status": "NO_MATCH",
                "message": "No reliable recovery was found.",
                "errorSignature": errorSignature,
                "strategies": []
            }

        return {
            "status": "MATCH_FOUND",
            "message": "Recovery options found.",
            "errorSignature": errorSignature,
            "bestChoice": strategies[0],
            "choices": strategies
        }