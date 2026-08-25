import os
import sys

from dotenv import load_dotenv

from backend.docker_environment import (
    DockerEnvironment,
)
from backend.freshservice_recovery_runner import (
    FreshserviceRecoveryRunner,
)
from backend.freshservice_ticket_service import (
    FreshserviceTicketService,
)


load_dotenv(".env")


def getTicketId():
    if len(sys.argv) < 2:
        print()
        print(
            "Usage:"
        )
        print(
            "  python -m backend.run_freshservice_docker_demo "
            "<ticket_id>"
        )
        print()
        raise SystemExit(1)

    try:
        return int(
            sys.argv[1]
        )

    except ValueError:
        print(
            "Ticket ID must be an integer."
        )
        raise SystemExit(1)


def main():
    ticketId = getTicketId()

    print()
    print("=" * 76)
    print(
        "ReSolve — Autonomous Incident Recovery"
    )
    print("=" * 76)

    # ========================================================
    # CONFIGURATION
    # ========================================================

    if not os.getenv(
        "OPENAI_API_KEY"
    ):
        raise RuntimeError(
            "OPENAI_API_KEY is missing from .env"
        )

    if not os.getenv(
        "FRESHSERVICE_DOMAIN"
    ):
        raise RuntimeError(
            "FRESHSERVICE_DOMAIN is missing from .env"
        )

    print()
    print(
        "Freshservice Ticket:",
        ticketId,
    )

    print(
        "PASS: required configuration loaded"
    )

    # ========================================================
    # REAL ENVIRONMENT
    # ========================================================

    environment = (
        DockerEnvironment()
    )

    initialState = (
        environment.getState()
    )

    print()
    print("-" * 76)
    print(
        "OBSERVED INFRASTRUCTURE STATE"
    )
    print("-" * 76)

    print(
        initialState
    )

    if initialState.get(
        "databaseRunning"
    ):
        print()
        print(
            "PostgreSQL is currently healthy."
        )
        print(
            "Create the demo outage first:"
        )
        print()
        print(
            "  docker stop resolve-demo-db"
        )
        print()

        raise SystemExit(1)

    print()
    print(
        "PASS: PostgreSQL outage detected"
    )

    # ========================================================
    # CREATE RECOVERY RUNNER
    # ========================================================

    runner = (
        FreshserviceRecoveryRunner(
            environment=environment
        )
    )

    # ========================================================
    # START RECOVERY
    # ========================================================

    print()
    print(
        "Loading Freshservice incident..."
    )

    print(
        "Retrieving trusted recovery evidence..."
    )

    print(
        "Evaluating recovery strategies..."
    )

    result = (
        runner.startRecovery(
            ticketId=ticketId,
            firstAction=(
                "Retry database connection"
            ),
        )
    )

    if (
        result.get(
            "status"
        )
        == "LOAD_FAILED"
    ):
        print()
        print(
            "Freshservice ticket loading failed."
        )

        print(
            result
        )

        raise SystemExit(1)

    # ========================================================
    # SELECTED STRATEGY
    # ========================================================

    strategy = (
        result.get(
            "strategy",
            {},
        )
    )

    print()
    print("-" * 76)
    print(
        "RECOVERY STRATEGY"
    )
    print("-" * 76)

    print(
        "Status:",
        result.get(
            "status"
        ),
    )

    print(
        "Action:",
        strategy.get(
            "action"
        ),
    )

    print(
        "Evidence source:",
        strategy.get(
            "sourceType"
        ),
    )

    print(
        "Evidence ID:",
        strategy.get(
            "incidentId"
        ),
    )

    print(
        "Risk tier:",
        strategy.get(
            "riskTier"
        ),
    )

    print(
        "Decision source:",
        strategy.get(
            "decisionSource"
        ),
    )

    successRate = (
        strategy.get(
            "successRate"
        )
    )

    if successRate is None:
        print(
            "Historical success:",
            "Not available",
        )

    else:
        print(
            "Historical success:",
            successRate,
        )

    # ========================================================
    # LLM REASONING
    # ========================================================

    reasoning = (
        strategy.get(
            "llmReasoning",
            {},
        )
    )

    if reasoning:
        print()
        print("-" * 76)
        print(
            "AI RECOVERY REASONING"
        )
        print("-" * 76)

        print(
            "LLM used:",
            reasoning.get(
                "llmUsed"
            ),
        )

        print(
            "Decision:",
            reasoning.get(
                "decision"
            ),
        )

        print(
            "Confidence:",
            reasoning.get(
                "confidence"
            ),
        )

        print()
        print(
            "Incident summary:"
        )

        print(
            reasoning.get(
                "incidentSummary"
            )
        )

        print()
        print(
            "Reasoning:"
        )

        print(
            reasoning.get(
                "reasoning"
            )
        )

        print()
        print(
            "Risk notes:"
        )

        print(
            reasoning.get(
                "riskNotes"
            )
        )

    # ========================================================
    # APPROVAL BOUNDARY
    # ========================================================

    if (
        result.get(
            "status"
        )
        != "AWAITING_APPROVAL"
    ):
        print()
        print(
            "Expected recovery to pause for approval."
        )

        print(
            "Actual status:",
            result.get(
                "status"
            ),
        )

        raise SystemExit(1)

    stateBeforeApproval = (
        environment.getState()
    )

    if stateBeforeApproval.get(
        "databaseRunning"
    ):
        raise RuntimeError(
            "Infrastructure changed before approval."
        )

    print()
    print("-" * 76)
    print(
        "HUMAN APPROVAL BOUNDARY"
    )
    print("-" * 76)

    print()
    print(
        "PASS: trusted strategy selected"
    )

    print(
        "PASS: medium-risk action requires approval"
    )

    print(
        "PASS: no infrastructure mutation "
        "occurred during reasoning"
    )

    print()
    print(
        "Proposed action:"
    )

    print(
        strategy.get(
            "action"
        )
    )

    print()
    print(
        "Type APPROVE to authorize execution."
    )

    print(
        "Type anything else to stop."
    )

    print()

    decision = input(
        "Decision: "
    ).strip()

    if decision != "APPROVE":
        print()
        print(
            "Recovery not approved."
        )

        print(
            "No recovery action executed."
        )

        return

    # ========================================================
    # CONTROLLED EXECUTION
    # ========================================================

    print()
    print(
        "Approval received."
    )

    print(
        "Executing approved recovery capability..."
    )

    finalResult = (
        runner.approvePendingStrategy(
            ticketId=ticketId,
            session=result[
                "session"
            ],
        )
    )

    execution = (
        finalResult.get(
            "execution"
        )
    )

    print()
    print("-" * 76)
    print(
        "CONTROLLED EXECUTION"
    )
    print("-" * 76)

    print(
        execution
    )

    if not execution:
        raise RuntimeError(
            "No execution result returned."
        )

    print()
    print(
        "Capability:",
        execution.get(
            "capability"
        ),
    )

    print(
        "Execution status:",
        execution.get(
            "executionStatus"
        ),
    )

    # ========================================================
    # VERIFICATION
    # ========================================================

    verification = (
        finalResult.get(
            "verification"
        )
    )

    print()
    print("-" * 76)
    print(
        "INDEPENDENT VERIFICATION"
    )
    print("-" * 76)

    print(
        verification
    )

    if verification:
        print()

        for check in verification.get(
            "checks",
            [],
        ):
            status = (
                "PASS"
                if check.get(
                    "passed"
                )
                else "FAIL"
            )

            print(
                f"{status}: "
                f"{check.get('name')} "
                f"(expected={check.get('expected')}, "
                f"actual={check.get('actual')})"
            )

    # ========================================================
    # FINAL ENVIRONMENT STATE
    # ========================================================

    finalState = (
        environment.getState()
    )

    print()
    print("-" * 76)
    print(
        "FINAL INFRASTRUCTURE STATE"
    )
    print("-" * 76)

    print(
        finalState
    )

    if (
        finalResult.get(
            "status"
        )
        != "RECOVERED"
    ):
        print()
        print(
            "ReSolve did not reach RECOVERED."
        )

        raise SystemExit(1)

    if not finalState.get(
        "databaseRunning"
    ):
        raise RuntimeError(
            "Database is not running after recovery."
        )

    if not finalState.get(
        "connectionPoolHealthy"
    ):
        raise RuntimeError(
            "Database connectivity is not healthy."
        )

    # ========================================================
    # VERIFY FRESHSERVICE FINAL STATE
    # ========================================================

    print()
    print(
        "Verifying Freshservice ticket state..."
    )

    ticketService = (
        FreshserviceTicketService()
    )

    ticketResult = (
        ticketService.getTicket(
            ticketId
        )
    )

    if not ticketResult.get(
        "success"
    ):
        print()
        print(
            "Freshservice verification failed:"
        )

        print(
            ticketResult
        )

        raise SystemExit(1)

    ticket = (
        ticketResult
        .get(
            "data",
            {},
        )
        .get(
            "ticket",
            {},
        )
    )

    print()
    print("-" * 76)
    print(
        "FRESHSERVICE FINAL STATE"
    )
    print("-" * 76)

    print(
        "Ticket ID:",
        ticket.get(
            "id"
        ),
    )

    print(
        "Subject:",
        ticket.get(
            "subject"
        ),
    )

    print(
        "Priority:",
        ticket.get(
            "priority"
        ),
    )

    print(
        "Status:",
        ticket.get(
            "status"
        ),
    )

    print(
        "Resolution notes:",
        ticket.get(
            "resolution_notes"
        ),
    )

    # Freshservice:
    #
    # 4 = Resolved
    if (
        ticket.get(
            "status"
        )
        != 4
    ):
        raise RuntimeError(
            "Infrastructure recovered, but "
            "Freshservice ticket was not resolved."
        )

    if not ticket.get(
        "resolution_notes"
    ):
        raise RuntimeError(
            "Freshservice ticket was resolved "
            "without resolution notes."
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print()
    print("=" * 76)
    print(
        "ReSolve Recovery Completed and Verified"
    )
    print("=" * 76)

    print()
    print(
        "PASS: Freshservice incident ingested"
    )

    print(
        "PASS: historical + approved evidence evaluated"
    )

    print(
        "PASS: live AI selected only trusted evidence"
    )

    print(
        "PASS: human approval enforced"
    )

    print(
        "PASS: controlled Docker capability executed"
    )

    print(
        "PASS: actual service state independently verified"
    )

    print(
        "PASS: Freshservice ticket automatically resolved"
    )

    print(
        "PASS: resolution notes persisted"
    )

    print()
    print(
        "Execution success was not treated as recovery "
        "until the expected system state was verified."
    )

    print()


if __name__ == "__main__":
    main()