from backend.demo_agent import DemoAgent
from backend.mock_environment import MockEnvironment


def printResult(result):
    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    print("Status:", result["status"])
    print("Message:", result.get("message"))
    print("Error Signature:", result.get("errorSignature"))

    print()
    print("ATTEMPTS")

    for index, attempt in enumerate(
        result["attempts"],
        start=1,
    ):
        print()
        print(f"Attempt {index}")
        print("Action:", attempt["action"])
        print("Result:", attempt["result"])
        print("Note:", attempt["note"])

        if "verification" in attempt:
            verification = attempt["verification"]

            print(
                "Verification:",
                verification["status"],
            )

            for check in verification["checks"]:
                print(
                    f"  - {check['name']}: "
                    f"{'PASS' if check['passed'] else 'FAIL'}"
                )

    print()
    print("FINAL ENVIRONMENT STATE")
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

    agent = DemoAgent(environment)

    result = agent.runIncident(
        incident,
        "Retry database connection",
    )

    printResult(result)


if __name__ == "__main__":
    main()