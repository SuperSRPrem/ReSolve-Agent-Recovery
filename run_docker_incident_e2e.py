import os
import subprocess
import time

from dotenv import load_dotenv

from backend.docker_environment import DockerEnvironment
from backend.freshservice_recovery_runner import FreshserviceRecoveryRunner
from backend.freshservice_ticket_service import FreshserviceTicketService


load_dotenv(".env")


DATABASE_CONTAINER = "resolve-demo-db"
REQUESTER_SOURCE_TICKET = 4


def heading(text):
    print()
    print("=" * 78)
    print(text)
    print("=" * 78)


def section(text):
    print()
    print("-" * 78)
    print(text)
    print("-" * 78)


def get_requester_id(service):
    configured = os.getenv(
        "FRESHSERVICE_REQUESTER_ID"
    )

    if configured:
        return int(configured)

    result = service.getTicket(
        REQUESTER_SOURCE_TICKET
    )

    if not result.get("success"):
        raise RuntimeError(
            "Unable to resolve a Freshservice requester."
        )

    ticket = (
        result
        .get("data", {})
        .get("ticket", {})
    )

    requester_id = ticket.get(
        "requester_id"
    )

    if not requester_id:
        raise RuntimeError(
            "Requester ID could not be resolved."
        )

    return requester_id


def stop_database():
    section(
        "INJECTING REAL DOCKER FAILURE"
    )

    result = subprocess.run(
        [
            "docker",
            "stop",
            DATABASE_CONTAINER,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or "Unable to stop PostgreSQL container."
        )

    print(
        "PostgreSQL container stopped."
    )


def wait_for_outage(
    environment,
    timeout=15,
):
    deadline = (
        time.time()
        + timeout
    )

    while time.time() < deadline:
        state = environment.getState()

        if (
            not state.get(
                "databaseRunning"
            )
            and not state.get(
                "apiHealthy"
            )
        ):
            return state

        time.sleep(1)

    raise RuntimeError(
        "Expected Docker outage was not detected."
    )


def create_freshservice_incident(
    service,
):
    section(
        "CREATING FRESHSERVICE INCIDENT FROM DETECTED FAILURE"
    )

    requester_id = get_requester_id(
        service
    )

    result = service.createTicket(
        subject=(
            "Production PostgreSQL database unavailable"
        ),
        description=(
            "ReSolve infrastructure monitoring detected "
            "that the production PostgreSQL database is "
            "not running. The backend service remains "
            "available, but database-dependent requests "
            "are failing and the API health check is "
            "degraded. Database connectivity has been "
            "lost and automated recovery analysis is "
            "required."
        ),
        source=2,
        priority=1,
        status=2,
        requesterId=requester_id,
    )

    if not result.get(
        "success"
    ):
        raise RuntimeError(
            "Freshservice ticket creation failed: "
            f"{result.get('error')}"
        )

    ticket = (
        result
        .get("data", {})
        .get("ticket", {})
    )

    ticket_id = ticket.get(
        "id"
    )

    if ticket_id is None:
        raise RuntimeError(
            "Freshservice ticket was created "
            "but no ticket ID was returned."
        )

    # Freshservice MCP create_ticket currently does not
    # reliably preserve high/urgent priorities.
    priority_result = service.updateTicket(
        ticket_id,
        {
            "priority": 4,
        },
    )

    if not priority_result.get(
        "success"
    ):
        raise RuntimeError(
            "Ticket was created but could not be "
            "updated to Urgent priority."
        )

    print(
        f"Freshservice Ticket #{ticket_id} created."
    )

    print(
        "Priority updated to URGENT."
    )

    return ticket_id


def run_recovery(
    ticket_id,
    environment,
):
    section(
        "STARTING RESOLVE RECOVERY"
    )

    runner = FreshserviceRecoveryRunner(
        environment=environment
    )

    result = runner.startRecovery(
        ticketId=ticket_id,
        firstAction=(
            "Retry database connection"
        ),
    )

    print(
        "Recovery status:",
        result.get("status"),
    )

    strategy = result.get(
        "strategy",
        {},
    )

    if strategy:
        print()
        print(
            "Selected action:",
            strategy.get("action"),
        )

        print(
            "Evidence source:",
            strategy.get("sourceType"),
        )

        print(
            "Evidence ID:",
            strategy.get("incidentId"),
        )

        print(
            "Risk:",
            strategy.get("riskTier"),
        )

        reasoning = strategy.get(
            "llmReasoning",
            {},
        )

        if reasoning:
            print(
                "Decision source:",
                strategy.get("decisionSource"),
            )

            print(
                "Confidence:",
                reasoning.get("confidence"),
            )

            print()
            print(
                "Reasoning:"
            )

            print(
                reasoning.get("reasoning")
            )

    if result.get(
        "status"
    ) != "AWAITING_APPROVAL":
        raise RuntimeError(
            "Expected recovery to stop at "
            "human approval boundary."
        )

    section(
        "HUMAN APPROVAL REQUIRED"
    )

    state_before = environment.getState()

    print(
        "Database running before approval:",
        state_before.get(
            "databaseRunning"
        ),
    )

    if state_before.get(
        "databaseRunning"
    ):
        raise RuntimeError(
            "Database changed before approval."
        )

    print()
    print(
        "Type APPROVE to authorize "
        "the selected recovery action."
    )

    decision = input(
        "Decision: "
    ).strip()

    if decision != "APPROVE":
        print(
            "Recovery stopped by human operator."
        )

        return None

    section(
        "EXECUTING APPROVED RECOVERY"
    )

    final_result = (
        runner.approvePendingStrategy(
            ticketId=ticket_id,
            session=result["session"],
        )
    )

    return final_result


def verify_freshservice(
    service,
    ticket_id,
):
    section(
        "VERIFYING FRESHSERVICE FINAL STATE"
    )

    result = service.getTicket(
        ticket_id
    )

    if not result.get(
        "success"
    ):
        raise RuntimeError(
            "Unable to fetch final Freshservice state."
        )

    ticket = (
        result
        .get("data", {})
        .get("ticket", {})
    )

    print(
        "Ticket ID:",
        ticket.get("id"),
    )

    print(
        "Subject:",
        ticket.get("subject"),
    )

    print(
        "Priority:",
        ticket.get("priority"),
    )

    print(
        "Status:",
        ticket.get("status"),
    )

    print(
        "Resolution notes:",
        ticket.get(
            "resolution_notes"
        ),
    )

    if ticket.get(
        "status"
    ) != 4:
        raise RuntimeError(
            "Freshservice ticket was not resolved."
        )

    if not ticket.get(
        "resolution_notes"
    ):
        raise RuntimeError(
            "Resolution notes were not persisted."
        )

    return ticket


def main():
    heading(
        "ReSolve — Docker Failure to Verified Freshservice Recovery"
    )

    environment = DockerEnvironment()

    service = FreshserviceTicketService()

    # ========================================================
    # BASELINE
    # ========================================================

    section(
        "BASELINE INFRASTRUCTURE STATE"
    )

    baseline = environment.getState()

    print(
        baseline
    )

    if not baseline.get(
        "databaseRunning"
    ):
        raise RuntimeError(
            "PostgreSQL must be healthy before "
            "starting this demo."
        )

    if not baseline.get(
        "apiHealthy"
    ):
        raise RuntimeError(
            "API must be healthy before "
            "starting this demo."
        )

    print()
    print(
        "PASS: infrastructure starts healthy"
    )

    # ========================================================
    # REAL FAILURE
    # ========================================================

    stop_database()

    failed_state = wait_for_outage(
        environment
    )

    print()
    print(
        failed_state
    )

    print()
    print(
        "PASS: real PostgreSQL outage detected"
    )

    print(
        "PASS: API degradation detected"
    )

    # ========================================================
    # CREATE TICKET AUTOMATICALLY
    # ========================================================

    ticket_id = (
        create_freshservice_incident(
            service
        )
    )

    # ========================================================
    # RECOVERY
    # ========================================================

    final_result = run_recovery(
        ticket_id,
        environment,
    )

    if final_result is None:
        return

    section(
        "RECOVERY RESULT"
    )

    print(
        "Status:",
        final_result.get(
            "status"
        ),
    )

    print()
    print(
        "Execution:"
    )

    print(
        final_result.get(
            "execution"
        )
    )

    print()
    print(
        "Verification:"
    )

    print(
        final_result.get(
            "verification"
        )
    )

    if final_result.get(
        "status"
    ) != "RECOVERED":
        raise RuntimeError(
            "ReSolve did not reach RECOVERED."
        )

    # ========================================================
    # REAL STATE VERIFICATION
    # ========================================================

    section(
        "REAL INFRASTRUCTURE FINAL STATE"
    )

    final_state = environment.getState()

    print(
        final_state
    )

    if not final_state.get(
        "databaseRunning"
    ):
        raise RuntimeError(
            "Database is still down."
        )

    if not final_state.get(
        "apiHealthy"
    ):
        raise RuntimeError(
            "API is still unhealthy."
        )

    if not final_state.get(
        "connectionPoolHealthy"
    ):
        raise RuntimeError(
            "Database connectivity "
            "was not restored."
        )

    print()
    print(
        "PASS: PostgreSQL is running"
    )

    print(
        "PASS: database connectivity restored"
    )

    print(
        "PASS: API health restored"
    )

    # ========================================================
    # FRESHSERVICE VERIFY
    # ========================================================

    verify_freshservice(
        service,
        ticket_id,
    )

    # ========================================================
    # DONE
    # ========================================================

    heading(
        "FULL END-TO-END RECOVERY VERIFIED"
    )

    print()
    print(
        f"Freshservice Ticket #{ticket_id}"
    )

    print()
    print(
        "Docker failure detected              PASS"
    )

    print(
        "Freshservice incident created        PASS"
    )

    print(
        "Trusted recovery evidence evaluated  PASS"
    )

    print(
        "AI recovery strategy selected        PASS"
    )

    print(
        "Human approval enforced              PASS"
    )

    print(
        "Real Docker recovery executed        PASS"
    )

    print(
        "Service state independently verified PASS"
    )

    print(
        "Freshservice ticket resolved         PASS"
    )

    print(
        "Resolution notes persisted           PASS"
    )

    print()
    print(
        "Execution success was not treated "
        "as recovery until the real service "
        "state was independently verified."
    )

    print()


if __name__ == "__main__":
    main()
