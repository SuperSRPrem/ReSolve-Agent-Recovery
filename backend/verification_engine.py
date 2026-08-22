from backend.outcome_tracker import computeErrorSignature


class VerificationEngine:
    """
    Verifies whether a recovery action actually restored
    the expected system state.

    A successful execution is not considered a successful recovery
    until the expected post-conditions are verified.
    """

    def verify(self, incident, environmentState):
        errorSignature = computeErrorSignature(incident)

        normalizedError = str(errorSignature).lower()

        checks = []

        # --------------------------------------------------
        # Database-related post-conditions
        # --------------------------------------------------

        if any(
            keyword in normalizedError
            for keyword in [
                "database",
                "db",
                "connection",
                "postgres",
                "mysql",
            ]
        ):
            databaseRunning = environmentState.get(
                "databaseRunning",
                False
            )

            checks.append({
                "name": "databaseRunning",
                "expected": True,
                "actual": databaseRunning,
                "passed": databaseRunning is True,
            })

        # --------------------------------------------------
        # Backend/API post-conditions
        # --------------------------------------------------

        if any(
            keyword in normalizedError
            for keyword in [
                "backend",
                "api",
                "service",
                "503",
                "500",
            ]
        ):
            backendRunning = environmentState.get(
                "backendRunning",
                False
            )

            checks.append({
                "name": "backendRunning",
                "expected": True,
                "actual": backendRunning,
                "passed": backendRunning is True,
            })

            apiHealthy = environmentState.get(
                "apiHealthy",
                False
            )

            checks.append({
                "name": "apiHealthy",
                "expected": True,
                "actual": apiHealthy,
                "passed": apiHealthy is True,
            })

        # --------------------------------------------------
        # Cache post-condition
        # --------------------------------------------------

        if any(
            keyword in normalizedError
            for keyword in [
                "cache",
                "stale",
                "redis",
            ]
        ):
            cacheHealthy = environmentState.get(
                "cacheHealthy",
                False
            )

            checks.append({
                "name": "cacheHealthy",
                "expected": True,
                "actual": cacheHealthy,
                "passed": cacheHealthy is True,
            })

        # --------------------------------------------------
        # Generic health check
        # --------------------------------------------------

        if not checks:
            checks.append({
                "name": "apiHealthy",
                "expected": True,
                "actual": environmentState.get(
                    "apiHealthy",
                    False
                ),
                "passed": environmentState.get(
                    "apiHealthy",
                    False
                ) is True,
            })

        recovered = all(
            check["passed"]
            for check in checks
        )

        return {
            "status": "VERIFIED" if recovered else "FAILED",
            "recovered": recovered,
            "errorSignature": errorSignature,
            "checks": checks,
            "message": (
                "Recovery verified successfully."
                if recovered
                else (
                    "Recovery action executed, but the expected "
                    "system state was not restored."
                )
            ),
        }