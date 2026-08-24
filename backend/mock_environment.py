from backend.recovery_environment import RecoveryEnvironment
from backend.environment_state import (
    createEnvironmentState,
    copyEnvironmentState,
)


class MockEnvironment(RecoveryEnvironment):
    """
    Simulates a small infrastructure environment.

    Recovery actions are not executed directly based on arbitrary text.
    Instead, the action text is mapped to an approved capability.

    MockEnvironment owns and changes its infrastructure state.

    The recovery engine only receives state snapshots through getState().
    It does not directly own or mutate infrastructure state.

    This prepares the same contract for future Docker/API environments.
    """

    def __init__(self, initialState=None):
        self.state = createEnvironmentState(
            initialState
        )

        self.executionLog = []

        self.actionHandlers = {
            "restart_database": self._restartDatabase,
            "restart_backend": self._restartBackend,
            "clear_cache": self._clearCache,
            "restore_connection_pool": self._restoreConnectionPool,
            "replace_unhealthy_replica": self._replaceUnhealthyReplica,
            "restore_configuration": self._restoreConfiguration,
            "recover_credentials": self._recoverCredentials,
            "restart_api_workers": self._restartApiWorkers
        }

    def getState(self):
        """
        Returns an immutable-style snapshot of the current
        environment state.

        Callers receive a copy and cannot directly mutate the
        environment's internal state.
        """

        return copyEnvironmentState(
            self.state
        )

    def executeAction(self, action):
        """
        Executes an action only if it can be mapped to an approved
        capability.

        Returns:

        {
            "action": ...,
            "capability": ...,
            "executionStatus": "success" / "failed",
            "message": ...,
            "state": ...
        }
        """

        if not action:
            return self._recordExecution(
                action=action,
                capability=None,
                executionStatus="failed",
                message="No recovery action was provided."
            )

        capability = self._resolveCapability(
            action
        )

        if capability is None:
            return self._recordExecution(
                action=action,
                capability=None,
                executionStatus="failed",
                message=(
                    "Action is not mapped to an approved "
                    "MockEnvironment capability."
                )
            )

        handler = self.actionHandlers.get(
            capability
        )

        if handler is None:
            return self._recordExecution(
                action=action,
                capability=capability,
                executionStatus="failed",
                message=(
                    "Approved capability exists but does not "
                    "have an execution handler."
                )
            )

        message = handler()

        return self._recordExecution(
            action=action,
            capability=capability,
            executionStatus="success",
            message=message
        )

    def _resolveCapability(self, action):
        """
        Maps natural-language recovery strategies to approved,
        controlled capabilities.

        This logic is intentionally preserved for now.

        The separate policy layer is being handled independently
        and can replace this later without affecting the environment
        interface.
        """

        normalizedAction = action.lower().strip()

        # --------------------------------------------------
        # Database restart
        # --------------------------------------------------

        if (
            "restart database" in normalizedAction
            or "restart db" in normalizedAction
        ):
            return "restart_database"

        # --------------------------------------------------
        # Connection pool recovery
        # --------------------------------------------------

        if (
            "connection pool" in normalizedAction
            or "pool configuration" in normalizedAction
            or "restore previous connection" in normalizedAction
        ):
            return "restore_connection_pool"

        # --------------------------------------------------
        # Unhealthy replica replacement
        # --------------------------------------------------

        if (
            "unhealthy replica" in normalizedAction
            or "provision replacement" in normalizedAction
            or "replace replica" in normalizedAction
            or "remove replica" in normalizedAction
        ):
            return "replace_unhealthy_replica"

        # --------------------------------------------------
        # Backend/API workers
        # --------------------------------------------------

        if (
            "restart api worker" in normalizedAction
            or "restart unhealthy api worker" in normalizedAction
            or "restart backend" in normalizedAction
            or "restart application" in normalizedAction
            or "restart service" in normalizedAction
        ):
            return "restart_api_workers"

        # --------------------------------------------------
        # Generic backend restart
        # --------------------------------------------------

        if (
            "restart api" in normalizedAction
            or "restart backend service" in normalizedAction
        ):
            return "restart_backend"

        # --------------------------------------------------
        # Cache
        # --------------------------------------------------

        if (
            "clear cache" in normalizedAction
            or "clear application cache" in normalizedAction
            or "invalidate cache" in normalizedAction
        ):
            return "clear_cache"

        # --------------------------------------------------
        # Credentials
        # --------------------------------------------------

        if (
            "rotate credential" in normalizedAction
            or "rotate credentials" in normalizedAction
            or "change credential" in normalizedAction
            or "change credentials" in normalizedAction
            or "restore credentials" in normalizedAction
        ):
            return "recover_credentials"

        # --------------------------------------------------
        # Configuration recovery
        # --------------------------------------------------

        if (
            "restore configuration" in normalizedAction
            or "restore previous configuration" in normalizedAction
            or "rollback configuration" in normalizedAction
            or "revert configuration" in normalizedAction
            or "update configuration" in normalizedAction
            or "update config" in normalizedAction
            or "change configuration" in normalizedAction
            or "change config" in normalizedAction
        ):
            return "restore_configuration"

        return None

    # ======================================================
    # APPROVED ACTION HANDLERS
    # ======================================================

    def _restartDatabase(self):
        self.state["databaseRunning"] = True

        return (
            "Database restart capability executed successfully."
        )

    def _restartBackend(self):
        self.state["backendRunning"] = True

        return (
            "Backend restart capability executed successfully."
        )

    def _clearCache(self):
        self.state["cacheHealthy"] = True

        return (
            "Cache recovery capability executed successfully."
        )

    def _restoreConnectionPool(self):
        """
        Simulates restoring the last known working database
        connection pool configuration.
        """

        self.state["connectionPoolHealthy"] = True
        self.state["databaseRunning"] = True

        return (
            "Previous connection pool configuration restored "
            "successfully."
        )

    def _replaceUnhealthyReplica(self):
        """
        Simulates removing an unhealthy replica and replacing it
        with a healthy one.
        """

        self.state["replicaHealthy"] = True
        self.state["databaseRunning"] = True

        return (
            "Unhealthy replica replaced successfully."
        )

    def _restoreConfiguration(self):
        """
        Simulates restoring a known-good configuration.
        """

        self.state["configurationHealthy"] = True

        return (
            "Known-good configuration restored successfully."
        )

    def _recoverCredentials(self):
        self.state["credentialsHealthy"] = True
        self.state["errorSignature"] = ""

        return (
            "Credential recovery capability executed successfully."
        )

    def _restartApiWorkers(self):
        self.state["backendRunning"] = True
        self.state["apiHealthy"] = True

        return (
            "API worker restart capability executed successfully."
        )

    # ======================================================
    # EXECUTION LOGGING
    # ======================================================

    def _recordExecution(
        self,
        action,
        capability,
        executionStatus,
        message
    ):
        """
        Records the action, capability and resulting state snapshot.
        """

        execution = {
            "action": action,
            "capability": capability,
            "executionStatus": executionStatus,
            "message": message,
            "state": self.getState()
        }

        self.executionLog.append(
            execution
        )

        return execution

    def getExecutionLog(self):
        """
        Returns all actions executed in this environment.
        """

        return self.executionLog.copy()