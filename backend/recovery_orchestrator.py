from backend.freshservice_ticket_service import FreshserviceTicketService
from backend.freshservice_recovery_runner import FreshserviceRecoveryRunner
from backend.freshservice_recovery_bridge import FreshserviceRecoveryBridge
from backend.incident_intake import IncidentIntake


class RecoveryOrchestrator:
    """
    Application-facing coordinator for the two entry paths:

    1. manual intake -> Freshservice ticket -> ReSolve recovery
    2. existing Freshservice ticket number -> ReSolve recovery

    Both paths converge into exactly the same recovery runner.
    """

    TERMINAL = {"RECOVERED", "ESCALATED"}

    def __init__(
        self,
        runner=None,
        ticketService=None,
        bridge=None,
    ):
        self.ticketService = ticketService or FreshserviceTicketService()
        self.bridge = bridge or FreshserviceRecoveryBridge(
            ticketService=self.ticketService
        )
        self.runner = runner or FreshserviceRecoveryRunner(
            bridge=self.bridge
        )

        self.sessions = {}
        self.latestResults = {}

    def _remember(self, result):
        run_id = result.get("runId")

        if run_id:
            self.sessions[run_id] = {
                "ticketId": result.get("freshserviceTicketId"),
                "session": result.get("session"),
            }

            self.latestResults[run_id] = result

            if result.get("status") in self.TERMINAL:
                # Keep the result for the UI/audit view. The live
                # agent itself is already released by the runner.
                pass

        return self._public(result)

    def _public(self, result):
        """
        Return a UI/API-safe state object without exposing the live
        Python session object itself.
        """

        state = dict(result)
        state.pop("session", None)

        attempts = state.get("attempts", [])

        state["loop"] = {
            "runId": state.get("runId"),
            "status": state.get("status"),
            "phase": self._phase(state),
            "awaitingApproval": (
                state.get("status") == "AWAITING_APPROVAL"
            ),
            "pendingStrategy": (
                state.get("strategy")
                if state.get("status") == "AWAITING_APPROVAL"
                else None
            ),
            "attempts": attempts,
            "recoveryAttempts": state.get("recoveryAttempts", 0),
            "maxAttempts": self.runner.maxRecoveryAttempts,
            "environmentState": state.get("environmentState"),
            "verification": state.get("verification"),
            "reason": state.get("reason"),
        }

        return state

    @staticmethod
    def _phase(result):
        status = result.get("status")

        return {
            "AWAITING_APPROVAL": "APPROVAL_GATE",
            "RECOVERED": "VERIFIED_RECOVERY",
            "ESCALATED": "ESCALATION",
            "LOAD_FAILED": "LOAD_FAILED",
        }.get(status, "RECOVERY")

    def startFromTicket(self, ticketId):
        result = self.runner.startRecovery(
            ticketId=ticketId,
            firstAction=None,
        )
        return self._remember(result)

    def startFromManualForm(self, form):
        created = self.ticketService.createTicketFromForm(form)

        if not created.get("success"):
            return {
                "success": False,
                "status": "TICKET_CREATE_FAILED",
                "message": "Freshservice ticket could not be created.",
                "ticketResult": created,
            }

        data = created.get("data") or {}
        ticket = data.get("ticket", data)

        ticket_id = ticket.get("id") or ticket.get("display_id")

        if ticket_id is None:
            return {
                "success": False,
                "status": "TICKET_ID_MISSING",
                "message": (
                    "Freshservice accepted the create request but "
                    "the MCP response did not expose a ticket ID."
                ),
                "ticketResult": created,
            }

        # Fetching through the bridge guarantees that manual and
        # existing-ticket flows use the same mapping and recovery path.
        result = self.runner.startRecovery(
            ticketId=ticket_id,
            firstAction=None,
        )
        result["manualTicketCreate"] = created
        return self._remember(result)

    def getRunState(self, runId):
        result = self.latestResults.get(runId)

        if result is None:
            return {
                "success": False,
                "status": "RUN_NOT_FOUND",
                "message": "No active or recorded ReSolve run was found.",
            }

        return self._public(result)

    def approve(self, runId):
        stored = self.sessions.get(runId)

        if not stored or stored.get("session") is None:
            return {
                "success": False,
                "status": "RUN_NOT_FOUND",
                "message": "The requested recovery session is unavailable.",
            }

        result = self.runner.approvePendingStrategy(
            ticketId=stored["ticketId"],
            session=stored["session"],
        )
        return self._remember(result)

    def reject(self, runId):
        stored = self.sessions.get(runId)

        if not stored or stored.get("session") is None:
            return {
                "success": False,
                "status": "RUN_NOT_FOUND",
                "message": "The requested recovery session is unavailable.",
            }

        result = self.runner.rejectPendingStrategy(
            ticketId=stored["ticketId"],
            session=stored["session"],
        )
        return self._remember(result)
