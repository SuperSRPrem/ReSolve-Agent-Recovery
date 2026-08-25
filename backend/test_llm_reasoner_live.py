import os

from dotenv import load_dotenv

from backend.llm_reasoner import LLMReasoner


load_dotenv(".env")


def main():
    print()
    print("=" * 70)
    print("LIVE LLM REASONING TEST")
    print("=" * 70)

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not configured in .env"
        )

    incident = {
        "incidentId": "LIVE-LLM-001",
        "title": (
            "Production PostgreSQL database "
            "connection refused"
        ),
        "description": (
            "Backend API remains running but cannot "
            "connect to PostgreSQL. Requests depending "
            "on the database are returning errors."
        ),
        "priority": "high",
        "status": "open",
    }

    choices = [
        {
            "incidentId": "HIST-DB-001",
            "title": "PostgreSQL service unavailable",
            "action": "Restart PostgreSQL database",
            "similarity": 0.96,
            "successRate": 0.92,
            "successRateIsConditioned": True,
            "riskTier": "medium",
            "riskScore": 0.6,
            "score": 0.89,
            "rootCause": (
                "PostgreSQL process stopped."
            ),
            "steps": [
                "Restart PostgreSQL.",
                "Verify database connectivity.",
            ],
        },
        {
            "incidentId": "HIST-API-001",
            "title": "Backend worker failure",
            "action": "Restart backend service",
            "similarity": 0.54,
            "successRate": 0.71,
            "successRateIsConditioned": False,
            "riskTier": "low",
            "riskScore": 1.0,
            "score": 0.67,
            "rootCause": (
                "Backend worker process failure."
            ),
            "steps": [
                "Restart backend workers."
            ],
        },
    ]

    environmentState = {
        "databaseRunning": False,
        "backendRunning": True,
        "apiHealthy": False,
        "connectionPoolHealthy": False,
    }

    reasoner = LLMReasoner()

    print(
        "Model:",
        reasoner.model
    )

    print()
    print("Sending evidence to LLM...")

    result = reasoner.analyzeRecovery(
        incident=incident,
        choices=choices,
        environmentState=environmentState,
        attemptHistory=[],
    )

    print()
    print("LLM used:", result["llmUsed"])
    print("Decision:", result["decision"])
    print(
        "Selected index:",
        result["selectedIndex"]
    )

    selectedChoice = result.get(
        "selectedChoice"
    )

    print(
        "Selected action:",
        (
            selectedChoice.get("action")
            if selectedChoice
            else None
        )
    )

    print()
    print("Incident summary:")
    print(result["incidentSummary"])

    print()
    print("Reasoning:")
    print(result["reasoning"])

    print()
    print("Risk notes:")
    print(result["riskNotes"])

    print()
    print("Verification focus:")

    for check in result[
        "verificationFocus"
    ]:
        print("-", check)

    print()
    print(
        "Confidence:",
        result["confidence"]
    )

    # ==================================================
    # LIVE LLM ASSERTIONS
    # ==================================================

    assert result["llmUsed"] is True, (
        "Live LLM was not used.\n"
        "Fallback reason:\n"
        f"{result['reasoning']}"
    )

    assert result["decision"] in {
        "USE_CANDIDATE",
        "ESCALATE",
    }

    if result["decision"] == "USE_CANDIDATE":
        assert (
            result["selectedChoice"]
            in choices
        )

        assert (
            result[
                "selectedChoice"
            ]["action"]
            in {
                "Restart PostgreSQL database",
                "Restart backend service",
            }
        )

        assert (
            result[
                "selectedChoice"
            ]["action"]
            == "Restart PostgreSQL database"
        )

    print()
    print(
        "PASS: live LLM returned a "
        "schema-valid decision"
    )

    if result["decision"] == "USE_CANDIDATE":
        print(
            "PASS: selected action came only "
            "from trusted candidates"
        )

    print()
    print("=" * 70)
    print("LIVE LLM REASONING TEST PASSED")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
