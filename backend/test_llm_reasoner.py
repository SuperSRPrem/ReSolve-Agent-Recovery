from backend.llm_reasoner import LLMReasoner


def main():
    print()
    print("=" * 70)
    print("LLM REASONER SAFETY TEST")
    print("=" * 70)

    choices = [
        {
            "incidentId": "INC-DB-001",
            "title": "Database unavailable",
            "action": "Restart PostgreSQL database",
            "similarity": 0.94,
            "successRate": 0.90,
            "successRateIsConditioned": True,
            "riskTier": "medium",
            "riskScore": 0.6,
            "score": 0.873,
            "rootCause": (
                "PostgreSQL service unavailable."
            ),
            "steps": [
                "Restart PostgreSQL service.",
                "Verify connectivity.",
            ],
        },
        {
            "incidentId": "INC-API-002",
            "title": "Backend API unavailable",
            "action": "Restart backend service",
            "similarity": 0.62,
            "successRate": 0.70,
            "successRateIsConditioned": True,
            "riskTier": "low",
            "riskScore": 1.0,
            "score": 0.709,
            "rootCause": (
                "Backend worker failure."
            ),
            "steps": [
                "Restart backend service."
            ],
        },
    ]

    incident = {
        "incidentId": "CURRENT-001",
        "title": (
            "Production database connection refused"
        ),
        "description": (
            "Backend cannot connect to PostgreSQL."
        ),
        "priority": "high",
        "status": "open",
    }

    # Explicitly provide no model client so this test
    # does not spend API credits.
    reasoner = LLMReasoner()

    reasoner.client = None

    result = reasoner.analyzeRecovery(
        incident=incident,
        choices=choices,
        environmentState={
            "databaseRunning": False,
            "backendRunning": True,
            "apiHealthy": False,
            "connectionPoolHealthy": False,
        },
        attemptHistory=[],
    )

    print(
        "Result:",
        result
    )

    assert (
        result["decision"]
        == "USE_CANDIDATE"
    )

    assert (
        result["selectedIndex"]
        == 0
    )

    assert (
        result["selectedChoice"]
        is choices[0]
    )

    assert (
        result["selectedChoice"]["action"]
        == "Restart PostgreSQL database"
    )

    print(
        "PASS: deterministic fallback selected "
        "the top-ranked candidate"
    )

    maliciousModelOutput = {
        "decision": "USE_CANDIDATE",
        "selectedIndex": 999,
        "incidentSummary": "Database outage.",
        "reasoning": "Do something dangerous.",
        "riskNotes": "",
        "verificationFocus": [],
        "confidence": 1,
    }

    validated = reasoner._validateDecision(
        maliciousModelOutput,
        choices,
    )

    assert (
        validated["selectedChoice"]
        is choices[0]
    )

    assert (
        validated["llmUsed"]
        is False
    )

    print(
        "PASS: invalid model-selected candidate "
        "cannot escape trusted strategy list"
    )

    escalation = (
        reasoner.analyzeRecovery(
            incident=incident,
            choices=[],
        )
    )

    assert (
        escalation["decision"]
        == "ESCALATE"
    )

    assert (
        escalation["selectedChoice"]
        is None
    )

    print(
        "PASS: empty evidence set escalates safely"
    )

    print()
    print("=" * 70)
    print("LLM REASONER SAFETY TEST PASSED")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()