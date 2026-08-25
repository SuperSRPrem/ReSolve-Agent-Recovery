from backend.demo_agent import DemoAgent

from backend.freshservice_recovery_bridge import (
    FreshserviceRecoveryBridge,
)

from backend.freshservice_recovery_service import (
    FreshserviceRecoveryService,
)

from backend.mock_environment import (
    MockEnvironment,
)

from backend.reasoned_recovery_memory import (
    ReasonedRecoveryMemory,
)


class FreshserviceRecoveryRunner:
    """
    Connects a Freshservice ticket to the complete ReSolve
    recovery pipeline.

    Flow:

        Freshservice Ticket
                ↓
        FreshserviceRecoveryBridge
                ↓
        Structured ReSolve Incident
                ↓
        RecoveryMemory
             +
        Approved Runbooks
                ↓
        LLMReasoner
                ↓
        Trusted Recovery Strategy
                ↓
        Risk / Approval Boundary
                ↓
        RecoveryEnvironment
                ↓
        VerificationEngine
                ↓
        Freshservice Notes / Resolution / Escalation

    The LLM has no direct execution authority.

    It may only select from trusted strategies supplied by
    historical recovery memory and approved runbooks.
    """

    def __init__(
        self,
        bridge=None,
        environment=None,
        recoveryService=None,
        maxRecoveryAttempts=5,
        reasoner=None,
        runbookStore=None,
    ):
        self.bridge = (
            bridge
            or FreshserviceRecoveryBridge()
        )

        # Safe default remains MockEnvironment.
        #
        # The real demo can explicitly inject
        # DockerEnvironment.
        self.environment = (
            environment
            or MockEnvironment()
        )

        self.recoveryService = (
            recoveryService
            or FreshserviceRecoveryService()
        )

        self.maxRecoveryAttempts = (
            maxRecoveryAttempts
        )

        self.reasoner = reasoner
        self.runbookStore = runbookStore

        # Keep the same configured agent alive while a ticket
        # is paused for approval.
        self.activeAgents = {}

    # ==================================================
    # ACTIVE AGENT MANAGEMENT
    # ==================================================

    def _ticketKey(
        self,
        ticketId,
    ):
        return str(
            ticketId
        )

    def _storeAgent(
        self,
        ticketId,
        agent,
    ):
        self.activeAgents[
            self._ticketKey(
                ticketId
            )
        ] = agent

    def _getStoredAgent(
        self,
        ticketId,
    ):
        return self.activeAgents.get(
            self._ticketKey(
                ticketId
            )
        )

    def _removeStoredAgent(
        self,
        ticketId,
    ):
        self.activeAgents.pop(
            self._ticketKey(
                ticketId
            ),
            None,
        )

    def _trackResult(
        self,
        ticketId,
        agent,
        result,
    ):
        """
        Retain the agent while recovery is paused.

        Remove it after terminal states.
        """

        status = result.get(
            "status"
        )

        if status in {
            "RECOVERED",
            "ESCALATED",
        }:
            self._removeStoredAgent(
                ticketId
            )

        else:
            self._storeAgent(
                ticketId,
                agent,
            )

        return result

    # ==================================================
    # FRESHSERVICE LIFECYCLE HOOKS
    # ==================================================

    def _createHooks(
        self,
        ticketId,
    ):
        """
        Connects DemoAgent lifecycle events to Freshservice
        while keeping DemoAgent independent of Freshservice.
        """

        def onRecoveryStarted(
            session,
        ):
            self.recoveryService.recordRecoveryStarted(
                ticketId=ticketId,
                incident=session.incident,
                errorSignature=session.errorSignature,
            )

        def onStrategySelected(
            session,
            strategy,
        ):
            self.recoveryService.recordStrategySelected(
                ticketId=ticketId,
                strategy=strategy,
            )

        def onApprovalRequired(
            session,
            strategy,
        ):
            self.recoveryService.recordApprovalRequired(
                ticketId=ticketId,
                strategy=strategy,
            )

        def onActionResult(
            session,
            action,
            result,
            verification,
        ):
            self.recoveryService.recordActionResult(
                ticketId=ticketId,
                action=action,
                result=result,
                verification=verification,
            )

        def onRecoverySuccess(
            session,
            result,
        ):
            self.recoveryService.recordRecoverySuccess(
                ticketId=ticketId,
                result=result,
            )

        def onRecoveryFailure(
            session,
            result,
        ):
            self.recoveryService.handleRecoveryFailure(
                ticketId=ticketId,
                incident=session.incident,
                result=result,
                createEscalationTicket=False,
            )

        return {
            "onRecoveryStarted": (
                onRecoveryStarted
            ),
            "onStrategySelected": (
                onStrategySelected
            ),
            "onApprovalRequired": (
                onApprovalRequired
            ),
            "onActionResult": (
                onActionResult
            ),
            "onRecoverySuccess": (
                onRecoverySuccess
            ),
            "onRecoveryFailure": (
                onRecoveryFailure
            ),
        }

    # ==================================================
    # CREATE RECOVERY AGENT
    # ==================================================

    def _createAgent(
        self,
        ticketId,
    ):
        """
        Creates a DemoAgent using the complete hybrid
        ReSolve reasoning pipeline.
        """

        hooks = self._createHooks(
            ticketId
        )

        agent = DemoAgent(
            environment=self.environment,
            maxRecoveryAttempts=(
                self.maxRecoveryAttempts
            ),
            hooks=hooks,
        )

        # DemoAgent already creates the real historical
        # RecoveryMemory. Reuse that exact instance.
        historicalMemory = (
            agent.memory
        )

        # Wrap historical memory with:
        #
        # historical evidence
        # +
        # approved runbooks
        # +
        # LLM reasoning
        agent.memory = (
            ReasonedRecoveryMemory(
                baseMemory=historicalMemory,
                reasoner=self.reasoner,
                environment=self.environment,
                runbookStore=(
                    self.runbookStore
                ),
            )
        )

        return agent

    def _getOrCreateAgent(
        self,
        ticketId,
    ):
        agent = self._getStoredAgent(
            ticketId
        )

        if agent is not None:
            return agent

        return self._createAgent(
            ticketId
        )

    # ==================================================
    # START RECOVERY
    # ==================================================

    def startRecovery(
        self,
        ticketId,
        firstAction,
    ):
        """
        Loads a Freshservice incident and begins the
        ReSolve recovery workflow.
        """

        bridgeResult = (
            self.bridge.loadIncident(
                ticketId
            )
        )

        if not bridgeResult.get(
            "success",
            False,
        ):
            return {
                "success": False,
                "status": "LOAD_FAILED",
                "message": (
                    "Unable to load Freshservice "
                    "ticket into ReSolve."
                ),
                "ticketId": ticketId,
                "error": bridgeResult.get(
                    "error"
                ),
                "bridgeResult": (
                    bridgeResult
                ),
            }

        incident = bridgeResult[
            "incident"
        ]

        agent = self._createAgent(
            ticketId
        )

        self._storeAgent(
            ticketId,
            agent,
        )

        recoveryResult = (
            agent.startRecovery(
                incident,
                firstAction,
            )
        )

        recoveryResult[
            "freshserviceTicketId"
        ] = ticketId

        recoveryResult[
            "incident"
        ] = incident

        recoveryResult[
            "bridgeResult"
        ] = {
            "conversationCount": len(
                bridgeResult.get(
                    "conversations",
                    [],
                )
            )
        }

        return self._trackResult(
            ticketId,
            agent,
            recoveryResult,
        )

    # ==================================================
    # APPROVE PENDING STRATEGY
    # ==================================================

    def approvePendingStrategy(
        self,
        ticketId,
        session,
    ):
        """
        Continues a paused recovery after human approval.

        The same configured hybrid reasoning agent is reused
        when available.
        """

        agent = self._getOrCreateAgent(
            ticketId
        )

        recoveryResult = (
            agent.approvePendingStrategy(
                session
            )
        )

        recoveryResult[
            "freshserviceTicketId"
        ] = ticketId

        return self._trackResult(
            ticketId,
            agent,
            recoveryResult,
        )

    # ==================================================
    # REJECT PENDING STRATEGY
    # ==================================================

    def rejectPendingStrategy(
        self,
        ticketId,
        session,
    ):
        """
        Continues recovery after a human rejects the
        current pending strategy.
        """

        agent = self._getOrCreateAgent(
            ticketId
        )

        recoveryResult = (
            agent.rejectPendingStrategy(
                session
            )
        )

        recoveryResult[
            "freshserviceTicketId"
        ] = ticketId

        return self._trackResult(
            ticketId,
            agent,
            recoveryResult,
        )