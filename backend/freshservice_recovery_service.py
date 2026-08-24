from backend.freshservice_ticket_service import (
    FreshserviceTicketService
)


class FreshserviceRecoveryService:
    """
    Connects ReSolve recovery events with Freshservice.

    Responsibilities:

        - add live recovery notes
        - record approval requests
        - record successful recovery
        - resolve recovered incidents
        - escalate unrecovered incidents
    """

    def __init__(
        self,
        ticketService=None
    ):

        self.ticketService = (
            ticketService
            or FreshserviceTicketService()
        )

    # ==================================================
    # RECOVERY START
    # ==================================================

    def recordRecoveryStarted(
        self,
        ticketId,
        incident,
        errorSignature
    ):

        body = (
            "ReSolve automated recovery started.\n\n"
            f"Incident: {incident.get('title', '')}\n"
            f"Error Signature: {errorSignature}\n"
            f"Severity: {incident.get('severity', 'unknown')}\n\n"
            "The system is now evaluating historical recovery "
            "strategies and executing only actions allowed by "
            "the policy-controlled action layer."
        )

        return self.ticketService.addNote(
            ticketId,
            body
        )

    # ==================================================
    # STRATEGY SELECTED
    # ==================================================

    def recordStrategySelected(
        self,
        ticketId,
        strategy
    ):

        body = (
            "ReSolve selected a recovery strategy.\n\n"
            f"Action: {strategy.get('action', '')}\n"
            f"Risk Tier: {strategy.get('riskTier', '')}\n"
            f"Similarity: "
            f"{strategy.get('similarity', 0):.2f}\n"
            f"Historical Success Rate: "
            f"{strategy.get('successRate', 0):.2f}\n"
        )

        if strategy.get(
            "successRateIsConditioned"
        ):

            body += (
                "\nSuccess rate is conditioned on "
                "the current error signature."
            )

        else:

            body += (
                "\nSuccess rate is based on overall "
                "historical resolution outcomes."
            )

        return self.ticketService.addNote(
            ticketId,
            body
        )

    # ==================================================
    # APPROVAL REQUIRED
    # ==================================================

    def recordApprovalRequired(
        self,
        ticketId,
        strategy
    ):

        body = (
            "Human approval required before execution.\n\n"
            f"Proposed Action: "
            f"{strategy.get('action', '')}\n"
            f"Risk Tier: "
            f"{strategy.get('riskTier', '')}\n\n"
            "Recovery is paused until an authorized "
            "human approves or rejects this strategy."
        )

        return self.ticketService.addNote(
            ticketId,
            body
        )

    # ==================================================
    # ACTION RESULT
    # ==================================================

    def recordActionResult(
        self,
        ticketId,
        action,
        result,
        verification=None
    ):

        body = (
            "Recovery action completed.\n\n"
            f"Action: {action}\n"
            f"Result: {result}\n"
        )

        if verification:

            body += (
                "\nVerification Status: "
                f"{verification.get('status')}\n"
            )

            for check in verification.get(
                "checks",
                []
            ):

                status = (
                    "PASS"
                    if check.get("passed")
                    else "FAIL"
                )

                body += (
                    f"- {check.get('name')}: "
                    f"{status}\n"
                )

        return self.ticketService.addNote(
            ticketId,
            body
        )

    # ==================================================
    # RECOVERY SUCCESS
    # ==================================================

    def recordRecoverySuccess(
        self,
        ticketId,
        result
    ):

        body = (
            "ReSolve recovery completed successfully.\n\n"
            f"Error Signature: "
            f"{result.get('errorSignature', '')}\n"
            f"Recovery Attempts: "
            f"{result.get('recoveryAttempts', 0)}\n\n"
            "Post-recovery verification passed."
        )

        noteResult = self.ticketService.addNote(
            ticketId,
            body
        )

        resolveResult = self.ticketService.resolveTicket(
            ticketId
        )

        return {
            "note": noteResult,
            "ticketUpdate": resolveResult
        }

    # ==================================================
    # RECOVERY FAILURE / ESCALATION
    # ==================================================

    def recordRecoveryFailure(
        self,
        ticketId,
        result
    ):

        body = (
            "ReSolve automated recovery could not restore "
            "the incident.\n\n"
            f"Error Signature: "
            f"{result.get('errorSignature', '')}\n"
            f"Recovery Attempts: "
            f"{result.get('recoveryAttempts', 0)}\n\n"
            f"Reason: "
            f"{result.get('reason', 'Unknown')}\n\n"
            "Human investigation is required."
        )

        return self.ticketService.addNote(
            ticketId,
            body
        )