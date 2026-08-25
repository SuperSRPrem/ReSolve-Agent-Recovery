import os
import subprocess
import time

from dotenv import load_dotenv

from backend.demo_agent import DemoAgent
from backend.docker_environment import DockerEnvironment
from backend.reasoned_recovery_memory import (
    ReasonedRecoveryMemory,
)


load_dotenv(".env")


DATABASE_CONTAINER = "resolve-demo-db"


class TestFeedbackManager:
    """
    Prevent this integration test from changing
    historical outcome statistics.
    """

    def addAttempt(
        self,
        *args,
        **kwargs,
    ):
        return None

    def recordResult(
        self,
        *args,
        **kwargs,
    ):
        return None


class TestRecoveryRecordManager:
    """
    Prevent integration-test records from being written
    into the persistent recovery-record dataset.

    Production still uses the real RecoveryRecordManager.
    """

    def buildRecord(
        self,
        session,
        environmentState,
        status,
        reason=None,
    ):
        return {
            "runId": session.runId,
            "status": status,
            "reason": reason,
            "environmentState": environmentState,
        }

    def generateDocumentation(
        self,
        recoveryRecord,
    ):
        return (
            "Real-memory live-LLM Docker integration test."
        )

    def saveRecord(
        self,
        recoveryRecord,
    ):
        return None


def runDocker(
    *arguments,
):
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
    print("=" * 76)
    print(
        "REAL MEMORY + LIVE LLM + REAL DOCKER RECOVERY"
    )
    print("=" * 76)

    # ==================================================
    # 1. LIVE LLM CONFIGURATION
    # ==================================================

    if not os.getenv(
        "OPENAI_API_KEY"
    ):
        raise RuntimeError(
            "OPENAI_API_KEY is missing from .env"
        )

    print(
        "PASS: OpenAI API configuration loaded"
    )

    # ==================================================
    # 2. REAL DOCKER ENVIRONMENT
    # ==================================================

    environment = (
        DockerEnvironment()
    )

    runDocker(
        "start",
        DATABASE_CONTAINER,
    )

    time.sleep(4)

    healthyState = (
        environment.getState()
    )

    assert (
        healthyState[
            "databaseRunning"
        ]
        is True
    )

    assert (
        healthyState[
            "connectionPoolHealthy"
        ]
        is True
    )

    assert (
        healthyState[
            "apiHealthy"
        ]
        is True
    )

    print(
        "PASS: real environment starts healthy"
    )

    # ==================================================
    # 3. CREATE REAL OUTAGE
    # ==================================================

    print()
    print(
        "Injecting real PostgreSQL outage..."
    )

    runDocker(
        "stop",
        DATABASE_CONTAINER,
    )

    time.sleep(2)

    failedState = (
        environment.getState()
    )

    print(
        "Failure state:",
        failedState,
    )

    assert (
        failedState[
            "databaseRunning"
        ]
        is False
    )

    assert (
        failedState[
            "connectionPoolHealthy"
        ]
        is False
    )

    assert (
        failedState[
            "apiHealthy"
        ]
        is False
    )

    print(
        "PASS: real database outage detected"
    )

    # ==================================================
    # 4. REAL DEMO AGENT
    # ==================================================

    print()
    print(
        "Loading real historical recovery memory..."
    )

    agent = DemoAgent(
        environment=environment
    )

    # DemoAgent already created the project's real
    # RecoveryMemory. Reuse that exact instance instead
    # of constructing another embedding model.
    historicalMemory = (
        agent.memory
    )

    # Replace only the selection layer with our hybrid:
    #
    # real historical memory
    # +
    # real approved runbooks
    # +
    # live LLM reasoner
    agent.memory = (
        ReasonedRecoveryMemory(
            baseMemory=historicalMemory,
            environment=environment,
        )
    )

    # Avoid modifying persistent learning/test data.
    agent.feedback = (
        TestFeedbackManager()
    )

    agent.recordManager = (
        TestRecoveryRecordManager()
    )

    # ==================================================
    # 5. CURRENT INCIDENT
    # ==================================================

    incident = {
        "incidentId": (
            "REAL-MEMORY-LIVE-001"
        ),

        "title": (
            "Production PostgreSQL database "
            "connection refused"
        ),

        "description": (
            "The backend API process remains running, "
            "but the PostgreSQL database service is "
            "unavailable and refusing connections. "
            "Database-dependent API requests are failing. "
            "No recent connection-pool configuration "
            "change has been reported."
        ),

        "priority": "high",

        "status": "open",
    }

    firstAction = (
        "Retry database connection"
    )

    # ==================================================
    # 6. START ACTUAL RECOVERY
    # ==================================================

    print()
    print(
        "ReSolve is retrieving real evidence "
        "and calling the live LLM..."
    )

    result = (
        agent.startRecovery(
            incident,
            firstAction,
        )
    )

    reasonedMemory = (
        agent.memory
    )

    candidates = (
        reasonedMemory.lastCandidates
    )

    reasoning = (
        reasonedMemory.lastReasoning
    )

    # ==================================================
    # 7. SHOW REAL CANDIDATE EVIDENCE
    # ==================================================

    print()
    print("-" * 76)
    print("TRUSTED CANDIDATES PRESENTED TO LLM")
    print("-" * 76)

    for index, candidate in enumerate(
        candidates
    ):
        print()
        print(
            f"Candidate {index}:"
        )

        print(
            "  Source:",
            candidate.get(
                "sourceType"
            ),
        )

        print(
            "  ID:",
            candidate.get(
                "incidentId"
            ),
        )

        print(
            "  Action:",
            candidate.get(
                "action"
            ),
        )

        print(
            "  Evidence score:",
            round(
                candidate.get(
                    "score",
                    0,
                ),
                4,
            ),
        )

        print(
            "  Historical success:",
            candidate.get(
                "successRate"
            ),
        )

        print(
            "  Risk:",
            candidate.get(
                "riskTier"
            ),
        )

    # ==================================================
    # 8. PROVE LIVE LLM DECISION
    # ==================================================

    assert reasoning is not None

    print()
    print("-" * 76)
    print("LIVE LLM DECISION")
    print("-" * 76)

    print(
        "LLM used:",
        reasoning[
            "llmUsed"
        ],
    )

    print(
        "Decision:",
        reasoning[
            "decision"
        ],
    )

    print(
        "Selected index:",
        reasoning[
            "selectedIndex"
        ],
    )

    selectedChoice = (
        reasoning.get(
            "selectedChoice"
        )
    )

    print(
        "Selected action:",
        (
            selectedChoice.get(
                "action"
            )
            if selectedChoice
            else None
        ),
    )

    print(
        "Selected source:",
        (
            selectedChoice.get(
                "sourceType"
            )
            if selectedChoice
            else None
        ),
    )

    print(
        "Confidence:",
        reasoning[
            "confidence"
        ],
    )

    print()
    print(
        "Incident summary:"
    )

    print(
        reasoning[
            "incidentSummary"
        ]
    )

    print()
    print(
        "Reasoning:"
    )

    print(
        reasoning[
            "reasoning"
        ]
    )

    print()
    print(
        "Risk notes:"
    )

    print(
        reasoning[
            "riskNotes"
        ]
    )

    assert (
        reasoning[
            "llmUsed"
        ]
        is True
    )

    assert (
        reasoning[
            "decision"
        ]
        == "USE_CANDIDATE"
    )

    # This proves the model selected an existing
    # trusted candidate rather than generating one.
    assert (
        selectedChoice
        in candidates
    )

    print()
    print(
        "PASS: live LLM selected only "
        "from trusted evidence"
    )

    # For this actual observed outage, we expect the
    # approved database-service recovery runbook.
    assert (
        selectedChoice[
            "action"
        ]
        == "Restart PostgreSQL database"
    ), (
        "Live LLM selected a different trusted strategy. "
        "Do not change the code yet; inspect its reasoning."
    )

    assert (
        selectedChoice[
            "sourceType"
        ]
        == "approved-runbook"
    )

    assert (
        selectedChoice[
            "successRate"
        ]
        is None
    )

    print(
        "PASS: approved runbook was selected "
        "without fabricating historical success"
    )

    # ==================================================
    # 9. HUMAN APPROVAL BOUNDARY
    # ==================================================

    print()
    print(
        "Recovery status:",
        result[
            "status"
        ],
    )

    assert (
        result["status"]
        == "AWAITING_APPROVAL"
    )

    strategy = (
        result["strategy"]
    )

    assert (
        strategy["action"]
        == "Restart PostgreSQL database"
    )

    assert (
        strategy["riskTier"]
        == "medium"
    )

    print(
        "PASS: medium-risk real recovery "
        "stopped for human approval"
    )

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
        "PASS: reasoning caused no "
        "infrastructure mutation"
    )

    # ==================================================
    # 10. HUMAN APPROVAL
    # ==================================================

    print()
    print(
        "Human approves trusted recovery..."
    )

    finalResult = (
        agent.approvePendingStrategy(
            result["session"]
        )
    )

    print(
        "Final recovery status:",
        finalResult[
            "status"
        ],
    )

    # ==================================================
    # 11. CONTROLLED REAL EXECUTION
    # ==================================================

    execution = (
        finalResult[
            "execution"
        ]
    )

    print()
    print(
        "Execution:",
        execution,
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
        "PASS: trusted action executed through "
        "controlled DockerEnvironment"
    )

    # ==================================================
    # 12. INDEPENDENT VERIFICATION
    # ==================================================

    verification = (
        finalResult[
            "verification"
        ]
    )

    print()
    print(
        "Verification:",
        verification,
    )

    assert (
        verification[
            "status"
        ]
        == "VERIFIED"
    )

    assert (
        verification[
            "recovered"
        ]
        is True
    )

    checks = {
        check["name"]:
        check["passed"]

        for check
        in verification["checks"]
    }

    assert (
        checks[
            "databaseRunning"
        ]
        is True
    )

    assert (
        checks[
            "connectionPoolHealthy"
        ]
        is True
    )

    print(
        "PASS: VerificationEngine independently "
        "verified actual system recovery"
    )

    # ==================================================
    # 13. FINAL REAL STATE
    # ==================================================

    finalState = (
        environment.getState()
    )

    assert (
        finalState[
            "databaseRunning"
        ]
        is True
    )

    assert (
        finalState[
            "connectionPoolHealthy"
        ]
        is True
    )

    assert (
        finalState[
            "apiHealthy"
        ]
        is True
    )

    assert (
        finalResult[
            "status"
        ]
        == "RECOVERED"
    )

    print(
        "PASS: ReSolve declared RECOVERED "
        "only after post-conditions passed"
    )

    # ==================================================
    # SUMMARY
    # ==================================================

    print()
    print("=" * 76)
    print(
        "REAL EVIDENCE AI RECOVERY PASSED"
    )
    print("=" * 76)

    print()
    print(
        "Historical incidents + approved runbooks"
    )
    print(
        "        -> live LLM reasoning"
    )
    print(
        "        -> human approval"
    )
    print(
        "        -> controlled Docker execution"
    )
    print(
        "        -> independent verification"
    )
    print(
        "        -> RECOVERED"
    )
    print()


if __name__ == "__main__":
    main()
