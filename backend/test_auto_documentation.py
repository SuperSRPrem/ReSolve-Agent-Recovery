from backend.demo_agent import DemoAgent
from backend.mock_environment import MockEnvironment


def main():
    environment = MockEnvironment({
        "databaseRunning": False,
        "backendRunning": False,
        "apiHealthy": False,
        "cacheHealthy": True,
        "connectionPoolHealthy": False
    })

    incident = {
        "incidentId": "demo-doc-001",
        "title": "Database connection failure",
        "description": (
            "Backend cannot connect to the database. "
            "Connection refused."
        ),
        "service": "backend",
        "severity": "high",
        "errorCode": "connection refused"
    }

    agent = DemoAgent(
        environment=environment,
        maxRecoveryAttempts=5
    )

    result = agent.startRecovery(
        incident,
        "Retry database connection"
    )

    while (
        result["status"]
        == "AWAITING_APPROVAL"
    ):
        print()
        print(
            "Approving:",
            result["strategy"]["action"]
        )

        result = (
            agent.approvePendingStrategy(
                result["session"]
            )
        )

    print()
    print("=" * 70)
    print("FINAL STATUS")
    print("=" * 70)
    print(result["status"])

    print()
    print("=" * 70)
    print("STRUCTURED RECORD")
    print("=" * 70)

    print(
        result["recoveryRecord"]
    )

    print()
    print("=" * 70)
    print("AUTO-GENERATED DOCUMENTATION")
    print("=" * 70)

    print(
        result["documentation"]
    )

    print()
    print(
        "Structured recovery record saved to:"
    )
    print(
        "data/recovery_records.json"
    )


if __name__ == "__main__":
    main()