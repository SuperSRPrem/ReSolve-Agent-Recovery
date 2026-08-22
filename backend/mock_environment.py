class MockEnvironment:
    """
    Simulates a small infrastructure environment.

    This is intentionally deterministic for the hackathon demo.
    The environment receives recovery actions and changes its
    internal state accordingly.

    It does NOT perform verification yet.
    Verification will be added as a separate recovery step.
    """

    def __init__(self, initialState=None):
        defaultState = {
            "databaseRunning": False,
            "backendRunning": True,
            "apiHealthy": False,
            "cacheHealthy": True,
            "errorSignature": "unknown"
        }

        self.state = defaultState.copy()

        if initialState:
            self.state.update(initialState)

        self.executionLog = []

    def getState(self):
        """
        Returns a copy of the current environment state.
        """

        return self.state.copy()

    def executeAction(self, action):
        """
        Simulates execution of a recovery action.

        Returns:
        {
            "action": ...,
            "executionStatus": "success" / "failed",
            "message": ...,
            "state": ...
        }
        """

        if not action:
            return self._recordExecution(
                action,
                "failed",
                "No recovery action was provided."
            )

        normalizedAction = action.lower().strip()

        # Database recovery actions
        if (
            "restart database" in normalizedAction
            or "restart db" in normalizedAction
        ):
            self.state["databaseRunning"] = True

            return self._recordExecution(
                action,
                "success",
                "Database restart command executed successfully."
            )

        # Backend/API recovery actions
        if (
            "restart backend" in normalizedAction
            or "restart application" in normalizedAction
            or "restart api" in normalizedAction
            or "restart service" in normalizedAction
        ):
            self.state["backendRunning"] = True

            return self._recordExecution(
                action,
                "success",
                "Backend restart command executed successfully."
            )

        # Cache recovery actions
        if (
            "clear cache" in normalizedAction
            or "clear application cache" in normalizedAction
            or "invalidate cache" in normalizedAction
        ):
            self.state["cacheHealthy"] = True

            return self._recordExecution(
                action,
                "success",
                "Cache clear operation executed successfully."
            )

        # Credential recovery actions
        if (
            "rotate credential" in normalizedAction
            or "rotate credentials" in normalizedAction
            or "change credential" in normalizedAction
            or "change credentials" in normalizedAction
        ):
            self.state["errorSignature"] = ""

            return self._recordExecution(
                action,
                "success",
                "Credential recovery action executed successfully."
            )

        # Configuration actions
        if (
            "change config" in normalizedAction
            or "change configuration" in normalizedAction
            or "update config" in normalizedAction
            or "update configuration" in normalizedAction
        ):
            return self._recordExecution(
                action,
                "success",
                "Configuration update executed successfully."
            )

        # Unknown actions fail safely.
        return self._recordExecution(
            action,
            "failed",
            "MockEnvironment does not have a handler for this action."
        )

    def _recordExecution(self, action, executionStatus, message):
        """
        Records the action and returns the current environment state.
        """

        execution = {
            "action": action,
            "executionStatus": executionStatus,
            "message": message,
            "state": self.getState()
        }

        self.executionLog.append(execution)

        return execution

    def getExecutionLog(self):
        """
        Returns all actions executed in this environment.
        """

        return self.executionLog.copy()