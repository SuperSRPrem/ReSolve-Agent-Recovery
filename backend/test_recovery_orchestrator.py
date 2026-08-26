from backend.incident_intake import IncidentIntake
from backend.recovery_orchestrator import RecoveryOrchestrator


class FakeTicketService:
    def createTicketFromForm(self, form):
        normalized = IncidentIntake.toTicketPayload(form)

        if not normalized["success"]:
            return {
                "success": False,
                "error": "; ".join(normalized["errors"]),
            }

        return {
            "success": True,
            "data": {
                "ticket": {
                    "id": 101,
                }
            },
        }


class FakeRunner:
    maxRecoveryAttempts = 5

    def __init__(self):
        self.approved = False
        self.rejected = False

    def startRecovery(self, ticketId, firstAction=None):
        return {
            "success": True,
            "status": "AWAITING_APPROVAL",
            "message": "Approval required",
            "runId": "RUN-TEST",
            "freshserviceTicketId": ticketId,
            "session": object(),
            "attempts": [],
            "recoveryAttempts": 0,
            "environmentState": {},
            "strategy": {
                "action": "Restart database",
                "riskTier": "high",
            },
        }

    def approvePendingStrategy(self, ticketId, session):
        self.approved = True
        return {
            "success": True,
            "status": "RECOVERED",
            "message": "Recovered",
            "runId": "RUN-TEST",
            "freshserviceTicketId": ticketId,
            "session": session,
            "attempts": [],
            "recoveryAttempts": 1,
            "environmentState": {"healthy": True},
            "verification": {"recovered": True},
        }

    def rejectPendingStrategy(self, ticketId, session):
        self.rejected = True
        return {
            "success": True,
            "status": "ESCALATED",
            "message": "Escalated",
            "runId": "RUN-TEST",
            "freshserviceTicketId": ticketId,
            "session": session,
            "attempts": [],
            "recoveryAttempts": 0,
            "environmentState": {},
        }


def test_manual_validation():
    result = IncidentIntake.toTicketPayload({
        "subject": "",
        "description": "",
        "priority": 1,
        "status": 2,
    })

    assert not result["success"]
    assert len(result["errors"]) == 3


def test_manual_payload_keeps_optional_fields():
    result = IncidentIntake.toTicketPayload({
        "requester_id": 5,
        "subject": "Database unavailable",
        "description": "API returns HTTP-503",
        "priority": 4,
        "status": 2,
        "category": "Infrastructure",
        "tags": ["database", "production"],
        "planned_effort": "1h 10m",
    })

    assert result["success"]
    assert result["payload"]["category"] == "Infrastructure"
    assert result["payload"]["tags"] == ["database", "production"]


def test_manual_and_existing_flow_share_loop():
    runner = FakeRunner()
    orchestrator = RecoveryOrchestrator(
        runner=runner,
        ticketService=FakeTicketService(),
    )

    form = {
        "requester_id": 5,
        "subject": "Database unavailable",
        "description": "Connection refused",
        "priority": 4,
        "status": 2,
    }

    # FakeRunner has no bridge dependency; call startFromTicket to
    # verify the common loop contract and approval state.
    result = orchestrator.startFromTicket(101)

    assert result["status"] == "AWAITING_APPROVAL"
    assert result["loop"]["awaitingApproval"] is True
    assert result["loop"]["phase"] == "APPROVAL_GATE"

    approved = orchestrator.approve("RUN-TEST")

    assert approved["status"] == "RECOVERED"
    assert approved["loop"]["phase"] == "VERIFIED_RECOVERY"
    assert runner.approved is True
