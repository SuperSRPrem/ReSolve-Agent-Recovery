from backend.reasoned_recovery_memory import (
    ReasonedRecoveryMemory,
)


class FakeHistoricalMemory:
    def getRecovery(
        self,
        currentIncident,
        attemptHistory=None,
        limit=5,
    ):
        choices = [
            {
                "incidentId": "INC-1421",
                "title": (
                    "Connection pool exhaustion "
                    "after configuration change"
                ),
                "action": (
                    "Restore previous connection "
                    "pool configuration"
                ),
                "similarity": 0.5484,
                "successRate": 0.875,
                "successRateIsConditioned": True,
                "riskTier": "medium",
                "riskScore": 0.6,
                "score": 0.6868,
                "rootCause": (
                    "Incorrect connection pool limits."
                ),
                "steps": [],
            }
        ]

        return {
            "status": "MATCH_FOUND",
            "errorSignature": (
                "CONNECTION_REFUSED"
            ),
            "bestChoice": choices[0],
            "choices": choices,
        }


class FakeReasoner:
    def analyzeRecovery(
        self,
        incident,
        choices,
        environmentState=None,
        attemptHistory=None,
    ):
        runbookChoice = next(
            choice
            for choice in choices
            if choice.get("sourceType")
            == "approved-runbook"
        )

        return {
            "llmUsed": True,
            "decision": "USE_CANDIDATE",
            "selectedIndex": (
                choices.index(
                    runbookChoice
                )
            ),
            "selectedChoice": (
                runbookChoice
            ),
            "incidentSummary": (
                "Database service is unavailable."
            ),
            "reasoning": (
                "The approved restart runbook "
                "matches the observed database outage."
            ),
            "riskNotes": (
                "Medium risk; approval required."
            ),
            "verificationFocus": [
                "databaseRunning",
                "connectionPoolHealthy",
            ],
            "confidence": 0.9,
            "model": "test-model",
        }


class FakeEnvironment:
    def getState(self):
        return {
            "databaseRunning": False,
            "backendRunning": True,
            "apiHealthy": False,
            "connectionPoolHealthy": False,
        }


def main():
    print()
    print("=" * 70)
    print("HYBRID RECOVERY EVIDENCE TEST")
    print("=" * 70)

    incident = {
        "incidentId": "CURRENT-001",
        "title": (
            "Production PostgreSQL "
            "database connection refused"
        ),
        "description": (
            "Backend cannot connect to PostgreSQL. "
            "Database connection refused."
        ),
    }

    memory = ReasonedRecoveryMemory(
        baseMemory=(
            FakeHistoricalMemory()
        ),
        reasoner=FakeReasoner(),
        environment=FakeEnvironment(),
    )

    result = memory.getRecovery(
        incident
    )

    choices = result[
        "choices"
    ]

    historical = [
        choice
        for choice in choices
        if choice["sourceType"]
        == "historical-incident"
    ]

    runbooks = [
        choice
        for choice in choices
        if choice["sourceType"]
        == "approved-runbook"
    ]

    assert historical
    assert runbooks

    print(
        "PASS: historical and approved "
        "runbook evidence were merged"
    )

    runbook = runbooks[0]

    assert (
        runbook["action"]
        == "Restart PostgreSQL database"
    )

    assert (
        runbook["successRate"]
        is None
    )

    assert (
        runbook[
            "historicalOutcomeAvailable"
        ]
        is False
    )

    print(
        "PASS: runbook evidence keeps "
        "honest provenance and no fake stats"
    )

    assert (
        result["bestChoice"]["action"]
        == "Restart PostgreSQL database"
    )

    assert (
        result["bestChoice"][
            "sourceType"
        ]
        == "approved-runbook"
    )

    print(
        "PASS: reasoning layer can select "
        "the trusted approved runbook"
    )

    print()
    print("Candidates presented to reasoner:")

    for candidate in choices:
        print(
            "-",
            candidate["sourceType"],
            "|",
            candidate["action"],
            "| successRate =",
            candidate["successRate"],
        )

    print()
    print("=" * 70)
    print(
        "HYBRID RECOVERY EVIDENCE TEST PASSED"
    )
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
