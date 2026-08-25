import json
import shutil
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from backend.environment_state import createEnvironmentState
from backend.recovery_environment import RecoveryEnvironment


class DockerEnvironment(RecoveryEnvironment):
    """
    Real recovery environment backed by allowlisted Docker containers.

    ReSolve never executes arbitrary shell commands.

    Only explicitly supported capabilities can operate on explicitly
    configured containers.

    Current hackathon demo:

        resolve-demo-api
              |
              v
        resolve-demo-db

    Public RecoveryEnvironment contract:

        executeAction(action)
        getState()
    """

    def __init__(
        self,
        databaseContainer="resolve-demo-db",
        apiContainer="resolve-demo-api",
        healthUrl="http://localhost:8080/health",
        recoveryTimeout=15,
    ):
        self.databaseContainer = databaseContainer
        self.apiContainer = apiContainer
        self.healthUrl = healthUrl
        self.recoveryTimeout = recoveryTimeout

        self.executionLog = []

        self.dockerExecutable = shutil.which("docker")

        if self.dockerExecutable is None:
            raise RuntimeError(
                "Docker CLI was not found. "
                "Install Docker before using DockerEnvironment."
            )

    # ======================================================
    # RECOVERY ENVIRONMENT CONTRACT
    # ======================================================

    def getState(self):
        """
        Derives environment state from the real Docker demo system.

        Container state and application health are observed
        independently.

        A running API container does NOT automatically mean the
        application is healthy.
        """

        databaseRunning = self._isContainerRunning(
            self.databaseContainer
        )

        backendRunning = self._isContainerRunning(
            self.apiContainer
        )

        healthResult = self._readHealthEndpoint()

        healthPayload = healthResult.get(
            "payload",
            {}
        )

        apiHealthy = (
            healthResult.get("statusCode") == 200
            and healthPayload.get("healthy") is True
        )

        connectionPoolHealthy = (
            healthPayload.get("databaseHealthy") is True
        )

        return createEnvironmentState({
            "databaseRunning": databaseRunning,
            "backendRunning": backendRunning,
            "apiHealthy": apiHealthy,
            "connectionPoolHealthy": connectionPoolHealthy,
        })

    def executeAction(self, action):
        """
        Executes only recovery actions that map to an explicitly
        supported Docker capability.

        This compatibility resolver is intentionally small.

        The shared policy layer being implemented separately can
        later replace the action-to-capability mapping without
        changing Docker execution itself.
        """

        if not action:
            return self._recordExecution(
                action=action,
                capability=None,
                executionStatus="failed",
                message="No recovery action was provided.",
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
                    "DockerEnvironment capability."
                ),
            )

        if capability == "restart_database":
            return self._restartDatabase(
                action
            )

        if capability == "restart_backend":
            return self._restartBackend(
                action
            )

        return self._recordExecution(
            action=action,
            capability=capability,
            executionStatus="failed",
            message=(
                "Capability is recognized but has no "
                "Docker execution handler."
            ),
        )

    # ======================================================
    # TEMPORARY COMPATIBILITY RESOLVER
    # ======================================================

    def _resolveCapability(self, action):
        """
        Minimal compatibility mapping required by the current
        DemoAgent contract.

        This is NOT intended to become the final policy engine.
        """

        normalizedAction = (
            str(action)
            .lower()
            .strip()
        )

        if (
            "restart database" in normalizedAction
            or "restart db" in normalizedAction
            or "restart postgresql" in normalizedAction
            or "restart postgres" in normalizedAction
            or "start database" in normalizedAction
            or "start db" in normalizedAction
        ):
            return "restart_database"

        if (
            "restart backend" in normalizedAction
            or "restart api" in normalizedAction
            or "restart application" in normalizedAction
            or "restart service" in normalizedAction
        ):
            return "restart_backend"

        return None

    # ======================================================
    # APPROVED DOCKER CAPABILITIES
    # ======================================================

    def _restartDatabase(self, action):
        """
        Starts/restarts only the allowlisted demo database container.
        """

        beforeState = self.getState()

        running = self._isContainerRunning(
            self.databaseContainer
        )

        if running:
            command = [
                self.dockerExecutable,
                "restart",
                self.databaseContainer,
            ]

            operation = "restarted"

        else:
            command = [
                self.dockerExecutable,
                "start",
                self.databaseContainer,
            ]

            operation = "started"

        commandResult = self._runDockerCommand(
            command
        )

        if not commandResult["success"]:
            return self._recordExecution(
                action=action,
                capability="restart_database",
                executionStatus="failed",
                message=(
                    "Database Docker operation failed: "
                    + commandResult["message"]
                ),
                beforeState=beforeState,
            )

        self._waitForDatabaseRecovery()

        return self._recordExecution(
            action=action,
            capability="restart_database",
            executionStatus="success",
            message=(
                f"Approved database container "
                f"'{self.databaseContainer}' was {operation}."
            ),
            beforeState=beforeState,
        )

    def _restartBackend(self, action):
        """
        Starts/restarts only the allowlisted demo API container.
        """

        beforeState = self.getState()

        running = self._isContainerRunning(
            self.apiContainer
        )

        if running:
            command = [
                self.dockerExecutable,
                "restart",
                self.apiContainer,
            ]

            operation = "restarted"

        else:
            command = [
                self.dockerExecutable,
                "start",
                self.apiContainer,
            ]

            operation = "started"

        commandResult = self._runDockerCommand(
            command
        )

        if not commandResult["success"]:
            return self._recordExecution(
                action=action,
                capability="restart_backend",
                executionStatus="failed",
                message=(
                    "Backend Docker operation failed: "
                    + commandResult["message"]
                ),
                beforeState=beforeState,
            )

        self._waitForAPI()

        return self._recordExecution(
            action=action,
            capability="restart_backend",
            executionStatus="success",
            message=(
                f"Approved backend container "
                f"'{self.apiContainer}' was {operation}."
            ),
            beforeState=beforeState,
        )

    # ======================================================
    # REAL DOCKER OBSERVATION
    # ======================================================

    def _isContainerRunning(
        self,
        containerName
    ):
        command = [
            self.dockerExecutable,
            "inspect",
            "--format",
            "{{.State.Running}}",
            containerName,
        ]

        result = self._runDockerCommand(
            command
        )

        if not result["success"]:
            return False

        return (
            result["stdout"]
            .strip()
            .lower()
            == "true"
        )

    def _runDockerCommand(
        self,
        command
    ):
        """
        Executes only programmatically constructed Docker commands.

        shell=False is intentional.

        Arbitrary recovery text is never passed to a shell.
        """

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )

        except Exception as error:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(error),
                "message": str(error),
            }

        success = (
            result.returncode == 0
        )

        message = (
            result.stdout.strip()
            if success
            else result.stderr.strip()
        )

        return {
            "success": success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "message": message,
        }

    # ======================================================
    # REAL APPLICATION HEALTH OBSERVATION
    # ======================================================

    def _readHealthEndpoint(self):
        """
        Reads the actual API health endpoint.

        A 503 response is still useful because its JSON body tells
        us whether the database dependency is healthy.
        """

        try:
            with urlopen(
                self.healthUrl,
                timeout=3,
            ) as response:

                body = response.read().decode(
                    "utf-8"
                )

                return {
                    "statusCode": response.status,
                    "payload": self._parseJSON(
                        body
                    ),
                }

        except HTTPError as error:
            try:
                body = error.read().decode(
                    "utf-8"
                )

                payload = self._parseJSON(
                    body
                )

            except Exception:
                payload = {}

            return {
                "statusCode": error.code,
                "payload": payload,
            }

        except (
            URLError,
            TimeoutError,
            ConnectionError,
        ):
            return {
                "statusCode": None,
                "payload": {},
            }

        except Exception:
            return {
                "statusCode": None,
                "payload": {},
            }

    def _parseJSON(
        self,
        value
    ):
        try:
            return json.loads(
                value
            )

        except Exception:
            return {}

    # ======================================================
    # RECOVERY WAITING
    # ======================================================

    def _waitForDatabaseRecovery(self):
        """
        Gives PostgreSQL time to become actually usable.

        This does not declare the incident recovered.

        DemoAgent's VerificationEngine still independently decides
        whether the required post-conditions are satisfied.
        """

        deadline = (
            time.time()
            + self.recoveryTimeout
        )

        while time.time() < deadline:
            state = self.getState()

            if (
                state["databaseRunning"]
                and state[
                    "connectionPoolHealthy"
                ]
            ):
                return True

            time.sleep(1)

        return False

    def _waitForAPI(self):
        deadline = (
            time.time()
            + self.recoveryTimeout
        )

        while time.time() < deadline:
            if self._isContainerRunning(
                self.apiContainer
            ):
                health = (
                    self._readHealthEndpoint()
                )

                if (
                    health.get("statusCode")
                    in [200, 503]
                ):
                    return True

            time.sleep(1)

        return False

    # ======================================================
    # EXECUTION AUDIT
    # ======================================================

    def _recordExecution(
        self,
        action,
        capability,
        executionStatus,
        message,
        beforeState=None,
    ):
        execution = {
            "action": action,
            "capability": capability,
            "executionStatus": executionStatus,
            "message": message,
            "beforeState": (
                beforeState
                if beforeState is not None
                else self.getState()
            ),
            "state": self.getState(),
        }

        self.executionLog.append(
            execution
        )

        return execution

    def getExecutionLog(self):
        return list(
            self.executionLog
        )
