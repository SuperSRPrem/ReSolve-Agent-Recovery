from backend.recovery_environment import RecoveryEnvironment
from backend.environment_state import createEnvironmentState


class FakeAPIEnvironment(RecoveryEnvironment):
    """
    Minimal fake implementation used only to prove that
    RecoveryEnvironment supports non-mock infrastructure providers.

    A real APIEnvironment could later replace these hardcoded values
    with REST/API health checks.

    A DockerEnvironment could derive the same state from containers.
    """

    def __init__(self):
        self.state = createEnvironmentState({
            "databaseRunning": True,
            "backendRunning": True,
            "apiHealthy": True,
            "connectionPoolHealthy": True,
        })

        self.executionLog = []

    def getState(self):
        return self.state.copy()

    def executeAction(self, action):
        execution = {
            "action": action,
            "capability": "fake_api_action",
            "executionStatus": "success",
            "message": (
                "Fake API environment executed the requested action."
            ),
            "state": self.getState(),
        }

        self.executionLog.append(execution)

        return execution


def main():
    print()
    print("=" * 70)
    print("RECOVERY ENVIRONMENT CONTRACT TEST")
    print("=" * 70)

    # --------------------------------------------------
    # 1. Alternative implementation can satisfy contract
    # --------------------------------------------------

    environment = FakeAPIEnvironment()

    assert isinstance(
        environment,
        RecoveryEnvironment
    )

    print(
        "PASS: alternative environment implements "
        "RecoveryEnvironment"
    )

    # --------------------------------------------------
    # 2. Standard state format works
    # --------------------------------------------------

    state = environment.getState()

    assert state["databaseRunning"] is True
    assert state["backendRunning"] is True
    assert state["apiHealthy"] is True
    assert state["connectionPoolHealthy"] is True

    # Fields not explicitly supplied should still exist.
    assert "cacheHealthy" in state
    assert "replicaHealthy" in state
    assert "configurationHealthy" in state
    assert "credentialsHealthy" in state
    assert "errorSignature" in state

    print(
        "PASS: alternative environment exposes "
        "standard ReSolve state"
    )

    # --------------------------------------------------
    # 3. executeAction contract works
    # --------------------------------------------------

    execution = environment.executeAction(
        "Example recovery action"
    )

    assert execution[
        "executionStatus"
    ] == "success"

    assert "action" in execution
    assert "capability" in execution
    assert "message" in execution
    assert "state" in execution

    print(
        "PASS: alternative environment satisfies "
        "execution contract"
    )

    # --------------------------------------------------
    # 4. State snapshot remains independent
    # --------------------------------------------------

    snapshot = environment.getState()

    snapshot["apiHealthy"] = False

    assert (
        environment.getState()["apiHealthy"]
        is True
    )

    print(
        "PASS: environment state remains isolated"
    )

    print()
    print("=" * 70)
    print(
        "RECOVERY ENVIRONMENT IS READY "
        "FOR DOCKER/API IMPLEMENTATIONS"
    )
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()