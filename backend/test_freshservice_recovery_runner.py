from backend.freshservice_recovery_runner import (
    FreshserviceRecoveryRunner
)

from backend.mock_environment import (
    MockEnvironment
)


def printAttempts(result):

    print()
    print("ATTEMPTS")

    for index, attempt in enumerate(
        result.get("attempts", []),
        start=1
    ):

        print()

        print(
            f"Attempt {index}"
        )

        print(
            "Action:",
            attempt["action"]
        )

        print(
            "Result:",
            attempt["result"]
        )

        print(
            "Note:",
            attempt["note"]
        )


def main():

    # --------------------------------------------------
    # SIMULATED ENVIRONMENT
    #
    # We are using the real Freshservice ticket,
    # but recovery actions still run against the
    # existing MockEnvironment.
    #
    # Real Docker/API actions come later.
    # --------------------------------------------------

    environment = MockEnvironment({
        "databaseRunning": False,
        "backendRunning": False,
        "apiHealthy": False,
        "cacheHealthy": True,
        "connectionPoolHealthy": False,
        "replicaHealthy": False,
        "configurationHealthy": False,
        "credentialsHealthy": True,
        "errorSignature": "unknown"
    })

    runner = FreshserviceRecoveryRunner(
        environment=environment,
        maxRecoveryAttempts=5
    )

    print()
    print("=" * 70)
    print("START REAL FRESHSERVICE INCIDENT RECOVERY")
    print("=" * 70)

    result = runner.startRecovery(
        ticketId=4,
        firstAction="Retry database connection"
    )

    print()

    print(
        "Status:",
        result["status"]
    )

    print(
        "Message:",
        result["message"]
    )

    print(
        "Freshservice Ticket:",
        result.get(
            "freshserviceTicketId"
        )
    )

    print(
        "Incident ID:",
        result["incident"]["incidentId"]
    )

    print(
        "Error Signature:",
        result.get(
            "errorSignature"
        )
    )

    print(
        "Recovery Attempts:",
        result.get(
            "recoveryAttempts"
        )
    )

    printAttempts(result)

    print()
    print("=" * 70)
    print("CURRENT ENVIRONMENT")
    print("=" * 70)

    print(
        result.get(
            "environmentState"
        )
    )


if __name__ == "__main__":
    main()