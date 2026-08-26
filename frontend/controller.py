from functools import lru_cache


@lru_cache(maxsize=1)
def get_demo_agent():
    from backend.demo_agent import DemoAgent
    return DemoAgent()


@lru_cache(maxsize=1)
def get_recovery_orchestrator():
    from backend.recovery_orchestrator import RecoveryOrchestrator
    return RecoveryOrchestrator()


def build_incident(title, service, environment, severity, symptoms, error_codes,
                   api_latency, database_cpu, change_type, change_description,
                   change_minutes):
    return {
        "title": title,
        "service": service,
        "environment": environment,
        "severity": severity,
        "symptoms": [item.strip() for item in symptoms.splitlines() if item.strip()],
        "errorCodes": [item.strip() for item in error_codes.splitlines() if item.strip()],
        "metrics": {"apiLatencyMs": api_latency, "databaseCpuPercent": database_cpu},
        "recentChange": {
            "type": change_type,
            "description": change_description,
            "minutesBeforeIncident": change_minutes,
        },
        "actionsTried": [],
    }


def run_local_recovery(incident, first_action, retry_result=None):
    return get_demo_agent().startRecovery(incident, first_action)


def start_ticket_recovery(ticket_id):
    return get_recovery_orchestrator().startFromTicket(ticket_id)


def start_manual_recovery(form):
    return get_recovery_orchestrator().startFromManualForm(form)


def approve_run(run_id):
    return get_recovery_orchestrator().approve(run_id)


def reject_run(run_id):
    return get_recovery_orchestrator().reject(run_id)
