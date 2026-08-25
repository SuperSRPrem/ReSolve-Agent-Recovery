from functools import lru_cache


@lru_cache(maxsize=1)
def get_demo_agent():
    from backend.demo_agent import DemoAgent

    return DemoAgent()


@lru_cache(maxsize=1)
def get_freshservice_runner():
    from backend.freshservice_recovery_runner import (
        FreshserviceRecoveryRunner,
    )

    return FreshserviceRecoveryRunner()


def build_incident(
    title,
    service,
    environment,
    severity,
    symptoms,
    error_codes,
    api_latency,
    database_cpu,
    change_type,
    change_description,
    change_minutes,
):
    return {
        "title": title,
        "service": service,
        "environment": environment,
        "severity": severity,
        "symptoms": [
            item.strip()
            for item in symptoms.splitlines()
            if item.strip()
        ],
        "errorCodes": [
            item.strip()
            for item in error_codes.splitlines()
            if item.strip()
        ],
        "metrics": {
            "apiLatencyMs": api_latency,
            "databaseCpuPercent": database_cpu,
        },
        "recentChange": {
            "type": change_type,
            "description": change_description,
            "minutesBeforeIncident": change_minutes,
        },
        "actionsTried": [],
    }


def run_local_recovery(
    incident,
    first_action,
    retry_result,
):
    """
    Preserves the original demo mode.

    Useful for testing ReSolve without Freshservice.
    """

    agent = get_demo_agent()

    return agent.runIncident(
        incident,
        first_action,
        retry_result,
    )


def start_freshservice_recovery(
    ticket_id,
    first_action,
):
    """
    Uses the actual Freshservice recovery pipeline.

    Freshservice
        -> Bridge
        -> Incident mapping
        -> ReSolve recovery
        -> lifecycle hooks
    """

    runner = get_freshservice_runner()

    return runner.startRecovery(
        ticket_id,
        first_action,
    )


def approve_strategy(
    ticket_id,
    session,
):
    runner = get_freshservice_runner()

    return runner.approvePendingStrategy(
        ticket_id,
        session,
    )


def reject_strategy(
    ticket_id,
    session,
):
    runner = get_freshservice_runner()

    return runner.rejectPendingStrategy(
        ticket_id,
        session,
    )