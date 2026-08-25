from backend.freshservice_ticket_service import (
    FreshserviceTicketService,
)


class FreshserviceRecoveryService:
    """
    Connects ReSolve recovery lifecycle events to Freshservice.

    Responsibilities:

        - record recovery start
        - record selected strategy
        - record evidence provenance
        - record LLM reasoning summary
        - record approval boundaries
        - record execution + verification results
        - resolve verified incidents
        - escalate unrecovered incidents
    """

    def __init__(
        self,
        ticketService=None,
    ):
        self.ticketService = (
            ticketService
            or FreshserviceTicketService()
        )

    # ==================================================
    # HELPERS
    # ==================================================

    def _formatFloat(
        self,
        value,
        default="Unknown",
    ):
        try:
            return f"{float(value):.2f}"

        except (
            TypeError,
            ValueError,
        ):
            return default

    def _formatSuccessRate(
        self,
        strategy,
    ):
        successRate = strategy.get(
            "successRate"
        )

        if successRate is None:
            return (
                "Not available "
                "(no historical outcome data)"
            )

        return self._formatFloat(
            successRate
        )

    def _formatEvidenceSource(
        self,
        strategy,
    ):
        sourceType = strategy.get(
            "sourceType",
            "historical-incident",
        )

        if (
            sourceType
            == "approved-runbook"
        ):
            return (
                "Approved recovery runbook"
            )

        if (
            sourceType
            == "historical-incident"
        ):
            return (
                "Historical resolved incident"
            )

        return str(
            sourceType
        )

    def _getReasoning(
        self,
        strategy,
    ):
        reasoning = strategy.get(
            "llmReasoning"
        )

        if isinstance(
            reasoning,
            dict,
        ):
            return reasoning

        return None

    # ==================================================
    # RECOVERY START
    # ==================================================

    def recordRecoveryStarted(
        self,
        ticketId,
        incident,
        errorSignature,
    ):
        body = (
            "ReSolve automated recovery started.\n\n"
            f"Incident: "
            f"{incident.get('title', '')}\n"
            f"Error Signature: "
            f"{errorSignature}\n"
            f"Severity: "
            f"{incident.get('severity', 'unknown')}\n\n"
            "ReSolve is evaluating trusted historical "
            "recovery evidence and approved recovery "
            "runbooks. Recovery remains subject to "
            "risk controls, approval boundaries, "
            "controlled execution, and independent "
            "post-recovery verification."
        )

        return self.ticketService.addNote(
            ticketId,
            body,
        )

    # ==================================================
    # STRATEGY SELECTED
    # ==================================================

    def recordStrategySelected(
        self,
        ticketId,
        strategy,
    ):
        evidenceSource = (
            self._formatEvidenceSource(
                strategy
            )
        )

        successRate = (
            self._formatSuccessRate(
                strategy
            )
        )

        similarity = (
            self._formatFloat(
                strategy.get(
                    "similarity"
                )
            )
        )

        body = (
            "ReSolve selected a recovery strategy.\n\n"
            f"Action: "
            f"{strategy.get('action', '')}\n"
            f"Evidence Source: "
            f"{evidenceSource}\n"
            f"Evidence ID: "
            f"{strategy.get('incidentId', '')}\n"
            f"Risk Tier: "
            f"{strategy.get('riskTier', '')}\n"
            f"Evidence Match Score: "
            f"{similarity}\n"
            f"Historical Success Rate: "
            f"{successRate}\n"
            f"Decision Source: "
            f"{strategy.get('decisionSource', 'deterministic')}\n"
        )

        sourceType = strategy.get(
            "sourceType"
        )

        if (
            sourceType
            == "approved-runbook"
        ):
            body += (
                "\nThis strategy comes from an approved "
                "recovery runbook. ReSolve does not "
                "fabricate historical success statistics "
                "when outcome data is unavailable.\n"
            )

        elif strategy.get(
            "successRateIsConditioned"
        ):
            body += (
                "\nHistorical success rate is conditioned "
                "on the current error signature.\n"
            )

        else:
            body += (
                "\nHistorical success rate is based on "
                "overall recorded recovery outcomes.\n"
            )

        reasoning = (
            self._getReasoning(
                strategy
            )
        )

        if reasoning:
            body += (
                "\nAI Reasoning Summary:\n"
                f"{reasoning.get('reasoning', '')}\n"
                f"Confidence: "
                f"{self._formatFloat(reasoning.get('confidence'))}\n"
            )

        return self.ticketService.addNote(
            ticketId,
            body,
        )

    # ==================================================
    # APPROVAL REQUIRED
    # ==================================================

    def recordApprovalRequired(
        self,
        ticketId,
        strategy,
    ):
        evidenceSource = (
            self._formatEvidenceSource(
                strategy
            )
        )

        body = (
            "Human approval required before execution.\n\n"
            f"Proposed Action: "
            f"{strategy.get('action', '')}\n"
            f"Risk Tier: "
            f"{strategy.get('riskTier', '')}\n"
            f"Evidence Source: "
            f"{evidenceSource}\n\n"
        )

        reasoning = (
            self._getReasoning(
                strategy
            )
        )

        if reasoning:
            body += (
                "Reasoning:\n"
                f"{reasoning.get('reasoning', '')}\n\n"
                "Risk Notes:\n"
                f"{reasoning.get('riskNotes', '')}\n\n"
            )

        body += (
            "Recovery is paused until an authorized "
            "human approves or rejects this strategy. "
            "No infrastructure mutation occurs before "
            "approval."
        )

        return self.ticketService.addNote(
            ticketId,
            body,
        )

    # ==================================================
    # ACTION RESULT
    # ==================================================

    def recordActionResult(
        self,
        ticketId,
        action,
        result,
        verification=None,
    ):
        body = (
            "Recovery action completed.\n\n"
            f"Action: {action}\n"
            f"Execution Result: {result}\n"
        )

        if verification:
            body += (
                "\nIndependent Verification Status: "
                f"{verification.get('status')}\n"
            )

            for check in verification.get(
                "checks",
                [],
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

            if not verification.get(
                "recovered",
                False,
            ):
                body += (
                    "\nExecution completed, but ReSolve "
                    "does not consider the incident "
                    "recovered because one or more "
                    "required post-conditions failed."
                )

        return self.ticketService.addNote(
            ticketId,
            body,
        )

    # ==================================================
    # TICKET UPDATE DURING RECOVERY
    # ==================================================

    def updateTicketDuringRecovery(
        self,
        ticketId,
        ticketFields,
    ):
        return self.ticketService.updateTicket(
            ticketId,
            ticketFields,
        )

    # ==================================================
    # RECOVERY SUCCESS
    # ==================================================

    def recordRecoverySuccess(
        self,
        ticketId,
        result,
    ):
        body = (
            "ReSolve recovery completed successfully.\n\n"
            f"Error Signature: "
            f"{result.get('errorSignature', '')}\n"
            f"Recovery Attempts: "
            f"{result.get('recoveryAttempts', 0)}\n\n"
            "Independent post-recovery verification "
            "passed. The incident is being resolved "
            "only after the expected system state was "
            "confirmed."
        )

        noteResult = (
            self.ticketService.addNote(
                ticketId,
                body,
            )
        )

        resolveResult = (
            self.ticketService.resolveTicket(
                ticketId
            )
        )

        return {
            "note": noteResult,
            "ticketUpdate": (
                resolveResult
            ),
        }

    # ==================================================
    # RECOVERY FAILURE
    # ==================================================

    def recordRecoveryFailure(
        self,
        ticketId,
        result,
        incident=None,
    ):
        body = (
            "ReSolve automated recovery could not "
            "restore the incident.\n\n"
        )

        if incident:
            body += (
                f"Incident: "
                f"{incident.get('title', '')}\n"
            )

        body += (
            f"Error Signature: "
            f"{result.get('errorSignature', '')}\n"
            f"Recovery Attempts: "
            f"{result.get('recoveryAttempts', 0)}\n"
            f"Reason: "
            f"{result.get('reason', 'Unknown')}\n\n"
            "ReSolve has stopped autonomous recovery. "
            "Human investigation is required."
        )

        return self.ticketService.addNote(
            ticketId,
            body,
        )

    # ==================================================
    # ESCALATE EXISTING TICKET
    # ==================================================

    def escalateTicket(
        self,
        ticketId,
        reason,
        priority=4,
    ):
        noteBody = (
            "ReSolve escalation required.\n\n"
            f"Reason: {reason}\n"
            f"Escalation Priority: {priority}\n\n"
            "Automated recovery was unable to safely "
            "restore the service. Human intervention "
            "is now required."
        )

        noteResult = (
            self.ticketService.addNote(
                ticketId,
                noteBody,
            )
        )

        updateResult = (
            self.ticketService.updateTicket(
                ticketId,
                {
                    "priority": priority,
                },
            )
        )

        return {
            "note": noteResult,
            "ticketUpdate": updateResult,
        }

    # ==================================================
    # CREATE ESCALATION TICKET
    # ==================================================

    def createEscalationTicket(
        self,
        originalTicketId,
        incident,
        result,
        priority=4,
    ):
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
            status=2,
        )

    # ==================================================
    # COMPLETE FAILURE + ESCALATION
    # ==================================================

    def handleRecoveryFailure(
        self,
        ticketId,
        incident,
        result,
        createEscalationTicket=False,
    ):
        """
        Complete failure handling:

            1. Record recovery failure.
            2. Escalate the existing ticket priority.
            3. Optionally create a separate escalation ticket.
        """

        failureNote = (
            self.recordRecoveryFailure(
                ticketId=ticketId,
                result=result,
                incident=incident,
            )
        )

        escalationResult = (
            self.updateTicketDuringRecovery(
                ticketId,
                {
                    "priority": 4,
                },
            )
        )

        newTicketResult = None

        if createEscalationTicket:
            newTicketResult = (
                self.createEscalationTicket(
                    ticketId,
                    incident,
                    result,
                )
            )

        return {
            "failureNote": failureNote,
            "escalation": escalationResult,
            "newEscalationTicket": (
                newTicketResult
            ),
        }