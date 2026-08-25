import os

from dotenv import load_dotenv

from backend.docker_environment import (
    DockerEnvironment,
)
from backend.freshservice_recovery_runner import (
    FreshserviceRecoveryRunner,
)


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv(".env")

TICKET_ID = 4


def main():
    print()
    print("=" * 76)
    print(
        "REAL FRESHSERVICE + LIVE LLM + DOCKER RECOVERY"
    )
    print("=" * 76)

    # ========================================================
    # 1. CONFIG CHECK
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

    print(
        "PASS: OpenAI configuration loaded"
    )

    print(
        "PASS: Freshservice configuration loaded"
    )

    # ========================================================
    # 2. REAL INFRASTRUCTURE
    # ========================================================

    environment = (
        DockerEnvironment()
    )

    print()
    print(
        "Current infrastructure state:"
    )

    currentState = (
        environment.getState()
    )

    print(
        currentState
    )

    # The demo intentionally begins with a real outage.
    if currentState.get(
        "databaseRunning"
    ):
        print()
        print(
            "ERROR: PostgreSQL is currently running."
        )

        print(
            "Create the outage first with:"
        )

        print()
        print(
            "    docker stop resolve-demo-db"
        )

        print()

        raise SystemExit(1)

    print()
    print(
        "PASS: real PostgreSQL outage exists"
    )

    # ========================================================
    # 3. CREATE FRESHSERVICE RECOVERY RUNNER
    # ========================================================

    runner = (
        FreshserviceRecoveryRunner(
            environment=environment
        )
    )

    # ========================================================
    # 4. LOAD REAL FRESHSERVICE INCIDENT
    # ========================================================

    print()
    print(
        f"Loading Freshservice Ticket #{TICKET_ID} "
        "and starting ReSolve..."
    )

    result = (
        runner.startRecovery(
            ticketId=TICKET_ID,
            firstAction=(
                "Retry database connection"
            ),
        )
    )

    # ========================================================
    # 5. RECOVERY DECISION
    # ========================================================

    print()
    print("-" * 76)
    print(
        "RECOVERY DECISION"
    )
    print("-" * 76)

    print(
        "Status:",
        result.get(
            "status"
        ),
    )

    print(
        "Freshservice Ticket:",
        result.get(
            "freshserviceTicketId"
        ),
    )

    print(
        "Incident:",
        result.get(
            "incident",
            {},
        ).get(
            "title"
        ),
    )

    strategy = result.get(
        "strategy",
        {},
    )

    print()
    print(
        "Selected action:",
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

    print(
        "Historical success rate:",
        strategy.get(
            "successRate"
        ),
    )

    print(
        "Evidence score:",
        strategy.get(
            "score"
        ),
    )

    # ========================================================
    # 6. LLM REASONING
    # ========================================================

    reasoning = strategy.get(
        "llmReasoning",
        {},
    )

    if reasoning:
        print()
        print("-" * 76)
        print(
            "LIVE LLM REASONING"
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
            "Selected index:",
            reasoning.get(
                "selectedIndex"
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

        verificationFocus = (
            reasoning.get(
                "verificationFocus",
                [],
            )
        )

        if verificationFocus:
            print()
            print(
                "Verification focus:"
            )

            for check in verificationFocus:
                print(
                    "-",
                    check,
                )

    # ========================================================
    # 7. APPROVAL BOUNDARY
    # ========================================================

    print()
    print("-" * 76)
    print(
        "APPROVAL BOUNDARY CHECK"
    )
    print("-" * 76)

    if (
        result.get(
            "status"
        )
        != "AWAITING_APPROVAL"
    ):
        print()
        print(
            "ReSolve did not reach the expected "
            "approval state."
        )

        print(
            "Actual status:",
            result.get(
                "status"
            ),
        )

        print(
            "Result:",
            result,
        )

        raise SystemExit(1)

    stateBeforeApproval = (
        environment.getState()
    )

    print(
        "Database running before approval:",
        stateBeforeApproval.get(
            "databaseRunning"
        ),
    )

    if stateBeforeApproval.get(
        "databaseRunning"
    ):
        raise RuntimeError(
            "Infrastructure changed before "
            "human approval."
        )

    print()
    print(
        "PASS: Freshservice incident loaded"
    )

    print(
        "PASS: trusted recovery strategy selected"
    )

    print(
        "PASS: human approval boundary enforced"
    )

    print(
        "PASS: no infrastructure mutation "
        "before approval"
    )

    # ========================================================
    # 8. HUMAN DECISION
    # ========================================================

    print()
    print("=" * 76)
    print(
        "RECOVERY IS PAUSED"
    )
    print("=" * 76)

    print()
    print(
        "Selected action:"
    )

    print(
        strategy.get(
            "action"
        )
    )

    print()
    print(
        "Risk tier:",
        strategy.get(
            "riskTier"
        ),
    )

    print()
    print(
        "Type APPROVE to execute the "
        "selected recovery."
    )

    print(
        "Type anything else to reject "
        "execution and exit."
    )

    print()

    decision = input(
        "Decision: "
    ).strip()

    # ========================================================
    # 9. REJECTION PATH
    # ========================================================

    if decision != "APPROVE":
        print()
        print(
            "Recovery was not approved."
        )

        print(
            "No recovery action will be executed."
        )

        print()
        print(
            "Current infrastructure state:"
        )

        print(
            environment.getState()
        )

        return

    # ========================================================
    # 10. HUMAN APPROVAL
    # ========================================================

    print()
    print(
        "Human approval received."
    )

    print(
        "Executing controlled recovery..."
    )

    finalResult = (
        runner.approvePendingStrategy(
            ticketId=TICKET_ID,
            session=result[
                "session"
            ],
        )
    )

    # ========================================================
    # 11. EXECUTION RESULT
    # ========================================================

    print()
    print("-" * 76)
    print(
        "CONTROLLED EXECUTION"
    )
    print("-" * 76)

    execution = (
        finalResult.get(
            "execution"
        )
    )

    print(
        execution
    )

    if execution:
        print()
        print(
            "Action:",
            execution.get(
                "action"
            ),
        )

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

        print(
            "Message:",
            execution.get(
                "message"
            ),
        )

    # ========================================================
    # 12. INDEPENDENT VERIFICATION
    # ========================================================

    print()
    print("-" * 76)
    print(
        "INDEPENDENT VERIFICATION"
    )
    print("-" * 76)

    verification = (
        finalResult.get(
            "verification"
        )
    )

    print(
        verification
    )

    if verification:
        print()
        print(
            "Verification status:",
            verification.get(
                "status"
            ),
        )

        print(
            "Recovered:",
            verification.get(
                "recovered"
            ),
        )

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
                f"(expected="
                f"{check.get('expected')}, "
                f"actual="
                f"{check.get('actual')})"
            )

    # ========================================================
    # 13. FINAL INFRASTRUCTURE STATE
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

    # ========================================================
    # 14. FINAL RECOVERY STATUS
    # ========================================================

    print()
    print("=" * 76)

    print(
        "FINAL RECOVERY STATUS:",
        finalResult.get(
            "status"
        ),
    )

    if (
        finalResult.get(
            "status"
        )
        == "RECOVERED"
    ):
        print()
        print(
            "PASS: controlled execution succeeded"
        )

        print(
            "PASS: independent verification passed"
        )

        print(
            "PASS: actual infrastructure recovered"
        )

        print(
            "PASS: Freshservice success lifecycle "
            "was triggered"
        )

        print()
        print(
            "REAL FRESHSERVICE CLOSED-LOOP "
            "RECOVERY PASSED"
        )

    else:
        print()
        print(
            "Recovery did not reach a verified "
            "RECOVERED state."
        )

        print(
            "Inspect execution and verification "
            "results above."
        )

    print("=" * 76)
    print()


if __name__ == "__main__":
    main()
