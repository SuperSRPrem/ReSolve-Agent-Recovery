from backend.reasoned_recovery_memory import (
    ReasonedRecoveryMemory,
)


class FakeRecoveryMemory:
    def getRecovery(
        self,
        currentIncident,
        attemptHistory=None,
        limit=5,
    ):
        choices = [
            {
                "incidentId": "HIST-DB",
                "title": "Database unavailable",
                "action": (
                    "Restart PostgreSQL database"
                ),
                "similarity": 0.95,
                "successRate": 0.92,
                "successRateIsConditioned": True,
                "riskTier": "medium",
                "riskScore": 0.6,
                "score": 0.88,
                "steps": [],
                "rootCause": (
                    "PostgreSQL unavailable."
                ),
            },
            {
                "incidentId": "HIST-API",
                "title": "Backend unavailable",
                "action": (
                    "Restart backend service"
                ),
                "similarity": 0.60,
                "successRate": 0.70,
                "successRateIsConditioned": False,
                "riskTier": "low",
                "riskScore": 1.0,
                "score": 0.70,
                "steps": [],
                "rootCause": (
                    "Backend worker unavailable."
                ),
            },
        ]

        return {
            "status": "MATCH_FOUND",
            "message": (
                "Recovery options found."
            ),
            "errorSignature": (
                "CONNECTION_REFUSED"
            ),
            "bestChoice": choices[0],
            "choices": choices,
        }


class FakeEnvironment:
    def getState(self):
        return {
            "databaseRunning": False,
            "backendRunning": True,
            "apiHealthy": False,
            "connectionPoolHealthy": False,
        }


class FakeReasoner:
    def analyzeRecovery(
        self,
        incident,
        choices,
        environmentState=None,
        attemptHistory=None,
    ):
        # Simulate an LLM choosing candidate 0.
        return {
            "llmUsed": True,
            "decision": "USE_CANDIDATE",
            "selectedIndex": 0,
            "selectedChoice": choices[0],
            "incidentSummary": (
                "Database dependency is unavailable."
            ),
            "reasoning": (
                "Database restart best matches "
                "the observed evidence."
            ),
            "riskNotes": (
                "Medium-risk action requires approval."
            ),
            "verificationFocus": [
                "databaseRunning",
                "connectionPoolHealthy",
            ],
            "confidence": 0.95,
            "model": "test-model",
        }


class InvalidReasoner:
    def analyzeRecovery(
        self,
        incident,
        choices,
        environmentState=None,
        attemptHistory=None,
    ):
        # Attempts to inject a strategy that did not
        # originate from RecoveryMemory.
        return {
            "llmUsed": True,
            "decision": "USE_CANDIDATE",
            "selectedIndex": 999,
            "selectedChoice": {
                "action": "rm -rf /"
            },
            "incidentSummary": "",
            "reasoning": "",
            "riskNotes": "",
            "verificationFocus": [],
            "confidence": 1,
            "model": "test-model",
        }


class EscalatingReasoner:
    def analyzeRecovery(
        self,
        incident,
        choices,
        environmentState=None,
        attemptHistory=None,
    ):
        return {
            "llmUsed": True,
            "decision": "ESCALATE",
            "selectedIndex": -1,
            "selectedChoice": None,
            "incidentSummary": (
                "Evidence is insufficient."
            ),
            "reasoning": (
                "Human investigation is required."
            ),
            "riskNotes": "",
            "verificationFocus": [],
            "confidence": 0.50,
            "model": "test-model",
        }


def main():
    print()
    print("=" * 70)
    print(
        "REASONED RECOVERY MEMORY TEST"
    )
    print("=" * 70)

    incident = {
        "incidentId": "CURRENT-001",
        "title": (
            "Production database connection refused"
        ),
        "description": (
            "Backend cannot connect to PostgreSQL."
        ),
    }

    # ==================================================
    # VALID TRUSTED SELECTION
    # ==================================================

    memory = ReasonedRecoveryMemory(
        baseMemory=FakeRecoveryMemory(),
        reasoner=FakeReasoner(),
        environment=FakeEnvironment(),
    )

    result = memory.getRecovery(
        incident
    )

    assert (
        result["status"]
        == "MATCH_FOUND"
    )

    assert (
        result["bestChoice"]["action"]
        == "Restart PostgreSQL database"
    )

    assert (
        result["decisionSource"]
        == "llm"
    )

    assert (
        result["llmReasoning"]["llmUsed"]
        is True
    )

    print(
        "PASS: LLM selected a trusted "
        "RecoveryMemory candidate"
    )

    # ==================================================
    # MODEL CANNOT INJECT AN ACTION
    # ==================================================

    unsafeMemory = (
        ReasonedRecoveryMemory(
            baseMemory=FakeRecoveryMemory(),
            reasoner=InvalidReasoner(),
            environment=FakeEnvironment(),
        )
    )

    unsafeResult = (
        unsafeMemory.getRecovery(
            incident
        )
    )

    assert (
        unsafeResult[
            "bestChoice"
        ]["action"]
        == "Restart PostgreSQL database"
    )

    assert (
        unsafeResult[
            "bestChoice"
        ]["action"]
        != "rm -rf /"
    )

    print(
        "PASS: untrusted model-generated "
        "action was rejected"
    )

    # ==================================================
    # ESCALATION REMAINS SAFE
    # ==================================================

    escalationMemory = (
        ReasonedRecoveryMemory(
            baseMemory=FakeRecoveryMemory(),
            reasoner=EscalatingReasoner(),
            environment=FakeEnvironment(),
        )
    )

    escalation = (
        escalationMemory.getRecovery(
            incident
        )
    )

    assert (
        escalation["status"]
        == "NO_MATCH"
    )

    assert (
        escalation["reason"]
        == "LLM_ESCALATION"
    )

    print(
        "PASS: LLM can recommend escalation "
        "without executing anything"
    )

    print()
    print("=" * 70)
    print(
        "REASONED RECOVERY MEMORY TEST PASSED"
    )
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
