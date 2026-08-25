import os
import subprocess
import time

from dotenv import load_dotenv

from backend.demo_agent import DemoAgent
from backend.docker_environment import DockerEnvironment
from backend.llm_reasoner import LLMReasoner
from backend.reasoned_recovery_memory import (
    ReasonedRecoveryMemory,
)


load_dotenv(".env")


DATABASE_CONTAINER = "resolve-demo-db"


class TrustedEvidenceMemory:
    """
    Controlled evidence source for this integration test.

    This test is specifically validating:

        live LLM reasoning
        +
        DemoAgent
        +
        approval
        +
        real Docker execution
        +
        real verification

    Full historical retrieval is tested separately.

    Importantly, the candidate actions supplied here are
    trusted application data. The LLM still cannot create
    its own executable action.
    """

    def getRecovery(
        self,
        currentIncident,
        attemptHistory=None,
        limit=5,
    ):
        choices = [
            {
                "incidentId": "HIST-DB-001",

                "title": (
                    "PostgreSQL service unavailable"
                ),

                "action": (
                    "Restart PostgreSQL database"
                ),

                "similarity": 0.96,

                "successRate": 0.92,

                "successRateIsConditioned": True,

                "riskTier": "medium",

                "riskScore": 0.6,

                "score": 0.89,

                "rootCause": (
                    "PostgreSQL process stopped."
                ),

                "steps": [
                    (
                        "Restart the approved "
                        "PostgreSQL service."
                    ),
                    (
                        "Verify database connectivity."
                    ),
                ],
            },

            {
                "incidentId": "HIST-API-001",

                "title": (
                    "Backend worker failure"
                ),

                "action": (
                    "Restart backend service"
                ),

                "similarity": 0.54,

                "successRate": 0.71,

                "successRateIsConditioned": False,

                "riskTier": "low",

                "riskScore": 1.0,

                "score": 0.67,

                "rootCause": (
                    "Backend worker process failure."
                ),

                "steps": [
                    (
                        "Restart backend workers."
                    ),
                ],
            },
        ]

        return {
            "status": "MATCH_FOUND",

            "message": (
                "Evidence-backed recovery "
                "options found."
            ),

            "errorSignature": (
                "CONNECTION_REFUSED"
            ),

            "bestChoice": choices[0],

            "choices": choices,
        }


class TestFeedbackManager:
    """
    Prevent this integration test from mutating the
    project's historical success statistics.
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
    Avoid persisting integration-test recovery records.

    Production DemoAgent still uses the real
    RecoveryRecordManager.
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
            "environmentState": (
                environmentState
            ),
        }

    def generateDocumentation(
        self,
        recoveryRecord,
    ):
        return (
            "Live LLM Docker integration test."
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
    print("=" * 72)
    print(
        "LIVE LLM + REAL DOCKER CLOSED-LOOP RECOVERY"
    )
    print("=" * 72)

    # ==================================================
    # CHECK LIVE LLM CONFIGURATION
    # ==================================================

    if not os.getenv(
        "OPENAI_API_KEY"
    ):
        raise RuntimeError(
            "OPENAI_API_KEY is missing."
        )

    print(
        "PASS: OpenAI API configuration loaded"
    )

    # ==================================================
    # REAL INFRASTRUCTURE
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
            "apiHealthy"
        ]
        is True
    )

    print(
        "PASS: real environment starts healthy"
    )

    # ==================================================
    # INJECT REAL INCIDENT
    # ==================================================

    print()
    print(
        "Injecting PostgreSQL outage..."
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
    # LIVE AI REASONING LAYER
    # ==================================================

    reasoner = (
        LLMReasoner()
    )

    reasonedMemory = (
        ReasonedRecoveryMemory(
            baseMemory=(
                TrustedEvidenceMemory()
            ),
            reasoner=reasoner,
            environment=environment,
        )
    )

    # ==================================================
    # REAL DEMO AGENT
    # ==================================================

    agent = DemoAgent(
        environment=environment
    )

    agent.memory = (
        reasonedMemory
    )

    agent.feedback = (
        TestFeedbackManager()
    )

    agent.recordManager = (
        TestRecoveryRecordManager()
    )

    incident = {
        "incidentId": (
            "LIVE-AI-DOCKER-001"
        ),

        "title": (
            "Production PostgreSQL "
            "database connection refused"
        ),

        "description": (
            "Backend API remains running, "
            "but PostgreSQL is unavailable. "
            "Database-dependent requests are "
            "failing with connection errors."
        ),

        "priority": "high",

        "status": "open",
    }

    firstAction = (
        "Retry database connection"
    )

    # ==================================================
    # START RECOVERY
    # ==================================================

    print()
    print(
        "ReSolve is retrieving evidence "
        "and calling the live LLM..."
    )

    result = (
        agent.startRecovery(
            incident,
            firstAction,
        )
    )

    print()
    print(
        "Recovery status:",
        result["status"],
    )

    # ==================================================
    # PROVE LIVE LLM WAS USED
    # ==================================================

    reasoning = (
        reasonedMemory.lastReasoning
    )

    assert reasoning is not None

    print()
    print(
        "LLM used:",
        reasoning["llmUsed"],
    )

    print(
        "Decision:",
        reasoning["decision"],
    )

    print(
        "Confidence:",
        reasoning["confidence"],
    )

    print()
    print(
        "LLM incident summary:"
    )

    print(
        reasoning[
            "incidentSummary"
        ]
    )

    print()
    print(
        "LLM reasoning:"
    )

    print(
        reasoning[
            "reasoning"
        ]
    )

    print()
    print(
        "LLM risk notes:"
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

    assert (
        reasoning[
            "selectedChoice"
        ]["action"]
        == "Restart PostgreSQL database"
    )

    print()
    print(
        "PASS: live LLM selected the "
        "trusted database recovery strategy"
    )

    # ==================================================
    # HUMAN APPROVAL GATE
    # ==================================================

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
        strategy[
            "decisionSource"
        ]
        == "llm"
    )

    print(
        "PASS: medium-risk strategy stopped "
        "at human approval boundary"
    )

    # LLM was allowed to reason,
    # but infrastructure must still be unchanged.
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
        "PASS: LLM reasoning caused no "
        "infrastructure mutation"
    )

    # ==================================================
    # HUMAN APPROVES
    # ==================================================

    print()
    print(
        "Human approves recovery..."
    )

    finalResult = (
        agent.approvePendingStrategy(
            result["session"]
        )
    )

    print(
        "Final recovery status:",
        finalResult["status"],
    )

    # ==================================================
    # REAL CONTROLLED EXECUTION
    # ==================================================

    execution = (
        finalResult["execution"]
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
        "PASS: approved action executed "
        "through DockerEnvironment"
    )

    # ==================================================
    # INDEPENDENT VERIFICATION
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
        "verified real post-conditions"
    )

    # ==================================================
    # FINAL STATE
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
        finalResult["status"]
        == "RECOVERED"
    )

    print(
        "PASS: ReSolve declared recovery only "
        "after the real system recovered"
    )

    # ==================================================
    # FINAL SUMMARY
    # ==================================================

    print()
    print("=" * 72)
    print(
        "LIVE AI CLOSED-LOOP RECOVERY PASSED"
    )
    print("=" * 72)

    print()
    print(
        "Incident"
        " -> evidence"
        " -> live LLM"
        " -> approval"
        " -> controlled execution"
        " -> independent verification"
        " -> RECOVERED"
    )

    print()


if __name__ == "__main__":
    main()
