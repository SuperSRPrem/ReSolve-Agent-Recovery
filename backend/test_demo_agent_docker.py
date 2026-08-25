import subprocess
import time

from backend.demo_agent import DemoAgent
from backend.docker_environment import DockerEnvironment


DATABASE_CONTAINER = "resolve-demo-db"


class FixedRecoveryMemory:
    """
    Deterministic recovery memory used only for this integration test.

    The purpose of this test is to validate:

        DemoAgent
            ->
        DockerEnvironment
            ->
        real infrastructure
            ->
        VerificationEngine

    Retrieval itself is tested separately.
    """

    def getRecovery(
        self,
        currentIncident,
        attemptHistory=None,
        limit=5
    ):
        strategy = {
            "incidentId": "historical-db-recovery",
            "title": (
                "PostgreSQL connection failure"
            ),
            "similarity": 0.95,
            "successRate": 0.90,
            "successRateIsConditioned": True,

            # Explicit approval lets us test the
            # human-governance path as well.
            "riskTier": "medium",
            "riskScore": 0.6,

            "score": 0.88,

            "action": (
                "Restart PostgreSQL database"
            ),

            "steps": [
                (
                    "Restart the approved PostgreSQL "
                    "service."
                ),
                (
                    "Verify database connectivity."
                ),
            ],

            "rootCause": (
                "PostgreSQL service unavailable."
            ),
        }

        return {
            "status": "MATCH_FOUND",
            "message": (
                "Recovery options found."
            ),
            "errorSignature": (
                "CONNECTION_REFUSED"
            ),
            "bestChoice": strategy,
            "choices": [
                strategy
            ],
        }


class TestFeedbackManager:
    """
    Prevents this integration test from modifying
    historical recovery statistics.
    """

    def addAttempt(self, *args, **kwargs):
        return None

    def recordResult(self, *args, **kwargs):
        return None


class TestRecoveryRecordManager:
    """
    Prevents the integration test from writing a recovery
    record to the project's persistent recovery history.

    Production DemoAgent still uses the real teammate-built
    RecoveryRecordManager.
    """

    def buildRecord(
        self,
        session,
        environmentState,
        status,
        reason=None
    ):
        return {
            "runId": session.runId,
            "status": status,
            "reason": reason,
            "environmentState": (
                environmentState
            ),
        }

    def generateDocumentation(
        self,
        recoveryRecord
    ):
        return (
            "Integration-test recovery record."
        )

    def saveRecord(
        self,
        recoveryRecord
    ):
        return None


def runDocker(*arguments):
    result = subprocess.run(
        [
            "docker",
            *arguments,
        ],
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
    print(
        "DEMO AGENT + REAL DOCKER "
        "CLOSED-LOOP TEST"
    )
    print("=" * 70)

    # ==================================================
    # CREATE REAL ENVIRONMENT
    # ==================================================

    environment = DockerEnvironment()

    runDocker(
        "start",
        DATABASE_CONTAINER
    )

    time.sleep(4)

    initialState = (
        environment.getState()
    )

    assert (
        initialState["databaseRunning"]
        is True
    )

    assert (
        initialState[
            "connectionPoolHealthy"
        ]
        is True
    )

    print(
        "PASS: demo environment starts healthy"
    )

    # ==================================================
    # CREATE REAL INCIDENT
    # ==================================================

    print()
    print(
        "Injecting real PostgreSQL outage..."
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
        failedState["databaseRunning"]
        is False
    )

    assert (
        failedState[
            "connectionPoolHealthy"
        ]
        is False
    )

    assert (
        failedState["apiHealthy"]
        is False
    )

    print(
        "PASS: real incident detected"
    )

    # ==================================================
    # BUILD RECOVERY AGENT
    # ==================================================

    agent = DemoAgent(
        environment=environment
    )

    # Keep this test focused on the real recovery loop.
    agent.memory = FixedRecoveryMemory()

    # Do not mutate project learning data.
    agent.feedback = (
        TestFeedbackManager()
    )

    # Do not persist test documentation.
    agent.recordManager = (
        TestRecoveryRecordManager()
    )

    incident = {
        "incidentId": (
            "docker-live-db-outage"
        ),
        "title": (
            "Production database connection refused"
        ),
        "description": (
            "Backend API is unable to connect "
            "to the PostgreSQL database. "
            "Database connection refused."
        ),
        "priority": "high",
        "status": "open",
    }

    # Represents the initial action that already failed
    # before ReSolve begins adaptive recovery.
    firstAction = (
        "Retry database connection"
    )

    # ==================================================
    # START RECOVERY
    # ==================================================

    print()
    print(
        "Starting ReSolve recovery..."
    )

    result = agent.startRecovery(
        incident,
        firstAction
    )

    print(
        "Initial recovery status:",
        result["status"]
    )

    # Medium-risk action must stop at approval gate.
    assert (
        result["status"]
        == "AWAITING_APPROVAL"
    )

    assert (
        result["strategy"]["action"]
        == "Restart PostgreSQL database"
    )

    assert (
        result["approval"]["approved"]
        is False
    )

    print(
        "PASS: ReSolve stopped at human "
        "approval boundary"
    )

    # Database should still be down because approval
    # has not yet been granted.
    preApprovalState = (
        environment.getState()
    )

    assert (
        preApprovalState[
            "databaseRunning"
        ]
        is False
    )

    print(
        "PASS: no infrastructure mutation "
        "occurred before approval"
    )

    # ==================================================
    # HUMAN APPROVAL
    # ==================================================

    print()
    print(
        "Approving recovery strategy..."
    )

    finalResult = (
        agent.approvePendingStrategy(
            result["session"]
        )
    )

    print(
        "Final status:",
        finalResult["status"]
    )

    # ==================================================
    # EXECUTION RESULT
    # ==================================================

    execution = (
        finalResult["execution"]
    )

    print()
    print(
        "Execution:",
        execution
    )

    assert (
        execution["executionStatus"]
        == "success"
    )

    assert (
        execution["capability"]
        == "restart_database"
    )

    print(
        "PASS: approved recovery action "
        "executed through DockerEnvironment"
    )

    # ==================================================
    # INDEPENDENT VERIFICATION
    # ==================================================

    verification = (
        finalResult["verification"]
    )

    print()
    print(
        "Verification:",
        verification
    )

    assert (
        verification["recovered"]
        is True
    )

    assert (
        verification["status"]
        == "VERIFIED"
    )

    print(
        "PASS: VerificationEngine independently "
        "verified real system state"
    )

    # ==================================================
    # FINAL SYSTEM STATE
    # ==================================================

    finalState = (
        environment.getState()
    )

    print()
    print(
        "Final environment state:",
        finalState
    )

    assert (
        finalState["databaseRunning"]
        is True
    )

    assert (
        finalState[
            "connectionPoolHealthy"
        ]
        is True
    )

    assert (
        finalState["apiHealthy"]
        is True
    )

    assert (
        finalResult["status"]
        == "RECOVERED"
    )

    print(
        "PASS: DemoAgent declared recovery "
        "only after verification passed"
    )

    print()
    print("=" * 70)
    print(
        "REAL CLOSED-LOOP RECOVERY PASSED"
    )
    print("=" * 70)
    print()

    print(
        "Failure -> strategy -> approval -> "
        "execution -> verification -> recovery"
    )
    print()


if __name__ == "__main__":
    main()