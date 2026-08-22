from backend.mock_environment import MockEnvironment


def printResult(title, result):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

    print("Action:", result["action"])
    print("Execution:", result["executionStatus"])
    print("Message:", result["message"])
    print("State:", result["state"])


def main():
    environment = MockEnvironment(
        {
            "databaseRunning": False,
            "backendRunning": False,
            "apiHealthy": False,
            "cacheHealthy": False
        }
    )

    print("INITIAL STATE")
    print(environment.getState())

    result1 = environment.executeAction(
        "Restart database"
    )

    printResult(
        "TEST 1: DATABASE RESTART",
        result1
    )

    result2 = environment.executeAction(
        "Restart backend service"
    )

    printResult(
        "TEST 2: BACKEND RESTART",
        result2
    )

    result3 = environment.executeAction(
        "Clear application cache"
    )

    printResult(
        "TEST 3: CACHE CLEAR",
        result3
    )

    result4 = environment.executeAction(
        "Destroy unknown infrastructure"
    )

    printResult(
        "TEST 4: UNKNOWN ACTION",
        result4
    )

    print()
    print("FINAL STATE")
    print(environment.getState())

    print()
    print("EXECUTION LOG")
    for entry in environment.getExecutionLog():
        print(entry)


if __name__ == "__main__":
    main()