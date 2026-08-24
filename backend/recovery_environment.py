from abc import ABC, abstractmethod


class RecoveryEnvironment(ABC):
    """
    Base interface for every infrastructure environment that ReSolve
    can execute recovery actions against.

    Implementations may include:

        - MockEnvironment
        - DockerEnvironment
        - APIEnvironment
        - KubernetesEnvironment
        - CloudEnvironment

    The recovery engine must depend only on this interface rather
    than knowing how the underlying infrastructure works.

    Required contract:

        executeAction(action)
            Execute a recovery action against the environment.

        getState()
            Return the current observable infrastructure state.

    This keeps the recovery engine independent from Docker,
    APIs, Kubernetes, or any other execution technology.
    """

    @abstractmethod
    def executeAction(self, action):
        """
        Execute a recovery action against the environment.

        Implementations should return a dictionary with a shape
        compatible with the current recovery engine:

        {
            "action": str,
            "capability": str | None,
            "executionStatus": "success" | "failed",
            "message": str,
            "state": dict
        }

        The method must not assume that execution success means
        recovery success.

        Recovery verification remains the responsibility of the
        VerificationEngine.
        """

        raise NotImplementedError

    @abstractmethod
    def getState(self):
        """
        Return the current observable state of the environment.

        Example:

        {
            "databaseRunning": True,
            "backendRunning": True,
            "apiHealthy": True,
            "connectionPoolHealthy": True
        }

        Mock environments may return simulated state.

        Real environments should derive this state from actual
        infrastructure probes.
        """

        raise NotImplementedError