from backend.demo_agent import DemoAgent
from backend.mock_environment import MockEnvironment


def printAttempts(result):
    print()
    print("ATTEMPTS")

    for index, attempt in enumerate(
        result["attempts"],
        start=1
    ):
        print()
        print(f"Attempt {index}")
        print("Action:", attempt["action"])
        print("Result:", attempt["result"])
        print("Note:", attempt["note"])

        verification = attempt.get("verification")

        if verification:
            print(
                "Verification:",
                verification["status"]
            )

            for check in verification["checks"]:
                status = (
                    "PASS"
                    if check["passed"]
                    else "FAIL"
                )

                print(
                    f"  - {check['name']}: {status}"
                )


def printResult(result):
    print()
    print("=" * 70)
    print("CURRENT RESULT")
    print("=" * 70)

    print("Status:", result["status"])
    print("Message:", result["message"])
    print(
        "Error Signature:",
        result["errorSignature"]
    )

    print(
        "Recovery Attempts:",
        result["recoveryAttempts"]
    )

    if result.get("reason"):
        print("Reason:", result["reason"])

    printAttempts(result)

    print()
    print("CURRENT ENVIRONMENT STATE")
    print(result["environmentState"])


def main():

    environment = MockEnvironment({
        "databaseRunning": False,
        "backendRunning": False,
        "apiHealthy": False,
        "cacheHealthy": True,
    })

    incident = {
        "incidentId": "demo-001",
        "title": "Database connection failure",
        "description": (
            "Backend cannot connect to database. "
            "Connection refused."
        ),
        "service": "backend",
        "severity": "high",
        "errorCode": "connection refused",
    }

    agent = DemoAgent(
        environment=environment,
        maxRecoveryAttempts=5
    )

    # ----------------------------------------------
    # Start recovery
    # ----------------------------------------------

    result = agent.startRecovery(
        incident,
        "Retry database connection"
    )

    printResult(result)

    # ----------------------------------------------
    # Demo human approval
    # ----------------------------------------------

    while result["status"] == "AWAITING_APPROVAL":

        print()
        print("=" * 70)
        print("HUMAN APPROVAL SIMULATION")
        print("=" * 70)

        strategy = result["strategy"]

        print(
            "Strategy requiring approval:",
            strategy["action"]
        )

        print(
            "Risk tier:",
            strategy["riskTier"]
        )

        print()
        print("Human decision: APPROVED")

        result = agent.approvePendingStrategy(
            result["session"]
        )

        printResult(result)

    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    print("Status:", result["status"])

    print()
    print("FINAL ENVIRONMENT STATE")
    print(result["environmentState"])


if __name__ == "__main__":
    main()