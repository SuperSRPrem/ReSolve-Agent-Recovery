from backend.incident_store import IncidentStore


DEFAULT_STATS = {"successCount": 0, "failureCount": 0}


def computeErrorSignature(incident):
    """
    A rough key for 'what kind of failure is this'. Error codes are the
    strongest signal when present; falls back to the first symptom line
    when they're not. This doesn't need to be perfect - it just needs to
    group "restart DB fixed this" and "restart DB did NOT fix this" under
    the same key so conditioned success rates mean something.
    """
    errorCodes = incident.get("errorCodes") or []
    if errorCodes:
        return "|".join(sorted(code.upper() for code in errorCodes))

    symptoms = incident.get("symptoms") or []
    if symptoms and symptoms[0].strip():
        return "symptom:" + symptoms[0].strip().lower()[:60]

    return "unknown"


def _rate(stats):
    success = stats.get("successCount", 0)
    failure = stats.get("failureCount", 0)
    total = success + failure

    if total == 0:
        return None

    return success / total


class OutcomeTracker:
    """
    Tracks success/failure per (source incident, error signature) instead
    of a single aggregate per incident. "Restart DB" can be 80% successful
    overall but far worse specifically when the error is 'auth failed' -
    conditioning on the error signature is what lets ranking reflect that.
    """

    def __init__(self, store=None):
        self.store = store or IncidentStore()

    def _ensureStatsShape(self, incident):
        stats = incident.get("resolutionStats", {})

        isOldFlatShape = "overall" not in stats and "conditioned" not in stats
        if isOldFlatShape:
            stats = {
                "overall": {
                    "successCount": stats.get("successCount", 0),
                    "failureCount": stats.get("failureCount", 0)
                },
                "conditioned": {}
            }
            incident["resolutionStats"] = stats

        stats.setdefault("overall", dict(DEFAULT_STATS))
        stats.setdefault("conditioned", {})

        return stats

    def recordOutcome(self, incidentId, errorSignature, result):
        if result not in ["success", "failed"]:
            return None

        incident = self.store.getIncident(incidentId)
        if incident is None:
            return None

        stats = self._ensureStatsShape(incident)
        conditioned = stats["conditioned"].setdefault(
            errorSignature, dict(DEFAULT_STATS)
        )

        key = "successCount" if result == "success" else "failureCount"
        conditioned[key] += 1
        stats["overall"][key] += 1

        self.store.saveIncidents()

        return stats

    def getSuccessRate(self, incident, errorSignature):
        """
        Returns (rate, isConditioned).

        isConditioned tells you whether this rate came from history
        specific to this error signature, or fell back to the incident's
        overall success rate because there wasn't conditioned data yet.
        Surface that distinction in the UI later - it's the difference
        between the agent being confident and the agent guessing.
        """
        stats = self._ensureStatsShape(incident)

        conditioned = stats["conditioned"].get(errorSignature)
        if conditioned is not None:
            rate = _rate(conditioned)
            if rate is not None:
                return rate, True

        overallRate = _rate(stats["overall"])
        if overallRate is not None:
            return overallRate, False

        return 0.0, False