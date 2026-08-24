import re

from backend.incident_store import IncidentStore


DEFAULT_STATS = {
    "successCount": 0,
    "failureCount": 0
}


def normalizeSignature(value):
    """
    Converts different textual representations of the same error
    into a consistent signature.

    Examples:

    "Connection refused"
        -> CONNECTION_REFUSED

    "database connection refused"
        -> DATABASE_CONNECTION_REFUSED
    """

    if not value:
        return ""

    value = str(value).strip().upper()

    value = re.sub(r"[^A-Z0-9]+", "_", value)

    value = re.sub(r"_+", "_", value)

    return value.strip("_")


def computeErrorSignature(incident):
    """
    Creates a stable error signature for an incident.

    Priority:

    1. Structured errorCodes
    2. Single errorCode
    3. Known error patterns in symptoms
    4. Known error patterns in title/description
    5. First available symptom/title text
    6. unknown

    The goal is not perfect NLP. The goal is to consistently group
    similar failures so conditioned success rates can be meaningful.
    """

    # --------------------------------------------------
    # 1. Multiple structured error codes
    # --------------------------------------------------

    errorCodes = incident.get("errorCodes") or []

    if errorCodes:
        normalizedCodes = [
            normalizeSignature(code)
            for code in errorCodes
            if normalizeSignature(code)
        ]

        if normalizedCodes:
            return "|".join(sorted(normalizedCodes))

    # --------------------------------------------------
    # 2. Single error code
    # --------------------------------------------------

    errorCode = incident.get("errorCode")

    if errorCode:
        normalizedCode = normalizeSignature(errorCode)

        if normalizedCode:
            return normalizedCode

    # --------------------------------------------------
    # Gather available text
    # --------------------------------------------------

    symptoms = incident.get("symptoms") or []

    textParts = []

    if symptoms:
        textParts.extend(
            symptom
            for symptom in symptoms
            if symptom
        )

    title = incident.get("title", "")
    description = incident.get("description", "")

    if title:
        textParts.append(title)

    if description:
        textParts.append(description)

    combinedText = " ".join(
        str(part)
        for part in textParts
    ).lower()

    # --------------------------------------------------
    # 3. Recognize common failure patterns
    # --------------------------------------------------

    # --------------------------------------------------
    # 3. Recognize common failure patterns
    # --------------------------------------------------

    knownPatterns = [
        (
            [
                "connection refused",
                "connection_refused",
                "unable to establish a connection",
                "unable to connect",
                "cannot connect",
                "can't connect",
                "failed to connect",
                "database connection error",
                "database endpoint is not responding",
                "database is not responding",
                "postgresql database",
            ],
            "CONNECTION_REFUSED"
        ),
        (
            [
                "connection timeout",
                "connection timed out",
                "timeout connecting",
                "timed out",
                "connection attempt timed out",
            ],
            "CONNECTION_TIMEOUT"
        ),
        (
            [
                "authentication failed",
                "auth failed",
                "invalid credentials",
                "credential failed",
                "login failed",
                "access denied",
            ],
            "AUTH_FAILED"
        ),
        (
            [
                "database unavailable",
                "database down",
                "db unavailable",
                "database is down",
                "database service unavailable",
            ],
            "DATABASE_UNAVAILABLE"
        ),
        (
            [
                "service unavailable",
                "http 503",
                "503 error",
                "503",
            ],
            "SERVICE_UNAVAILABLE"
        ),
        (
            [
                "internal server error",
                "http 500",
                "500 error",
            ],
            "INTERNAL_SERVER_ERROR"
        ),
        (
            [
                "rate limit",
                "too many requests",
                "429",
            ],
            "RATE_LIMITED"
        ),
        (
            [
                "stale cache",
                "cache unavailable",
                "cache error",
                "redis unavailable",
                "redis connection",
            ],
            "CACHE_FAILURE"
        ),
        (
            [
                "out of memory",
                "memory exhausted",
                "oom",
            ],
            "OUT_OF_MEMORY"
        ),
    ]

    for patterns, signature in knownPatterns:
        if any(
            pattern in combinedText
            for pattern in patterns
        ):
            return signature

    # --------------------------------------------------
    # 4. Fall back to first symptom
    # --------------------------------------------------

    if symptoms:
        firstSymptom = str(symptoms[0]).strip()

        if firstSymptom:
            normalized = normalizeSignature(
                firstSymptom[:80]
            )

            if normalized:
                return normalized

    # --------------------------------------------------
    # 5. Fall back to title
    # --------------------------------------------------

    if title:
        normalized = normalizeSignature(title[:80])

        if normalized:
            return normalized

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
    Tracks recovery outcomes per:

        (source incident, error signature)

    This allows the system to distinguish:

        "Restart database usually works"

    from:

        "Restart database works for CONNECTION_REFUSED
         but not for AUTH_FAILED."
    """

    def __init__(self, store=None):
        self.store = store or IncidentStore()

    def _ensureStatsShape(self, incident):
        stats = incident.get("resolutionStats", {})

        isOldFlatShape = (
            "overall" not in stats
            and "conditioned" not in stats
        )

        if isOldFlatShape:
            stats = {
                "overall": {
                    "successCount": stats.get(
                        "successCount",
                        0
                    ),
                    "failureCount": stats.get(
                        "failureCount",
                        0
                    )
                },
                "conditioned": {}
            }

            incident["resolutionStats"] = stats

        stats.setdefault(
            "overall",
            dict(DEFAULT_STATS)
        )

        stats.setdefault(
            "conditioned",
            {}
        )

        return stats

    def recordOutcome(
        self,
        incidentId,
        errorSignature,
        result
    ):
        """
        Records a verified recovery outcome.

        Only 'success' and 'failed' are valid outcomes.
        """

        if result not in ["success", "failed"]:
            return None

        incident = self.store.getIncident(
            incidentId
        )

        if incident is None:
            return None

        stats = self._ensureStatsShape(
            incident
        )

        errorSignature = (
            normalizeSignature(errorSignature)
            or "unknown"
        )

        conditioned = stats[
            "conditioned"
        ].setdefault(
            errorSignature,
            dict(DEFAULT_STATS)
        )

        key = (
            "successCount"
            if result == "success"
            else "failureCount"
        )

        conditioned[key] += 1

        stats["overall"][key] += 1

        self.store.saveIncidents()

        return stats

    def getSuccessRate(
        self,
        incident,
        errorSignature
    ):
        """
        Returns:

            (successRate, isConditioned)

        Example:

            (0.8, True)

        means the 80% rate came specifically from historical
        outcomes for this error signature.

        If there is no conditioned history, the system falls
        back to the overall success rate:

            (0.8, False)
        """

        stats = self._ensureStatsShape(
            incident
        )

        errorSignature = (
            normalizeSignature(errorSignature)
            or "unknown"
        )

        conditioned = stats[
            "conditioned"
        ].get(errorSignature)

        if conditioned is not None:

            rate = _rate(conditioned)

            if rate is not None:
                return rate, True

        overallRate = _rate(
            stats["overall"]
        )

        if overallRate is not None:
            return overallRate, False

        return 0.0, False