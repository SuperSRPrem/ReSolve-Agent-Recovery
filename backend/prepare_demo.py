import os
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from dotenv import load_dotenv

from backend.docker_environment import DockerEnvironment
from backend.freshservice_ticket_service import FreshserviceTicketService


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

ENV_PATH = PROJECT_ROOT / ".env"

COMPOSE_FILE = (
    PROJECT_ROOT
    / "demo_service"
    / "docker-compose.yml"
)

DATABASE_CONTAINER = "resolve-demo-db"
API_CONTAINER = "resolve-demo-api"

HEALTH_URL = "http://localhost:8080/health"

# Existing Freshservice demo ticket. We only use it to obtain
# a valid requester ID if one is not explicitly configured.
REQUESTER_SOURCE_TICKET = 4

load_dotenv(
    dotenv_path=ENV_PATH
)


# ============================================================
# TERMINAL HELPERS
# ============================================================

def heading(text):
    print()
    print("=" * 76)
    print(text)
    print("=" * 76)


def section(text):
    print()
    print("-" * 76)
    print(text)
    print("-" * 76)


def passed(message):
    print(
        f"PASS: {message}"
    )


def failed(message):
    print(
        f"ERROR: {message}"
    )


# ============================================================
# CONFIGURATION CHECKS
# ============================================================

def checkConfiguration():
    section(
        "CONFIGURATION"
    )

    requiredVariables = [
        "OPENAI_API_KEY",
        "FRESHSERVICE_DOMAIN",
        "FRESHSERVICE_APIKEY",
    ]

    missing = [
        variable
        for variable in requiredVariables
        if not os.getenv(variable)
    ]

    if missing:
        failed(
            "Missing required environment variables:"
        )

        for variable in missing:
            print(
                f"  - {variable}"
            )

        raise SystemExit(1)

    # Never print the actual secrets.
    passed(
        "OpenAI API configuration found"
    )

    passed(
        "Freshservice configuration found"
    )

    if not COMPOSE_FILE.exists():
        failed(
            f"Docker Compose file not found: "
            f"{COMPOSE_FILE}"
        )

        raise SystemExit(1)

    passed(
        "Docker demo Compose file found"
    )


# ============================================================
# DOCKER HELPERS
# ============================================================

def runDocker(
    *arguments,
):
    result = subprocess.run(
        [
            "docker",
            *arguments,
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or result.stdout.strip()
            or (
                "Docker command failed: "
                + " ".join(arguments)
            )
        )

    return result.stdout.strip()


def startDemoEnvironment():
    section(
        "STARTING DEMO INFRASTRUCTURE"
    )

    print(
        "Starting PostgreSQL and API containers..."
    )

    result = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(COMPOSE_FILE),
            "up",
            "-d",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        failed(
            "Unable to start Docker demo environment."
        )

        print(
            result.stderr
        )

        raise SystemExit(1)

    passed(
        "Docker Compose stack started"
    )


def readHealthEndpoint():
    try:
        with urlopen(
            HEALTH_URL,
            timeout=3,
        ) as response:
            return {
                "statusCode": (
                    response.status
                ),
                "body": (
                    response
                    .read()
                    .decode(
                        "utf-8"
                    )
                ),
            }

    except HTTPError as error:
        return {
            "statusCode": (
                error.code
            ),
            "body": (
                error
                .read()
                .decode(
                    "utf-8"
                )
            ),
        }

    except URLError as error:
        return {
            "statusCode": None,
            "body": str(
                error
            ),
        }


def waitForHealthyEnvironment(
    timeoutSeconds=30,
):
    section(
        "VERIFYING HEALTHY BASELINE"
    )

    environment = (
        DockerEnvironment()
    )

    deadline = (
        time.time()
        + timeoutSeconds
    )

    while (
        time.time()
        < deadline
    ):
        state = (
            environment.getState()
        )

        if (
            state.get(
                "databaseRunning"
            )
            and state.get(
                "backendRunning"
            )
            and state.get(
                "apiHealthy"
            )
            and state.get(
                "connectionPoolHealthy"
            )
        ):
            print(
                state
            )

            passed(
                "PostgreSQL is healthy"
            )

            passed(
                "API is healthy"
            )

            passed(
                "Database connectivity is healthy"
            )

            return environment

        time.sleep(1)

    failed(
        "Demo environment did not become healthy "
        f"within {timeoutSeconds} seconds."
    )

    print(
        environment.getState()
    )

    raise SystemExit(1)


# ============================================================
# FRESHSERVICE HELPERS
# ============================================================

def getRequesterId(
    ticketService,
):
    """
    Prefer an explicitly configured requester.

    Otherwise use the requester attached to the existing
    Freshservice demo ticket.
    """

    configuredRequester = os.getenv(
        "FRESHSERVICE_REQUESTER_ID"
    )

    if configuredRequester:
        try:
            return int(
                configuredRequester
            )

        except ValueError:
            failed(
                "FRESHSERVICE_REQUESTER_ID must "
                "be an integer."
            )

            raise SystemExit(1)

    print(
        "Resolving Freshservice requester..."
    )

    result = (
        ticketService.getTicket(
            REQUESTER_SOURCE_TICKET
        )
    )

    if not result.get(
        "success"
    ):
        failed(
            "Unable to load requester from "
            f"Ticket #{REQUESTER_SOURCE_TICKET}."
        )

        print(
            result.get(
                "error"
            )
        )

        raise SystemExit(1)

    ticket = (
        result
        .get(
            "data",
            {}
        )
        .get(
            "ticket",
            {}
        )
    )

    requesterId = (
        ticket.get(
            "requester_id"
        )
    )

    if requesterId is None:
        failed(
            "No requester ID found on "
            f"Ticket #{REQUESTER_SOURCE_TICKET}."
        )

        raise SystemExit(1)

    passed(
        "Freshservice requester resolved"
    )

    return requesterId


def createDemoTicket(
    ticketService,
    requesterId,
):
    section(
        "CREATING FRESHSERVICE DEMO INCIDENT"
    )

    result = (
        ticketService.createTicket(
            subject=(
                "Production PostgreSQL "
                "database unavailable"
            ),
            description=(
                "The production backend is currently "
                "unable to establish a connection with "
                "the PostgreSQL database. "
                "The backend service remains running, "
                "but database-dependent requests are "
                "failing with connection errors. "
                "Initial checks show that the PostgreSQL "
                "endpoint is not responding. "
                "No recent connection-pool configuration "
                "change has been reported. "
                "Recovery assistance is required."
            ),
            source=2,
            priority=1,
            status=2,
            requesterId=requesterId,
        )
    )

    if not result.get(
        "success"
    ):
        failed(
            "Freshservice ticket creation failed."
        )

        print(
            result.get(
                "error"
            )
        )

        raise SystemExit(1)

    ticket = (
        result
        .get(
            "data",
            {}
        )
        .get(
            "ticket",
            {}
        )
    )

    ticketId = (
        ticket.get(
            "id"
        )
    )

    if ticketId is None:
        failed(
            "Freshservice created a ticket but "
            "ReSolve could not determine its ID."
        )

        print(
            result
        )

        raise SystemExit(1)

    passed(
        f"Freshservice Ticket #{ticketId} created"
    )

    return ticketId


def makeTicketUrgent(
    ticketService,
    ticketId,
):
    """
    The MCP create_ticket tool did not reliably preserve
    priority=4 in testing, while update_ticket does.

    Therefore set Urgent explicitly after creation.
    """

    print()
    print(
        "Setting incident priority to Urgent..."
    )

    result = (
        ticketService.updateTicket(
            ticketId,
            {
                "priority": 4,
            },
        )
    )

    if not result.get(
        "success"
    ):
        failed(
            "Unable to set Freshservice "
            "ticket priority."
        )

        print(
            result.get(
                "error"
            )
        )

        raise SystemExit(1)

    passed(
        "Freshservice incident priority set to Urgent"
    )


def verifyFreshserviceTicket(
    ticketService,
    ticketId,
):
    print()
    print(
        "Verifying Freshservice incident..."
    )

    result = (
        ticketService.getTicket(
            ticketId
        )
    )

    if not result.get(
        "success"
    ):
        failed(
            "Unable to verify Freshservice ticket."
        )

        raise SystemExit(1)

    ticket = (
        result
        .get(
            "data",
            {}
        )
        .get(
            "ticket",
            {}
        )
    )

    if (
        ticket.get(
            "status"
        )
        != 2
    ):
        failed(
            "Demo ticket is not Open."
        )

        raise SystemExit(1)

    if (
        ticket.get(
            "priority"
        )
        != 4
    ):
        failed(
            "Demo ticket is not Urgent."
        )

        raise SystemExit(1)

    passed(
        "Freshservice incident is Open"
    )

    passed(
        "Freshservice incident is Urgent"
    )

    return ticket


# ============================================================
# OUTAGE INJECTION
# ============================================================

def injectDatabaseOutage(
    environment,
):
    section(
        "INJECTING DEMO FAILURE"
    )

    print(
        "Stopping approved PostgreSQL "
        "demo container..."
    )

    runDocker(
        "stop",
        DATABASE_CONTAINER,
    )

    deadline = (
        time.time()
        + 15
    )

    while (
        time.time()
        < deadline
    ):
        state = (
            environment.getState()
        )

        if (
            not state.get(
                "databaseRunning"
            )
            and not state.get(
                "apiHealthy"
            )
            and not state.get(
                "connectionPoolHealthy"
            )
        ):
            print()
            print(
                state
            )

            passed(
                "PostgreSQL outage injected"
            )

            passed(
                "API degradation detected"
            )

            passed(
                "Database connectivity failure detected"
            )

            return state

        time.sleep(1)

    failed(
        "Outage was injected but expected "
        "failure state was not observed."
    )

    print(
        environment.getState()
    )

    raise SystemExit(1)


# ============================================================
# SUMMARY
# ============================================================

def printSummary(
    ticketId,
    ticket,
    failedState,
):
    heading(
        "ReSolve Demo Ready"
    )

    print()
    print(
        "Freshservice"
    )

    print(
        f"  Ticket:    #{ticketId}"
    )

    print(
        f"  Subject:   "
        f"{ticket.get('subject')}"
    )

    print(
        "  Status:    OPEN"
    )

    print(
        "  Priority:  URGENT"
    )

    print()
    print(
        "Demo Infrastructure"
    )

    print(
        "  Backend API:  "
        + (
            "RUNNING"
            if failedState.get(
                "backendRunning"
            )
            else "DOWN"
        )
    )

    print(
        "  PostgreSQL:   "
        + (
            "RUNNING"
            if failedState.get(
                "databaseRunning"
            )
            else "DOWN"
        )
    )

    print(
        "  API Health:   "
        + (
            "HEALTHY"
            if failedState.get(
                "apiHealthy"
            )
            else "DEGRADED"
        )
    )

    print(
        "  DB Connection:"
        + (
            " HEALTHY"
            if failedState.get(
                "connectionPoolHealthy"
            )
            else " FAILED"
        )
    )

    print()
    print("-" * 76)

    print(
        "Run the recovery demo:"
    )

    print()

    print(
        "  python -m "
        "backend.run_freshservice_docker_demo "
        f"{ticketId}"
    )

    print()
    print("-" * 76)

    print(
        "Expected recovery flow:"
    )

    print()

    print(
        "  Freshservice incident"
    )

    print(
        "      -> trusted recovery evidence"
    )

    print(
        "      -> AI strategy reasoning"
    )

    print(
        "      -> human approval"
    )

    print(
        "      -> controlled Docker capability"
    )

    print(
        "      -> independent verification"
    )

    print(
        "      -> Freshservice Resolved"
    )

    print()


# ============================================================
# MAIN
# ============================================================

def main():
    heading(
        "ReSolve — Demo Preparation"
    )

    checkConfiguration()

    startDemoEnvironment()

    environment = (
        waitForHealthyEnvironment()
    )

    section(
        "FRESHSERVICE"
    )

    ticketService = (
        FreshserviceTicketService()
    )

    requesterId = (
        getRequesterId(
            ticketService
        )
    )

    ticketId = (
        createDemoTicket(
            ticketService,
            requesterId,
        )
    )

    makeTicketUrgent(
        ticketService,
        ticketId,
    )

    ticket = (
        verifyFreshserviceTicket(
            ticketService,
            ticketId,
        )
    )

    failedState = (
        injectDatabaseOutage(
            environment
        )
    )

    printSummary(
        ticketId,
        ticket,
        failedState,
    )


if __name__ == "__main__":
    main()
