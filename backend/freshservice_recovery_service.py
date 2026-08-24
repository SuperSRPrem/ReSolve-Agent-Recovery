from backend.freshservice_ticket_service import (
    FreshserviceTicketService
)


class FreshserviceRecoveryService:
    """
    Connects ReSolve recovery events with Freshservice.

    Responsibilities:

        - add live recovery notes
        - record strategy selection
        - record approval requests
        - record action results
        - update tickets during recovery
        - resolve recovered incidents
        - escalate unrecovered incidents
        - optionally create a separate escalation ticket
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
    # TICKET UPDATE DURING RECOVERY
    # ==================================================

    def updateTicketDuringRecovery(
        self,
        ticketId,
        ticketFields
    ):
        """
        Updates Freshservice ticket fields while
        automated recovery is still in progress.

        Example:

            updateTicketDuringRecovery(
                ticketId=4,
                ticketFields={
                    "priority": 4
                }
            )
        """

        return self.ticketService.updateTicket(
            ticketId,
            ticketFields
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
    # RECOVERY FAILURE
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

    # ==================================================
    # ESCALATE EXISTING TICKET
    # ==================================================

    def escalateTicket(
        self,
        ticketId,
        reason,
        priority=4
    ):
        """
        Escalates the existing Freshservice ticket.

        The ticket is kept open, while its priority
        can be increased.

        A recovery failure note is also added.
        """

        noteBody = (
            "ReSolve escalation required.\n\n"
            f"Reason: {reason}\n"
            f"Escalation Priority: {priority}\n\n"
            "Automated recovery was unable to safely "
            "restore the service. Human intervention "
            "is now required."
        )

        noteResult = self.ticketService.addNote(
            ticketId,
            noteBody
        )

        updateResult = self.ticketService.updateTicket(
            ticketId,
            {
                "priority": priority
            }
        )

        return {
            "note": noteResult,
            "ticketUpdate": updateResult
        }

    # ==================================================
    # CREATE ESCALATION TICKET
    # ==================================================

    def createEscalationTicket(
        self,
        originalTicketId,
        incident,
        result,
        priority=4
    ):
        """
        Creates a separate Freshservice ticket when
        the existing incident needs to be escalated
        to another team or handled separately.
        """

        subject = (
            "[ESCALATION] "
            f"{incident.get('title', 'Recovery Failed')}"
        )

        description = (
            "ReSolve automated recovery failed and "
            "requires human investigation.\n\n"
            f"Original Freshservice Ticket: "
            f"{originalTicketId}\n"
            f"Incident ID: "
            f"{incident.get('incidentId', '')}\n"
            f"Error Signature: "
            f"{result.get('errorSignature', '')}\n"
            f"Recovery Attempts: "
            f"{result.get('recoveryAttempts', 0)}\n"
            f"Reason: "
            f"{result.get('reason', 'Unknown')}\n\n"
            "Please investigate the incident and "
            "continue recovery manually."
        )

        return self.ticketService.createTicket(
            subject=subject,
            description=description,
            source=2,
            priority=priority,
            status=2
        )

    # ==================================================
    # COMPLETE FAILURE + ESCALATION
    # ==================================================

    def handleRecoveryFailure(
        self,
        ticketId,
        incident,
        result,
        createEscalationTicket=False
    ):
        """
        Complete failure handling.

        Steps:

            1. Add recovery failure note.
            2. Escalate the existing ticket.
            3. Optionally create a separate escalation ticket.
        """

        reason = result.get(
            "reason",
            "Automated recovery failed."
        )

        failureNote = self.recordRecoveryFailure(
            ticketId,
            result
        )

        escalationResult = self.updateTicketDuringRecovery(
            ticketId,
            {
                "priority": 4
            }
        )

        newTicketResult = None

        if createEscalationTicket:

            newTicketResult = (
                self.createEscalationTicket(
                    ticketId,
                    incident,
                    result
                )
            )

        return {
            "failureNote": failureNote,
            "escalation": escalationResult,
            "newEscalationTicket": newTicketResult
        }