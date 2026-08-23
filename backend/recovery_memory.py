from backend.retriever import IncidentRetriever
from backend.outcome_tracker import OutcomeTracker, computeErrorSignature
from backend.risk_tiering import RiskTierer


class RecoveryMemory:
    def __init__(self, minScore=0.5):
        self.retriever = IncidentRetriever()
        self.outcomeTracker = OutcomeTracker(
            self.retriever.store
        )
        self.minScore = minScore

    def getUnavailableActions(self, attemptHistory):
        """
        Returns actions that should not be selected again
        during the current recovery run.

        This includes actions that:

        - failed verification
        - were rejected by a human
        - are already waiting for approval

        This prevents the recovery loop from repeatedly
        suggesting the same strategy.
        """

        unavailableResults = {
            "failed",
            "rejected",
            "pending-approval"
        }

        unavailableActions = set()

        for attempt in attemptHistory:
            result = attempt.get("result")

            if result in unavailableResults:
                action = attempt.get("action", "")

                if action:
                    unavailableActions.add(
                        action.lower().strip()
                    )

        return unavailableActions

    def getRecovery(
        self,
        currentIncident,
        attemptHistory=None,
        limit=5
    ):
        """
        Finds and ranks recovery strategies.

        Ranking formula:

        45% -> similarity to current incident
        40% -> historical success rate conditioned
               on the error signature
        15% -> safety / risk score

        Actions that have already failed or been rejected
        during this recovery session are excluded.
        """

        attemptHistory = attemptHistory or []

        results = self.retriever.getSimilarIncidents(
            currentIncident,
            limit
        )

        unavailableActions = self.getUnavailableActions(
            attemptHistory
        )

        errorSignature = computeErrorSignature(
            currentIncident
        )

        strategies = []

        for result in results:
            incident = result["incident"]
            similarity = result["score"]

            # Ignore weak matches.
            if similarity < self.minScore:
                continue

            # Do not use deprecated historical resolutions.
            if (
                incident.get("resolutionStatus")
                == "deprecated"
            ):
                continue

            resolution = incident.get(
                "resolution",
                {}
            )

            action = resolution.get(
                "action",
                ""
            )

            if not action:
                continue

            normalizedAction = action.lower().strip()

            # Never retry an action that already failed,
            # was rejected, or is already pending.
            if normalizedAction in unavailableActions:
                continue

            (
                successRate,
                isConditioned
            ) = self.outcomeTracker.getSuccessRate(
                incident,
                errorSignature
            )

            risk = RiskTierer.classify(
                action
            )

            riskTier = risk["riskTier"]
            riskScore = risk["riskScore"]

            score = (
                (similarity * 0.45)
                + (successRate * 0.40)
                + (riskScore * 0.15)
            )

            strategy = {
                "incidentId": incident[
                    "incidentId"
                ],
                "title": incident["title"],
                "similarity": similarity,
                "successRate": successRate,
                "successRateIsConditioned": (
                    isConditioned
                ),
                "riskTier": riskTier,
                "riskScore": riskScore,
                "score": score,
                "action": action,
                "steps": resolution.get(
                    "steps",
                    []
                ),
                "rootCause": incident.get(
                    "rootCause",
                    ""
                ),
            }

            strategies.append(strategy)

        strategies.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        if not strategies:
            return {
                "status": "NO_MATCH",
                "message": (
                    "No reliable untried recovery "
                    "strategy was found."
                ),
                "errorSignature": errorSignature,
                "strategies": [],
            }

        return {
            "status": "MATCH_FOUND",
            "message": (
                "Recovery options found."
            ),
            "errorSignature": errorSignature,
            "bestChoice": strategies[0],
            "choices": strategies,
        }