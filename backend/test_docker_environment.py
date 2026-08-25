import subprocess
import time

from backend.docker_environment import DockerEnvironment
from backend.recovery_environment import RecoveryEnvironment


DATABASE_CONTAINER = "resolve-demo-db"


def runDocker(*arguments):
    result = subprocess.run(
        ["docker", *arguments],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
        )

    return result.stdout.strip()


def main():
    print()
    print("=" * 70)
    print("DOCKER ENVIRONMENT INTEGRATION TEST")
    print("=" * 70)

    environment = DockerEnvironment()

    assert isinstance(
        environment,
        RecoveryEnvironment
    )

    print(
        "PASS: DockerEnvironment implements "
        "RecoveryEnvironment"
    )

    # --------------------------------------------------
    # Ensure starting healthy state
    # --------------------------------------------------

    runDocker(
        "start",
        DATABASE_CONTAINER
    )

    time.sleep(4)

    healthyState = (
        environment.getState()
    )

    print()
    print(
        "Healthy state:",
        healthyState
    )

    assert (
        healthyState[
            "databaseRunning"
        ]
        is True
    )

    assert (
        healthyState[
            "backendRunning"
        ]
        is True
    )

    assert (
        healthyState[
            "apiHealthy"
        ]
        is True
    )

    assert (
        healthyState[
            "connectionPoolHealthy"
        ]
        is True
    )

    print(
        "PASS: real healthy Docker state detected"
    )

    # --------------------------------------------------
    # Create real database outage
    # --------------------------------------------------

    print()
    print(
        "Stopping real PostgreSQL container..."
    )

    runDocker(
        "stop",
        DATABASE_CONTAINER
    )

    time.sleep(2)

    failedState = (
        environment.getState()
    )

    print(
        "Failure state:",
        failedState
    )

    assert (
        failedState[
            "databaseRunning"
        ]
        is False
    )

    assert (
        failedState[
            "apiHealthy"
        ]
        is False
    )

    assert (
        failedState[
            "connectionPoolHealthy"
        ]
        is False
    )

    print(
        "PASS: real database failure detected"
    )

    # --------------------------------------------------
    # Execute recovery through DockerEnvironment
    # --------------------------------------------------

    print()
    print(
        "Executing ReSolve Docker recovery..."
    )

    execution = (
        environment.executeAction(
            "Restart PostgreSQL database"
        )
    )

    print(
        "Execution:",
        execution
    )

    assert (
        execution[
            "executionStatus"
        ]
        == "success"
    )

    assert (
        execution[
            "capability"
        ]
        == "restart_database"
    )

    print(
        "PASS: approved Docker recovery executed"
    )

    # --------------------------------------------------
    # Observe actual post-recovery state
    # --------------------------------------------------

    recoveredState = (
        environment.getState()
    )

    print()
    print(
        "Recovered state:",
        recoveredState
    )

    assert (
        recoveredState[
            "databaseRunning"
        ]
        is True
    )

    assert (
        recoveredState[
            "apiHealthy"
        ]
        is True
    )

    assert (
        recoveredState[
            "connectionPoolHealthy"
        ]
        is True
    )

    print(
        "PASS: actual application state recovered"
    )

    # --------------------------------------------------
    # Arbitrary action must not become a shell command
    # --------------------------------------------------

    denied = (
        environment.executeAction(
            "rm -rf /"
        )
    )

    assert (
        denied[
            "executionStatus"
        ]
        == "failed"
    )

    assert (
        denied[
            "capability"
        ]
        is None
    )

    print(
        "PASS: arbitrary command rejected"
    )

    print()
    print("=" * 70)
    print(
        "REAL DOCKER RECOVERY TEST PASSED"
    )
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
