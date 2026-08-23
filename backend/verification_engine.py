from backend.outcome_tracker import computeErrorSignature


class VerificationEngine:
    """
    Verifies whether a recovery action actually restored the
    expected post-conditions for the detected incident type.

    Execution success is NOT recovery success.

    The verification requirements depend on the error signature.
    """

    def verify(self, incident, environmentState):
        errorSignature = computeErrorSignature(incident)

        normalizedError = str(errorSignature).lower()

        checks = []

        # ==================================================
        # CONNECTION / DATABASE FAILURES
        # ==================================================

        if self._matchesAny(
            normalizedError,
            [
                "connection",
                "connection_refused",
                "database",
                "db",
                "postgres",
                "mysql",
                "connection_timeout",
            ]
        ):
            self._addCheck(
                checks,
                environmentState,
                "databaseRunning"
            )

            self._addCheck(
                checks,
                environmentState,
                "connectionPoolHealthy"
            )

        # ==================================================
        # REPLICA FAILURES
        # ==================================================

        if self._matchesAny(
            normalizedError,
            [
                "replica",
                "replication",
                "replica_unhealthy",
            ]
        ):
            self._addCheck(
                checks,
                environmentState,
                "replicaHealthy"
            )

            self._addCheck(
                checks,
                environmentState,
                "databaseRunning"
            )

        # ==================================================
        # BACKEND / API FAILURES
        # ==================================================

        if self._matchesAny(
            normalizedError,
            [
                "backend",
                "api",
                "service",
                "http_500",
                "http_503",
                "500",
                "503",
                "unavailable",
            ]
        ):
            self._addCheck(
                checks,
                environmentState,
                "backendRunning"
            )

            self._addCheck(
                checks,
                environmentState,
                "apiHealthy"
            )

        # ==================================================
        # CACHE FAILURES
        # ==================================================

        if self._matchesAny(
            normalizedError,
            [
                "cache",
                "redis",
                "stale",
                "cache_error",
            ]
        ):
            self._addCheck(
                checks,
                environmentState,
                "cacheHealthy"
            )

        # ==================================================
        # CREDENTIAL / AUTHENTICATION FAILURES
        # ==================================================

        if self._matchesAny(
            normalizedError,
            [
                "credential",
                "credentials",
                "auth",
                "authentication",
                "unauthorized",
                "forbidden",
                "access_denied",
            ]
        ):
            self._addCheck(
                checks,
                environmentState,
                "credentialsHealthy"
            )

            self._addCheck(
                checks,
                environmentState,
                "errorSignature",
                expected=""
            )

        # ==================================================
        # CONFIGURATION FAILURES
        # ==================================================

        if self._matchesAny(
            normalizedError,
            [
                "config",
                "configuration",
                "misconfiguration",
                "invalid_config",
            ]
        ):
            self._addCheck(
                checks,
                environmentState,
                "configurationHealthy"
            )

        # ==================================================
        # UNKNOWN ERROR
        #
        # Conservative fallback.
        # We do NOT declare recovery based on a single
        # unrelated field.
        # ==================================================

        if not checks:

            self._addCheck(
                checks,
                environmentState,
                "backendRunning"
            )

            self._addCheck(
                checks,
                environmentState,
                "apiHealthy"
            )

        recovered = all(
            check["passed"]
            for check in checks
        )

        return {
            "status": (
                "VERIFIED"
                if recovered
                else "FAILED"
            ),
            "recovered": recovered,
            "errorSignature": errorSignature,
            "checks": checks,
            "message": (
                "Recovery verified successfully."
                if recovered
                else (
                    "Recovery action executed, but one or more "
                    "required post-conditions were not satisfied."
                )
            ),
        }

    def _matchesAny(self, value, keywords):
        """
        Returns True if any keyword appears in the
        normalized error signature.
        """

        return any(
            keyword in value
            for keyword in keywords
        )

    def _addCheck(
        self,
        checks,
        environmentState,
        field,
        expected=True
    ):
        """
        Adds a structured verification check.
        """

        actual = environmentState.get(field)

        checks.append({
            "name": field,
            "expected": expected,
            "actual": actual,
            "passed": actual == expected,
        })