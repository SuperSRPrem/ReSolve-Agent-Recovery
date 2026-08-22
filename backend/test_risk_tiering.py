from backend.risk_tiering import RiskTierer


def runTest(action, expected):
    result = RiskTierer.getRiskTier(action)

    status = "PASS" if result == expected else "FAIL"

    print(
        f"[{status}] "
        f"Action: {action} | "
        f"Expected: {expected} | "
        f"Got: {result}"
    )

    return result == expected


def main():
    tests = [
        ("Restart backend service", "low"),
        ("Clear application cache", "low"),
        ("Run health check", "low"),

        ("Change database configuration", "medium"),
        ("Rotate database credentials", "medium"),
        ("Restart database", "medium"),

        ("Delete database", "high"),
        ("Destroy server", "high"),
        ("Terminate infrastructure", "high"),

        ("Perform unknown recovery operation", "medium"),
    ]

    passed = 0

    for action, expected in tests:
        if runTest(action, expected):
            passed += 1

    total = len(tests)

    print()
    print(f"Passed {passed}/{total} tests.")

    if passed == total:
        print("All risk tiering tests passed.")
    else:
        print("Some tests failed.")


if __name__ == "__main__":
    main()