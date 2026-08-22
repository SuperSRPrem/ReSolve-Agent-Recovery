from backend.retriever import IncidentRetriever
from backend.outcome_tracker import OutcomeTracker, computeErrorSignature
from backend.risk_tiering import RiskTierer


class RecoveryMemory:
    def __init__(self, minScore=0.5):
        self.retriever = IncidentRetriever()
        self.outcomeTracker = OutcomeTracker(self.retriever.store)
        self.minScore = minScore

    def getFailedActions(self, attemptHistory):
        """
        Returns actions that have already failed during
        the current recovery run.

        These actions will not be selected again for Plan B.
        """

        return [
            attempt["action"].lower()
            for attempt in attemptHistory
            if attempt.get("result") == "failed"
        ]

    def getRecovery(self, currentIncident, attemptHistory=None, limit=5):
        """
        Finds and ranks recovery strategies.

        Ranking formula:

        45% -> similarity to current incident
        40% -> historical success rate conditioned on error signature
        15% -> risk score

        attemptHistory contains actions already attempted during
        this recovery run.
        """

        attemptHistory = attemptHistory or []

        results = self.retriever.getSimilarIncidents(
            currentIncident,
            limit
        )

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

            if not action:
                continue

            if action.lower() in failedActions:
                continue

            successRate, isConditioned = (
                self.outcomeTracker.getSuccessRate(
                    incident,
                    errorSignature
                )
            )

            risk = RiskTierer.classify(action)

            riskTier = risk["riskTier"]
            riskScore = risk["riskScore"]

            score = (
                (similarity * 0.45)
                + (successRate * 0.40)
                + (riskScore * 0.15)
            )

            strategy = {
                "incidentId": incident["incidentId"],
                "title": incident["title"],
                "similarity": similarity,
                "successRate": successRate,
                "successRateIsConditioned": isConditioned,
                "riskTier": riskTier,
                "riskScore": riskScore,
                "score": score,
                "action": action,
                "steps": resolution.get("steps", []),
                "rootCause": incident.get("rootCause", ""),
            }

            strategies.append(strategy)

        strategies.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        if len(strategies) == 0:
            return {
                "status": "NO_MATCH",
                "message": "No reliable recovery was found.",
                "errorSignature": errorSignature,
                "strategies": [],
            }

        return {
            "status": "MATCH_FOUND",
            "message": "Recovery options found.",
            "errorSignature": errorSignature,
            "bestChoice": strategies[0],
            "choices": strategies,
        }